#!/usr/bin/env bash
# PreToolUse hook: PR作成時に「生成環境」ブロックの記載漏れをブロックする
#
# exit 0 = 許可, exit 2 = ブロック
#
# 対象:
#   - Bash の `gh pr create`
#   - mcp__github__create_pull_request
#
# 本文に claude-env マーカーが無ければブロックし、
# .claude/hooks/pr-env-metadata.sh の実行を促す（.claude/rules/git-workflow.md）。
#
# 判定できないケース（--body-file の内容がまだ存在しない・変数展開が必要）は
# ブロックせず systemMessage で注意喚起するだけにする。誤ブロックで作業が
# 詰まる方が実害が大きいため。

set -u

INPUT=$(cat)

python3 - "$INPUT" <<'PY_EOF'
import json
import os
import re
import sys

MARKER = "claude-env"
GUIDE = (
    "BLOCKED: PR本文に生成環境ブロックがありません。\n"
    "`.claude/hooks/pr-env-metadata.sh` を実行し、その出力"
    "（claude-env マーカー行から表まで）をPR本文に含めてから再実行してください。\n"
    "詳細: .claude/rules/git-workflow.md「PR本文の生成環境記載」"
)
REMIND = (
    "📝 PR本文に生成環境ブロック（.claude/hooks/pr-env-metadata.sh の出力）が"
    "含まれているか確認してください。"
)

try:
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}


def block():
    sys.stderr.write(GUIDE + "\n")
    sys.exit(2)


def remind(detail):
    print(json.dumps({"systemMessage": "%s（%s）" % (REMIND, detail)}))
    sys.exit(0)


# --- GitHub MCP 経由のPR作成 ---
if tool == "mcp__github__create_pull_request":
    if MARKER not in (tool_input.get("body") or ""):
        block()
    sys.exit(0)

if tool != "Bash":
    sys.exit(0)

# --- gh pr create ---
command = tool_input.get("command", "")
if not re.search(r"\bgh\s+pr\s+create\b", command):
    sys.exit(0)

# ヘルプ表示・ブラウザ入力は対象外
if re.search(r"(?:^|\s)(?:--help|-h|--web)(?:\s|$)", command):
    sys.exit(0)

# コマンド中に本文がインラインで書かれていてマーカーがあればOK
if MARKER in command:
    sys.exit(0)

body_file = re.search(r"(?:--body-file|-F)[=\s]+(\S+)", command)
if body_file:
    path = body_file.group(1).strip("\"'")
    # 変数展開・コマンド置換が必要なパスはフック側で解決できない
    if "$" in path or "`" in path:
        remind("本文ファイルのパスが変数のため自動判定できませんでした")
    if not os.path.isfile(path):
        # 同一コマンド内で本文ファイルを生成する場合、この時点では存在しない
        remind("本文ファイル %s がまだ存在せず自動判定できませんでした" % path)
    try:
        with open(path, encoding="utf-8", errors="replace") as f:
            if MARKER in f.read():
                sys.exit(0)
    except OSError:
        remind("本文ファイル %s を読めませんでした" % path)
    block()

# --body / --fill / 本文指定なし のいずれもマーカー無しとみなす
block()
PY_EOF
