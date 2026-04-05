---
name: add-repo
description: |
  既存プロジェクトに新しいリポジトリを追加する。Workspaceにリポを追加した後、
  CLAUDE.md・設計書・ドメイン構成を差分更新する。
  「モバイルリポを追加した」「新しいリポを取り込んで」「リポを追加したので設計書を更新して」
  「Workspaceにリポを足した」などのリクエストで使用する。
  init-spec の移行モードではファイル存在チェックしか行わないため、
  既存ドキュメントの内容を新リポに合わせて拡張するにはこのスキルを使う。
context:
  required:
    - _shared/tech-stack-guide.md
    - _shared/project-scale-thresholds.md
    - _shared/screen-transition-diagram.md
---

# 既存プロジェクトへのリポジトリ追加

## 前提

- プロジェクトは `init-spec`（または `spec-all`）で初期セットアップ済み
- 新しいリポジトリが Claude Code の Workspace に追加済み（`/add-dir` 等で追加されている）
- 既存のドキュメント（overview.md、architecture.md 等）はフロント＋バックエンド等の既存リポのみをカバーしている

## 引数

ユーザーの発言から以下を特定する：
- **新リポのパス**（例: `../myproject-mobile/`）— Workspace に追加済みのパスを確認
- **リポの役割**（例: モバイルアプリ、管理画面、バッチ処理）— 不明な場合はユーザーに確認

---

## 手順

### Phase 1: 新リポの分析

1. **リポの存在確認:** 指定されたパスが Workspace 内でアクセス可能か確認する
   - アクセスできない場合は「`/add-dir ../path/` で Workspace に追加してください」と案内して終了

2. **規模チェック:** [プロジェクト規模の閾値定義](../_shared/project-scale-thresholds.md) に従い、ファイル数を計測する
   - 200ファイル超の場合は骨格ファイルのみ分析（init-spec と同じ方針）

3. **技術スタック検出:** 新リポのパッケージファイルから技術スタックを自動検出する
   - `package.json` → Node.js 系
   - `pubspec.yaml` → Flutter / Dart
   - `Podfile` / `*.xcodeproj` → iOS (Swift)
   - `build.gradle.kts` / `build.gradle`（`com.android.*` plugin） → Android (Kotlin)
   - `Gemfile` → Rails 系
   - `pyproject.toml` / `requirements.txt` → Python 系
   - `go.mod` → Go 系
   - `Cargo.toml` → Rust 系

   project_type の判定:
   - Flutter / React Native / Swift / Kotlin（モバイル向け） → `mobile`
   - 管理画面 UI → `web-app`
   - API のみ → `api-only`
   - CLI → `cli`
   - バッチ → `batch`

4. **検出結果をユーザーに提示して確認する:**
   ```
   新リポ分析結果:
   - パス: ../myproject-mobile/
   - 役割: モバイルアプリ
   - project_type: mobile
   - フレームワーク: flutter 3.x
   - 状態管理: riverpod
   - テスト: flutter_test
   - API通信: dio
   この内容で設計書を更新しますか？
   ```

### Phase 2: CLAUDE.md の更新

5. **プロジェクト構成セクション:** 新リポのパスと説明を追加する
   ```markdown
   ## プロジェクト構成
   - ../myproject-frontend/: フロントエンドリポ
   - ../myproject-backend/: バックエンドリポ
   - ../myproject-mobile/: モバイルリポ    ← 追加
   ```

6. **技術スタックセクション:** 既存のスタック情報を保持しつつ、新リポの情報を追記する
   - 複数の project_type がある場合はカンマ区切りにする（例: `web-app, mobile`）
   - リポ別に技術スタックが異なる場合はリポ名をプレフィックスにする:
     ```markdown
     - project_type: web-app, mobile
     - backend: rails 7.1
     - frontend: next.js 14
     - mobile: flutter 3.x  ← 追加
     - db: postgresql
     ```

7. **テスト設定セクション:** 新リポのテストフレームワーク・コマンドを追記する

8. **開発コマンドセクション:** 新リポ固有の開発コマンドがあれば追記する

### Phase 3: 設計書の差分更新

既存ドキュメントの**内容**を確認し、新リポの情報が欠けている箇所を補完する。
ファイルの有無ではなく、内容のカバー範囲で判定する。

#### 3a. ドキュメント構造の判定

新リポの project_type に応じて、各ドキュメントの更新方式を判定する:

| ドキュメント | UI を持つリポ追加時（mobile / web-app） | UI を持たないリポ追加時（api-only / batch / cli） |
|---|---|---|
| **screen-flow.md** | タブ分離（`=== "Web"` / `=== "モバイル"`） | 変更不要 |
| **performance-design.md** | 性能指標セクションをタブ分離 | セクション追記のみ |
| **architecture.md** | Mermaid 図に Client 層追加 + コンポーネントサブセクション追加 | サブセクション追加 |
| **api-spec.md** | 変更不要（新 API がある場合のみ追記） | 新 API があれば追記 |
| **db-design.md** | 変更不要（新 DB がある場合のみ追記） | 新 DB があれば追記 |

**タブ分離の実施条件:**
- 既存ドキュメントにタブ構文（`=== "`）が未使用であること
- 既存の内容を `=== "Web"` タブに移動し、新プラットフォームを `=== "モバイル"` タブに追加する
- タブ化する際、既存の内容は一切変更しない（タブでラップするのみ）

**タブ分離の対象セクション（screen-flow.md）:**
- 「2. 画面遷移図」「3. 画面一覧」「4. 遷移一覧」をタブ化
- 「1. 概要」「5. 共通遷移ルール」はタブの外（共通）

**タブ分離の対象セクション（performance-design.md）:**
- 「1.1 プラットフォーム固有の性能指標」をタブ化
- それ以外のセクション（SLO、可用性、セキュリティ、運用）はタブの外（共通）

#### 3b. 各ドキュメントの更新

9. **architecture.md の更新:**
   - 既存の Mermaid 構成図の Client サブグラフに新クライアントを追加する（タブ分離しない — 全体像は1つの図）
   - コンポーネント一覧テーブルに新リポのコンポーネントを追加する
   - 通信方式テーブルに新リポ固有の通信（プッシュ通知 FCM/APNs 等）を追加する
   - 技術スタックテーブルにモバイルフレームワーク行を追加する

10. **screen-flow.md の更新（UI を持つリポの場合のみ）:**
    - 3a の判定に従いタブ構文を適用する
    - 既存の内容を `=== "Web"` タブに移動（内容は変更しない）
    - 新プラットフォームの画面遷移図・画面一覧・遷移一覧を `=== "モバイル"` タブに追加
    - [画面遷移図ルール](../_shared/screen-transition-diagram.md) に従う

11. **非機能要件関連ファイルの更新（UI を持つリポの場合のみ）:**
    - `docs/design/performance-design.md`: 3a の判定に従い、性能指標セクションにタブを適用する（Web: 既存の Web Vitals テーブル、モバイル: アプリ起動時間、画面遷移速度、メモリ使用量テーブル）
    - `docs/design/operations-design.md`: デプロイ戦略セクションにモバイルリリースフロー（TestFlight / Google Play Console）を追記。法的要件にアプリストア審査ガイドラインを追記（該当する場合）

12. **api-spec.md の更新:**
    - 新リポが新しい API を提供する場合のみ: エンドポイントを追加
    - 新リポが既存 API を消費するだけの場合: 変更不要

13. **db-design.md の更新:**
    - 新リポが独自 DB を持つ場合のみ: 新しいスキーマセクションを追加
    - 既存 DB を共有する場合: 変更不要

14. **openapi.yaml の更新:**
    - 新リポ固有の API エンドポイントがある場合のみ追加

15. **overview.md の更新:**
    - 新リポ固有の機能グループを追加（REQ-ID は `-`、ステータスは「未着手」）
    - 既存機能にモバイル対応が含まれる場合は備考列に「モバイル対応要」と追記

16. **dependency-graph.md の更新:**
    - 既存の依存グラフに新リポ関連の Spec 依存を追加する

#### 3c. プラットフォーム間連携設計（該当時のみ）

17. 以下のいずれかに該当する場合、`docs/design/platform-integration.md` を `docs/templates/phase2/platform-integration.md` テンプレートに従って新規作成する:
    - ディープリンク（Web URL → モバイルアプリ遷移）がある
    - プッシュ通知がある
    - 認証トークンの共有・引き継ぎがある
    - オフライン同期がある
    - QRコード等によるクロスデバイス連携がある

    該当しない場合（新リポが独立して API を叩くだけ等）はスキップする。
    判定に迷う場合はユーザーに確認する。

### Phase 4: ドメイン構成の更新（orchestrate 使用時のみ）

18. `domains/` が存在する場合のみ実行する。存在しない場合はスキップ。

19. 新リポ用のドメインが必要か判定する:
    - 新リポの関心事が既存ドメインに収まる → 既存ドメインの CLAUDE.md にリポパスを追記
    - 新リポの関心事が独立している → 新ドメインを作成:
      - `domains/_template/CLAUDE.md` をコピーして `domains/[新ドメイン名]/CLAUDE.md` を作成
      - `interfaces/[新ドメイン名]_interface.md` を作成
      - 既存ドメインの IF に新ドメインとの連携を追記

### Phase 5: 周辺ファイルの更新

20. **mkdocs.yml:** nav に新しいドキュメントエントリがあれば追加する
    - `platform-integration.md` を新規作成した場合: nav の「基本設計」セクションに追加

21. **spec-map.yml:** 新リポのファイルパスを含むエントリの追加が必要な場合は空テンプレートを追加する
    - 既存の Spec にモバイル実装ファイルが追加される場合: 該当 REQ-ID の implementation にパスを追加

22. **CI ワークフロー:** 新リポにCIが必要な場合、以下を提案する（自動実行はしない）:
    ```
    新リポ用のCIワークフローが必要です。以下のコマンドで生成できます:
    cd ../myproject-mobile/
    python3 ci-templates/generate-ci.py --claude-md CLAUDE.md --output .github/workflows/ci.yml --repo-structure single
    ```

### Phase 6: 確認とコミット

23. **変更サマリーを提示する:**
    ```
    リポ追加サマリー:
    新リポ: ../myproject-mobile/（Flutter モバイルアプリ）

    更新:
    - CLAUDE.md（プロジェクト構成・技術スタック・テスト設定）
    - docs/design/architecture.md（モバイル層追加）
    - docs/design/screen-flow.md（タブ分離 → Web / モバイル）
    - docs/design/performance-design.md（性能指標タブ分離）
    - docs/requirements/overview.md（モバイル機能グループ追加）
    - docs/design/dependency-graph.md（モバイル依存追加）
    - domains/mobile/CLAUDE.md（新ドメイン作成）
    - interfaces/mobile_interface.md（新IF作成）
    - mkdocs.yml（nav更新）

    新規作成:
    - docs/design/platform-integration.md（ディープリンク・プッシュ通知設計）

    変更なし:
    - docs/design/db-design.md（モバイルは既存DBを参照、スキーマ変更なし）
    - docs/api/openapi.yaml（既存APIをそのまま利用）
    ```

24. ユーザー確認後、コミットする

25. **次のステップを提案する:**
    - 「モバイル固有の機能を `draft-spec` で要件定義しますか？」
    - 「既存機能のモバイル対応を `revise-spec` で追加しますか？」
    - 「モバイルリポのコードを `spec-feature` でSpec化しますか？」（既にコードがある場合）

---

## ルール

- **既存ドキュメントの記述は削除・上書きしない。** 追記のみ行う
- **新リポのコードは変更しない。** ドキュメントの更新のみ
- **推測で機能を追加しない。** 新リポのコードから読み取れる情報のみ記述する。不明な点は TODO コメントを残す
- **ユーザー確認を2回行う:** Phase 1（技術スタック検出後）と Phase 6（コミット前）
- 新リポに既にドキュメントがある場合（README.md 等）はその内容も参考にする
