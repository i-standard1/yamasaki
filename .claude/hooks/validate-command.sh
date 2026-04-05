#!/usr/bin/env bash
# PreToolUse hook: Bash コマンドの危険パターンを検出してブロックする
# exit 0 = 許可, exit 2 = ブロック
#
# Claude Code は stdin に JSON を渡す:
# { "tool_name": "Bash", "tool_input": { "command": "..." } }

set -u

# stdin から実行予定のコマンドを取得
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tool_input',{}).get('command',''))" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# --- 危険パターン定義 ---

# 1. 本番環境への直接接続を示唆するパターン
if echo "$COMMAND" | grep -qiE '(production|prod)\s*(db|database|server|host|env)'; then
  echo "BLOCKED: 本番環境への直接接続が検出されました" >&2
  exit 2
fi

# 2. 環境変数経由での機密情報漏洩
if echo "$COMMAND" | grep -qiE '(echo|printf|cat).*\$[{(]?[A-Za-z_]*(_KEY|_SECRET|_TOKEN|_PASSWORD|_CREDENTIAL)[A-Za-z_]*[})]?'; then
  echo "BLOCKED: 機密環境変数の出力が検出されました" >&2
  exit 2
fi

# 3. SSH/SCP による外部サーバー操作
if echo "$COMMAND" | grep -qE '^(ssh|scp)\s'; then
  echo "BLOCKED: SSH/SCP コマンドは手動で実行してください" >&2
  exit 2
fi

# 4. Docker の特権モード
if echo "$COMMAND" | grep -qE 'docker\s+run.*--privileged'; then
  echo "BLOCKED: Docker の特権モードは禁止されています" >&2
  exit 2
fi

# 5. ディスク全体への再帰的な権限変更
if echo "$COMMAND" | grep -qE 'chmod\s+-R\s+.*\s+/[^.]'; then
  echo "BLOCKED: ルートディレクトリ配下への再帰的 chmod は禁止されています" >&2
  exit 2
fi

# 6. git の危険な履歴改変（deny ルールの補完）
#    通常の git rebase main は許可。--onto, filter-branch, push --force をブロック
if echo "$COMMAND" | grep -qE 'git\s+(filter-branch|rebase\s+--onto|push.*--force)'; then
  echo "BLOCKED: git の履歴改変コマンドは手動で実行してください" >&2
  exit 2
fi

# 7. base64 エンコードによるデータ持ち出しの疑い
if echo "$COMMAND" | grep -qE 'base64.*\|.*(curl|wget|nc|ncat)'; then
  echo "BLOCKED: エンコードデータの外部送信パターンが検出されました" >&2
  exit 2
fi

# すべてのチェックを通過
exit 0
