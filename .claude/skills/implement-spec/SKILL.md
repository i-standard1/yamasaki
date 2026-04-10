---
name: implement-spec
description: |
  Specに基づく新規機能実装。要件定義書と基本設計を読んで実装プラン作成→コード実装→テスト→レビューを実行する。
  実装はAgent(Sonnet)に委任可能、レビューは本体が直接実行する。
  「REQ-AUTH-001を実装して」「ログイン機能を作って」「○○を実装して」
  「これを作って」「実装に入って」などのリクエストで使用する。
  要件定義書が存在する未実装機能を新規実装するときに使う。既存機能の変更はrevise-spec。
context:
  required:
    - _shared/spec-map-operations.md
    - _shared/design-priority.md
  on_error:
    - _shared/error-recovery.md
---
<!-- オンデマンド参照（必要時に読む）:
- _shared/code-search-2stage.md → step 7
- _shared/finish-impl.md → step 18
- _shared/coding-quality.md → step 13 設計情報不足時
- _shared/review-checklist.md → step 15 レビュー観点
- _shared/review-standards.md → step 15 指摘フォーマット
- _shared/review-report.md → step 15 レビューレポート構成
- _shared/impact-report.md → step 13 影響範囲レポート作成時
- _shared/loop-protocol.md → step 15 レビューループ管理時
- .claude/agents/coder/AGENT.md → step 12 Agent委任時 -->

# Specに基づく機能実装

## 準備フェーズ（リーダーが実行、コードには触れない）

1. 指定されたSpec ID（またはユーザーの意図から該当Specを特定）をdocs/requirements/から検索
   - **要件定義書が見つからない場合：実装に進まない。** 「先に要件定義が必要です。作成しますか？」と提案し、draft-specに誘導する
2. 要件定義書の**全セクション**を読む（概要・背景・目的・受入条件・画面・技術仕様）
   - 特に「背景・目的」から**既存UIへの影響方針**を判断する（追加 / 置換 / 削除）
   - 受入条件だけを見ると設計意図を見落とす。背景にある「なぜ作るか」が実装方針を決める
3. 要件定義書のステータスを「実装中」に更新、overview.mdも同期
4. **必須読取リスト** — 以下のファイルを優先順に読む。存在しないファイルはスキップするが、★付きが欠落している場合はユーザーに報告し続行可否を確認する：

   | 優先度 | ファイル | 目的 |
   |--------|---------|------|
   | ★必須 | `docs/requirements/features/[REQ-ID].md` | WHAT: 受入条件・背景・目的 |
   | ★必須 | `docs/design/features/[REQ-ID]-logic.md` | HOW: API・DB・バリデーション・権限 |
   | ★必須 | `docs/api/openapi.yaml` | API仕様の Single Source of Truth |
   | ★必須 | `CLAUDE.md` | 技術スタック・テスト設定・開発コマンド |
   | 推奨 | `docs/design/features/[REQ-ID]-design.md` | 画面構成・UIコンポーネント |
   | 推奨 | `docs/design/shared-components.md` | 既存共通コンポーネント（再発明防止） |
   | 推奨 | `docs/design/db-schema.md` | テーブル定義・カラム制約 |
   | 推奨 | `docs/design/architecture.md` | システム構成・データフロー |
   | 条件付き | `interfaces/[domain]_interface.md` | orchestrate経由でドメイン間連携がある場合のみ |
   | 条件付き | `docs/design/features/[REQ-ID]-api-spec.md` | 外部連携がある場合のみ |
   | 条件付き | `docs/design/security-design.md` | 認証・認可に関わる場合のみ |
   | 条件付き | `docs/design/error-codes.md` | エラーハンドリングに関わる場合のみ |

5. **依存Spec健全性チェック** — `spec-map.yml` で以下を確認する：
   - [ ] 対象REQ-ID自体の `confirmed == spec_version` か（不一致なら先に追従が必要）
   - [ ] `depends_on` に列挙された依存Spec全てが `confirmed == spec_version` か
   - 不一致がある場合：「[REQ-XXX] の実装が spec_version に追従していません。先に revise-spec で対応しますか？」と提案する。ユーザーが続行を選んだ場合は影響範囲レポートの「リスク」セクションに記録する
6. **openapi.yaml 存在チェック** — 対象機能がAPIを含む場合（要件定義書にエンドポイント記載がある場合）：
   - `docs/api/openapi.yaml` が存在し、該当エンドポイントの定義を含んでいるか確認する
   - **存在しない場合:** 「openapi.yaml が未作成です。detail-design を実行して API 仕様を生成しますか？」と提案する。ユーザーが続行を選んだ場合は、要件定義書のAPI記述を暫定仕様として使い、影響範囲レポートに記録する
   - **存在するがエンドポイント定義が不足の場合:** 不足分を補完してコミットする
7. [2段階探索](../_shared/code-search-2stage.md) を読み、その手順に従って既存コードを把握する
7b. **画面遷移図の確認（UIを含む機能の場合）:** 要件定義書に画面遷移図がある場合、新規画面の追加・既存画面の遷移先変更がないか確認する。実装後に [画面遷移図ルール](../_shared/screen-transition-diagram.md) に従って更新が必要になる箇所を把握しておく
8. 基本設計に不足があれば更新してコミット（API追加、テーブル追加など）
9. **品質ゲートチェック（Gate 2: 設計→実装）:** `docs/quality-gates.md` のGate 2項目を確認する
   - 全てのSpecにREQ-IDが採番されているか
   - 基本設計書（architecture.md, db-design.md, openapi.yaml）が存在し、Specと整合しているか
   - 未通過項目がある場合はユーザーに提示し、続行するか確認する。ユーザーが中止を選んだ場合は要件定義書のステータスを「実装中」から元に戻す
10. CLAUDE.mdのブランチ戦略に従い、feature/[Spec ID] ブランチを作成
11. **実装プランの作成** — 準備フェーズで読んだ情報を元に `impl-plans/[REQ-ID].md` を作成する：
   - 実装順序（ファイル単位、依存関係順に）
   - 各ステップで作成/変更するファイルパスと概要
   - 流用すべき既存コード（grep結果から特定したファイル:行番号）
   - 使用するAPIエンドポイント一覧（openapi.yaml から抽出）
   - 使用するテーブル・カラム一覧（logic.md / db-schema.md から抽出）
   - 活用すべき共通コンポーネント一覧（shared-components.md から抽出）
   - 判断メモ（WHY NOT）: やらないこと・スコープ外の理由・仮採用した判断
   - テスト計画（何をどの順でテストするか）
   - 実装プランをコミット: `docs: [REQ-ID] 実装プラン作成`

## 設計書間の優先順位・判断ヒューリスティクス

設計書の矛盾解決 → [design-priority.md](../_shared/design-priority.md) を参照
設計情報不足時の判断 → [coding-quality.md](../_shared/coding-quality.md) を参照

## テスト先行フェーズ（TDD: RED）

11b. `docs/design/test-design.md` が存在するか確認する
   - **存在する場合:** gen-tests をTDDモードで呼び出し、テストコードを先行生成する
     - ユニットテスト + E2Eテスト（test.skip付き）がRED状態で生成される
     - コミット: `test: [REQ-ID] テストコードを先行生成（RED状態）`
   - **存在しない場合:** 従来フロー（実装フェーズでテストも同時生成）にフォールバック
   - **注:** test-design.md は detail-design スキルの成果物。TDDを使いたい場合は先に detail-design を実行すること

## 実装フェーズ

12. 実装プラン（`impl-plans/[REQ-ID].md`）の順序に従ってコードを実装する。
    以下の基準で実装方法を自動判断する：
    - **本体が直接実装する**（デフォルト）: 途中判断が必要な場合は規模に関係なく本体が実行する
    - **Agent に委任する**: 実装プランの全ステップが明確で途中判断が不要な場合のみ。`Agent(subagent_type: "coder")` で起動し、実装プランのパスと設計書パスリストを prompt に渡す

13. 実装時の共通ルール（本体/Agent 共通）：
   - 要件に書かれていない機能は実装しない
   - `openapi.yaml` のリクエスト/レスポンス定義に忠実に実装する
   - 共通コンポーネントが使える箇所では既存のものを使う（再発明しない）
   - ユニットテストが全てGREENになるまで繰り返す
   - E2Eテストの `test.skip()` を解除し、全てGREENになるまで修正する
   - [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い、実装ファイルのエントリを追加
   - [影響範囲レポート](../_shared/impact-report.md) を docs/impact-reports/[Spec ID].md に作成

14. 実装プランの判断メモに変更が生じた場合は、実装プランを更新してコミットする

## レビューフェーズ（本体が直接実行）

15. [レビューチェックリスト](../_shared/review-checklist.md) を読み、全観点を確認する
    - 指摘フォーマット・深刻度・信頼度は [review-standards](../_shared/review-standards.md) に従う（信頼度80以上のみ修正対象）
    - レポート構成は [review-report](../_shared/review-report.md) に従う
    - 指摘があれば修正→再レビュー（最大3ループ、[loop-protocol](../_shared/loop-protocol.md) に従う）

## 仕上げ

16. 要件定義書のステータスを「完了」に更新、overview.mdも同期
17. `.claude/skills/_shared/finish-impl.md` を読み、共通仕上げ手順を実行する
18. 次のステップを提案（「次の機能を実装しますか？」「テストを補強しますか？」）

## コンテキスト管理
- `/cost` でトークン使用量を随時確認する
- 使用率が70%を超えたら、作業状態を `impl-plans/[REQ-ID].md` の末尾に追記し、新セッションでの再開を提案する

## ルール
- 要件の受入条件に書かれていない機能を実装しない
- レビュー→修正のループは最大3回
- PR作成は行わない。コミットまでで完了とする
