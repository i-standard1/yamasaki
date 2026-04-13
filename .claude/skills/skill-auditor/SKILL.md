---
name: skill-auditor
description: |
  SKILLポートフォリオの健全性を監査する。実セッションのトランスクリプトを分析し、
  ルーティング正確性・注意力予算・スキル間競合・カバレッジギャップを定量評価する。
  「スキルの動作確認をして」「SKILLが正常か確認して」「スキル監査して」
  「skill audit」「スキルの健全性チェック」などのリクエストで使用する。
  disable-model-invocation: false
context:
  required:
    - _shared/subagent-task-format.md
    - skill-auditor/decision-tree.md
    - _shared/health-check.md
---

# Skill Auditor — ポートフォリオ健全性監査

実セッションのトランスクリプトを分析し、スキルポートフォリオ全体の健全性を
定量評価する 6 フェーズパイプライン。

## 設計原則

| レイヤー | 担当 | 理由 |
|----------|------|------|
| Python スクリプト | トランスクリプト収集、トークン計測、HTML 生成 | 決定論的精度が必要 |
| サブエージェント | ルーティング判定、競合分類、カスケードリスク評価 | 推論・判断が必要 |
| SKILL.md（本ファイル） | データフロー制御、バッチ分割、ユーザー対話 | 薄い指揮者 |

---

## パイプライン概要

| Phase | 実行者 | 概要 |
|-------|--------|------|
| Phase 1 | Python スクリプト | `~/.claude/` からセッション JSONL を収集・構造化 |
| Phase 2 | Python スクリプト | `.claude/skills/` を走査してスキル定義を収集 |
| Phase 3 | routing-analyst サブエージェント（並列） | セッションをバッチ分割してルーティング正確性を分析 |
| Phase 4 | portfolio-analyst サブエージェント | 競合・デッドスキル・カバレッジギャップを分析 |
| Phase 5 | improvement-planner サブエージェント | 改善パッチ提案を生成（優先度付き） |
| Phase 6 | Python スクリプト | HTML レポート生成・health-history 追記 |

詳細な手順（コマンド・処理内容・入出力・バッチ分割ルール・エージェント起動方法）:
→ [references/phase-details.md](references/phase-details.md)

---

## 中間成果物

```
logs/skill-auditor/{run_id}/
├── transcripts.json      ← Phase 1
├── skills.json            ← Phase 2
├── routing/
│   ├── batch_0.json       ← Phase 3
│   ├── batch_1.json
│   └── ...
├── portfolio.json         ← Phase 4
├── patches.json           ← Phase 5
└── report.html            ← Phase 6
```

`{run_id}` はタイムスタンプ形式: `YYYYMMDD_HHMMSS`

パッチ適用手順・成果物配置の詳細:
→ [references/patch-and-artifacts.md](references/patch-and-artifacts.md)
