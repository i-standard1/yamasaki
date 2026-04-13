# パッチ適用と中間成果物

## パッチ適用（オプション）

ユーザーが承認した場合のみ実行。

```bash
python3 .claude/skills/skill-auditor/scripts/apply_patches.py \
  --patches logs/skill-auditor/{run_id}/patches.json \
  --skills-dir .claude/skills \
  --dry-run  # まずドライランで差分表示
```

---

## 中間成果物の配置

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
