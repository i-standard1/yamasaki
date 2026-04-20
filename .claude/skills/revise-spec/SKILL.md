---
name: revise-spec
description: |
  実装済み機能の仕様変更。要件定義書と基本設計を先に更新してからコード修正→テスト→レビューを実行する。
  変更種別を自動判定し、実装はAgent(Sonnet)に委任可能、レビューは本体が直接実行する。
  「アップロード上限を10MBに変えて」「この画面にフィールド追加して」「○○の仕様を変更して」
  「○○を修正して」「バリデーションを変えて」などのリクエストで使用する。
  既に実装済みの機能を変更するときに使う。新規実装はimplement-spec。
context:
  required:
    - _shared/spec-writing-standard.md
    - _shared/spec-unified-base.md
    - _shared/spec-map-operations.md
    - _shared/screen-transition-diagram.md
    - _shared/design-priority.md
  on_error:
    - _shared/error-recovery.md
---
<!-- オンデマンド参照（必要時に読む）:
- _shared/code-search-2stage.md → フェーズ1 step 2
- _shared/finish-impl.md → フェーズ「仕上げ」
- _shared/coding-quality.md → 実装フェーズ 設計情報不足時
- _shared/review-checklist.md → レビューフェーズ レビュー観点
- _shared/review-standards.md → レビューフェーズ 指摘フォーマット
- _shared/review-report.md → レビューフェーズ レビューレポート構成
- _shared/impact-report.md → 実装フェーズ 影響範囲レポート
- _shared/loop-protocol.md → レビューフェーズ レビューループ管理
- .claude/agents/coder/AGENT.md → 実装フェーズ Agent委任時 -->

# 実装済み機能の仕様変更

本スキルは**親=分析・方針・レビュー / spec-writer(Sonnet)=設計書更新執筆 / integrity-checker=機械的整合性検査 / coder(Sonnet)=コード実装**の四者分担で進める。

## 統一基盤の確認

[Spec 統一基盤確認](../_shared/spec-unified-base.md) を実施する。新しい概念が出てきた場合は glossary.md にも追記する。

---

### フェーズ1: 分析（親エージェント、コードには触れない）

1. 該当Specを読む
2. [2段階探索](../_shared/code-search-2stage.md) で現在の実装を全て把握する
3. **依存Spec健全性チェック** — `spec-map.yml` で以下を確認する：
   - [ ] 該当REQ-ID自体の `confirmed == spec_version` か（不一致なら先にコード追従が必要）
   - [ ] `depends_on` に列挙された依存Spec全てが `confirmed == spec_version` か
   - [ ] このREQ-IDに**依存しているSpec**（被依存先）も `confirmed == spec_version` か
   - 不一致がある場合：「[REQ-XXX] の実装が spec_version に追従していません。先に対応しますか？」と提案する
4. **openapi.yaml 存在確認（API変更がある場合）:**
   - 変更内容にAPIエンドポイントの追加・変更・削除がある場合、`docs/api/openapi.yaml` が存在し対象エンドポイント定義を含んでいるか確認する
   - 存在しない場合：「openapi.yaml が未作成です。detail-design を実行して API 仕様を生成しますか？」と提案する
   - 存在するがエンドポイント定義が不足の場合：ドキュメント更新フェーズで補完する
5. 変更種別を自動判定：
   - 見た目のみ（CSS、テキスト）→ コードだけ修正。Spec更新不要
   - 動作の変更（バリデーション、ロジック）→ 要件定義書・基本設計・コード・テスト全て同期更新
   - 機能追加レベル（Specの範囲を超える）→ 新REQ-IDの追加を提案
6. **依存グラフ影響分析（推移的閉包）:**
   a. `spec-map.yml` の全エントリから `depends_on` を読み取り、逆引きインデックスを構築する
      - 例: REQ-B が `depends_on: [REQ-A]` → REQ-A の被依存先に REQ-B を追加
   b. 変更対象のREQ-IDから、被依存先を**再帰的に**辿り、推移的影響範囲を特定する
      - 直接依存（1段階）: 変更対象に直接依存しているSpec
      - 推移的依存（2段階以上）: 直接依存のSpecにさらに依存しているSpec
      - 循環依存を検出した場合は警告を出す
   c. `docs/design/dependency-graph.md` が存在する場合はそちらも参照し、spec-map.yml と突合する
   d. 影響範囲を以下の形式で整理する：
      ```
      ## 影響範囲
      ### 直接影響（変更必須）
      - REQ-XXX-001: [変更理由]
      ### 推移的影響（要確認）
      - REQ-YYY-001 → REQ-XXX-001 経由: [確認観点]
      ### コードファイル
      - [2段階探索で見つけた全ファイル]
      ```
7. 影響範囲を提示して確認を求める。推移的影響がある場合は「これらのSpecも再テストが必要になる可能性があります」と明示する

### フェーズ2: 執筆プラン整理（親エージェント）

8. 「見た目のみ」変更の場合はこのフェーズをスキップして実装フェーズへ進む
9. 変更内容に基づき、spec-writer へ渡す委任プロンプトを組み立てる:
   - 更新対象ファイルと更新箇所（セクション・項目レベルで特定）
   - 変更前後の具体的な値
   - 新REQ-IDを追加する場合は採番値と依存関係
   - 画面遷移に影響する変更がある場合は [画面遷移図ルール](../_shared/screen-transition-diagram.md) の適用を指示

### フェーズ3: 設計書更新委任（spec-writer）

10. `Agent(subagent_type: spec-writer)` に設計書更新を委任する:
    - 更新対象ファイルが複数かつ独立している場合は**並列**委任可

    **委任プロンプト形式**:
    ```
    あなたは spec-writer です。以下のドキュメントを差分更新してください。

    ## 更新対象
    docs/requirements/features/[REQ-ID].md

    ## 更新箇所
    - セクション名: [XXX]
    - 変更前: [値]
    - 変更後: [値]

    ## 更新方針
    - 差分更新が基本。既存文書の全面書き換えはしない
    - 変更箇所のセクションだけを更新し、周辺は触らない
    - 画面遷移に影響する変更の場合は画面遷移図も更新する
    - 不明点は「※ 要確認」マーカーを残し、推測で埋めない

    ## 変更内容サマリ
    [フェーズ1で整理した変更内容・影響範囲]

    ## 厳守事項
    - index系ファイル（overview.md / spec-map.yml / mkdocs.yml / dependency-graph.md）は触らない（親が更新）
    - コードを変更しない（コード変更は親が coder エージェントに委任する）
    - 完了時に軽量セルフチェックを実行し、結果を報告すること
    ```

    **並列委任する対象**（該当するもののみ）:
    - docs/requirements/features/ の要件定義書
    - docs/design/ の基本設計（API・DB変更がある場合）
    - docs/api/openapi.yaml（API変更がある場合）

### フェーズ4: index系更新（親エージェント）

spec-writer は index 系に触らないため、親が責任を持って更新する:

11. ドキュメントを新規作成した場合は `mkdocs.yml` の nav に追加する
12. [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い、該当 REQ-ID の `spec_version` をインクリメントする（「見た目のみ」変更ではインクリメント不要）
13. `docs/requirements/overview.md` を更新（新REQ-IDを追加した場合）
14. `docs/design/dependency-graph.md` が存在する場合、変更対象Specの依存関係を更新する

### フェーズ5: ドキュメントのレビューと整合性チェック（親エージェント）

15. spec-writer が更新したドキュメントを**本体が直接レビュー**する（Agent委任不可）
    - 変更内容との整合性確認
    - 要確認マーカーの確認と対応（必要ならユーザーに追加ヒアリング）
16. `Agent(subagent_type: integrity-checker)` を起動して機械的整合性チェック
    - 変更ファイルリスト・新規REQ-ID（あれば）を prompt で渡す
    - チェック項目: `.claude/skills/_shared/doc-integrity-check.md` 参照
    - FAIL があれば修正 → 再チェック（最大3ループ）
17. ドキュメント更新をコミット（ドキュメントとコードのコミットを分ける）

### フェーズ6: 実装プラン作成（親エージェント）

18. 変更内容に基づき `impl-plans/[REQ-ID].md` を作成（または更新）する：
   - 変更対象ファイルと変更内容の一覧（依存関係順）
   - 流用・修正すべき既存コード（grep結果から特定）
   - 判断メモ（WHY NOT）: スコープ外とした変更・仮採用した判断の理由
   - テスト計画（追加・修正するテストケース）
   - 実装プランをコミット: `docs: [REQ-ID] 実装プラン作成`

### フェーズ7: 実装フェーズ（coder Agent または親エージェント）

19. 実装プラン（`impl-plans/[REQ-ID].md`）の順序に従ってコードを修正する。
    以下の基準で実装方法を自動判断する：
    - **本体が直接実装する**（デフォルト）: 途中判断が必要な場合は規模に関係なく本体が実行する
    - **Agent に委任する**: 実装プランの全ステップが明確で途中判断が不要な場合のみ。`Agent(subagent_type: "coder")` で起動し、実装プランのパスと設計書パスリストを prompt に渡す

20. 実装時の共通ルール（本体/Agent 共通）：
   - 更新済みの要件定義書と基本設計の通りにコード・テストを修正する
   - 共通コンポーネントが使える箇所では既存のものを使う（再発明しない）
   - [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い、修正ファイルの confirmed を更新
   - UIを含む変更の場合、E2Eテストも追加・修正する
   - [影響範囲レポート](../_shared/impact-report.md) を docs/impact-reports/[Spec ID].md に作成（または更新）

### フェーズ8: レビューフェーズ（本体が直接実行）

21. [レビューチェックリスト](../_shared/review-checklist.md) を読み、全観点を確認する
    - 指摘フォーマット・深刻度・信頼度は [review-standards](../_shared/review-standards.md) に従う（信頼度80以上のみ修正対象）
    - レポート構成は [review-report](../_shared/review-report.md) に従う
    - 指摘があれば修正→再レビュー（最大3ループ、[loop-protocol](../_shared/loop-protocol.md) に従う）

## 仕上げ

22. `.claude/skills/_shared/finish-impl.md` の共通仕上げ手順を実行
23. 次のステップを提案（「他に変更する箇所はありますか？」）

## コンテキスト管理
- `/cost` でトークン使用量を随時確認する
- 使用率が70%を超えたら、作業状態を `impl-plans/[REQ-ID].md` の末尾に追記し、新セッションでの再開を提案する

## ルール
- ドキュメントを確定させてからコードを変更すること
- 実行前に必ず影響範囲を提示して確認を求めること
- 変更種別の判定理由を説明すること
- PR作成は行わない。コミットまでで完了とする
