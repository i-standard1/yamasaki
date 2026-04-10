# フェーズ 3: mkdocs.yml 更新 & 整合性チェック

## 3.1 mkdocs.yml のナビゲーション更新

生成した設計書を `mkdocs.yml` の nav に「詳細設計」カテゴリとして追加する：

```yaml
nav:
  - 基本設計:
    - アーキテクチャ: design/architecture.md
    - 画面遷移図: design/screen-flow.md
    - 外部連携仕様: design/api-spec.md
    - DB設計: design/db-design.md
  - 詳細設計:
    - 横断設計:
      - 性能設計: design/performance-design.md
      - 可用性・スケーラビリティ設計: design/availability-design.md
      - 運用・コンプライアンス設計: design/operations-design.md
      - DB詳細スキーマ: design/db-schema.md
      - マスタデータ定義: design/master-data.md
      - 外部連携仕様: design/external-integration.md
      - セキュリティ設計: design/security-design.md
      - 環境構築手順書: design/setup-guide.md
    - 機能別設計:                          # ← 要件定義書に対応
      - 認証: design/features/auth.md
      - プロフィール: design/features/profile.md
      # ... 要件定義書の数だけ追加
```

フェーズ0.3でスキップした成果物は nav に含めない。

## 3.2 既存設計書との整合性チェック

サブエージェントを起動し、以下の横断チェックを実行する：

```
整合性チェックサブエージェント:
  以下のファイルペアの整合性を検証してください:
  1. db-schema.md ↔ db-design.md: テーブル・カラムの漏れ/矛盾
  2. features/*.md ↔ openapi.yaml: 機能別設計書のAPI記述とOpenAPIの整合
  3. features/*.md ↔ db-schema.md: 機能別設計書のDB参照が正しいか
  4. features/*.md ↔ error-codes.md: エラーコードの漏れ/矛盾
  5. external-integration.md ↔ architecture.md: 外部連携の漏れ/矛盾
  6. setup-guide.md ↔ architecture.md: 技術スタックの漏れ/矛盾
  7. security-design.md ↔ architecture.md: セキュリティ要件の漏れ/矛盾
  8. features/*.md ↔ 各Spec: 要件定義書の受入条件が全て設計に反映されているか

  出力形式:
  | チェック対象 | 結果 | 不整合の内容 | 修正提案 |
  |------------|------|-------------|---------|
```

不整合があればこのフェーズで修正する。

## 3.3 仕様カバレッジレビュー（コード分析モードのみ）

設計書生成エージェントとは**別のレビューエージェント**を起動し、コードに存在する仕様が設計書に漏れなく記載されているかを検証する。

[仕様カバレッジレビュー](../_shared/spec-coverage-review.md) に従い、以下の5観点をチェック：
1. バリデーション漏れ（CHECK制約・パラメータ検証・フォームバリデーション）
2. エラーハンドリング漏れ（HTTPステータスコード・エラーメッセージ）
3. 条件分岐漏れ（権限チェック・状態による分岐）
4. DBトリガー・関数漏れ
5. 外部API呼び出し漏れ

漏れがあれば該当設計書に追記してコミット。再レビューは不要（1回で十分）。

## 3.4 mkdocs build 確認

`mkdocs build` を実行し、ビルドエラーがないことを確認する。

→ コミット: `docs: mkdocs.yml更新 + 整合性修正`
