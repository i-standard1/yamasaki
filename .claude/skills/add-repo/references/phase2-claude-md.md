# Phase 2: CLAUDE.md の更新 — 詳細手順

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
