# 実装後・生成後レビュー

実装またはドキュメント生成が完了したら、**コミット前に**レビューを実行する。

## コード変更の場合

- レビューは本体が直接実行する（Agent に委任しない）。実装コンテキストを持つ本体が最も精度が高い
- レビュー観点: `.claude/skills/_shared/review-checklist.md` を参照
- 指摘基準: `.claude/skills/_shared/review-standards.md` に従う（信頼度80以上のみ修正対象）
- 指摘があれば修正→再レビュー（最大3ループ）

## ドキュメント生成・更新の場合

`docs/requirements/**/*.md` / `docs/design/**/*.md` / `docs/api/openapi.yaml` / `mkdocs.yml` / `spec-map.yml` を変更した場合、以下の2種類のレビューを行う:

### 機械的整合性チェック（必須）

- `integrity-checker` エージェントに委任して機械的整合性を検証する
- チェック項目: `.claude/skills/_shared/doc-integrity-check.md` を参照（mkdocs build、Mermaid構文、リンク切れ、index漏れ、Markdownフォーマット、画面遷移整合性）
- FAIL があれば本体が修正 → 再チェック（最大3ループ）

### 意味的整合性レビュー（スキル内で既定済み）

- 用語ゆれ・REQ-ID整合・相互参照の意味的整合は `.claude/skills/_shared/spec-consistency-review.md` が担当
- `spec-all` / `spec-feature` / `detail-design` 等のSKILL内で既に実行される設計のため、ルール側で二重に発火させない

## 適用外

- コミットメッセージの修正や `.gitignore` 等の設定ファイルのみの変更
- `docs/` 配下でも README・ガイド・雑記など、要件定義・設計書に該当しないファイル
