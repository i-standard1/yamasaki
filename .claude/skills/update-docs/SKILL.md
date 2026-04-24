---
name: update-docs
description: |
  コード変更からドキュメントを追従更新する。設計書ファースト原則の例外措置。
  やむを得ず先にコードを変更した場合にのみ使用する。
  「さっきの変更をドキュメントに反映して」「設計書を最新にして」
  「コードと設計書がズレてるから直して」「ドキュメントを最新化して」
  「ドキュメント更新して」「設計書を現状に合わせて」などのリクエストで使用する。
  通常はドキュメントを先に更新してからコードを修正すること（revise-specを使う）。
context:
  required:
    - _shared/spec-writing-standard.md
    - _shared/spec-unified-base.md
    - _shared/spec-map-operations.md
    - _shared/code-search-2stage.md
---

# ドキュメントの追従更新（例外措置）

※ これは「設計書ファースト」原則の例外措置です。通常はrevise-specでドキュメントを先に更新してからコードを修正する。

本スキルは**親=変更箇所特定・方針・レビュー / spec-writer(Sonnet)=ドキュメント書き換え / integrity-checker=機械的整合性検査**の三者分担で進める。

## 引数の解釈
- `HEAD~1` → 直前のコミットとの差分
- `HEAD~3` → 直近3コミット分の差分
- コミットハッシュ → そのコミット単体の変更
- 引数なし → ステージされた変更（`git diff --cached`）

## 統一基盤の確認

[Spec 統一基盤確認](../_shared/spec-unified-base.md) を実施する。

## 手順

### フェーズ1: 変更箇所の特定（親エージェント）

1. コードリポで `git diff` を実行し、変更内容を把握する
2. `spec-map.yml` を読み、変更されたファイルパスに一致するエントリからSpec IDを特定する
   - spec-map.yml に該当パスがない場合は新規REQ-IDの採番を提案する
3. [2段階探索](../_shared/code-search-2stage.md) でdiffに含まれない関連ファイルも探索する
4. 変更の種別と影響範囲を整理する:
   - 更新対象ドキュメントの一覧（要件定義書・基本設計・openapi.yaml）
   - 各ドキュメントの該当セクション・箇所の特定
   - 差分の具体的な値（変更前 → 変更後）

### フェーズ2: 執筆プラン整理（親エージェント）

5. 以下を整理し、spec-writer へ渡す委任プロンプトを組み立てる:
   - 更新対象ファイルと更新箇所（セクション・行レベルで特定）
   - 変更前後の具体的な値（diffから抽出）
   - 差分更新の方針（全面書き換えではなく該当セクションのみ更新）
   - 新規REQ-IDが必要な場合はその採番値

### フェーズ3: 書き換え委任（spec-writer）

6. `Agent(subagent_type: spec-writer)` に更新を委任する:
   - 更新対象ファイルが複数かつ独立している場合は**並列**委任

   **委任プロンプト形式**:
   ```
   あなたは spec-writer です。以下のドキュメントを差分更新してください。

   ## 更新対象
   docs/requirements/features/[REQ-ID].md

   ## 更新箇所
   - セクション名: [XXX]
   - 変更前: [値]
   - 変更後: [値]
   - コード根拠: [ファイル名:行番号]

   ## 更新方針
   - 差分更新が基本。既存文書の全面書き換えはしない
   - 変更箇所のセクションだけを更新し、周辺は触らない
   - 不明点は「※ 要確認」マーカーを残し、推測で埋めない

   ## ヒアリング結果サマリ
   [フェーズ1で整理した変更内容]

   ## 厳守事項
   - index系ファイル（overview.md / spec-map.yml / mkdocs.yml / dependency-graph.md）は触らない（親が更新）
   - 完了時に軽量セルフチェックを実行し、結果を報告すること
   ```

### フェーズ4: index系更新（親エージェント）

spec-writer は index 系に触らないため、親が責任を持って更新する:

7. ドキュメントを新規作成した場合は `mkdocs.yml` の nav に追加する
8. [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い `spec-map.yml` を同期する
9. OVERVIEW同期チェック: 変更内容がOVERVIEW同期トリガー（spec-management.mdルール参照）に該当する場合、`docs/requirements/overview.md` も更新する
10. `docs/design/dependency-graph.md` が存在し変更対象に新規Specがある場合、依存関係を追記する

### フェーズ5: レビューと整合性チェック（親エージェント）

11. spec-writer が更新したドキュメントを**本体が直接レビュー**する（Agent委任不可）
    - diffの具体的な値がドキュメントに反映されているか確認（grep検証）
    - 要確認マーカーの確認と対応
12. `Agent(subagent_type: integrity-checker)` を起動して機械的整合性チェック
    - 変更ファイルリスト・新規REQ-ID（あれば）を prompt で渡す
    - チェック項目: `.claude/skills/_shared/doc-integrity-check.md` 参照
    - 小さな変更でも integrity-checker を通す（リンク切れ・Mermaid 崩れ防止）
    - FAIL があれば修正 → 再チェック（最大3ループ）

### フェーズ6: コミット（親エージェント）

13. 変更を `git add` してコミット

### フェーズ7: 次ステップ提案

14. 次のステップを提案（「他に反映すべき変更はありますか？」）

## ルール
- 変更がSpec IDに紐づかない場合は新規REQ-IDの採番を提案する
- 同じ定数・バリデーション値を参照している箇所も漏れなく更新する
