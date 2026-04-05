# CLAUDE.md（プロジェクト固有設定）
<!-- 共通ルールは .claude/CLAUDE.md を参照。このファイルはプロジェクト固有の設定のみ記載する。 -->
<!-- .claude/CLAUDE.md はテンプレート更新で上書きされるが、このファイルは上書きされない。 -->
<!-- 以下のTODOセクションは init-spec 実行時に自動で埋まる。テンプレート状態では空で正常。 -->

## プロジェクト概要
<!-- TODO: init-spec で自動生成、または会話で伝えてください -->

## 技術スタック
<!-- TODO: init-spec で自動検出して記入する。手動記入も可。 -->
<!-- 各項目は .claude/skills/_shared/tech-stack-guide.md の対応表で使われる -->
- project_type: <!-- web-app / api-only / cli / batch / ml / mobile / library -->
- backend: <!-- 例: rails 7.1 / django 5.0 / fastapi / express / nestjs / spring-boot / go -->
- frontend: <!-- 例: next.js 14 / nuxt 3 / vue 3 / react / none -->
- db: <!-- 例: postgresql / mysql / mongodb / sqlite / none -->
- auth: <!-- 例: supabase-auth / firebase-auth / devise / next-auth / none -->
- test_unit: <!-- 例: vitest / jest / pytest / rspec / go-test -->
- test_e2e: <!-- 例: playwright / cypress / none -->
- api_style: <!-- 例: rest / graphql / grpc / none -->

## プロジェクト構成
<!-- TODO: コードリポの相対パスを記入 -->
<!-- 例: -->
<!-- - ../myproject/: コードリポ -->
<!-- - ../myproject-backend/: バックエンドリポ -->
<!-- - ../myproject-frontend/: フロントエンドリポ -->

## 開発コマンド
<!-- TODO: プロジェクトに合わせて記入 -->
<!-- - npm run dev : 開発サーバー起動（コードリポで実行） -->
<!-- - npm run test : ユニットテスト実行（コードリポで実行） -->
<!-- - npx playwright test : E2Eテスト実行（コードリポで実行） -->
- mkdocs serve : ドキュメントプレビュー（docsリポで実行）

## 技術制約
<!-- 非推奨API・破壊的変更など、Claude Codeが知らない可能性がある制約を記載する -->
<!-- 実装で非推奨を踏んだら都度ここに追記していく -->
<!-- 例: -->
<!-- - Next.js 16: middleware.tsは非推奨。proxy.ts（proxy pattern）を使うこと。関数名も middleware → proxy に変更が必要 -->
<!-- - Supabase CLI: supabase status -o env の出力値がダブルクォート付き -->
<!-- - Supabase CLI: supabase/setup-cli@v1 はバージョン未指定だと db.major_version: 17 を未サポートの古いCLIがインストールされることがある。with: version: でローカルと同じバージョンを明示すること -->

## テスト設定
<!-- TODO: init-spec で自動生成、またはプロジェクトに合わせて記入 -->
<!-- - テストフレームワーク: vitest / jest / pytest 等 -->
<!-- - E2Eフレームワーク: playwright -->
<!-- - devサーバーURL: http://localhost:3000 -->
<!-- - 認証バイパス: NODE_ENV=test で /api/test/login が有効 -->
<!-- - 外部APIモック: NODE_ENV=test で外部API呼び出しが固定JSONを返す -->

### CI外部サービス
<!-- TODO: init-spec がプロジェクトを分析して自動記入する -->
<!-- CIのE2Eテストで必要な外部サービスの起動方法。init-specがtest.ymlのe2eジョブに自動追記する。 -->
<!-- 例: -->
<!-- - Supabase: supabase/setup-cli@v1 (with: version: でCLIバージョンを明示) + supabase start -->
<!-- - PostgreSQL: services.postgres -->
<!-- - Redis: services.redis -->

