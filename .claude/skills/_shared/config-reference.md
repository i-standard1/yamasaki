# Claude Code 設定リファレンス

スキル・ルール・設定ファイルの作成・編集時に参照する公式仕様。

## 1. Skill フロントマター（.claude/skills/*/SKILL.md）

| フィールド | 型 | デフォルト | 説明 |
|-----------|---|----------|------|
| `name` | string | ディレクトリ名 | スキル名。`/name` でスラッシュコマンドになる（小文字・ハイフンのみ、64文字以内） |
| `description` | string | 本文の最初の段落 | スキルの説明。Claudeが自動発火判定に使う。250文字で切られる。用途を先頭に書く |
| `argument-hint` | string | なし | 補完時のヒント表示（例: `[issue-number]`, `[filename] [format]`） |
| `disable-model-invocation` | boolean | `false` | `true` でClaudeの自動発火を禁止。手動 `/name` でのみ起動 |
| `user-invocable` | boolean | `true` | `false` で `/` メニューから非表示。背景知識用 |
| `allowed-tools` | string/list | なし | スキル実行中に確認なしで使えるツール |
| `model` | string | セッション継承 | 使用モデル（`opus`, `sonnet`, `haiku`, フルモデル名） |
| `effort` | string | セッション継承 | 推論レベル（`low`, `medium`, `high`, `max`）。`max` は Opus 4.6 のみ |
| `context` | string | inline | `fork` で親会話から隔離されたサブエージェントとして実行 |
| `agent` | string | `general-purpose` | `context: fork` 時のサブエージェント種別 |
| `hooks` | object | なし | スキルライフサイクルにスコープされたフック |
| `paths` | string/list | なし | ファイルglobパターン。マッチするファイル操作時のみ発火 |
| `shell` | string | `bash` | `` !`command` `` のシェル種別 |

### 文字列置換

- `$ARGUMENTS` — スキル呼び出し時の全引数
- `$ARGUMENTS[N]` / `$N` — N番目の引数（0始まり）
- `${CLAUDE_SESSION_ID}` — セッションID
- `${CLAUDE_SKILL_DIR}` — スキルディレクトリパス

## 2. Rule ファイル（.claude/rules/*.md）

| フィールド | 型 | 説明 |
|-----------|---|------|
| `paths` | string/list | ファイルglobパターン。マッチするファイルをClaudeが**読んだとき**にロード |
| `description` | string | ルールの説明 |
| `alwaysApply` | boolean | `true` で常時ロード |

### ロード動作

- `paths` なし → セッション開始時に無条件ロード
- `paths` あり → マッチするファイルを**読んだとき**にロード（編集時だけでなく参照時も発火）
- `alwaysApply: true` → 常時ロード

### 優先順位

1. ユーザールール（`~/.claude/rules/`）→ 先にロード（低優先）
2. プロジェクトルール（`.claude/rules/`）→ 後にロード（高優先）
3. 同レベル内はファイル名のアルファベット順

## 3. Settings ファイル

### ファイルの優先順位（上が優先）

| ファイル | スコープ | 共有 |
|---------|---------|------|
| マネージドポリシー | 組織全体 | Yes |
| CLIフラグ | セッション | No |
| `.claude/settings.local.json` | プロジェクト | No（gitignore） |
| `.claude/settings.json` | プロジェクト | Yes |
| `~/.claude/settings.json` | 全プロジェクト | No |

### 主要キー

| キー | 型 | 説明 |
|-----|---|------|
| `permissions.allow` | array | 確認なしで許可するツール |
| `permissions.deny` | array | 完全にブロックするツール |
| `permissions.ask` | array | 初回使用時に確認するツール |
| `model` | string | デフォルトモデル |
| `effortLevel` | string | デフォルトエフォート（`low`, `medium`, `high`） |
| `hooks` | object | フック設定 |
| `env` | object | 環境変数 |
| `sandbox.enabled` | boolean | Bashのサンドボックス |

## 4. Agent ツール パラメータ

| パラメータ | 型 | 説明 |
|-----------|---|------|
| `model` | string | モデル（`opus`, `sonnet`, `haiku`, フルモデル名）。省略時はセッション継承 |
| `isolation` | string | `worktree` でgit worktree隔離 |
| `prompt` | string | サブエージェントへの指示（唯一のコンテキスト伝達手段） |
| `effort` | string | 推論レベル |
| `maxTurns` | number | 最大ターン数 |

## 5. カスタムサブエージェント（.claude/agents/*/AGENT.md）

Skillと同様のフロントマターに加え以下が使える:

| フィールド | 型 | 説明 |
|-----------|---|------|
| `tools` | list | 許可ツール（ホワイトリスト） |
| `disallowedTools` | list | ブロックするツール |
| `permissionMode` | string | 権限モード |
| `mcpServers` | list | 利用可能なMCPサーバー |
| `skills` | list | プリロードするスキル |
| `memory` | boolean | 自動メモリ有効化 |
| `color` | string | ターミナル表示色 |

## 6. 重要な制約・注意事項

### Skill のモデル切替

- **本体 → Skill(model: X)**: 動作する。スキル実行中はXモデルが使われる
- **Skill → Skill(model: X)**: 未文書化。ネスト時のモデル切替は動作保証なし
- Skillは「会話に注入されるプロンプト」であり、スコープの開始・終了が明確でない

### Agent のコンテキスト

- サブエージェントは**親の会話履歴を一切持たない**（フレッシュコンテキスト）
- 親→子の情報伝達は `prompt` パラメータのみ
- CLAUDE.md はロードされるが、親の rules はロードされない
- MCP サーバーは自動継承されない（明示的に `mcpServers` で指定が必要）

### コンテキスト圧縮時のスキル挙動

- 呼び出し済みスキルは圧縮後に再注入される（スキルあたり先頭5,000トークン）
- 全スキル合計で25,000トークンの予算
- 多数のスキルを1セッションで呼ぶと、古いスキルが完全に落ちる可能性あり

### パーミッションルール構文

```
Tool              → 全操作を許可
Tool(*)           → 同上
Tool(npm run *)   → npm run で始まるコマンド
Edit(*.ts)        → TypeScript ファイルの編集
Read(./.env)      → .env の読み取り
mcp__server__*    → MCPサーバーの全ツール
```

## 7. Hooks（フック）

### ライフサイクルイベント

| タイミング | イベント |
|-----------|---------|
| セッション単位 | `SessionStart`, `SessionEnd` |
| ターン単位 | `UserPromptSubmit`, `Stop`, `StopFailure` |
| ツール呼び出し単位 | `PreToolUse`, `PostToolUse`, `PostToolUseFailure`, `PermissionRequest`, `PermissionDenied` |
| 非同期 | `FileChanged`, `ConfigChange`, `CwdChanged`, `Notification`, `SubagentStart`, `SubagentStop`, `InstructionsLoaded` |

### フックの種類

| type | 説明 |
|------|------|
| `command` | シェルコマンド実行。stdinにJSON、exit code 0=成功、2=ブロッキングエラー |
| `http` | URLにPOST送信 |
| `prompt` | Claudeにyes/no判定させる |
| `agent` | サブエージェントで条件検証 |

### フック設定フィールド

| フィールド | 型 | 説明 |
|-----------|---|------|
| `type` | string | フック種別（`command`, `http`, `prompt`, `agent`） |
| `if` | string | パーミッションルール構文でフィルタ（例: `Bash(git *)`, `Edit(*.ts)`） |
| `matcher` | string | イベント名のフィルタ。完全一致、パイプ区切り、正規表現 |
| `timeout` | number | タイムアウト秒数 |
| `statusMessage` | string | 実行中のスピナーメッセージ |
| `once` | boolean | スキル内のみ: セッションで1回だけ実行 |

### matcher パターン

- `"*"`, `""`, 省略 → 全マッチ
- 英数字・`_`・`|` のみ → 完全一致またはパイプ区切り（例: `"Bash"`, `"Edit|Write"`）
- その他の文字を含む → JavaScript正規表現（例: `"^Notebook"`, `"mcp__.*"`）

### フック入力JSON（全フックが受け取る）

```json
{
  "session_id": "abc123",
  "transcript_path": "/path/to/transcript.jsonl",
  "cwd": "/current/directory",
  "permission_mode": "default|plan|auto|...",
  "hook_event_name": "PreToolUse",
  "agent_id": "optional",
  "agent_type": "optional"
}
```

### フック出力JSON

```json
{
  "continue": true,
  "stopReason": "停止理由",
  "suppressOutput": false,
  "systemMessage": "警告メッセージ",
  "hookSpecificOutput": { "..." }
}
```

### コマンドフック変数

- `$CLAUDE_PROJECT_DIR` — プロジェクトルート
- `${CLAUDE_PLUGIN_ROOT}` — プラグインディレクトリ
- `${CLAUDE_PLUGIN_DATA}` — プラグイン永続データディレクトリ

## 8. 公式ドキュメントURL

変更・作成時に最新仕様を確認する場合:

- Skills: https://docs.anthropic.com/en/docs/claude-code/skills
- Memory/Rules: https://docs.anthropic.com/en/docs/claude-code/memory
- Settings: https://docs.anthropic.com/en/docs/claude-code/settings
- Hooks: https://docs.anthropic.com/en/docs/claude-code/hooks
- Model Config: https://docs.anthropic.com/en/docs/claude-code/model-configuration
- Subagents: https://docs.anthropic.com/en/docs/claude-code/sub-agents
- Permissions: https://docs.anthropic.com/en/docs/claude-code/permissions
