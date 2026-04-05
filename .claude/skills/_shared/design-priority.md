# 設計書間の優先順位（矛盾時のルール）

複数の設計書で同じ情報が矛盾している場合、以下の優先順位で正とする：

| 情報 | Single Source of Truth | 矛盾時に無視する側 |
|------|----------------------|-------------------|
| APIリクエスト/レスポンス定義 | `openapi.yaml` | feature-logic.md のAPI記述 |
| DBカラム型・制約 | `db-schema.md` | feature-logic.md のテーブル記述 |
| 処理フロー | feature-logic.md の**処理ステップ表** | Mermaid図（視覚的補助） |
| 画面レイアウト・UI | feature-design.md | デザインカンプ（実装困難な場合） |
| バリデーション値 | openapi.yaml のスキーマ定義 | feature-logic.md のバリデーション表 |
| 受入条件（何を作るか） | 要件定義書 | 設計書の解釈 |
| Enum/定数の許容値 | `master-data.md` | db-schema.md のCHECK制約 |
| エラーコード体系 | `openapi.yaml`（responses） | features/*.md |
| 外部API仕様 | `external-integration.md` | features/*.md |

## 矛盾発見時のアクション

1. 影響範囲レポートの「設計判断と根拠」セクションに記録する
2. 優先側に従って実装する
3. 可能であれば、矛盾している側の設計書も同コミットで修正する
4. 判断に迷う場合はユーザーに確認する
