# PR本文への生成環境（モデル・エフォート）記載 — 作業引き継ぎ

## 依頼内容

PR作成時に、その時点の Claude Code のモデル・エフォート設定を PR 本文に記載できるようにする。

確定したスコープ（ユーザー承認済み）:

- 記載項目: **モデル / エフォート / Claude Code バージョン**（生成日時・entrypoint は不採用）
- 実装範囲: **生成スクリプト + ルール + PRテンプレ + フックによる記載漏れブロック**
- テンプレートリポ向け PR（feedback-template スキル）にも同じブロックを含める

## ブランチとコミット（push 済み）

ブランチ: `claude/pr-model-effort-metadata-ipcu5e`

| コミット | 内容 |
|---------|------|
| `0bd3c56` | 生成スクリプト・PRテンプレ・git-workflow ルール |
| `9e89e38` | feedback-template のPR本文に生成環境ブロックを追加 |
| `9349a05` | PreToolUse フックで記載漏れをブロック |

変更ファイル（7件・+278/-7）:

```
.claude/hooks/pr-env-metadata.sh            新規  値の生成
.claude/hooks/check-pr-env-metadata.sh      新規  記載漏れの検出・ブロック
.claude/settings.json                       変更  フック登録
.claude/rules/git-workflow.md               変更  PR本文ルール
.claude/rules/security.md                   変更  フック一覧に追記
.claude/skills/feedback-template/SKILL.md   変更  PR作成手順を --body-file 方式に
.github/pull_request_template.md            新規  PRテンプレ
```

## 仕組み

### 1. 値の取得元（調査で確定した根拠）

- **一次ソース: セッションのトランスクリプト** `~/.claude/projects/<cwdスラッグ>/<session_id>.jsonl`
  assistant レコードに `message.model` / `effort` / `version` が記録されている
  （本セッションでの実測: `claude-opus-5` / `high` / `2.1.246`）
- **フックの入力 JSON には model / effort は含まれない**（`.claude/skills/_shared/config-reference.md:169-185`）
  ため、フック経由でもトランスクリプトを読む必要がある
- フォールバック: 環境変数 `CLAUDE_EFFORT`、`AI_AGENT`（`claude-code_2-1-246_agent` からバージョン抽出）
- 取得できない項目は **「不明」** と出力する（推測で埋めない = エビデンス検証ルール準拠）

### 2. 出力フォーマット

```markdown
<!-- claude-env -->
## 生成環境

| 項目 | 値 |
|------|-----|
| モデル | claude-opus-5 |
| エフォート | high |
| Claude Code | 2.1.246 |
```

`<!-- claude-env -->` がフックの検出マーカーを兼ねる。

### 3. 運用フロー

1. PR 作成時に `.claude/hooks/pr-env-metadata.sh` を実行
2. 出力を PR 本文（テンプレの該当箇所）に貼る。`--body-file` 利用時はファイルに追記
3. マーカーが無いまま `gh pr create` / `mcp__github__create_pull_request` を実行すると
   `check-pr-env-metadata.sh` が exit 2 でブロックする

## 検証済み事項（実行証跡あり）

`pr-env-metadata.sh`:

| ケース | 結果 |
|--------|------|
| 通常実行 / トランスクリプト明示指定 | 実測値を出力 |
| トランスクリプト不在（環境変数のみ） | モデル「不明」、他は環境変数から補完 |
| 何も取得できない | 3項目とも「不明」+ stderr 警告、exit 0 |

`check-pr-env-metadata.sh`（11ケース）:

| ケース | 結果 |
|--------|------|
| `--body` マーカー無し / 有り | ブロック / 通過 |
| `--body-file` 実在（無し / 有り） | ブロック / 通過 |
| `--body-file "$PR_BODY"`（変数） | 通過 + 警告のみ |
| `--body-file` 未作成ファイル | 通過 + 警告のみ |
| MCP `create_pull_request`（無し / 有り） | ブロック / 通過 |
| `--fill` | ブロック |
| `--web` / 無関係コマンド / 別ツール / 壊れたJSON | すべて通過 |

feedback-template の手順6: PR作成直前まで実行し、本文末尾に生成環境ブロックが付くことを確認済み。

**未検証**: `gh` が当環境に無いため、実際の `gh pr create` 実行とフック連携の実地確認は未実施。

## 残タスク

1. **この変更の PR を作成する**（未作成）
   - compare: https://github.com/i-standard1/yamasaki/compare/main...claude/pr-model-effort-metadata-ipcu5e
   - 本文には `.claude/hooks/pr-env-metadata.sh` の出力を含めること（自分自身が第1号の適用例になる）
2. **実地確認**: 実際に `gh pr create` を叩き、(a) マーカー無しでブロックされる (b) マーカー有りで通る、を確認
3. マージ後、他プロジェクトへ `sync-template` で展開するか判断

## 注意点・判断メモ（WHY NOT）

- **リモート実行セッション（Claude Code on the web）ではPR本文にモデル識別子を書けない**
  システム側ポリシーによる制約のため、PR 作成はローカル CLI / Cowork 側で行う必要がある。
  これが本作業を引き継ぐ主な理由。
- `--body-file` の中身が判定できない場合に**ブロックしない**のは意図的。
  フックは PreToolUse で走るため、同一コマンド内で本文ファイルを生成するケースでは
  実行時点でファイルが存在せず、厳格に判定すると feedback-template の手順自体が詰まる。
- `gh pr create --fill` はマーカーが入らないためブロックされる。
  人間が手動で作る場合は `--web`（対象外）を使うか、ブロックを貼ってから実行する。
- テンプレートリポ側の PR（`/tmp/yamasaki` から作成）でこの仕組みが効くのは、
  本変更がテンプレートリポの main にマージされて以降。
- 手順の番号飛び（feedback-template の「### 6」→「### 8」）は既存の不整合。
  依頼範囲外のため触っていない。
