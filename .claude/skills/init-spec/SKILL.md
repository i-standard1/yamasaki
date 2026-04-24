---
name: init-spec
description: |
  既存プロジェクトの初期セットアップ（初回のみ）。コードリポジトリを分析してCLAUDE.md、要件概要、
  基本設計書（アーキテクチャ、DB設計、API設計）、OpenAPI仕様、MkDocs設定を自動生成する。
  「このプロジェクトをセットアップして」「既存コードを分析して」「設計書を初期化して」
  「プロジェクトの構造を把握して」などのリクエストで使用する。
  既にドキュメントがある場合は移行モードで差分だけ補完する。
  ※ 既存Specの全更新・再生成には spec-all を使う。
context:
  required:
    - _shared/project-scale-thresholds.md
    - _shared/code-search-2stage.md
    - _shared/screen-transition-diagram.md
    - _shared/tech-stack-guide.md
---

# 既存プロジェクトの初期セットアップ

本スキルは**親=コード分析・方針・レビュー / spec-writer(Sonnet)=ドキュメント執筆 / integrity-checker=機械的整合性検査**の三者分担で進める。

## 規模による前処理判定

[プロジェクト規模の閾値定義](../_shared/project-scale-thresholds.md) の判定ロジックに従い、必要に応じて `analyze-codebase` スキルの実行を提案する。

---

## モード判定

まず以下をチェックし、モードを自動判定する：

- `docs/requirements/features/` にmdファイルが1つ以上ある → **移行モード**
- `CLAUDE.md` の「プロジェクト概要」にTODO/コメント以外の実際の記述がある → **移行モード**
- 上記いずれもない → **新規モード**

**判定の注意:** テンプレートのCLAUDE.mdには最初から `## プロジェクト概要` のヘッダーとTODOコメントがある。ヘッダーやHTMLコメント（`<!-- -->`）だけの場合は「記述なし」と判定すること。

判定結果をユーザーに提示して確認する：
「既存のドキュメントを検出しました。移行モードで差分のみ補完します。」
または「ドキュメントが見つかりません。新規セットアップを行います。」

---

## テンプレート参照

以下のテンプレートが存在する場合、生成する文書のセクション構成を合わせる：

| テンプレート | 用途 |
|------------|------|
| `docs/templates/phase2/system-architecture.md` | アーキテクチャ文書の構成 |
| `docs/templates/phase1/screen-flow.md` | 画面遷移図の構成 |
| `docs/templates/phase2/db-design.md` | DB設計書の構成 |
| `docs/templates/phase2/api-spec.md` | 外部連携仕様書の構成 |

テンプレートが存在しない場合は、従来の手順でそのまま生成する（テンプレート不在でブロックしない）。

---

## 新規モード

生成するもの:
- CLAUDE.md（プロジェクト概要・技術スタック・テスト設定・CI外部サービス）
- docs/requirements/overview.md
- docs/design/architecture.md
- docs/design/db-design.md
- docs/design/api-spec.md（外部連携がある場合のみ）
- docs/design/screen-flow.md（UIがある場合のみ）
- docs/api/openapi.yaml
- spec-map.yml
- docs/quality-gates.md
- mkdocs.yml nav 更新
- .github/workflows/ci.yml（generate-ci.py で自動生成）

コード分析の詳細手順（規模チェック・2段階探索・技術スタック自動検出・テストフレームワークデフォルト表・自動生成ファイル一覧・CIワークフロー生成）:
→ [references/new-mode-detail.md](references/new-mode-detail.md)

---

## 移行モード

原則:
- **既存ドキュメントは絶対に上書き・削除しない**
- **既存のフォーマットにテンプレートを合わせる**（テンプレートに既存を合わせるのではない）
- 足りないものだけ追加する

詳細手順（棚卸し手順・CLAUDE.md配置・フォーマット差分チェック・不足ドキュメント生成・CI/テスト設定・スキルファイルコピー・移行後の注意）:
→ [references/migration-mode-detail.md](references/migration-mode-detail.md)

---

## 手順

### フェーズ1: コード分析・現状把握（親エージェント）

1. [references/new-mode-detail.md](references/new-mode-detail.md)（新規モード）または [references/migration-mode-detail.md](references/migration-mode-detail.md)（移行モード）に従い、コードリポジトリを分析する
   - 規模チェック・2段階探索・技術スタック自動検出を実施
   - `analyze-codebase` スキルで並列分析済みの場合はその結果を活用する
2. 生成対象ドキュメントの一覧と、各ドキュメントに埋める情報を整理する

### フェーズ2: 執筆プラン整理（親エージェント）

3. 以下を整理し、spec-writer へ渡す委任プロンプトを組み立てる:
   - 生成対象ファイルとその役割（ドキュメント種別ごとに整理）
   - 各ファイルに埋める情報（コード分析で得た根拠付き）
   - テンプレート参照先
   - 並列委任が可能なファイルの組み合わせ（ファイル間の依存関係を確認）

### フェーズ3: 執筆委任（spec-writer、並列可）

4. `Agent(subagent_type: spec-writer)` に以下を**並列**で委任する（ファイル単位で独立しているため）:

   **委任プロンプト形式（例: architecture.md）**:
   ```
   あなたは spec-writer です。以下のドキュメントを生成してください。

   ## 生成対象
   docs/design/architecture.md

   ## 参照テンプレート
   docs/templates/phase2/system-architecture.md

   ## 埋める情報
   - プロジェクト名: [検出値]
   - 技術スタック: [検出値（ファイル名:行番号の根拠付き）]
   - アーキテクチャ概要: [分析結果]
   - コンポーネント構成: [分析結果]
   - 外部サービス依存: [検出値]
   - デプロイ構成: [検出値]

   ## コード根拠
   - [ファイル名:行番号] → [記述内容]

   ## 厳守事項
   - 全ての記述に根拠（ファイル名:行番号）を明記する
   - 不明点は「※ 要確認」マーカーを残し、推測で埋めない
   - index系ファイル（overview.md / spec-map.yml / mkdocs.yml / dependency-graph.md）は触らない（親が更新）
   - 完了時に軽量セルフチェックを実行し、結果を報告すること
   ```

   **並列委任する対象**（該当するもののみ）:
   - docs/design/architecture.md
   - docs/design/db-design.md
   - docs/design/api-spec.md（外部連携がある場合のみ）
   - docs/design/screen-flow.md（UIがある場合のみ）
   - docs/api/openapi.yaml
   - docs/requirements/overview.md（機能グループ一覧）
   - CLAUDE.md（プロジェクト概要・技術スタックセクション）
   - docs/quality-gates.md

### フェーズ4: index系更新（親エージェント）

spec-writer は index 系に触らないため、親が責任を持って更新する:

5. `spec-map.yml` を生成（空テンプレートまたは既存機能エントリ付き）
6. `mkdocs.yml` の nav を更新（新規生成ファイルを全て追加）
7. `docs/design/dependency-graph.md` が存在する場合、初期エントリを追加
8. CIワークフロー生成（[references/new-mode-detail.md](references/new-mode-detail.md) Step 6 参照）
   ```bash
   python3 ci-templates/generate-ci.py \
     --claude-md CLAUDE.md \
     --output .github/workflows/ci.yml \
     --repo-structure auto
   ```

### フェーズ5: レビューと整合性チェック（親エージェント）

9. spec-writer が生成したドキュメントを**本体が直接レビュー**する（Agent委任不可）
   - コード分析結果との整合性確認
   - 根拠（ファイル名:行番号）が適切に記載されているか確認
   - 要確認マーカーの確認と対応（必要ならユーザーに追加確認）
   - テンプレート構造の再現確認
10. `Agent(subagent_type: integrity-checker)` を起動して機械的整合性チェック
    - 変更ファイルリストを prompt で渡す
    - チェック項目: `.claude/skills/_shared/doc-integrity-check.md` 参照
    - FAIL があれば修正 → 再チェック（最大3ループ）

### フェーズ6: コミット（親エージェント）

11. 変更を `git add` してコミット（docsリポとコードリポそれぞれ）

### フェーズ7: 次ステップ提案

12. 次のステップを提案:
    - 「次はどの機能からSpec化しますか？overview.mdに以下の機能グループがあります：…」
    - 「テスト失敗時にマージをブロックするには、GitHubのBranch Protection Ruleを設定してください」とリマインドする

---

## 共通ルール
- 既存コードのロジックは一切変更しない
- 生成内容が不明確な場合はTODOコメントを残す
- .claude/CLAUDE.mdは上書きしてよい（共通ルール）。ルートCLAUDE.mdのプロジェクト固有セクションは変更しない（移行モードでは追加のみ）
- **一度に全てのSpec化を試みない。** overview.mdに機能一覧を作った後は、ユーザーに「どの機能からSpec化しますか？」と確認し、5〜10個ずつ進める

**コード分析時の注意:** .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること。
