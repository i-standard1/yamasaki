---
alwaysApply: true
description: Claude Codeの仕組み・仕様・設定について質問されたときにリファレンスを参照する
---

# Claude Code 仕様の質問対応

Claude Code の仕組み・仕様・設定（スキル、ルール、フック、エージェント、モデル設定、パーミッション等）について質問されたら:

1. `.claude/skills/_shared/config-reference.md` を Read して回答の根拠にする
2. リファレンスに記載がない場合は公式ドキュメント（リファレンス末尾のURL）を WebFetch で確認する
