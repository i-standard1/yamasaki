# Architecture — 設計根拠

## 多層処理戦略

### なぜ Python + サブエージェント + SKILL.md の3層か

| 処理の性質 | 最適な実行者 | 理由 |
|-----------|------------|------|
| トランスクリプト収集・パース | Python | 決定論的精度が必要。JSON パースミスは許容できない |
| トークン計測 | Python | 再現可能な数値が必要 |
| ルーティング判定 | サブエージェント | ユーザー意図の解釈に推論が必要 |
| 競合分類 | サブエージェント | 概念レベルの類似度判断が必要 |
| HTML 生成 | Python | テンプレート適用は決定論的 |
| フロー制御 | SKILL.md | ユーザー対話・承認フローが必要 |

### SKILL.md は「薄い指揮者」

SKILL.md は以下のみを担当:
1. Python スクリプトの実行とエラーハンドリング
2. サブエージェントへのデータ受け渡し
3. バッチ分割ロジック
4. ユーザーへの中間報告
5. パッチ適用の承認フロー

判断ロジックや分析ロジックは SKILL.md に書かない。

## agents/ ディレクトリの設計

### なぜエージェント定義を分離するか

1. **再利用性**: routing-analyst は他のプロジェクトでもそのまま使える
2. **テスト可能性**: エージェント単体でプロンプトの品質をテストできる
3. **関心の分離**: SKILL.md（フロー）とエージェント（判断）が混ざらない
4. **コンテキスト効率**: Agent ツールの prompt にファイル内容を渡すため、分離されていると読み込みが明確

### エージェント間の依存関係

```
Phase 1-2: Python scripts (並列実行可能)
    ↓
Phase 3: routing-analyst × N (並列実行)
    ↓
Phase 4: portfolio-analyst (Phase 3 の結果を統合)
    ↓
Phase 5: improvement-planner (Phase 4 の結果を使用)
    ↓
Phase 6: Python script (Phase 4-5 の結果を統合)
```

Phase 3 のみ並列。Phase 4-5 は順次実行（前のフェーズの出力に依存）。

## バッチ分割戦略

### セッション数ベースの分割

単一プロジェクト向けの簡易版。マルチプロジェクト版（参考記事）の
「プロジェクト間スキルセット類似度によるグルーピング」は不要。

```
セッション数 < 50   → 3 バッチ
セッション数 50-200  → 6 バッチ
セッション数 > 200   → 12 バッチ
```

各バッチはセッション時系列順で均等分割。
理由: 時系列順にすることで、スキル追加前後の変化を各バッチ内で一貫して評価できる。

### バッチサイズの制約

- 1 バッチあたり最大 50 セッション
- 1 セッションあたりの平均ターン数を考慮（~30-50 ターン想定）
- Agent ツールのコンテキスト制限を超えないよう、1 バッチの入力を ~100K トークン以内に抑える

## 中間成果物の設計

### なぜ JSON 中間ファイルか

1. **デバッグ可能性**: 各フェーズの出力を個別に検証できる
2. **再実行可能性**: Phase 3 が失敗しても Phase 1-2 からやり直す必要がない
3. **セッション復帰**: Claude Code のセッションが切れても中間成果物から再開可能
4. **透明性**: ユーザーが各フェーズの出力を直接確認できる

### ディレクトリ構造

```
logs/skill-auditor/{run_id}/
├── transcripts.json   ← Phase 1 output
├── skills.json        ← Phase 2 output
├── routing/
│   ├── batch_0.json   ← Phase 3 output (per batch)
│   ├── batch_1.json
│   └── ...
├── portfolio.json     ← Phase 4 output
├── patches.json       ← Phase 5 output
└── report.html        ← Phase 6 output
```

`{run_id}` = `YYYYMMDD_HHMMSS` タイムスタンプ。
run 間の比較は health-history.json で追跡。

## 経時変化追跡

### health-history.json

```
.claude/skills/skill-auditor/health-history.json
```

- 直近 50 回分の実行結果を保持
- 各エントリ: run_id, timestamp, routing_precision, false_negatives 等
- スキル変更後の効果測定に使用
- 精度が低下した場合のアラートトリガー

## セキュリティ考慮

- トランスクリプトにはユーザーの入力が含まれる
- `~/.claude/` の読み取りはサンドボックス制限の対象外（Claude Code 自身のデータ）
- レポート HTML はローカルのみ（外部送信しない）
- patches.json はドライラン必須（自動適用しない）
