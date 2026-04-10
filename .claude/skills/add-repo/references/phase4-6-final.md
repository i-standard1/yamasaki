# Phase 4〜6: ドメイン構成・周辺ファイル・確認とコミット — 詳細手順

## Phase 4: ドメイン構成の更新（orchestrate 使用時のみ）

18. `domains/` が存在する場合のみ実行する。存在しない場合はスキップ。

19. 新リポ用のドメインが必要か判定する:
    - 新リポの関心事が既存ドメインに収まる → 既存ドメインの CLAUDE.md にリポパスを追記
    - 新リポの関心事が独立している → 新ドメインを作成:
      - `domains/_template/CLAUDE.md` をコピーして `domains/[新ドメイン名]/CLAUDE.md` を作成
      - `interfaces/[新ドメイン名]_interface.md` を作成
      - 既存ドメインの IF に新ドメインとの連携を追記

## Phase 5: 周辺ファイルの更新

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

## Phase 6: 確認とコミット

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
