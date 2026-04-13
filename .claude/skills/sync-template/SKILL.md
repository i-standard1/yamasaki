---
name: sync-template
description: |
  テンプレートリポの最新をプロジェクトに取り込む。
  「テンプレートの最新を取り込んで」「テンプレートを同期して」「スキルを更新して」
  「テンプレートをアップデートして」などのリクエストで使用する。
---

# テンプレート同期

## 基本方針

**テンプレートにあるファイルは原則すべて上書きで取り込む。**
除外は以下の最小限リストのみ。このリストに載っていないファイルは全て同期対象。

## 除外リスト（これだけがスキップされる）

| ファイル | 理由 |
|---------|------|
| `CLAUDE.md`（ルート） | プロジェクト固有設定 |
| `.claude/settings.json` | プロジェクト固有権限設定 |
| `.claude/settings.local.json` | プロジェクト固有権限設定 |
| `mkdocs.yml` | プロジェクト固有ナビゲーション |
| `README.md` | プロジェクト固有の説明 |
| `spec-map.yml` | プロジェクト固有のSpec管理 |
| `CHANGELOG.md` | プロジェクト固有の変更履歴 |
| `.github/workflows/ci.yml` | generate-ci.pyで生成済み |
| `.github/demo-screenshots/` | テンプレートリポ固有のデモ画像 |

**除外リストにないファイルをスキップしてはいけない。**
判断に迷ったら取り込む。取り込んで問題があれば後から戻せるが、漏れは気づきにくい。

## 手順

### 1. テンプレートリポの取得

.claude/CLAUDE.mdの「テンプレートリポ」からURLを取得する（URLが未設定の場合はユーザーに確認）。

```bash
OWNER_REPO=$(echo "<URL>" | sed -E 's#.+[:/]([^/]+/[^/]+?)(\.git)?$#\1#')
git remote add template "https://github.com/${OWNER_REPO}.git" 2>/dev/null \
  || git remote set-url template "https://github.com/${OWNER_REPO}.git"
git fetch template main
```

### 2. 全ファイルの差分検出

テンプレートの全ファイルを3カテゴリに分類する:

```bash
git ls-tree -r --name-only template/main | sort > /tmp/tpl_files.txt
git ls-tree -r --name-only HEAD | sort > /tmp/local_files.txt
```

#### 2a. 追加（テンプレートにのみ存在）
```bash
comm -23 /tmp/tpl_files.txt /tmp/local_files.txt
```

#### 2b. 更新（両方に存在、内容が異なる）
```bash
comm -12 /tmp/tpl_files.txt /tmp/local_files.txt | while read f; do
  t_hash=$(git rev-parse template/main:"$f" 2>/dev/null)
  l_hash=$(git rev-parse HEAD:"$f" 2>/dev/null)
  [ "$t_hash" != "$l_hash" ] && echo "$f"
done
```

#### 2c. 構造変更（ローカルにあるがテンプレートにないインフラ系ファイル）

**この検出を省略してはいけない。** ローカルにあってテンプレートにないファイルのうち、
テンプレートのインフラ系パスに該当するものを検出する:

```bash
comm -13 /tmp/tpl_files.txt /tmp/local_files.txt | grep -E \
  '^\.(claude|github)/|^ci-templates/|^docs/templates/|^domains/(_template|\.gitkeep)|^interfaces/(_template|\.gitkeep)|^tasks/(lessons|session-state|todo|\.gitkeep)|^logs/context/'
```

検出されたファイルは以下のいずれかに分類する:
- **移動**: テンプレート側に同名ファイル（basename一致 or 内容類似）が別パスに存在 → 旧パス削除
- **リネーム**: 同ディレクトリ内で名前変更 → 旧ファイル削除
- **削除**: テンプレートにどこにも対応物がない → 削除
- **.gitkeep置換**: .gitkeepが実ファイルに置き換わった → .gitkeep削除

### 3. 除外リストを適用してフィルタリング

2a・2bの結果から除外リストに該当するファイルを除く。
**除外リストに載っていないファイルは全て同期対象に含める。**

### 4. 差分をユーザーに提示して確認を取る

```
テンプレートとの差分:

【追加】N件
  追加: .claude/agents/coder/AGENT.md
  ...

【更新】N件
  更新: .claude/skills/init-spec/SKILL.md
  更新: docs/api/openapi.yaml
  ...

【構造変更】N件
  移動: .claude/skills/skill-auditor/agents/*.md → .claude/agents/*/AGENT.md
  削除: docs/templates/phase2/screen-design.md（テンプレートで廃止）
  置換: domains/.gitkeep → domains/_template/CLAUDE.md
  ...

【除外】N件（スキップ）
  除外: CLAUDE.md — プロジェクト固有
  除外: mkdocs.yml — プロジェクト固有
  ...

取り込みますか？
```

### 5. 適用

#### 5a. テンプレートの全対象ファイルを上書き
```bash
# 追加 + 更新を一括処理
for f in <同期対象の全ファイル>; do
  mkdir -p "$(dirname "$f")"
  git show template/main:"$f" > "$f"
done
```

#### 5b. 構造変更の適用（旧ファイルの削除）
```bash
# 移動・リネーム・削除・.gitkeep置換で不要になったファイルを削除
for f in <削除対象>; do
  rm -f "$f"
done
```

#### 5c. .claude/CLAUDE.md のプレースホルダー復元
上書き後、テンプレートURLの `<your-org>` をプロジェクトの実際の値に戻す。

### 6. 検証（省略してはいけない）

**適用後に必ず全件検証を行う:**

```bash
# テンプレートの全ファイルについて、除外リスト以外は内容が一致することを確認
cat /tmp/tpl_files.txt | while read f; do
  # 除外リストに該当するものはスキップ
  case "$f" in
    CLAUDE.md|.claude/settings.json|.claude/settings.local.json|mkdocs.yml|README.md|spec-map.yml|CHANGELOG.md) continue ;;
    .github/workflows/ci.yml|.github/demo-screenshots/*) continue ;;
  esac
  # .claude/CLAUDE.md はプレースホルダー復元があるので除外
  [ "$f" = ".claude/CLAUDE.md" ] && continue
  # sync-template/SKILL.md 自体は今回改善しているので除外
  [ "$f" = ".claude/skills/sync-template/SKILL.md" ] && continue

  if [ -f "$f" ]; then
    tpl=$(git show template/main:"$f" | md5)
    cur=$(cat "$f" | md5)
    [ "$tpl" != "$cur" ] && echo "DIFF: $f"
  else
    echo "MISSING: $f"
  fi
done
```

**MISSING または DIFF が1件でもあれば、原因を調査して修正する。**
検証をパスするまでコミットしない。

### 7. ci-templates/ が更新された場合の案内
```
ci-templates/ が更新されました。
.github/workflows/ への反映が必要です。
「CI設定をci-templates/の最新版に合わせて更新して」と指示してください。
```

### 8. クリーンアップとコミット
```bash
git remote remove template 2>/dev/null || true
git add -A
git commit -m "chore: sync template to latest"
```

## ルール

### 同期の原則
- **テンプレートにあるファイルは原則すべて上書き。除外リストだけがスキップされる**
- 除外リストにないファイルを独自判断でスキップしてはいけない
- 判断に迷ったら取り込む

### 構造変更
- 構造変更（移動・リネーム・削除・.gitkeep置換）は必ず検出・報告・適用する
- 旧パスのファイル削除を忘れない。新パスへのコピーと旧パスの削除は必ずセットで行う

### プロジェクト固有ルール
- `.claude/rules/` はテンプレートに存在するファイルのみ上書き。プロジェクト固有で追加したルールファイルは削除しない
- `.claude/CLAUDE.md` は上書きOKだが、テンプレートURLのプレースホルダーは復元すること
- `.github/workflows/ci.yml` は直接上書きしない。generate-ci.py の再実行をユーザーに促す

### 検証の義務
- **適用後の全件検証は省略してはいけない**
- MISSING/DIFF が0件になるまで修正を続ける
- 検証をパスするまでコミットしない
