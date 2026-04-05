# 2段階探索（コード探索ルール）

コードを分析・実装・レビューする際は、必ず以下の手順で探索すること。
このファイルが2段階探索の **Single Source of Truth**。

**ティア別の適用範囲:**
- **Tier 1（小修正）:** Step 2（キーワード検索）のみで十分
- **Tier 2以上（機能実装・リファクタ）:** Step 1 → Step 2 → Step 3 の順に実行

## Step 1: 構造ベース探索

- エントリーポイント（ルーティング定義、ページコンポーネント等）から import/require の依存関係を辿る
- 直接の依存先だけでなく、1階層先（依存先が使っている共通モジュール）まで確認する
- 探索打ち切り基準: 3階層以上の間接依存、または `node_modules` 等の外部パッケージに到達したら停止

## Step 2: キーワード全文検索

- 機能に関連するキーワード（モデル名、テーブル名、API パス、画面名）でリポジトリ全体を grep する
- Step 1 で見つからなかったファイルを追加で読む
- 検索キーワード例: モデルのクラス名、DB テーブル名、URL パス、イベント名、環境変数名
- 修正後は変更前の値・名称でも grep し、旧記述が他ファイルに残っていないか確認すること

## Step 3: 非同期・イベント駆動コードの探索

Step 1-2 は同期的なコードパスの探索。以下のパターンがプロジェクトに存在する場合は追加探索する：

- **イベントリスナー/Observer**: イベント名・モデル名で `on(`, `addEventListener`, `subscribe`, `observe`, `emit`, `dispatch` を grep
- **キュー/バックグラウンドジョブ**: ジョブ名・キュー名で `queue`, `worker`, `job`, `perform`, `process` を grep
- **Webhook**: エンドポイント名で `webhook`, `callback`, `hook` を grep
- **Pub/Sub**: トピック名で `publish`, `subscribe`, `channel`, `topic` を grep
- **スケジュールタスク**: `cron`, `schedule`, `interval`, `recurring` を grep

## 見落としやすいファイル

以下は Step 1-2 で見つかりにくいため、意識的に探索すること：

| カテゴリ | 探索方法 |
|---------|---------|
| バリデーション | フォーム名・フィールド名で grep。middleware チェーンも確認 |
| 定数定義 | `const`, `enum`, `config` を含むファイルを確認 |
| 共通UI | `components/`, `shared/`, `common/` 配下を確認 |
| バックグラウンドジョブ | `jobs/`, `workers/`, `queues/` 配下を確認 |
| i18n | `locales/`, `translations/`, `messages/` 配下を確認 |
| ミドルウェア | `middleware/` 配下 + ルーティング定義のミドルウェアチェーン |
| テスト用ヘルパー | `__tests__/helpers/`, `test/fixtures/`, `test/utils/` |
| 認証・認可ガード | `guards/`, `policies/`, `permissions/` + デコレーター |
| 型定義・インターフェース | `types/`, `interfaces/`, `*.d.ts` |
| 設定ファイル | `config/`, `.env.example`, 環境変数参照箇所 |
| Feature flag | `flags`, `toggle`, `feature`, `experiment` を grep |
| エラーハンドラ | `error`, `exception`, `boundary`, `fallback` を grep |
