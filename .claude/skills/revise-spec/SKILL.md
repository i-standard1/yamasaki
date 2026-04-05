---
name: revise-spec
description: |
  実装済み機能の仕様変更。要件定義書と基本設計を先に更新してからコード修正→テスト→レビューを自動実行する。
  変更種別を自動判定し、Agent Teamsでcoder(Sonnet)とreviewer(Opus)を分離する。
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
- _shared/code-search-2stage.md → step 2
- _shared/finish-impl.md → step 14
- _shared/coding-quality.md → step 12 設計情報不足時
- _shared/review-standards.md → step 13 レビュー基準
- _shared/review-report.md → step 13 レビューレポート構成
- _shared/impact-report.md → step 12d 影響範囲レポート
- _shared/loop-protocol.md → step 13 レビューループ管理 -->

# 実装済み機能の仕様変更

## 統一基盤の確認

[Spec 統一基盤確認](../_shared/spec-unified-base.md) を実施する。新しい概念が出てきた場合は glossary.md にも追記する。

## 分析フェーズ（リーダーが実行、コードには触れない）

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

## ドキュメント更新フェーズ（リーダーが実行、確認後）

8. 変更種別に応じて、先にドキュメントを更新する：
   - docs/requirements/features/ の要件定義書を更新（新REQ-IDを追加した場合は新規作成）
   - 画面遷移に影響する変更（画面追加・削除・遷移先変更等）がある場合、要件定義書内の画面遷移図も [画面遷移図ルール](../_shared/screen-transition-diagram.md) に従って更新する（コード根拠セクションも適用）
   - docs/design/ の基本設計を更新（API・DB変更がある場合）
   - docs/api/openapi.yaml を更新（API変更がある場合）
9. ドキュメントを新規作成した場合は mkdocs.yml の nav に追加
10. ドキュメント更新をコミット（ドキュメントとコードのコミットを分ける）
10b. [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い、該当 REQ-ID の spec_version をインクリメントする（「見た目のみ」変更ではインクリメント不要）

## 実装フェーズ（Agent Teams）

11. エージェントチームを作成し、以下の2名を生成：
   - **coder**（Sonnet）: 実装担当
   - **reviewer**（Opus）: レビュー担当

12. coderが実行：
   a. 更新済みの要件定義書と基本設計を読み、その通りにコード・テストを修正する
      - `docs/design/shared-components.md` が存在すれば読み、既存の共通コンポーネントを活用する（再発明しない）
      - 変更で新たに共通化すべきパターンが見つかった場合は共通化し、shared-components.md に追記する
   b. [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い、修正ファイルの confirmed を更新
   c. UIを含む変更の場合、E2Eテストも追加・修正する
   d. [影響範囲レポート](../_shared/impact-report.md) を docs/impact-reports/[Spec ID].md に作成（または既存を更新）
   e. 完了したらreviewerにメッセージ

13. reviewerが実行：
    - 自身でも2段階探索を実行してcoderの探索漏れがないか検証
    - **共通コンポーネントの活用チェック**: `shared-components.md` に記載のコンポーネントで代替できる箇所に独自実装がないか検証
    - **コンポーネント粒度チェック**: feature-design.md のセクション4に従ったコンポーネント分割がされているか検証
    - 要件通りの実装か、変更種別の妥当性、受入条件、影響範囲を検証
    - 指摘フォーマット・深刻度・信頼度は [review-standards](../_shared/review-standards.md) に従う（信頼度80以上のみ修正依頼）
    - レポート構成は [review-report](../_shared/review-report.md) に従う
    - 指摘→修正→再レビュー（最大3ループ、[loop-protocol](../_shared/loop-protocol.md) に従う）

14. リーダーが仕上げ：
    - `.claude/skills/_shared/finish-impl.md` の共通仕上げ手順を実行
    - チームをシャットダウン
    - 次のステップを提案（「他に変更する箇所はありますか？」）

## ルール
- ドキュメントを確定させてからコードを変更すること
- 実行前に必ず影響範囲を提示して確認を求めること
- 変更種別の判定理由を説明すること
- PR作成は行わない。コミットまでで完了とする
