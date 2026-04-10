#!/usr/bin/env bash
# =============================================================================
# PreToolUse hook: execution-rules.yml に基づくコマンド実行制約の強制
# =============================================================================
#
# 1. execution-rules.yml が存在しない場合:
#    テスト・ビルド系コマンドをブロックし、ルール定義を促す
# 2. 存在する場合:
#    コマンドがルールに該当すれば、正しい実行方法を強制する
#
# exit 0 = 許可, exit 2 = ブロック
# =============================================================================

set -u

# stdin から実行予定のコマンドを取得
INPUT=$(cat)
COMMAND=$(echo "$INPUT" | python3 -c "
import sys, json
data = json.load(sys.stdin)
print(data.get('tool_input', {}).get('command', ''))
" 2>/dev/null || echo "")

if [ -z "$COMMAND" ]; then
  exit 0
fi

# --- execution-rules.yml のパスを探す ---
# カレントディレクトリから上方向に探索
RULES_FILE=""
SEARCH_DIR="$(pwd)"
for _ in 1 2 3 4 5; do
  if [ -f "$SEARCH_DIR/.claude/execution-rules.yml" ]; then
    RULES_FILE="$SEARCH_DIR/.claude/execution-rules.yml"
    break
  fi
  SEARCH_DIR="$(dirname "$SEARCH_DIR")"
done

# --- テスト・ビルド系コマンドのパターン ---
BUILD_TEST_PATTERNS="npm run test|npm run build|npx jest|npx prisma|tsc |tsc$|npm run dev|npm run start|npm run lint|npx playwright"

# --- ルールファイルが存在しない場合 ---
if [ -z "$RULES_FILE" ]; then
  if echo "$COMMAND" | grep -qE "$BUILD_TEST_PATTERNS"; then
    cat >&2 <<'MSG'
BLOCKED: execution-rules.yml が未定義です。

テスト・ビルド系コマンドを実行する前に、プロジェクトの実行ルールを定義してください。
.claude/execution-rules.yml を作成し、各コマンドの正しい実行方法を記述してください。

参考: .claude/execution-rules.example.yml
MSG
    exit 2
  fi
  # テスト・ビルド系でなければ素通し
  exit 0
fi

# --- ルールファイルを解析してチェック ---
# Python で YAML を解析（PyYAML 不要、簡易パーサー）
RESULT=$(python3 << PYEOF
import sys, re

command = '''$COMMAND'''
rules_file = '''$RULES_FILE'''

# 簡易 YAML パーサー（PyYAML なしで動作）
current_rule = {}
rules = []
in_rules = False

with open(rules_file) as f:
    for line in f:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        if stripped == 'rules:':
            in_rules = True
            continue
        if not in_rules:
            continue
        # 新しいルールの開始
        if stripped.startswith('- pattern:'):
            if current_rule:
                rules.append(current_rule)
            current_rule = {'pattern': stripped.split('"')[1] if '"' in stripped else stripped.split("'")[1]}
        elif stripped.startswith('must:') and current_rule:
            val = stripped[5:].strip().strip('"').strip("'")
            current_rule['must'] = None if val == 'null' else val
        elif stripped.startswith('reason:') and current_rule:
            current_rule['reason'] = stripped[7:].strip().strip('"').strip("'")
        elif stripped.startswith('scope:') and current_rule:
            current_rule['scope'] = stripped[6:].strip().strip('"').strip("'")

    if current_rule:
        rules.append(current_rule)

# コマンドをルールに照合
for rule in rules:
    pattern = rule.get('pattern', '')
    if not re.search(pattern, command):
        continue

    must = rule.get('must')
    reason = rule.get('reason', '')

    # must が null なら制約なし（通過）
    if must is None:
        print('ALLOW')
        sys.exit(0)

    # must が指定されている場合、コマンドがそのプレフィックスで始まるか確認
    if command.strip().startswith(must):
        print('ALLOW')
        sys.exit(0)

    # ルール違反
    print(f'BLOCK|{must}|{reason}')
    sys.exit(0)

# どのルールにもマッチしなかった → 許可
print('ALLOW')
PYEOF
)

# --- 結果に基づいて許可/ブロック ---
if echo "$RESULT" | grep -q "^BLOCK"; then
  MUST=$(echo "$RESULT" | cut -d'|' -f2)
  REASON=$(echo "$RESULT" | cut -d'|' -f3)

  cat >&2 <<MSG
BLOCKED: 実行ルール違反

$REASON

正しい実行方法:
  $MUST <コマンド>

実行ルール定義: $RULES_FILE
MSG
  exit 2
fi

# --- require_services チェック ---
# ルールに require_services が定義されている場合、Docker サービスの稼働を確認
SERVICES_CHECK=$(python3 << PYEOF
import re

command = '''$COMMAND'''
rules_file = '''$RULES_FILE'''

current_rule = {}
rules = []
in_rules = False
in_services = False

with open(rules_file) as f:
    for line in f:
        stripped = line.strip()
        if stripped.startswith('#') or not stripped:
            continue
        if stripped == 'rules:':
            in_rules = True
            continue
        if not in_rules:
            continue
        if stripped.startswith('- pattern:'):
            if current_rule:
                rules.append(current_rule)
            current_rule = {'pattern': stripped.split('"')[1] if '"' in stripped else stripped.split("'")[1]}
            in_services = False
        elif stripped.startswith('require_services:') and current_rule:
            services_str = stripped[17:].strip()
            # インライン配列: ["front", "api", "db"]
            if '[' in services_str:
                import json
                current_rule['require_services'] = json.loads(services_str.replace("'", '"'))
            in_services = True
        elif stripped.startswith('must:') and current_rule:
            in_services = False
        elif stripped.startswith('reason:') and current_rule:
            in_services = False
        elif stripped.startswith('scope:') and current_rule:
            in_services = False

    if current_rule:
        rules.append(current_rule)

for rule in rules:
    pattern = rule.get('pattern', '')
    if not re.search(pattern, command):
        continue
    services = rule.get('require_services', [])
    if services:
        print(','.join(services))
        break
PYEOF
)

if [ -n "$SERVICES_CHECK" ]; then
  # Docker Compose のプロジェクトディレクトリを探す
  COMPOSE_DIR=""
  SEARCH_DIR="$(pwd)"
  for _ in 1 2 3 4 5; do
    if [ -f "$SEARCH_DIR/docker-compose.yml" ]; then
      COMPOSE_DIR="$SEARCH_DIR"
      break
    fi
    SEARCH_DIR="$(dirname "$SEARCH_DIR")"
  done

  if [ -n "$COMPOSE_DIR" ]; then
    MISSING=""
    IFS=',' read -ra REQUIRED_SERVICES <<< "$SERVICES_CHECK"
    for svc in "${REQUIRED_SERVICES[@]}"; do
      STATUS=$(docker compose -f "$COMPOSE_DIR/docker-compose.yml" ps --format '{{.Service}} {{.State}}' 2>/dev/null | grep "^$svc " | awk '{print $2}')
      if [ "$STATUS" != "running" ]; then
        MISSING="$MISSING $svc"
      fi
    done

    if [ -n "$MISSING" ]; then
      cat >&2 <<MSG
BLOCKED: 必要な Docker サービスが起動していません

停止中のサービス:$MISSING

以下のコマンドで起動してください:
  cd $COMPOSE_DIR && docker compose up -d$MISSING
MSG
      exit 2
    fi
  fi
fi

# 許可
exit 0
