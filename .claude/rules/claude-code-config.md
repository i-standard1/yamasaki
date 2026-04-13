---
paths:
  - ".claude/skills/**"
  - ".claude/rules/**"
  - ".claude/settings*.json"
  - ".claude/agents/**"
description: Claude Code設定・スキル・ルール操作時のリファレンス参照ルール
---

# Claude Code 設定変更ルール

`.claude/` 配下のスキル・ルール・設定・エージェント定義を**作成または編集**する場合:

1. `.claude/skills/_shared/config-reference.md` を Read して正しいフロントマター・設定値を確認する
2. 不明な仕様がある場合は公式ドキュメント（リファレンス末尾のURL）を WebFetch で確認する
3. 以下の制約を守る:
   - Skill→Skill のネストでモデル切替は使わない（未文書化で動作保証なし）
   - Agent に委任する場合、コンテキストは prompt 経由でしか渡せないことを考慮する
   - ルールの `paths` は Read でも発火する。大きなルールは参照ファイルを分離する
