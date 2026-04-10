# 新規モード 詳細手順

## 手順

1. コードリポのディレクトリ構造を分析
2. **規模チェック：** ファイル数・ディレクトリ数を計測する
   - `find . -type f | wc -l` でファイル数を確認
   - **500ファイル超の場合：** 全ファイルは読まず、以下の骨格ファイルだけ分析する
     - ルーティング定義（routes.ts、app/ディレクトリ構造等）
     - DBスキーマ / マイグレーション
     - package.json / pyproject.toml 等の依存関係
     - ディレクトリ名・ファイル名の一覧
   - overview.mdの機能一覧には「※ 骨格分析による暫定一覧。Spec化時に詳細を確認する」と注記する
   - **500ファイル以下の場合：** 全体分析に進む
3. [2段階探索](../../_shared/code-search-2stage.md) で全体像を把握（規模が大きい場合は指定領域のみ）
4. **技術スタック自動検出:**
   パッケージファイルからプロジェクトの技術スタックを自動検出し、CLAUDE.md の「技術スタック」セクションに記入する。
   - `package.json` → Node.js系（Next.js/Nuxt/Express/NestJS等のフレームワーク、vitest/jest/playwright/cypress等のテスト）
   - `Gemfile` → Rails系（rspec、devise等）
   - `pyproject.toml` / `requirements.txt` → Python系（Django/FastAPI、pytest等）
   - `go.mod` → Go系
   - `pom.xml` / `build.gradle` → Spring Boot系
   - `pubspec.yaml` → Flutter / Dart
   - `Podfile` / `*.xcodeproj` → iOS (Swift)
   - `build.gradle.kts`（`com.android.*` plugin） → Android (Kotlin)
   - `app.json` + `node_modules/react-native` → React Native
   - `app/` or `pages/` or `components/` ディレクトリ → フロントエンドの有無
   - `docker-compose.yml` / スキーマファイル → DB種別
   - `supabase/` → supabase-auth
   - ルーティング定義 → api_style（REST/GraphQL/gRPC）
   - project_type は以下で判定:
     - UI + API あり → `web-app`
     - UIなし + APIあり → `api-only`
     - `bin/` or CLI引数処理 → `cli`
     - ジョブ/スケジューラのみ → `batch`
     - ML/AIフレームワーク（PyTorch, TensorFlow等） → `ml`
     - Flutter / React Native / Swift / Kotlin（モバイル向け） → `mobile`

   **テストフレームワーク未導入時のデフォルト:**
   test_unit / test_e2e がプロジェクトに未導入（依存関係に含まれない）場合、
   検出した技術スタックに応じた最もメジャーなフレームワークをデフォルト値として記入する。

   | 技術スタック | test_unit デフォルト | test_e2e デフォルト |
   |------------|-------------------|-------------------|
   | Next.js / React / Vue / Nuxt (TypeScript) | vitest | playwright |
   | Express / NestJS (TypeScript) | vitest | playwright |
   | Rails | rspec | playwright |
   | Django / FastAPI | pytest | playwright |
   | Go | go-test | playwright |
   | Spring Boot | junit | playwright |
   | Flutter | flutter_test | integration_test |
   | React Native | jest | detox |
   | Swift (iOS) | XCTest | XCUITest |
   | Kotlin (Android) | JUnit | Espresso |

   未導入の項目には `（未導入・推奨デフォルト）` と注記して提示する。

   検出結果をユーザーに提示して確認する：
   ```
   技術スタック検出結果:
   - project_type: web-app
   - backend: rails 7.1
   - frontend: next.js 14
   - db: postgresql
   - auth: devise
   - test_unit: rspec
   - test_e2e: playwright（未導入・推奨デフォルト）
   - api_style: rest
   この内容でCLAUDE.mdに記入しますか？
   ```
   確認後、CLAUDE.md の技術スタックセクションを更新する。
5. 以下を自動生成：
   - CLAUDE.md の「プロジェクト概要」セクション（プロジェクト固有）
   - CLAUDE.md の「テスト設定」セクション（テストフレームワーク、devサーバーURL等を自動検出して記入。技術スタックで検出済みの情報を活用する）
   - CLAUDE.md の「CI外部サービス」セクション（以下を自動検出して記入）
     - `supabase/` ディレクトリがある → Supabase（supabase start でCI起動）
     - `docker-compose.yml` にpostgres → PostgreSQL（services.postgres でCI起動）
     - `docker-compose.yml` にredis → Redis（services.redis でCI起動）
   - docs/requirements/overview.md（機能グループの一覧。全機能を列挙する。REQ-IDは `-` 、ステータスは全て「未着手」。Spec化時にREQ-IDが採番されステータスが更新される）
   - docs/design/architecture.md（アーキテクチャ概要。500超の場合は骨格ベースの暫定版）
   - docs/design/db-design.md（DB設計）
   - docs/design/api-spec.md（外部連携仕様書。外部サービス連携がある場合のみ）
   - docs/design/screen-flow.md（画面遷移図。[画面遷移図ルール](../../_shared/screen-transition-diagram.md) に従う。UIの有無は `app/`・`pages/`・`components/` ディレクトリまたはルーティング定義ファイルの存在で判断し、いずれもなければスキップ）
   - docs/api/openapi.yaml（OpenAPI仕様。500超の場合はルーティングから検出したエンドポイントのみ）
   - spec-map.yml（空テンプレート。Spec化時にエントリが追加される）
   - docs/quality-gates.md（フェーズ間の品質ゲート定義。既にテンプレートに含まれている場合はスキップ）
   - mkdocs.yml の nav を更新
6. CIワークフローを自動生成：
   CLAUDE.mdの技術スタック設定から `ci-templates/generate-ci.py` で CI ワークフローを動的に生成する。
   パイプラインフロー: PR → Lint → Type check → Unit test → E2E test → AI review → Summary

   **手順:**
   ```bash
   python3 ci-templates/generate-ci.py \
     --claude-md CLAUDE.md \
     --output .github/workflows/ci.yml \
     --repo-structure auto
   ```

   **リポ構成の指定:**
   - `auto` — ディレクトリ構成から自動判定（`apps/` or `turbo.json` → monorepo、それ以外 → single）
   - `monorepo` — モノレポ（apps/web + apps/api）
   - `separated-front` — 分離リポ・フロントエンド（バックエンドを自動checkout してE2E実行）
   - `separated-back` — 分離リポ・バックエンド（E2Eなし）
   - `separated-mobile` — 分離リポ・モバイルアプリ（flutter test / XCTest / JUnit）
   - `single` — 単体アプリ

   **対応する技術スタック:**
   - test_unit: jest / vitest / pytest / rspec / go-test
   - test_e2e: playwright / cypress / none
   - backend: express / nestjs / django / fastapi / rails / go / spring-boot
   - frontend: next.js / nuxt / vue / react / none

   **生成後の手動調整:**
   - `ci-templates/review-prompt.md` → `.github/review-prompt.md` にコピー
   - 分離型フロントの場合: `BACKEND_REPO` 環境変数を実際のリポ名に変更
   - モノレポの場合: `apps/web`, `apps/api` のパスを実際の構成に合わせる
   - E2Eテストのdevサーバーコマンド・ポートをプロジェクトに合わせて調整
   - CLAUDE.mdの「CI外部サービス」に記載がある場合、生成されたymlにサービス起動ステップを追加:
     - Supabase: `supabase/setup-cli@v1` + `supabase start` + 環境変数を `supabase status -o env` から取得（出力値がクォート付きのため `| tr -d '"'` で除去すること）
     - PostgreSQL: `services.postgres` + `DATABASE_URL` を設定
     - Redis: `services.redis` + `REDIS_URL` を設定
   - 外部API（X API等）のクレデンシャルは `dummy` 値を設定し、`ENABLE_TEST_AUTH=true` でバイパスする
   - E2Eが playwright の場合、playwright.config.ts が未作成なら `npx playwright init` で生成する
7. コミット（docsリポとコードリポそれぞれ）
8. 次のステップを提案（「次はどの機能からSpec化しますか？overview.mdに以下の機能グループがあります：…」）
   - 「テスト失敗時にマージをブロックするには、GitHubのBranch Protection Ruleを設定してください」とリマインドする
