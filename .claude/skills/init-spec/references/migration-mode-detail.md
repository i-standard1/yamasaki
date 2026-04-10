# 移行モード 詳細手順

既にドキュメントやCLAUDE.mdがあるプロジェクトに、このテンプレートのワークフローを導入する。

**注意:** 移行モードはファイルの**存在**をチェックして不足分を補完するが、既存ファイルの**内容**が全リポをカバーしているかは判定しない。セットアップ済みプロジェクトに新しいリポジトリを追加する場合は `add-repo` スキルを使うこと。

## 手順

1. 既存ドキュメントの棚卸し：何があるかリストアップして提示する
   ```
   検出結果：
   ✅ CLAUDE.md（プロジェクト概要あり）
   ✅ docs/requirements/overview.md（機能5件）
   ✅ docs/requirements/features/auth.md（REQ-AUTH-001）
   ❌ docs/design/architecture.md → 不足
   ❌ docs/design/screen-flow.md → 不足
   ❌ .github/workflows/ci.yml → 不足
   ❌ playwright.config.ts → 不足
   ```

2. CLAUDE.md / .claude/CLAUDE.md の配置：
   - .claude/CLAUDE.md がなければテンプレートからコピー（共通ルール）
   - .claude/CLAUDE.md が既にあれば上書き（テンプレートの最新版に更新）
   - CLAUDE.md の既存の「プロジェクト概要」「技術スタック」はそのまま残す
   - CLAUDE.md に不足セクションがあれば追加（「開発コマンド」「技術制約」「テスト設定」等）
   - 既存の記述と矛盾する場合はユーザーに確認する

3. 既存ドキュメントのフォーマット差分チェック：
   - overview.md にステータス列があるか → なければ列を追加
   - 要件定義書にREQ-IDがあるか → なければ既存の命名規則に合わせて採番
   - 受入条件がチェックリスト形式か → 違う形式でも内容があればそのまま残す
   - **フォーマットを強制変更しない。** 内容が揃っていれば形式は問わない

4. 不足ドキュメントのみ生成：
   - 既にあるファイルはスキップ
   - ないものだけ新規作成（architecture.md、db-design.md、screen-flow.md等）

5. CI/テスト設定の追加：
   - .github/workflows/ci.yml が既にある場合はスキップし、差分をユーザーに提示する
   - ci.yml がない場合: `python3 ci-templates/generate-ci.py` で自動生成（新規モード Step 6 参照）
   - playwright.config.ts が既にある場合はスキップ
   - .github/review-prompt.md がない場合: ci-templates/review-prompt.md をコピー

6. スキルファイルのコピー：
   - .claude/skills/ をコピー（これが移行の本体）
   - .claude/settings.json をマージ

7. 変更内容のサマリーを提示してからコミット：
   ```
   移行サマリー：
   追加: .claude/skills/（10スキル）, docs/design/architecture.md, .github/workflows/ci.yml
   変更: CLAUDE.md（AI主動開発ルール追加）, overview.md（ステータス列追加）
   変更なし: docs/requirements/features/*（既存のまま）
   ```

## 移行後の注意

移行直後に「テスト作って」「全部の設計書を更新して」等の大きな指示を出すと、
既存ドキュメントとスキルの想定が食い違って不整合が起きる。

**推奨：** 移行後の最初の作業は小さい修正（既存機能のバグ修正、軽微な変更）で
スキルが正しく動くことを確認してから、新機能の実装に進む。
