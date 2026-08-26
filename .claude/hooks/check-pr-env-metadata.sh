#!/usr/bin/env bash
# PreToolUse hook: PR作成時に「生成環境」ブロックの記載漏れをブロックする
#
# exit 0 = 許可, exit 2 = ブロック
#
# 対象:
#   - Bash の `gh pr create`（セグメントの先頭トークンとして現れる場合のみ）
#   - mcp__github__create_pull_request
#
# 本文に claude-env マーカーと、値が埋まった表が無ければブロックし、
# .claude/hooks/pr-env-metadata.sh の実行を促す（.claude/rules/git-workflow.md）。
#
# 判定できないケース（--body-file の内容がまだ存在しない・変数展開が必要）は
# ブロックせず systemMessage で注意喚起するだけにする。誤ブロックで作業が
# 詰まる方が実害が大きいため。
#
# python3 が使えない環境では python / py -3 にフォールバックする
# （.claude/hooks/_python.sh）。どれも無い場合は grep による縮退判定に落ちる。

set -u

# stdin の読み取りは組み込みの read で行う（cat のプロセス起動を避ける）。
# 入力末尾に NUL は無いため read は非ゼロで返るが、INPUT には全量が入る。
IFS= read -r -d '' INPUT || true

# PR作成に無関係な呼び出しは、ここより下の処理に入る前に抜ける。
# このフックは Bash マッチャに掛かるため、全 Bash 呼び出しがこのコストを払う。
# 粗いふるい分けなので、通過後に下の厳密判定で改めて絞る。
PR_HINT='pr[^A-Za-z0-9_]+create|create_pull_request'
if [[ ! "$INPUT" =~ $PR_HINT ]]; then
  exit 0
fi

# 以下は PR 作成コマンドのみが通る。Python インタプリタの解決（実プロセス起動を
# 伴うため高価）とパス算出のコストをここまで遅延させている。Windows 実測では
# 無関係な Bash 呼び出し1回あたりのフック負荷が +103ms から +11ms になった。
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
# shellcheck source=./_python.sh
. "$SCRIPT_DIR/_python.sh"

# Python が使えない環境（Windows の python3 スタブ等）向けの縮退判定。
# このフックは Bash 全体に掛かるため、PR作成コマンド以外は必ず素通しさせる。
if [ -z "$PYTHON" ]; then
  if [[ ! "$INPUT" =~ \"tool_name\"[[:space:]]*:[[:space:]]*\"(Bash|mcp__github__create_pull_request)\" ]]; then
    exit 0
  fi
  if printf '%s' "$INPUT" | grep -q 'claude-env'; then
    exit 0
  fi
  if printf '%s' "$INPUT" | grep -qE '\-\-body-file|\-F '; then
    # 本文ファイルの中身は縮退判定では追えないため、ブロックせず注意喚起のみ
    printf '{"systemMessage": "%s"}\n' \
      "動作する Python が無いため PR本文の自動判定ができません。生成環境ブロックが含まれているか手で確認してください。"
    exit 0
  fi
  printf 'BLOCKED: PR本文に生成環境ブロックがありません（Python 未検出のため縮退判定）。\n' >&2
  printf '`.claude/hooks/pr-env-metadata.sh` の出力をPR本文に含めてから再実行してください。\n' >&2
  exit 2
fi

# shellcheck disable=SC2086
$PYTHON - "$INPUT" <<'PY_EOF'
import json
import os
import re
import shlex
import sys

# Windows では既定の出力エンコーディングが cp932 等になり、
# PR本文にリダイレクトすると文字化けするため UTF-8 に固定する。
sys.stdout.reconfigure(encoding="utf-8")
sys.stderr.reconfigure(encoding="utf-8")

MARKER = "claude-env"
ROWS = ("モデル", "エフォート", "Claude Code")
ROW_RE = re.compile(
    r"^\|\s*(モデル|エフォート|Claude Code)\s*\|\s*([^|]*?)\s*\|\s*$", re.MULTILINE
)
# コマンドをコマンドに分割する演算子。shlex が独立トークンとして返す。
SEPARATORS = (";", "&&", "||", "|", "&", "\n")
# gh の前に置かれても実行本体を変えない語
WRAPPERS = ("env", "command", "time", "nohup")
ASSIGNMENT_RE = re.compile(r"^[A-Za-z_][A-Za-z0-9_]*=")

REMIND = (
    "📝 PR本文に生成環境ブロック（.claude/hooks/pr-env-metadata.sh の出力）が"
    "含まれているか確認してください。"
)


def block(detail):
    sys.stderr.write(
        "BLOCKED: PR本文の生成環境ブロックに問題があります（%s）。\n"
        "`.claude/hooks/pr-env-metadata.sh` を実行し、その出力"
        "（claude-env マーカー行から表まで）をPR本文に含めてから再実行してください。\n"
        "詳細: .claude/rules/git-workflow.md「PR本文の生成環境記載」\n" % detail
    )
    sys.exit(2)


def remind(detail):
    print(json.dumps({"systemMessage": "%s（%s）" % (REMIND, detail)}))
    sys.exit(0)


def block_reason(text):
    """生成環境ブロックの不備を返す。問題が無ければ None。

    マーカーの有無だけでなく表の値まで見る。テンプレート
    （.github/pull_request_template.md）を貼っただけの空表を通さないため。
    「不明」は正当な値なので空欄判定のみ行う。
    """
    if MARKER not in text:
        return "claude-env マーカーがありません"
    found = dict(ROW_RE.findall(text))
    missing = [label for label in ROWS if label not in found]
    if missing:
        return "表の行がありません: %s" % "/".join(missing)
    empty = [label for label in ROWS if not found[label].strip()]
    if empty:
        return "表の値が空です: %s（取得できない項目は「不明」と書く）" % "/".join(empty)
    return None


def segments(command):
    """コマンドを ; && || | & 改行 で分割し、各セグメントのトークン列を返す。

    shlex はクォートを解いてトークン化するため、`echo 'gh pr create ...'` の
    ように引用符の中に語が現れるだけのコマンドを実行と誤認しない。
    トークン化に失敗した場合（クォート未閉じ等）は None を返す。
    """
    lexer = shlex.shlex(command, posix=True, punctuation_chars=True)
    lexer.whitespace_split = True
    lexer.commenters = ""  # `#` 以降を捨てさせない
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    result, current = [], []
    for token in tokens:
        if token in SEPARATORS:
            result.append(current)
            current = []
        else:
            current.append(token)
    result.append(current)
    return result


def is_gh_pr_create(tokens):
    """セグメントが gh pr create の実行かどうかを返す。"""
    index = 0
    while index < len(tokens) and (
        ASSIGNMENT_RE.match(tokens[index]) or tokens[index] in WRAPPERS
    ):
        index += 1
    rest = tokens[index:]
    if len(rest) < 3:
        return False
    name = os.path.basename(rest[0])
    if name.lower().endswith(".exe"):
        name = name[:-4]
    return name == "gh" and rest[1] == "pr" and rest[2] == "create"


def find_flag_value(tokens, names):
    """`--flag value` / `--flag=value` の値を返す。指定が無ければ None。"""
    for index, token in enumerate(tokens):
        for name in names:
            if token == name:
                return tokens[index + 1] if index + 1 < len(tokens) else ""
            if token.startswith(name + "="):
                return token[len(name) + 1:]
    return None


def path_candidates(path):
    """パスの解決候補を返す。

    Git Bash から渡されるコマンドは `/c/Users/...` のような MSYS 形式の絶対パスを
    含むことがあり、Windows の Python では os.path.isfile が False になる。
    ドライブレター形式へ読み替えた候補も試す。
    """
    yield path
    matched = re.match(r"^/([A-Za-z])/(.*)$", path)
    if matched:
        yield "%s:/%s" % (matched.group(1).upper(), matched.group(2))


try:
    data = json.loads(sys.argv[1]) if len(sys.argv) > 1 else {}
except (json.JSONDecodeError, ValueError):
    sys.exit(0)

tool = data.get("tool_name", "")
tool_input = data.get("tool_input") or {}

# --- GitHub MCP 経由のPR作成 ---
if tool == "mcp__github__create_pull_request":
    reason = block_reason(tool_input.get("body") or "")
    if reason:
        block(reason)
    sys.exit(0)

if tool != "Bash":
    sys.exit(0)

# --- gh pr create ---
command = tool_input.get("command", "")
parsed = segments(command)
if parsed is None:
    # トークン化できないコマンド。素通しはせず注意喚起に留める
    if re.search(r"\bgh\s+pr\s+create\b", command):
        remind("コマンドを解析できず自動判定できませんでした")
    sys.exit(0)

target = None
for tokens in parsed:
    if is_gh_pr_create(tokens):
        target = tokens
        break
if target is None:
    sys.exit(0)

# ヘルプ表示・ブラウザ入力は対象外
if any(token in ("--help", "-h", "--web", "-w") for token in target):
    sys.exit(0)

body_file = find_flag_value(target, ("--body-file", "-F"))
if body_file is not None:
    if not body_file or "$" in body_file or "`" in body_file:
        remind("本文ファイルのパスが変数のため自動判定できませんでした")
    if body_file == "-":
        remind("本文が標準入力から渡されるため自動判定できませんでした")
    resolved = ""
    for candidate in path_candidates(body_file):
        if os.path.isfile(candidate):
            resolved = candidate
            break
    if not resolved:
        # 同一コマンド内で本文ファイルを生成する場合、この時点では存在しない
        remind("本文ファイル %s がまだ存在せず自動判定できませんでした" % body_file)
    try:
        with open(resolved, encoding="utf-8", errors="replace") as f:
            content = f.read()
    except OSError:
        remind("本文ファイル %s を読めませんでした" % body_file)
    reason = block_reason(content)
    if reason:
        block("%s: %s" % (body_file, reason))
    sys.exit(0)

body = find_flag_value(target, ("--body", "-b"))
if body is not None:
    if "$" in body or "`" in body:
        remind("本文に変数展開・コマンド置換が含まれるため自動判定できませんでした")
    reason = block_reason(body)
    if reason:
        block(reason)
    sys.exit(0)

# --fill / --fill-first / 本文指定なし
block("本文が指定されていません")
PY_EOF
