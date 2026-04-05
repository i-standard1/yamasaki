---
name: init-spec
description: |
  既存プロジェクトの初期セットアップ（初回のみ）。コードリポジトリを分析してCLAUDE.md、要件概要、
  基本設計書（アーキテクチャ、DB設計、API設計）、OpenAPI仕様、MkDocs設定を自動生成する。
  「このプロジェクトをセットアップして」「既存コードを分析して」「設計書を初期化して」
  「プロジェクトの構造を把握して」などのリクエストで使用する。
  既にドキュメントがある場合は移行モードで差分だけ補完する。
  ※ 既存Specの全更新・再生成には spec-all を使う。
context:
  required:
    - _shared/project-scale-thresholds.md
    - _shared/code-search-2stage.md
    - _shared/screen-transition-diagram.md
    - _shared/tech-stack-guide.md
---

# 既存プロジェクトの初期セットアップ

## 規模による前処理判定

[プロジェクト規模の閾値定義](../_shared/project-scale-thresholds.md) の判定ロジックに従い、必要に応じて `analyze-codebase` スキルの実行を提案する。

---

## モード判定

まず以下をチェックし、モードを自動判定する：

- `docs/requirements/features/` にmdファイルが1つ以上ある → **移行モード**
- `CLAUDE.md` の「プロジェクト概要」にTODO/コメント以外の実際の記述がある → **移行モード**
- 上記いずれもない → **新規モード**

**判定の注意:** テンプレートのCLAUDE.mdには最初から `## プロジェクト概要` のヘッダーとTODOコメントがある。ヘッダーやHTMLコメント（`<!-- -->`）だけの場合は「記述なし」と判定すること。

判定結果をユーザーに提示して確認する：
「既存のドキュメントを検出しました。移行モードで差分のみ補完します。」
または「ドキュメントが見つかりません。新規セットアップを行います。」

---

## テンプレート参照

以下のテンプレートが存在する場合、生成する文書のセクション構成を合わせる：

| テンプレート | 用途 |
|------------|------|
| `docs/templates/phase2/system-architecture.md` | アーキテクチャ文書の構成 |
| `docs/templates/phase1/screen-flow.md` | 画面遷移図の構成 |
| `docs/templates/phase2/db-design.md` | DB設計書の構成 |
| `docs/templates/phase2/api-spec.md` | 外部連携仕様書の構成 |

テンプレートが存在しない場合は、従来の手順でそのまま生成する（テンプレート不在でブロックしない）。

## 新規モード

### 手順

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
3. [2段階探索](../_shared/code-search-2stage.md) で全体像を把握（規模が大きい場合は指定領域のみ）
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
   - docs/design/screen-flow.md（画面遷移図。[画面遷移図ルール](../_shared/screen-transition-diagram.md) に従う。UIの有無は `app/`・`pages/`・`components/` ディレクトリまたはルーティング定義ファイルの存在で判断し、いずれもなければスキップ）
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

---

## 移行モード

既にドキュメントやCLAUDE.mdがあるプロジェクトに、このテンプレートのワークフローを導入する。

**注意:** 移行モードはファイルの**存在**をチェックして不足分を補完するが、既存ファイルの**内容**が全リポをカバーしているかは判定しない。セットアップ済みプロジェクトに新しいリポジトリを追加する場合は `add-repo` スキルを使うこと。

### 原則
- **既存ドキュメントは絶対に上書き・削除しない**
- **既存のフォーマットにテンプレートを合わせる**（テンプレートに既存を合わせるのではない）
- 足りないものだけ追加する

### 手順

1. 既存ドキュメントの棚卸し：何があるかリストアップして提示する
   ```
   検出結果：
   ✅ CLAUDE.md（プロジェクト概要あり）
   ✅ docs/requirements/overview.md（機能5件）
   ✅ docs/requirements/features/auth.md（REQ-AUTH-001）
   ❌ docs/design/architecture.md → 不足
   ❌ docs/design/screen-flow.md → 不足
   ❌ .github/workflows/ci.yml → 不足
   ❌ playwright.config.ts → 不足
   ```

2. CLAUDE.md / .claude/CLAUDE.md の配置：
   - .claude/CLAUDE.md がなければテンプレートからコピー（共通ルール）
   - .claude/CLAUDE.md が既にあれば上書き（テンプレートの最新版に更新）
   - CLAUDE.md の既存の「プロジェクト概要」「技術スタック」はそのまま残す
   - CLAUDE.md に不足セクションがあれば追加（「開発コマンド」「技術制約」「テスト設定」等）
   - 既存の記述と矛盾する場合はユーザーに確認する

3. 既存ドキュメントのフォーマット差分チェック：
   - overview.md にステータス列があるか → なければ列を追加
   - 要件定義書にREQ-IDがあるか → なければ既存の命名規則に合わせて採番
   - 受入条件がチェックリスト形式か → 違う形式でも内容があればそのまま残す
   - **フォーマットを強制変更しない。** 内容が揃っていれば形式は問わない

4. 不足ドキュメントのみ生成：
   - 既にあるファイルはスキップ
   - ないものだけ新規作成（architecture.md、db-design.md、screen-flow.md等）

5. CI/テスト設定の追加：
   - .github/workflows/ci.yml が既にある場合はスキップし、差分をユーザーに提示する
   - ci.yml がない場合: `python3 ci-templates/generate-ci.py` で自動生成（新規モード Step 6 参照）
   - playwright.config.ts が既にある場合はスキップ
   - .github/review-prompt.md がない場合: ci-templates/review-prompt.md をコピー

6. スキルファイルのコピー：
   - .claude/skills/ をコピー（これが移行の本体）
   - .claude/settings.json をマージ

7. 変更内容のサマリーを提示してからコミット：
   ```
   移行サマリー：
   追加: .claude/skills/（10スキル）, docs/design/architecture.md, .github/workflows/ci.yml
   変更: CLAUDE.md（AI主動開発ルール追加）, overview.md（ステータス列追加）
   変更なし: docs/requirements/features/*（既存のまま）
   ```

### 移行後の注意

移行直後に「テスト作って」「全部の設計書を更新して」等の大きな指示を出すと、
既存ドキュメントとスキルの想定が食い違って不整合が起きる。

**推奨：** 移行後の最初の作業は小さい修正（既存機能のバグ修正、軽微な変更）で
スキルが正しく動くことを確認してから、新機能の実装に進む。

---

## 共通ルール
- 既存コードのロジックは一切変更しない
- 生成内容が不明確な場合はTODOコメントを残す
- .claude/CLAUDE.mdは上書きしてよい（共通ルール）。ルートCLAUDE.mdのプロジェクト固有セクションは変更しない（移行モードでは追加のみ）
- **一度に全てのSpec化を試みない。** overview.mdに機能一覧を作った後は、ユーザーに「どの機能からSpec化しますか？」と確認し、5〜10個ずつ進める


**コード分析時の注意:** .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること。
