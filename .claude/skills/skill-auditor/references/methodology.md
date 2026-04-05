# Methodology — 評価手法の理論的背景

## 問題設定: Attention Competition（注意力競合）

複数のスキルが LLM のルーティング判断を巡って競合する問題。
スキル数が増えるほど、各スキルの description が「注意力予算」を奪い合い、
個々のスキルの選択精度が低下する。

### Whack-a-Mole 問題

- スキル A の description を強化すると、隣接するスキル B の選択率が低下
- 個別最適化がポートフォリオ全体の劣化を招く
- 単体テスト（skill-creator）では検出できず、結合テスト（skill-auditor）が必要

### 根拠論文

1. **"Tool Preferences in Agentic LLMs are Unreliable"**
   - assertive なキーワードを追加すると、同一機能のツールでも使用率が 7-11x に増加
   - description のトーンが選択率に直接影響する

2. **"How Many Instructions Can LLMs Follow at Once?"**
   - フロンティアモデルでも 500 指示で精度 68% に低下
   - 劣化パターン: threshold decay, linear decline, early collapse

## 評価手法: Agent-as-a-Judge

### IR アナロジー

スキルルーティングを情報検索（IR）問題として捉える:

| IR 概念 | skill-auditor での対応 |
|---------|----------------------|
| Query | ユーザーメッセージ |
| Document | スキル定義（description） |
| Relevance | スキルの適合性 |
| Precision | 発火したスキルのうち正しかった割合 |
| Recall | 発火すべきだったスキルのうち実際に発火した割合 |

### 3世代の評価パラダイム

| 世代 | 手法 | skill-auditor での適用 |
|------|------|----------------------|
| Outcome-only | 最終結果の正否 | スキルが発火したか否か |
| Trajectory-aware | プロセス品質 | セッションコンテキストを含めた判定 |
| Agent-as-a-Judge | LLM が LLM を評価 | 構造化ルブリックによるルーティング判定 |

### High-score Illusion への対処

TRACE 論文の指摘: スキルが「発火した」だけでは正しいとは限らない。
wrong context で発火した場合も outcome-only では correct と誤判定される。

skill-auditor は trajectory-aware:
- ユーザーメッセージの文脈（前後のターン）を考慮
- 発火タイミングの妥当性を評価
- 連続発火パターンの識別

## 品質制御

### 信頼度レベル

各判定に high / medium / low の信頼度を付与:
- **high**: 明確なキーワードマッチまたは明確な不一致
- **medium**: コンテキスト依存の判断
- **low**: 曖昧なケース（参考値扱い）

### ノイズフィルタリング

- 単発のインシデントはノイズとして扱う
- 2件以上の同一パターンをシグナルとする
- false_negative は保守的に判定（「あったら便利」は含めない）

### 自己参照回避

- skill-auditor 自体の発火は評価対象外
- 組み込みコマンド（/help 等）は除外

## skill-creator との関係

| 次元 | skill-creator | skill-auditor |
|------|---------------|---------------|
| タイミング | デプロイ前（作成時） | デプロイ後（運用時） |
| スコープ | 単体スキル | スキルポートフォリオ全体 |
| データ | 合成テストクエリ | 実セッションログ |
| 単位 | 1 つの description | 全スキルセット（カスケードチェック付き） |
| 核心の問い | 「このスキルは良いか？」 | 「スキル群は協調して動くか？」 |

アナロジー: **unit test（skill-creator）** vs **integration test（skill-auditor）**
