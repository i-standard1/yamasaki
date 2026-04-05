# 技術スタック対応ガイド

CLAUDE.md の「技術スタック」セクションの値に基づき、プロジェクトの具体的なファイルパス・コマンド・キーワードを解決する。
スキルがコード分析・生成時にこのガイドを参照し、技術スタックに応じた正しいパス・用語を使う。

---

## バックエンド別ファイルパス対応表

| 層 | Rails | Django | FastAPI | Express / NestJS | Spring Boot | Go |
|----|-------|--------|---------|-----------------|-------------|-----|
| **モデル層** | `app/models/*.rb` | `*/models.py` | `*/models.py` | `*/models/`, `*/entities/` | `*/entity/*.java` | `*/model/*.go` |
| **コントローラ層** | `app/controllers/*.rb` | `*/views.py` | `*/routers/*.py` | `*/controllers/`, `*/routes/` | `*/controller/*.java` | `*/handler/*.go` |
| **サービス層** | `app/services/*.rb` | `*/services.py` | `*/services/*.py` | `*/services/` | `*/service/*.java` | `*/service/*.go` |
| **ルーティング定義** | `config/routes.rb` | `*/urls.py` | `*/routers/*.py`（デコレータ） | `*/routes/*.ts`, `app.module.ts` | `*/controller/*.java`（アノテーション） | `*/router.go`, `main.go` |
| **スキーマ定義** | `db/schema.rb` | `*/models.py`（class定義） | `*/models.py`（SQLAlchemy） | `prisma/schema.prisma`, `*/migrations/` | `*/entity/*.java` | `*/migration/*.sql` |
| **マイグレーション** | `db/migrate/*.rb` | `*/migrations/*.py` | `alembic/versions/*.py` | `prisma/migrations/`, `db/migrations/` | `resources/db/migration/*.sql` | `*/migration/*.sql` |
| **バリデーション** | モデル内 `validates` | `*/serializers.py`, `*/forms.py` | Pydantic `*/schemas.py` | `*/dto/*.ts`, `class-validator` | `@Valid`, `@NotNull` 等 | `*/validator.go`, struct tag |
| **バックグラウンドジョブ** | `app/jobs/*.rb` | `*/tasks.py`（Celery） | `*/tasks.py`（Celery/ARQ） | `*/jobs/`, `*/workers/` | `*/scheduler/*.java` | `*/worker/*.go` |
| **メーラー** | `app/mailers/*.rb` | `*/mail.py`, `*/email.py` | `*/email.py` | `*/mail/`, `*/email/` | `*/mail/*.java` | `*/mail/*.go` |
| **シリアライザ/レスポンス整形** | `app/views/*.jbuilder`, `*/serializers/` | `*/serializers.py` | Pydantic `*/schemas.py` | `*/dto/*.ts` | `*/dto/*.java` | レスポンス構造体 |
| **リクエストパラメータ定義** | Strong Parameters（コントローラ内） | `*/serializers.py`, `*/forms.py` | Pydantic `*/schemas.py` | `*/dto/*.ts`, `class-validator` | `@RequestBody` DTO | リクエスト構造体 |

---

## フロントエンド別ファイルパス対応表

| 層 | Next.js (App Router) | Next.js (Pages Router) | Nuxt 3 | Vue 3 (Vite) | React (Vite/CRA) |
|----|---------------------|----------------------|--------|-------------|------------------|
| **ページ** | `app/**/page.tsx` | `pages/**/*.tsx` | `pages/**/*.vue` | `src/views/**/*.vue` | `src/pages/**/*.tsx` |
| **コンポーネント** | `components/**/*.tsx` | `components/**/*.tsx` | `components/**/*.vue` | `src/components/**/*.vue` | `src/components/**/*.tsx` |
| **ルーティング** | `app/` ディレクトリ構造 | `pages/` ディレクトリ構造 | `pages/` ディレクトリ構造 | `src/router/index.ts` | `src/router.tsx`, `src/App.tsx` |
| **状態管理** | React Context, Zustand, Jotai | 同左 | Pinia `stores/*.ts` | Pinia `stores/*.ts` | Redux `store/`, Zustand |
| **API通信** | `lib/`, `utils/`, `services/` | 同左 | `composables/`, `utils/` | `src/api/`, `src/services/` | `src/api/`, `src/services/` |
| **レイアウト** | `app/layout.tsx` | `components/Layout.tsx` | `layouts/*.vue` | `src/layouts/*.vue` | `src/layouts/*.tsx` |

---

## モバイル別ファイルパス対応表

| 層 | Flutter | React Native | Swift (iOS) | Kotlin (Android) |
|----|---------|-------------|-------------|-----------------|
| **画面** | `lib/screens/**/*.dart`, `lib/pages/**/*.dart` | `src/screens/**/*.tsx` | `*/Views/**/*.swift`, `*/Screens/**/*.swift` | `*/ui/**/*.kt`, `*/screens/**/*.kt` |
| **コンポーネント（Widget）** | `lib/widgets/**/*.dart` | `src/components/**/*.tsx` | `*/Views/Components/**/*.swift` | `*/ui/components/**/*.kt` |
| **ルーティング/ナビゲーション** | `lib/router.dart`, `lib/routes.dart`, `go_router` | `src/navigation/**/*.tsx` | `*/App.swift`, `NavigationStack` | `*/navigation/**/*.kt`, `NavHost` |
| **状態管理** | `lib/providers/**/*.dart`（Riverpod）, `lib/blocs/**/*.dart`（BLoC） | Redux `store/`, Zustand, Jotai | `*/ViewModels/**/*.swift`（MVVM）, `@Observable` | `*/viewmodel/**/*.kt`（MVVM）, `StateFlow` |
| **API通信** | `lib/api/**/*.dart`, `lib/services/**/*.dart`（dio, http） | `src/api/**/*.ts`（axios, fetch） | `*/Services/**/*.swift`（URLSession, Alamofire） | `*/api/**/*.kt`（Retrofit, Ktor） |
| **モデル/エンティティ** | `lib/models/**/*.dart`（freezed, json_serializable） | `src/models/**/*.ts` | `*/Models/**/*.swift`（Codable） | `*/model/**/*.kt`（data class, kotlinx.serialization） |
| **ローカルストレージ** | `lib/storage/**/*.dart`（shared_preferences, hive, drift） | `src/storage/**/*.ts`（AsyncStorage, MMKV） | `*/Storage/**/*.swift`（UserDefaults, CoreData, SwiftData） | `*/db/**/*.kt`（Room, DataStore） |
| **プッシュ通知** | `lib/notifications/**/*.dart`（firebase_messaging） | `src/notifications/**/*.ts` | `*/Notifications/**/*.swift`（UNUserNotificationCenter） | `*/notifications/**/*.kt`（FirebaseMessaging） |
| **設定ファイル** | `pubspec.yaml`, `analysis_options.yaml` | `package.json`, `app.json`, `metro.config.js` | `*.xcodeproj`, `Info.plist`, `Package.swift` | `build.gradle.kts`, `AndroidManifest.xml` |
| **テスト** | `test/**/*_test.dart` | `__tests__/**/*.test.tsx` | `*Tests/**/*.swift`（XCTest） | `*/test/**/*.kt`（JUnit, Espresso） |
| **E2Eテスト** | `integration_test/**/*.dart` | `e2e/**/*.spec.ts`（Detox） | UI Tests `*UITests/**/*.swift` | `*/androidTest/**/*.kt`（Espresso） |

---

## モバイルテストフレームワーク別対応表

| 項目 | Flutter Test | Jest (React Native) | XCTest (Swift) | JUnit (Kotlin) |
|------|-------------|--------------------|--------------------|----------------|
| **テストファイル命名** | `*_test.dart` | `*.test.tsx`, `*.spec.tsx` | `*Tests.swift` | `*Test.kt` |
| **テスト実行コマンド** | `flutter test` | `npx jest` | `xcodebuild test` | `./gradlew test` |
| **カバレッジ** | `flutter test --coverage` | `npx jest --coverage` | `xcodebuild test -enableCodeCoverage YES` | `./gradlew testDebugUnitTest jacocoTestReport` |
| **テストディレクトリ** | `test/` | `__tests__/` | `*Tests/` | `src/test/` |
| **E2Eテスト実行** | `flutter test integration_test/` | `npx detox test` | `xcodebuild test（UI Tests target）` | `./gradlew connectedAndroidTest` |

---

## テストフレームワーク別対応表

| 項目 | Vitest | Jest | Pytest | RSpec | Go test |
|------|--------|------|--------|-------|---------|
| **テストファイル命名** | `*.test.ts`, `*.spec.ts` | `*.test.ts`, `*.spec.ts` | `test_*.py`, `*_test.py` | `*_spec.rb` | `*_test.go` |
| **テスト実行コマンド** | `npx vitest run` | `npx jest` | `pytest` | `bundle exec rspec` | `go test ./...` |
| **カバレッジ** | `npx vitest run --coverage` | `npx jest --coverage` | `pytest --cov` | `bundle exec rspec --format doc` | `go test -cover ./...` |
| **テストディレクトリ** | `tests/`, `__tests__/`, コロケーション | `tests/`, `__tests__/` | `tests/` | `spec/` | ソースと同階層 |

## E2Eテストフレームワーク別対応表

| 項目 | Playwright | Cypress |
|------|-----------|---------|
| **テストファイル命名** | `*.spec.ts` | `*.cy.ts` |
| **テスト実行コマンド** | `npx playwright test` | `npx cypress run` |
| **設定ファイル** | `playwright.config.ts` | `cypress.config.ts` |
| **テストディレクトリ** | `e2e/`, `tests/` | `cypress/e2e/` |
| **ページオブジェクト** | `e2e/pages/`, `tests/pages/` | `cypress/support/pages/` |
| **待機API** | `waitForSelector`, `waitForResponse` | `cy.wait`, `cy.intercept` |
| **認証ヘルパー** | `storageState` | `cy.session` |

---

## grepキーワード逆引き表

スキルがコード分析で特定の機能を検索する際のキーワード対応表。

| 探す対象 | Rails | Django/FastAPI | Node.js/TypeScript | Spring Boot | Go | Flutter | Swift | Kotlin |
|---------|-------|---------------|-------------------|-------------|-----|---------|-------|--------|
| **Enum定義** | `enum`, `CONSTANT` | `TextChoices`, `IntegerChoices`, `Enum` | `enum`, `as const` | `enum`, `@Enumerated` | `iota`, `const (` | `enum` | `enum`, `CaseIterable` | `enum class` |
| **HTTPクライアント** | `Faraday`, `HTTParty`, `Net::HTTP` | `httpx`, `requests`, `aiohttp` | `axios`, `fetch`, `got` | `RestTemplate`, `WebClient` | `http.Client`, `resty` | `dio`, `http` | `URLSession`, `Alamofire` | `Retrofit`, `Ktor`, `OkHttp` |
| **メール送信** | `ActionMailer`, `deliver` | `send_mail`, `EmailMessage` | `nodemailer`, `@sendgrid` | `JavaMailSender`, `@Async` | `smtp`, `gomail` | `url_launcher`（mailto） | `MFMailComposeViewController` | `Intent.ACTION_SEND` |
| **バックグラウンドジョブ** | `Sidekiq`, `ActiveJob`, `perform_later` | `@shared_task`, `celery`, `dramatiq` | `bull`, `agenda`, `bee-queue` | `@Scheduled`, `@Async` | `goroutine`, `worker` | `workmanager`, `Isolate` | `BGTaskScheduler` | `WorkManager`, `CoroutineWorker` |
| **帳票/ファイル生成** | `wicked_pdf`, `prawn`, `caxlsx` | `reportlab`, `openpyxl`, `weasyprint` | `pdfkit`, `exceljs`, `xlsx` | `JasperReports`, `Apache POI` | `excelize`, `gofpdf` | `pdf`, `printing` | `PDFKit`, `UIGraphicsPDFRenderer` | `PdfDocument`, `iText` |
| **認証** | `Devise`, `has_secure_password` | `django.contrib.auth`, `JWT` | `passport`, `next-auth`, `lucia` | `Spring Security`, `@PreAuthorize` | `jwt-go`, `casbin` | `firebase_auth`, `supabase_flutter` | `AuthenticationServices`, `FirebaseAuth` | `FirebaseAuth`, `BiometricPrompt` |
| **シード/初期データ** | `seeds.rb`, `fixtures/` | `fixtures/`, `loaddata` | `prisma/seed.ts`, `seeds/` | `data.sql`, `CommandLineRunner` | `seed.go`, `fixtures/` | `assets/data/` | `*.json`（Bundle resources） | `assets/`, `prePopulateFrom` |
| **プッシュ通知** | — | — | — | — | — | `firebase_messaging`, `flutter_local_notifications` | `UNUserNotificationCenter`, `APNs` | `FirebaseMessaging`, `NotificationCompat` |
| **ディープリンク** | — | — | — | — | — | `go_router`（deeplink）, `uni_links` | `UIApplicationDelegate`, `universalLinks` | `intent-filter`, `Navigation deeplink` |
| **ローカルDB** | — | — | — | — | — | `drift`, `hive`, `sqflite` | `SwiftData`, `CoreData`, `Realm` | `Room`, `DataStore` |

---

## パッケージマネージャ別コマンド対応表

| 操作 | npm | yarn | pnpm | pip | poetry | bundler | go mod | flutter (pub) | CocoaPods | Gradle (Kotlin) |
|------|-----|------|------|-----|--------|---------|--------|--------------|-----------|----------------|
| **依存インストール** | `npm install` | `yarn install` | `pnpm install` | `pip install -r requirements.txt` | `poetry install` | `bundle install` | `go mod download` | `flutter pub get` | `pod install` | `./gradlew dependencies` |
| **パッケージ追加** | `npm install [pkg]` | `yarn add [pkg]` | `pnpm add [pkg]` | `pip install [pkg]` | `poetry add [pkg]` | `bundle add [pkg]` | `go get [pkg]` | `flutter pub add [pkg]` | Podfile に追記 | build.gradle に追記 |
| **スクリプト実行** | `npm run [script]` | `yarn [script]` | `pnpm [script]` | - | `poetry run [cmd]` | `bundle exec [cmd]` | `go run .` | `flutter run` | - | `./gradlew [task]` |
| **ロックファイル** | `package-lock.json` | `yarn.lock` | `pnpm-lock.yaml` | `requirements.txt` | `poetry.lock` | `Gemfile.lock` | `go.sum` | `pubspec.lock` | `Podfile.lock` | `gradle.lockfile` |
| **パッケージ定義** | `package.json` | `package.json` | `package.json` | `requirements.txt`, `pyproject.toml` | `pyproject.toml` | `Gemfile` | `go.mod` | `pubspec.yaml` | `Podfile` | `build.gradle.kts` |

---

## project_type 別スキップ判定

スキルの成果物生成時に、project_type に応じてスキップすべき項目。

| 成果物 | web-app | api-only | cli | batch | ml | mobile | library |
|--------|---------|----------|-----|-------|-----|--------|---------|
| 画面遷移図 | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| ワイヤーフレーム | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| E2Eテスト | ✅ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ |
| API設計書 | ✅ | ✅ | ❌ | ❌ | ✅ | ✅ | ❌ |
| DB設計書 | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |
| バッチ設計書 | 判定 | 判定 | ❌ | ✅ | 判定 | ❌ | ❌ |

✅ = 生成する、❌ = スキップ、判定 = コード分析で要否を判定

---

## CI パイプライン対応表

`ci-templates/generate-ci.py` が CLAUDE.md の技術スタックからCIワークフローを自動生成する際のマッピング。

### Lint コマンド

| 技術スタック | コマンド |
|------------|---------|
| Express / NestJS / Next.js / React | `npm run lint` |
| Nuxt / Vue | `npm run lint` |
| Django / FastAPI | `ruff check . \|\| flake8 .` |
| Rails | `bundle exec rubocop` |
| Go | `golangci-lint run` |
| Spring Boot | `./gradlew checkstyleMain \|\| mvn checkstyle:check` |
| Flutter | `dart analyze` |
| React Native | `npm run lint` |
| Swift (iOS) | `swiftlint` |
| Kotlin (Android) | `./gradlew ktlintCheck \|\| ./gradlew detekt` |

### Type Check コマンド

| 技術スタック | コマンド |
|------------|---------|
| Express / NestJS / Next.js / React | `npx tsc --noEmit` |
| Nuxt | `npx nuxi typecheck` |
| Vue | `npx vue-tsc --noEmit` |
| Django / FastAPI | `mypy . --ignore-missing-imports` |
| Go | `go build ./...` |
| Spring Boot | `./gradlew compileJava \|\| mvn compile` |
| Flutter | `dart analyze`（Lint と兼用） |
| React Native | `npx tsc --noEmit` |
| Swift (iOS) | `xcodebuild build`（コンパイルで型チェック） |
| Kotlin (Android) | `./gradlew compileDebugKotlin` |

### Unit Test コマンド（モバイル）

| 技術スタック | コマンド |
|------------|---------|
| Flutter | `flutter test` |
| React Native | `npx jest` |
| Swift (iOS) | `xcodebuild test -scheme [Scheme] -destination 'platform=iOS Simulator,name=iPhone 16'` |
| Kotlin (Android) | `./gradlew testDebugUnitTest` |

### リポ構成判定

| 条件 | 判定 |
|------|------|
| `apps/` or `packages/` ディレクトリが存在 | monorepo |
| `turbo.json` or `nx.json` が存在 | monorepo |
| CLAUDE.mdに frontend と backend 両方あり + 分離指定 | separated |
| CLAUDE.mdに mobile フィールドあり | separated-mobile |
| 上記いずれでもない | single |
