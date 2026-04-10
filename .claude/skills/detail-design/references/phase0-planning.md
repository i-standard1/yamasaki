# フェーズ 0: 現状把握と計画

### 0.1 前提ファイルの存在チェック

前提条件テーブルの全ファイルの存在を確認する。不足があれば：
```
前提ファイルが不足しています:
  ❌ docs/design/db-design.md が存在しません
  → 先に init-spec（コード分析モード）または draft-spec（設計書ファーストモード）を実行してください
```

**設計書ファーストモードでの基本設計書不足時のフォールバック:**
コードが存在しない0→1プロジェクトでは `architecture.md` や `db-design.md` が未生成の場合がある。
この場合、detail-design が要件定義書から基本設計書の雛形を自動生成してから詳細設計に進む：
- `docs/design/architecture.md` が不在 → 要件定義書の技術スタック・OVERVIEW Specから雛形を生成
- `docs/design/db-design.md` が不在 → 要件定義書のデータモデル記述から雛形を生成
- `docs/api/openapi.yaml` が不在 → 要件定義書のAPI記述から雛形を生成
- 生成した雛形はコミットし、「基本設計の雛形を自動生成しました。確認してください」とユーザーに提示する
- **コード分析モードでは** init-spec で既に生成済みのため、このフォールバックは動作しない

全て存在する（またはフォールバックで生成した）場合のみ次に進む。

### 0.2 既存ドキュメントの読み込み

以下を読み、プロジェクトの全体像を把握する：

1. `CLAUDE.md` — プロジェクト概要・技術スタック・プロジェクト構成
2. `docs/requirements/overview.md` — 機能一覧
3. `docs/design/architecture.md` — アーキテクチャ概要
4. `docs/design/db-design.md` — 既存DB設計
5. `docs/design/api-spec.md` — 外部連携仕様書（存在する場合のみ）
6. `docs/api/openapi.yaml` — 既存OpenAPI仕様

### 0.3 成果物の要否判定

以下の判定ロジックで「任意」成果物の要否を決定する。
**コード分析モード** と **設計書ファーストモード** で判定方法が異なる：

**事前スキップ:** [技術スタック対応ガイド](../_shared/tech-stack-guide.md) の「project_type 別スキップ判定」表を参照。

| 成果物 | スキップ条件 | コード分析モード | 設計書ファーストモード |
|--------|------------|----------------|-------------------|
| master-data.md | Enum/定数なし | コードリポで Enum定義キーワード（[技術スタック対応ガイド](../_shared/tech-stack-guide.md) の grepキーワード逆引き表「Enum定義」参照）を grep して**0件** | 要件定義書に選択肢・ステータス・カテゴリ等の固定値の記載がない |
| external-integration.md | 外部連携なし | `architecture.md` に外部連携セクションがなく、コードリポで HTTPクライアントキーワード（tech-stack-guide.md「HTTPクライアント」参照）を grep して**0件** | `architecture.md` に外部連携セクションがない |
| mail-templates.md | メール機能なし | コードリポでメール送信キーワード（tech-stack-guide.md「メール送信」参照）を grep して**0件** | 要件定義書にメール送信・通知機能の記載がない |
| report-design.md | 帳票なし | コードリポで帳票/ファイル生成キーワード（tech-stack-guide.md「帳票/ファイル生成」参照）を grep して**0件** | 要件定義書に帳票・レポート出力の記載がない |
| data-migration.md | スキーマ変更なし | コードリポに `db/migrate/`・`migrations/`・`alembic/` が存在しないか、テーブルの追加・削除・変更を含むマイグレーションがない | 要件定義書にデータ移行・スキーマ変更の記載がない |
判定結果をユーザーに提示して確認する：
```
生成予定の詳細設計書:
  横断設計:
    ✅ 非機能要件 (performance-design.md, availability-design.md, operations-design.md)
    ✅ DB詳細スキーマ (db-schema.md) — DBの正
    ✅ OpenAPI完全版 (openapi.yaml) — APIの正
    ⬚ マスタデータ定義 → スキップ（Enum/定数が検出されなかったため）
    ✅ 外部連携詳細仕様 (external-integration.md)
    ✅ 環境構築手順書 (setup-guide.md)
    ✅ セキュリティ設計 (security-design.md)
  機能別設計:
    ✅ features/*.md (XX機能分)
この内容で進めますか？
```

### 0.4 統一基盤の確認

統一基盤確認チェックリスト（`.claude/rules/pm-orchestration.md` で自動ロード）を実施する。
