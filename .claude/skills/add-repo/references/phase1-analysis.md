# Phase 1: 新リポの分析 — 詳細手順

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
