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

詳細手順（規模チェック・2段階探索・技術スタック自動検出・テストフレームワークデフォルト表・自動生成ファイル一覧・CIワークフロー生成）:
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

## 共通ルール
- 既存コードのロジックは一切変更しない
- 生成内容が不明確な場合はTODOコメントを残す
- .claude/CLAUDE.mdは上書きしてよい（共通ルール）。ルートCLAUDE.mdのプロジェクト固有セクションは変更しない（移行モードでは追加のみ）
- **一度に全てのSpec化を試みない。** overview.mdに機能一覧を作った後は、ユーザーに「どの機能からSpec化しますか？」と確認し、5〜10個ずつ進める

**コード分析時の注意:** .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること。
