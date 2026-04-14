# NotebookLM MCP セットアップガイド

チームのナレッジベース（議事録・設計メモ・決定事項など）をClaude Codeから参照するための設定手順。

## 概要

NotebookLM MCPを設定すると、実装時に「先週のミーティングで決まった方針で実装して」と指示するだけで、Claudeが自動的にNotebookLMのノートブックを検索し、決定事項や背景を踏まえて実装に反映します。

## 前提条件

- Python 3.11 以上
- Google アカウント（対象ノートブックへのアクセス権あり）
- Chrome ブラウザ（初回認証で使用）

## セットアップ手順（所要時間: 約15分）

### 1. MCP CLI のインストール

```bash
# pipx 推奨（Homebrew管理のPythonでも安全にインストールできる）
pipx install notebooklm-mcp-cli

# pipx がない場合は先にインストール
brew install pipx
```

### 2. Google アカウントでログイン

**Chrome を完全に閉じてから**実行してください（Cookie 抽出のため）。

```bash
nlm login --profile work
```

ブラウザが開くので、対象ノートブックにアクセス権のある Google アカウントでログインします。

### 3. ノートブックのエイリアス設定

> **ノートブックID**: NotebookLM のURL `https://notebooklm.google.com/notebook/<ここがID>` から取得

```bash
nlm alias set <エイリアス名> <ノートブックID> --profile work
```

複数のノートブックを設定できます:

```bash
# 例: 用途別に複数設定
nlm alias set team-meetings <ID> --profile work
nlm alias set design-notes <ID> --profile work
```

<!-- プロジェクト固有のノートブックID・エイリアス名・検索優先順位はここに追記する -->

### 4. 動作確認

```bash
nlm query notebook -p work <エイリアス名> "最近の決定事項は？"
```

検索結果が返ってくれば設定完了です。

## .mcp.json の設定

プロジェクトルートに `.mcp.json` を作成（または追記）します:

```json
{
  "mcpServers": {
    "notebooklm": {
      "command": "nlm",
      "args": ["mcp", "--profile", "work"],
      "env": {}
    }
  }
}
```

## Claude Code での使い方

設定が完了すれば、Claude Code のセッション内で以下のように使えます:

### ナレッジの参照

```
先週のミーティングで決まったアーキテクチャを踏まえて実装して
```

```
/notebook-query 認証方式の決定事項
```

## トラブルシューティング

### 認証エラーが出る

セッションCookieの有効期限は2〜4週間です。期限切れの場合は再ログインしてください:

```bash
nlm login --profile work
```

### ノートブックが見つからない

エイリアスが正しく設定されているか確認:

```bash
nlm alias list
```

### MCP サーバーが起動しない

Claude Code を再起動すると `.mcp.json` が再読み込みされます。

## 注意事項

- `auth.json`（認証情報）は **絶対にgitにコミットしない** こと（`.gitignore` に追加済み）
- セッションCookieは個人のGoogle認証に紐づくため、共有不可
- NotebookLMの内容は各自のGoogleアカウントの権限に基づいてアクセスされる
