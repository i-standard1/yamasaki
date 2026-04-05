# 品質ゲート定義

フェーズ間の遷移条件を定義する。各ゲートの全項目をクリアしないと次フェーズに進めない。

## Gate 1: 要件定義 → 基本設計

| # | チェック項目 | 確認方法 |
|---|------------|---------|
| 1 | 全REQ-IDに受入条件（チェックリスト形式）がある | 各Specの「機能要件」セクションを確認 |
| 2 | glossary.md のカバー率100%（Spec内の専門用語が全て定義済み） | glossary.md と各Specを突合 |
| 3 | REQ-OVERVIEW-001 が存在し、非機能要件・技術スタック・外部依存が記載済み | overview.md を確認 |
| 4 | Spec間の依存関係が dependency-graph.md に反映済み | dependency-graph.md を確認 |
| 5 | 循環依存がない | dependency-graph.md の循環依存セクションを確認 |
| 6 | 全Specのステータスが「確定」（ドラフトが残っていない） | docs/requirements/features/ を確認 |
| 7 | ユーザーの承認を得ている | 人間に確認 |

## Gate 2: 基本設計 → 詳細設計/実装

| # | チェック項目 | 確認方法 |
|---|------------|---------|
| 1 | architecture.md にシステム構成図がある | docs/design/architecture.md を確認 |
| 2 | APIを持つ場合: openapi.yaml が全エンドポイントを網羅 | docs/api/openapi.yaml を確認 |
| 3 | DBを持つ場合: db-design.md に全テーブルのER図がある | docs/design/db-design.md を確認 |
| 4 | UIを持つ場合: screen-flow.md に画面遷移図がある | docs/design/screen-flow.md を確認 |
| 5 | 基本設計の各項目が要件定義のREQ-IDにトレース可能 | 設計書内のREQ-ID参照を確認 |
| 6 | ユーザーの承認を得ている | 人間に確認 |

## Gate 3: 実装 → テスト

| # | チェック項目 | 確認方法 |
|---|------------|---------|
| 1 | spec-map.yml の全REQ-IDで `confirmed == spec_version` | spec-map.yml を確認 |
| 2 | ユニットテストが全パス | テスト実行 |
| 3 | E2Eテストが存在する場合: 全パス | Playwright実行 |
| 4 | 設計書⇔コードの一致性検証済み | finish-impl.md の手順3を実施済み |
| 5 | shared-components.md が最新（該当する場合） | docs/design/shared-components.md を確認 |
| 6 | openapi.yaml がコードと一致（該当する場合） | openapi.yaml とコードを突合 |

## Gate 4: テスト → リリース

| # | チェック項目 | 確認方法 |
|---|------------|---------|
| 1 | 全テスト種別（unit, E2E, system, UAT）の結果が記録済み | docs/tests/test-report.md を確認 |
| 2 | Critical/Majorバグがゼロ | テスト結果報告書を確認 |
| 3 | manual-test-cases.xlsx の全項目が実施済み（該当する場合） | Excelを確認 |
| 4 | デプロイ手順が文書化済み | docs/design/setup-guide.md を確認 |
| 5 | ユーザーの最終承認を得ている | 人間に確認 |

## ゲート判定の運用

- **判定者:** 人間（AIはゲート項目の自動チェック結果を提示し、人間が最終判定する）
- **例外:** ホットフィックスはGate 1〜2をスキップ可能（ただし24時間以内にSpec同期が必要）
- **記録:** ゲート通過時は `tasks/todo.md` に通過日時を記録する
