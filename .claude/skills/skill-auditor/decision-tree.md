# スキル選択フローチャート

ユーザーのリクエストに対して、どのスキルを使うべきかを判定する。

## 判定フロー

```
リクエストを受け取る
│
├─ コードが存在しない（新規プロジェクト）
│  ├─ 「機能を作りたい」→ draft-spec
│  ├─ 「全部設計して」→ draft-spec を繰り返し → detail-design
│  └─ 「実装して」→ まず draft-spec を提案
│
├─ コードが存在する（既存プロジェクト）
│  ├─ Specが存在しない
│  │  ├─ 「セットアップして」→ init-spec
│  │  ├─ 「この機能のSpecを作って」→ spec-feature
│  │  ├─ 「全機能のSpecを作って」→ spec-all
│  │  └─ 「既存プロジェクトを分析して」
│  │     ├─ ファイル200以上 → analyze-codebase → init-spec
│  │     └─ ファイル200未満 → init-spec（直接）
│  │
│  └─ Specが存在する
│     ├─ ドキュメントのみの作業
│     │  ├─ 「詳細設計を作って」→ detail-design
│     │  ├─ 「テスト仕様書を作って」→ gen-test-specs
│     │  ├─ 「テスト報告書を作って」→ gen-test-report
│     │  └─ 「設計書を最新にして」→ update-docs
│     │
│     ├─ コード変更を伴う作業
│     │  ├─ 緊急？（本番障害・セキュリティ）
│     │  │  ├─ YES → hotfix
│     │  │  └─ NO ↓
│     │  ├─ 新機能の実装？
│     │  │  ├─ YES → implement-spec（→ orchestrate が自動起動）
│     │  │  └─ NO ↓
│     │  ├─ 既存機能の変更？
│     │  │  ├─ YES → revise-spec（→ orchestrate が自動起動）
│     │  │  └─ NO ↓
│     │  ├─ 見た目だけの変更？
│     │  │  ├─ YES → apply-design
│     │  │  └─ NO ↓
│     │  └─ テストの追加・補強？
│     │     └─ YES → gen-tests
│     │
│     └─ テンプレート管理
│        ├─ 「テンプレートを更新して」→ sync-template
│        └─ 「この改善をテンプレートに反映して」→ feedback-template
```

## よくある迷いポイント

### draft-spec vs spec-feature
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| まだコードがない新機能 | draft-spec | WHATを定義する |
| 既に動いているコードがある | spec-feature | コードからSpecを逆生成する |
| 既存コードに新機能を追加 | draft-spec | 新機能部分はWHATから定義する |

### spec-all vs spec-feature
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| プロジェクト全体を一括Spec化 | spec-all | PM並列オーケストレーションで効率化 |
| 特定機能だけをSpec化 | spec-feature | 1機能に集中して精度を上げる |
| 20機能以上のSpec化 | spec-all | 個別にspec-featureを繰り返すより効率的 |

### spec-all vs detail-design
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| 要件定義書（WHAT）を作りたい | spec-all | Phase 1 のドキュメント生成 |
| 詳細設計書（HOW）を作りたい | detail-design | Phase 3 のドキュメント生成 |
| 両方必要 | spec-all → detail-design | 順番に実行する |

### hotfix vs revise-spec
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| 本番障害で今すぐ直す必要がある | hotfix | コード先行を許可（24h以内にSpec同期） |
| セキュリティ脆弱性の即時修正 | hotfix | 同上 |
| 通常の仕様変更・機能改善 | revise-spec | 設計書ファースト原則を守る |
| ユーザーが「緊急」と明示 | hotfix | 例外措置として許可 |

### implement-spec vs revise-spec
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| Specはあるがコードがまだない | implement-spec | 新規実装 |
| Specもコードも存在し、仕様を変える | revise-spec | Spec更新 → コード修正 |
| Specもコードも存在し、バグ修正 | revise-spec | 仕様の明確化として扱う |

### revise-spec vs update-docs
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| 仕様変更が先にある（設計書ファースト） | revise-spec | Spec更新 → コード修正（正規フロー） |
| やむを得ずコードを先に変更した | update-docs | コード変更 → Spec追従（例外措置） |
| hotfix後のSpec同期 | update-docs | コードが先行しているため |
| Specが存在しないが実装済み | spec-feature → revise-spec | まずSpec化してから変更する |

### apply-design vs revise-spec
| 状況 | 使うスキル | 理由 |
|------|-----------|------|
| CSS・テキスト・レイアウトのみ変更 | apply-design | ロジック不変、Spec更新不要 |
| 見た目の変更 + バリデーション追加 | revise-spec | ロジック変更を伴うため |
| デザインカンプの差し替え | apply-design | HTML/CSS/テンプレートのみ |
