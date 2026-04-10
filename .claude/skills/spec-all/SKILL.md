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
メインエージェントが PM として Spec を一元執筆する。

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

## フェーズ 3: Spec 執筆（メインが一元管理）

バッチ開始時の読取ファイル・バッチ処理・Specフォーマット・付随更新・コミット・バッチ完了時レビュー。
詳細: [references/phase3-writing.md](./references/phase3-writing.md)

---

## フェーズ 4〜7: 設計書統合・最終仕上げ

設計書統合更新・共通コンポーネント設計書・依存グラフ生成・最終レビュー・完了。
詳細: [references/phase4-7-final.md](./references/phase4-7-final.md)

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
- 既存コードは一切変更しない

**コード分析時の注意:** .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること。
