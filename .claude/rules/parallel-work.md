---
paths:
  - "**/*"
description: 並列エージェント作業時の worktree 分離・ブランチ命名・統合ルール（複数タスクの同時作業時にロード）
triggers:
  - "並列"
  - "同時に"
  - "worktree"
  - "parallel"
---

# 並列作業ルール

## 原則

**タスク単位で作業環境を分離する。** 複数タスクを同時に処理する場合、各タスクは独立した worktree で作業し、互いの変更が干渉しないようにする。

**コンテキスト効率を最大化する。** 各タスクを専用エージェントに委任し、エージェント間でコンテキストを共有しない。これにより各エージェントが必要最小限の情報だけを持ち、精度と速度を両立する。

**品質は取りまとめエージェントが担保する。** 全タスクエージェント完了後、必ず横断レビュー専用の取りまとめエージェントを起動し、整合性・品質を検証する。

## 分離の判断基準

| 状況 | 方針 |
|------|------|
| 複数タスクを同時に処理 | タスクごとに別 worktree（並列） |
| 1タスクが複数リポにまたがる | リポごとに worktree を作り、同名ブランチで束ねる |
| 1タスクが単一リポで完結 | 1 worktree で処理 |
| タスク間に依存関係がある | 依存元を先に完了 → 依存先を後で実行（直列） |

## ブランチ命名

**同一タスク内は全リポで同名ブランチを使う。** これによりタスクとブランチの対応が明確になる。

```
{type}/{issue番号}-{概要}
```

例:
```
fix/201-login-error       ← back, front, docs 全リポ共通
feat/100-delivery-route   ← back, front, docs 全リポ共通
docs/26-overview-format   ← docs リポのみ
```

## Agent 起動パターン

### パターン A: 複数タスク × 単一リポ

```python
# 各タスクを独立 worktree で並列実行
Agent(isolation="worktree", prompt="Task A: foo.md を修正。ブランチ名: docs/task-a-foo")
Agent(isolation="worktree", prompt="Task B: bar.md を修正。ブランチ名: docs/task-b-bar")
Agent(isolation="worktree", prompt="Task C: baz.md を修正。ブランチ名: docs/task-c-baz")
```

### パターン B: 単一タスク × 複数リポ

```python
# 同一タスクをリポ別に並列実行（同名ブランチ）
Agent(isolation="worktree", prompt="Task #201: back リポで修正。ブランチ名: fix/201-login-error", cwd="back/")
Agent(isolation="worktree", prompt="Task #201: front リポで修正。ブランチ名: fix/201-login-error", cwd="front/")
# 両方完了後
Agent(prompt="Task #201: 統合テスト実行")
```

### パターン C: 複数タスク × 複数リポ

パターン A と B の組み合わせ。タスク × リポ の直積で worktree を生成。

```python
# Task #201 (back + front)
Agent(isolation="worktree", prompt="#201 back修正。branch: fix/201-login-error", cwd="back/")
Agent(isolation="worktree", prompt="#201 front修正。branch: fix/201-login-error", cwd="front/")

# Task #202 (back のみ)
Agent(isolation="worktree", prompt="#202 back修正。branch: fix/202-csv-encoding", cwd="back/")

# 全完了後 → 統合レビュー
```

## エージェント構成

### 作業エージェント（タスクごとに1体）
- 1タスク = 1エージェント = 1 worktree
- そのタスクに必要な情報だけをプロンプトに含める（他タスクの情報は渡さない）
- 完了したら変更内容のサマリだけを返す

### 取りまとめエージェント（最後に1体）
- 全作業エージェント完了後に起動する
- 全ブランチ/worktree の差分を横断的にレビュー
- 以下を検証する:
  1. **整合性**: ファイル間の相互参照・リンク切れがないか
  2. **品質**: 受入条件・コーディング規約を満たしているか
  3. **コンテンツ保全**: 既存コンテンツが消えていないか
  4. **ビルド**: `mkdocs build`、`npm run build` 等がエラーなく通るか
- 問題があれば自分で修正する（報告だけでなく実際に直す）

## 統合フェーズ

取りまとめエージェントのレビュー完了後:

1. **PR作成**: タスク単位で PR を作成（1タスク = 1PR）
2. **マルチリポの場合**: 各リポの PR を相互参照（`See also: back#XX, front#YY`）
3. **まとめて1PRが適切な場合**: 関連タスクの worktree を1ブランチに集約してから PR

## 禁止事項

- 同一ブランチ・同一ワーキングツリーで複数エージェントが同時に書き込むこと
- worktree を使わずに並列エージェントでファイル編集すること
- タスクをまたいで1つの worktree にまとめること（コンフリクトの原因）
