---
name: sync-template
description: |
  テンプレートリポの最新をプロジェクトに取り込む。
  「テンプレートの最新を取り込んで」「テンプレートを同期して」「スキルを更新して」
  「テンプレートをアップデートして」などのリクエストで使用する。
---

# テンプレート同期

## 手順

1. .claude/CLAUDE.mdの「テンプレートリポ」からURLを取得
   - URLが未設定の場合はユーザーに確認する

2. テンプレートリポを /tmp/yamasaki にclone（gh CLI経由でHTTPS接続）
   ```bash
   # URLからオーナー/リポ名を抽出（git@github.com:owner/repo.git → owner/repo）
   OWNER_REPO=$(echo "<URL>" | sed -E 's#.+[:/]([^/]+/[^/]+?)(\.git)?$#\1#')
   gh repo clone "$OWNER_REPO" /tmp/yamasaki -- --depth 1
   ```

3. 差分を検出して表示する。対象は以下のみ：

   **取り込むもの（安全）：**
   - `.claude/skills/` — 全スキル（SKILL.md + サブファイル含む）
   - `.claude/hooks/` — セキュリティフック
   - `.claude/rules/` — ルールファイル（プロジェクト固有ルールは残す）
   - `.claude/CLAUDE.md` — 共通ルール（上書きOK）
   - `ci-templates/` — CIテンプレート
   - `DESIGN_INTENT.md` — 設計意図ドキュメント
   - `.github/review-prompt.md` — レビュープロンプト
   - `.github/workflows/auto-review.yml` — 自動レビュー（テンプレートリポ専用、プロジェクトでは無害）
   **取り込まないもの（プロジェクト固有）：**
   - `CLAUDE.md` — プロジェクト固有設定
   - `.claude/rules/` のうちテンプレートに存在しないファイル — プロジェクト固有ルール
   - `docs/` — プロジェクトの設計書
   - `.github/workflows/ci.yml` — プロジェクトごとにgenerate-ci.pyで生成済み
   - `mkdocs.yml` — プロジェクトのナビゲーション
   - `README.md` — プロジェクト固有の説明がある場合
   - `.claude/settings.json` / `.claude/settings.local.json` — 権限設定はプロジェクト固有

4. 差分をユーザーに提示して確認を取る

   **重要**: テンプレートにのみ存在するファイル（追加）も漏れなく検出すること。
   既存ファイルの内容差分だけでなく、テンプレート側の新規ファイルも必ずリストアップする。

   ```
   テンプレートとの差分：
     追加: .claude/hooks/validate-command.sh
     追加: .claude/skills/_shared/coding-quality.md
     更新: .claude/skills/init-spec/SKILL.md
     更新: ci-templates/generate-ci.py
     変更なし: .claude/skills/implement-spec/SKILL.md
   
   取り込みますか？
   ```

5. ユーザーが同意したらコピー実行
   ```bash
   cp -r /tmp/yamasaki/.claude/skills/ .claude/skills/
   cp -r /tmp/yamasaki/.claude/hooks/ .claude/hooks/
   # ルールはテンプレートにあるものだけ上書き（プロジェクト固有ルールは残す）
   for f in /tmp/yamasaki/.claude/rules/*.md; do
     cp "$f" .claude/rules/
   done
   cp -r /tmp/yamasaki/ci-templates/ ci-templates/ 2>/dev/null || true
   cp /tmp/yamasaki/.claude/CLAUDE.md .claude/CLAUDE.md
   cp /tmp/yamasaki/DESIGN_INTENT.md DESIGN_INTENT.md 2>/dev/null || true
   # その他の対象ファイルも同様
   ```

6. CLAUDE.md の確認
   .claude/CLAUDE.mdは上書き済みなので共通ルールは最新。ルートCLAUDE.md側は変更不要。

7. ci-templates/ が更新された場合の案内
   ```
   ci-templates/ が更新されました。
   .github/workflows/ への反映が必要です。
   「CI設定をci-templates/の最新版に合わせて更新して」と指示してください。
   ```

8. クリーンアップ
   ```bash
   find /tmp/yamasaki -delete 2>/dev/null || true
   ```

9. コミット
   ```bash
   git add -A
   git commit -m "chore: sync template to latest"
   ```

## ルール
- .claude/CLAUDE.mdは上書きOK（共通ルール）
- ルートCLAUDE.mdは変更しない（プロジェクト固有）
- .claude/rules/ はテンプレートに存在するファイルのみ上書き。プロジェクト固有で追加したルールファイルは削除しない
- .github/workflows/ci.yml は直接上書きしない。generate-ci.py の再実行をユーザーに促す
- プロジェクト固有の設定（ポート、リポ名、環境変数等）を消さない
