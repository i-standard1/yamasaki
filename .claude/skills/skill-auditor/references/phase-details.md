# Phase 詳細手順

## Phase 1: トランスクリプト収集

**実行者**: Python スクリプト（決定論的）

```bash
python3 .claude/skills/skill-auditor/scripts/collect_transcripts.py \
  --project-dir "$(pwd)" \
  --output logs/skill-auditor/{run_id}/transcripts.json
```

### 処理内容
1. `~/.claude/projects/` からプロジェクトパスに一致するセッション JSONL を検索
2. 各 JSONL をパースし、以下を抽出:
   - `type: "user"` → ユーザー意図（message.content[].text）
   - `type: "assistant"` の `tool_use` where `name == "Skill"` → スキル発火
   - `type: "assistant"` の `tool_use` where `name == "Agent"` → サブエージェント起動
   - `message.usage` → トークン消費
3. セッション単位で構造化し `transcripts.json` を出力

### 出力確認
- セッション数・ターン数をユーザーに報告
- セッション数が 0 の場合は中断し、`~/.claude/` のパス構造を報告

---

## Phase 2: スキル定義収集

**実行者**: Python スクリプト（決定論的）

```bash
python3 .claude/skills/skill-auditor/scripts/collect_skills.py \
  --skills-dir .claude/skills \
  --output logs/skill-auditor/{run_id}/skills.json
```

### 処理内容
1. `.claude/skills/*/SKILL.md` を走査
2. 各スキルから抽出:
   - frontmatter: name, description, context.required
   - description のトークン数（単語数 × 1.3 で近似）
   - `_shared/` 参照先の存在確認
   - `on_error` ハンドラの有無
3. `skills.json` を出力

### 出力確認
- スキル数・合計トークン数をユーザーに報告

---

## Phase 3: 並列ルーティング分析

**実行者**: routing-analyst サブエージェント（並列 N バッチ）

### バッチ分割
```
セッション数 < 50  → 3 バッチ
セッション数 50-200 → 6 バッチ
セッション数 > 200  → 12 バッチ
```

各バッチはセッション時系列順で均等分割する。

### エージェント起動

各バッチについて Agent ツールを **1 つのメッセージで同時に呼び出す**（並列実行）。

```
Agent ツール呼び出し:
  subagent_type: routing-analyst
  prompt: skills.json（全スキル定義）
        + transcripts.json のバッチ N 分
  output: logs/skill-auditor/{run_id}/routing/batch_{N}.json
```

### 完了確認
- 全バッチの完了を待機
- 各バッチの判定件数・カテゴリ分布をユーザーに報告

---

## Phase 4: ポートフォリオ分析

**実行者**: portfolio-analyst サブエージェント（単体）

### 入力
- `skills.json`（Phase 2）
- `routing/batch_*.json`（Phase 3 の全結果）

### エージェント起動

```
Agent ツール呼び出し:
  subagent_type: portfolio-analyst
  prompt: skills.json
        + 全 routing batch 結果
  output: logs/skill-auditor/{run_id}/portfolio.json
```

### 出力
- Attention Budget（全スキルの description トークン分布）
- Competition Matrix（競合ペア一覧 + 重複キーワード）
- Dead Skill Detection（全セッションで発火ゼロ）
- Coverage Map（カバレッジギャップ一覧）

---

## Phase 5: 改善パッチ生成

**実行者**: improvement-planner サブエージェント（単体）

### 入力
- `skills.json`（Phase 2）
- `portfolio.json`（Phase 4）
- 各スキルの SKILL.md 原文

### エージェント起動

```
Agent ツール呼び出し:
  subagent_type: improvement-planner
  prompt: skills.json
        + portfolio.json
  output: logs/skill-auditor/{run_id}/patches.json
```

### 出力
- パッチ提案リスト（優先度: high / medium / low）
- 各パッチのカスケード影響評価
- 競合ペアは coordinated patch（セットで修正提案）

---

## Phase 6: レポート生成

**実行者**: Python スクリプト（決定論的）

```bash
python3 .claude/skills/skill-auditor/scripts/generate_report.py \
  --run-dir logs/skill-auditor/{run_id} \
  --template .claude/skills/skill-auditor/assets/report_template.html \
  --history .claude/skills/skill-auditor/health-history.json \
  --output logs/skill-auditor/{run_id}/report.html
```

### 処理内容
1. portfolio.json + patches.json + routing 結果を統合
2. report_template.html にデータを注入して HTML レポート生成
3. health-history.json に今回の実行結果を追記（経時変化追跡）
4. `report.html` を出力

### ユーザー報告
- レポートファイルパスを提示
- 主要指標のサマリーを表示:
  - ルーティング精度（correct / total）
  - false_negative 件数（要改善スキル）
  - 競合ペア数
  - 提案パッチ数（優先度別）
- `apply_patches.py` でのパッチ適用を提案
