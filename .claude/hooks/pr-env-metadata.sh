#!/usr/bin/env bash
# PR本文に貼り付ける「生成環境」ブロックを出力する。
#
# 出力元はセッションのトランスクリプト（~/.claude/projects/<proj>/<session_id>.jsonl）。
# assistant レコードに実際に使われたモデル・エフォート・Claude Code バージョンが
# 記録されているため、自己申告ではなく実測値を PR に残せる。
#
# 使い方:
#   .claude/hooks/pr-env-metadata.sh                 # セッションを自動特定
#   .claude/hooks/pr-env-metadata.sh <transcript.jsonl>  # 明示指定
#
# 取得できなかった項目は「不明」と出力する（推測で埋めない）。
# python3 が使えない環境（Windows の Microsoft Store スタブ等）では
# python / py -3 にフォールバックする（.claude/hooks/_python.sh）。
# 終了コードは常に 0。特定できなかった場合のみ stderr に警告を出す。

set -u

CONFIG_DIR="${CLAUDE_CONFIG_DIR:-$HOME/.claude}"
PROJECTS_DIR="$CONFIG_DIR/projects"

TRANSCRIPT=""

# 1. 引数で明示指定
if [ "$#" -ge 1 ] && [ -f "$1" ]; then
  TRANSCRIPT="$1"
fi

# 2. セッションIDから探索
if [ -z "$TRANSCRIPT" ] && [ -n "${CLAUDE_CODE_SESSION_ID:-}" ]; then
  TRANSCRIPT=$(find "$PROJECTS_DIR" -type f -name "${CLAUDE_CODE_SESSION_ID}.jsonl" 2>/dev/null | head -1)
fi

# 3. カレントディレクトリ由来のプロジェクトディレクトリから最新のものを使う
if [ -z "$TRANSCRIPT" ]; then
  SLUG=$(pwd | sed 's/[^A-Za-z0-9]/-/g')
  TRANSCRIPT=$(ls -t "$PROJECTS_DIR/$SLUG"/*.jsonl 2>/dev/null | head -1)
fi

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./_python.sh
. "$SCRIPT_DIR/_python.sh"

# Python が使えない環境（Windows の python3 スタブ等）ではトランスクリプトを
# 解析できないため、環境変数で埋められる分だけ埋めて出力する。
if [ -z "$PYTHON" ]; then
  FB_EFFORT="${CLAUDE_EFFORT:-}"
  FB_VERSION=$(printf '%s' "${AI_AGENT:-}" \
    | sed -n 's/^claude-code_\([0-9-]\{1,\}\)_.*$/\1/p' | tr '-' '.')
  printf '<!-- claude-env -->\n## 生成環境\n\n| 項目 | 値 |\n|------|-----|\n'
  printf '| モデル | %s |\n' "不明"
  printf '| エフォート | %s |\n' "${FB_EFFORT:-不明}"
  printf '| Claude Code | %s |\n' "${FB_VERSION:-不明}"
  printf 'WARN: 動作する Python が見つからないためトランスクリプトを解析できませんでした。%s\n' \
    "不明の項目は推測で埋めず、そのまま残してください。" >&2
  exit 0
fi

# shellcheck disable=SC2086
$PYTHON - "$TRANSCRIPT" <<'PY_EOF'
import json
import os
import re
import sys

# Windows では既定の出力エンコーディングが cp932 等になり、
# PR本文にリダイレクトすると文字化けするため UTF-8 に固定する。
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

path = sys.argv[1] if len(sys.argv) > 1 else ""
model = ""
effort = ""
version = ""

if path and os.path.isfile(path):
    try:
        with open(path, encoding="utf-8") as f:
            for line in f:
                if '"assistant"' not in line:
                    continue
                try:
                    rec = json.loads(line)
                except (json.JSONDecodeError, ValueError):
                    continue
                # サブエージェント（isSidechain）は別モデルの可能性があるため本体のみ見る
                if rec.get("type") != "assistant" or rec.get("isSidechain"):
                    continue
                model = (rec.get("message") or {}).get("model") or model
                effort = rec.get("effort") or effort
                version = rec.get("version") or version
    except OSError:
        pass

# トランスクリプトから取れなかった場合の補完（環境変数）
effort = effort or os.environ.get("CLAUDE_EFFORT", "")
if not version:
    matched = re.match(r"claude-code_([0-9-]+)_", os.environ.get("AI_AGENT", ""))
    if matched:
        version = matched.group(1).replace("-", ".")


def shown(value):
    return value if value else "不明"


print("<!-- claude-env -->")
print("## 生成環境")
print()
print("| 項目 | 値 |")
print("|------|-----|")
print("| モデル | %s |" % shown(model))
print("| エフォート | %s |" % shown(effort))
print("| Claude Code | %s |" % shown(version))

if not model:
    sys.stderr.write(
        "WARN: トランスクリプトを特定できませんでした（%s）。"
        "不明の項目は推測で埋めず、そのまま残してください。\n" % (path or "未検出")
    )
PY_EOF

exit 0
