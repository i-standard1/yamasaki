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

リポ存在確認 → 規模チェック → 技術スタック検出（project_type 判定）→ 検出結果をユーザーに提示して確認

詳細: [references/phase1-analysis.md](references/phase1-analysis.md)

### Phase 2: CLAUDE.md の更新

プロジェクト構成・技術スタック・テスト設定・開発コマンドの各セクションに新リポ情報を追記する

詳細: [references/phase2-claude-md.md](references/phase2-claude-md.md)

### Phase 3: 設計書の差分更新

既存ドキュメントの内容カバー範囲を確認し、新リポの情報が欠けている箇所を補完する。
project_type に応じてドキュメント構造（タブ分離など）を判定してから各ファイルを更新する。
対象: architecture / screen-flow / performance-design / operations-design / api-spec / db-design / openapi / overview / dependency-graph / platform-integration（該当時のみ新規作成）

詳細: [references/phase3-docs.md](references/phase3-docs.md)

### Phase 4: ドメイン構成の更新（orchestrate 使用時のみ）

`domains/` が存在する場合のみ。既存ドメインへの追記か新ドメイン作成かを判定して実行する。

詳細: [references/phase4-6-final.md](references/phase4-6-final.md)

### Phase 5: 周辺ファイルの更新

mkdocs.yml の nav 更新、spec-map.yml のエントリ追加、CI ワークフローの提案（自動実行しない）

詳細: [references/phase4-6-final.md](references/phase4-6-final.md)

### Phase 6: 確認とコミット

変更サマリーを提示 → ユーザー確認 → コミット → 次のステップを提案

詳細: [references/phase4-6-final.md](references/phase4-6-final.md)

---

## ルール

- **既存ドキュメントの記述は削除・上書きしない。** 追記のみ行う
- **新リポのコードは変更しない。** ドキュメントの更新のみ
- **推測で機能を追加しない。** 新リポのコードから読み取れる情報のみ記述する。不明な点は TODO コメントを残す
- **ユーザー確認を2回行う:** Phase 1（技術スタック検出後）と Phase 6（コミット前）
- 新リポに既にドキュメントがある場合（README.md 等）はその内容も参考にする
