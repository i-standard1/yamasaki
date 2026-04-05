# Spec 統一基盤確認

Spec の執筆・更新前に必ず以下を実行し、統一ルールを把握する。
このファイルが統一基盤確認の **Single Source of Truth**。他のドキュメントからはここを参照すること。

## チェックリスト

1. **glossary.md**: `docs/requirements/glossary.md` が存在すれば読む → 定義済みの用語を使う
   - 新しい概念が出てきた場合は glossary.md にも追記する
   - glossary.md が存在しない場合は、Spec 執筆と同時に新規作成する（コードのモデル名から用語を決定）
   - 排他制御・フォーマットの詳細は `.claude/rules/spec-management.md` の「glossary.md ルール」を参照
2. **Spec 執筆標準**: [spec-writing-standard.md](./spec-writing-standard.md) を読む → セクション構成・記述ルールに従う
3. **既存 Spec のフォーマット確認**: `docs/requirements/features/` に既存 Spec があれば1つ読む → フォーマットを揃える
4. **進捗把握**（バッチ処理の場合のみ）: `docs/requirements/overview.md` の機能一覧と `logs/context/` の計画ファイルを確認する
