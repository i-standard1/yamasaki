---
name: update-docs
description: |
  コード変更からドキュメントを追従更新する。設計書ファースト原則の例外措置。
  やむを得ず先にコードを変更した場合にのみ使用する。
  「さっきの変更をドキュメントに反映して」「設計書を最新にして」
  「コードと設計書がズレてるから直して」「ドキュメントを最新化して」
  「ドキュメント更新して」「設計書を現状に合わせて」などのリクエストで使用する。
  通常はドキュメントを先に更新してからコードを修正すること（revise-specを使う）。
context:
  required:
    - _shared/spec-writing-standard.md
    - _shared/spec-unified-base.md
    - _shared/spec-map-operations.md
    - _shared/code-search-2stage.md
---

# ドキュメントの追従更新（例外措置）

※ これは「設計書ファースト」原則の例外措置です。通常はrevise-specでドキュメントを先に更新してからコードを修正する。

## 引数の解釈
- `HEAD~1` → 直前のコミットとの差分
- `HEAD~3` → 直近3コミット分の差分
- コミットハッシュ → そのコミット単体の変更
- 引数なし → ステージされた変更（`git diff --cached`）

## 統一基盤の確認

[Spec 統一基盤確認](../_shared/spec-unified-base.md) を実施する。

## 手順
1. コードリポで `git diff` を実行し、変更内容を把握
2. spec-map.yml を読み、変更されたファイルパスに一致するエントリからSpec IDを特定
   - spec-map.yml に該当パスがない場合は新規REQ-IDの採番を提案する
3. [2段階探索](../_shared/code-search-2stage.md) でdiffに含まれない関連ファイルも探索
4. 以下を更新（新規作成する場合あり）：
   - docs/requirements/features/ の要件定義書
   - docs/design/ の基本設計（API・DB変更がある場合）
   - docs/api/openapi.yaml（API変更がある場合）
5. ドキュメントを新規作成した場合は mkdocs.yml の nav に追加
6. 更新後に grep で検証（diffの具体的な値がドキュメントに反映されているか確認）
7. [spec-map.yml 操作ガイド](../_shared/spec-map-operations.md) に従い spec-map.yml を同期する
8. OVERVIEW同期チェック: 変更内容がOVERVIEW同期トリガー（spec-management.mdルール参照）に該当する場合、OVERVIEWも更新する
9. コミット
10. 次のステップを提案（「他に反映すべき変更はありますか？」）

## ルール
- 変更がSpec IDに紐づかない場合は新規REQ-IDの採番を提案する
- 同じ定数・バリデーション値を参照している箇所も漏れなく更新する
