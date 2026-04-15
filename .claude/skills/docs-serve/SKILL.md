---
name: docs-serve
description: MkDocs プレビュー（:8000）と承認API（:8765）を同時起動する。「ドックを起動して」「docsプレビュー見たい」「設計書をブラウザで確認したい」「承認ボタン使いたい」等のリクエストで発火する。
allowed-tools: Bash
---

# docs-serve スキル

`scripts/docs_serve.py` を実行し、MkDocs のプレビューサーバと、レビュー承認用のローカル API を同時に起動する。

## 実行

プロジェクトルートから:

```bash
python scripts/docs_serve.py
```

バックグラウンド実行する場合は `run_in_background: true` で Bash を叩くこと。

## ポート

| 用途             | URL                          |
|------------------|------------------------------|
| MkDocs プレビュー | http://localhost:8000        |
| 未承認一覧       | http://localhost:8000/review-pending/ |
| 承認 API         | http://localhost:8765        |

`REVIEW_API_PORT` 環境変数で API ポートは変更可能。

## 使い方

1. 起動後、ブラウザで http://localhost:8000 を開く
2. 変更箇所が赤背景で表示される
3. 右上の「✓ 承認」ボタンをクリックすると、該当マーカーだけが Markdown から除去される
4. livereload によって画面も自動更新され、赤が消える

## 停止

- フォアグラウンド起動: Ctrl+C で両プロセス終了
- バックグラウンド起動: `kill <pid>` で Python プロセスを落とす（mkdocs serve も連動して終了）

## トラブルシューティング

### ポート競合

```
OSError: [Errno 48] Address already in use
```

他の mkdocs serve が動いていないか確認:

```bash
lsof -i :8000 -sTCP:LISTEN -P -n
lsof -i :8765 -sTCP:LISTEN -P -n
```

該当 PID を kill してから再起動する。

### mkdocs コマンドが見つからない

```bash
pip install -r requirements.txt
```

### 承認ボタンがエラーを出す

`scripts/docs_serve.py` ではなく素の `mkdocs serve` を使っている可能性。必ずラッパー経由で起動する。
