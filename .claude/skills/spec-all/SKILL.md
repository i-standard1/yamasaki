---
name: spec-all
description: |
  全機能の一括Spec化・一括更新。PM として並列サブエージェントにコード分析を委任し、
  結果を統合して全機能の要件定義書を一括生成・更新する。
  「全部のSpecを作って」「設計書を全部作って」「全機能をドキュメント化して」
  「要件定義を全て更新して」「Specを全部更新して」などのリクエストで使用する。
  個別のSpec化には spec-feature を使う。init-specは初期セットアップ専用。
context:
  required:
    - _shared/spec-writing-standard.md
    - _shared/spec-unified-base.md
    - _shared/spec-map-operations.md
    - _shared/subagent-task-format.md
    - _shared/spec-consistency-review.md
    - _shared/screen-transition-diagram.md
    - _shared/tech-stack-guide.md
    - _shared/spec-coverage-review.md
    - spec-all/execution.md
---

# 全機能一括 Spec 化（PM オーケストレーション）

PM オーケストレーション共通パターン（`.claude/rules/pm-orchestration.md` で自動ロード）に従い、
**親 Opus = コード分析の統合・執筆プラン・レビュー / spec-writer(Sonnet) = 執筆**の分担で進める。

## 前提条件

- `docs/requirements/overview.md` に機能一覧が存在すること（init-spec 済み）
- コードリポのパスが `CLAUDE.md` の「プロジェクト構成」に記載されていること

---

## フェーズ 0: 統一基盤の確立

用語辞書作成・統一基盤確認・REQ-ID カテゴリ事前採番。
詳細: [references/phase0-foundation.md](./references/phase0-foundation.md)

---

## フェーズ 1: ドメイン分割計画

現状把握・ドメイン分割・ファイル割り当て・ナビゲーション階層決定・計画記録・ユーザー確認。
詳細: [references/phase1-domain-split.md](./references/phase1-domain-split.md)

---

## フェーズ 2: 並列コード分析

[spec-all 実行詳細](./execution.md) の「分析エージェントへの指示テンプレート」「結果収集と品質検証」に従い、全ドメインのサブエージェントを並列起動してコード分析を実行する。

---

## フェーズ 3: 執筆プラン整理（親エージェント）

フェーズ2のコード分析結果をもとに、バッチ単位で spec-writer 用の執筆プロンプトを組み立てる。

詳細: [references/phase3-writing.md](./references/phase3-writing.md)

**バッチサイズの原則**（詳細は references/phase3-writing.md 参照）:
- 大規模機能 → 1〜2 機能/バッチ
- 中規模機能 → 3〜5 機能/バッチ
- トークン残量 7万以下 → 1機能ずつ

---

## フェーズ 4: 執筆委任（spec-writer、バッチ単位で並列）

`Agent(subagent_type: spec-writer)` をバッチ単位で並列起動し、Spec を執筆させる。

委任プロンプト形式・バッチ管理・index系更新・コミット手順の詳細:
[references/phase3-writing.md](./references/phase3-writing.md)

---

## フェーズ 5: 設計書統合・最終仕上げ

設計書統合更新・共通コンポーネント設計書・依存グラフ生成・最終レビュー・完了。
詳細: [references/phase4-7-final.md](./references/phase4-7-final.md)

---

## フェーズ 6: 最終レビューと整合性チェック（親エージェント）

全バッチ完了後、2種類のレビューを実行する。

### 6.1 統一性レビュー
[Spec 統一性レビュー](../_shared/spec-consistency-review.md) をフルチェックモードで起動し、結果を全て反映する。

### 6.2 仕様カバレッジレビュー（コード分析モードのみ）
[仕様カバレッジレビュー](../_shared/spec-coverage-review.md) に従い、コードと要件定義書を突合する。漏れがあれば該当 Spec に追記する。

### 6.3 機械的整合性チェック
`Agent(subagent_type: integrity-checker)` を起動する（直列1回のみ）:
- 全変更ファイルリスト・新規REQ-IDリストを prompt で渡す
- チェック項目: `.claude/skills/_shared/doc-integrity-check.md` 参照
- FAIL があれば修正 → 再チェック（最大3ループ）

---

## フェーズ 7: コミット（親エージェント）

全ドキュメント完成後、変更を `git add` してコミットする。

---

## セッション中断時の再開

「spec-all を再開して」で新セッションから復元できる。
詳細: [references/session-resume.md](./references/session-resume.md)

---

## トークン節約ルール

PM オーケストレーション共通パターン（自動ロード済み） の「トークン節約ルール」に従う。
追加ルール：
- バッチサイズは機能規模に応じて動的に決定し、コンテキスト圧縮を防ぐ

## ルール

- PM オーケストレーション共通パターン（自動ロード済み） の全ルールに従う
- **実装に書いていないことは書かない。** spec-feature と同じ正確性ルールを適用する
- **統一性レビューを省略しない。** バッチごと + 最終の両方で必ず実行する
- **機械的整合性チェック（integrity-checker）は最終に1回必ず実行する**
- **spec-writer には「渡されたリストのみ使う、独自にgrepしない」と必ず明記する**
- 既存コードは一切変更しない

**コード分析時の注意:** .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること。
