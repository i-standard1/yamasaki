---
description: 複数タスクの並列作業を指示された場合に parallel-work ルールをロードするトリガー
alwaysApply: true
---

# 並列作業トリガー

ユーザーが複数のイシュー・機能・タスクの同時実装を指示した場合:

1. `.claude/rules/parallel-work.md` を Read する
2. 読み込んだルール（worktree 分離・ブランチ命名・統合フェーズ等）に従って作業を進める
