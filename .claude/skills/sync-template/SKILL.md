---
name: sync-template
description: |
  テンプレートリポの最新をプロジェクトに取り込む。
  「テンプレートの最新を取り込んで」「テンプレートを同期して」「スキルを更新して」
  「テンプレートをアップデートして」などのリクエストで使用する。
---

# テンプレート同期

## 基本方針

ファイルを3カテゴリに分けて扱う:

1. **除外**（完全にスキップ）: プロジェクト固有設定ファイル
2. **保護**（add-only: ローカルに無ければ新規取り込み、既存なら**絶対に上書きしない**）: プロジェクトが生成・編集する成果物ドキュメント
3. **同期**（上記以外すべて: 上書きで取り込む）: テンプレ定義・スキル・ルール・CIテンプレ等

**保護カテゴリを設けている理由:** テンプレリポ側の `docs/` 配下（`docs/templates/` 以外）にはスタブ／プレースホルダーのひな形が置かれている。これを無条件で上書きすると、プロジェクトが自動生成・手動編集した設計書・API仕様書・要件定義がテンプレートのスタブで破壊される。過去の事故（PR #59）ではこれで openapi.yaml / api-spec.md / architecture.md / db-design.md 等が空スタブ化した。

## 除外リスト（完全にスキップ）

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

## 保護リスト（add-only: 既存ファイルは上書きしない）

以下のパスは、プロジェクトが `init-spec` / `draft-spec` / `spec-all` / `implement-spec` 等のスキルで生成・編集する成果物。テンプレ側に同名ファイル（スタブ）があっても、**ローカルに既に存在する場合は上書きしない**。ローカルに無ければ新規作成のみ許可する。

| パスパターン | 内容 |
|-------------|------|
| `docs/**` （ただし `docs/templates/**` を除く） | プロジェクトの要件定義・設計書・API仕様・テスト仕様・品質ゲート・ホームページ・CSS等 |
| `domains/**`（ただし `domains/_template/**` を除く） | ドメイン別の実装計画・ドキュメント |
| `interfaces/**`（ただし `interfaces/_template/**` を除く） | リポ間連携インターフェース定義 |
| `tasks/**`（ただし `tasks/.gitkeep` を除く） | 作業状態・セッション履歴・lessons |
| `impl-plans/**` | 実装プラン（作業中の一時ファイル） |
| `DESIGN_INTENT.md` | auto-review 用の設計意図メモ |

**判定の優先順位:** 除外 > 保護 > 同期。除外パスは同期対象にしない。保護パスはローカルに存在すれば同期対象にしない。それ以外のテンプレ側ファイルは全て同期（上書き）する。

**`docs/templates/` は同期対象。** テンプレート定義そのもののSingle Source of Truthなので、上書きで最新化する。

**保護リストにないファイル（`.claude/**`, `ci-templates/**`, `docs/templates/**` 等）はスキップしてはいけない。**
判断に迷ったら保護側に倒す。プロジェクト固有コンテンツを誤って上書きする方が、テンプレ更新が遅れるよりも被害が大きい。

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

### 3. 除外リスト・保護リストを適用してフィルタリング

2a・2bの結果を以下のルールで分類する:

1. **除外パス**に該当 → 完全にスキップ（同期対象にしない）
2. **保護パス**に該当:
   - ローカルに同パスが**存在する場合** → スキップ（上書きしない）
   - ローカルに同パスが**存在しない場合** → 「新規取り込み」として追加対象に含める
3. 上記以外 → 通常の同期対象に含める（上書きで取り込む）

判定用シェル例:

```bash
is_excluded() {
  case "$1" in
    CLAUDE.md|.claude/settings.json|.claude/settings.local.json) return 0 ;;
    mkdocs.yml|README.md|spec-map.yml|CHANGELOG.md) return 0 ;;
    .github/workflows/ci.yml) return 0 ;;
    .github/demo-screenshots/*) return 0 ;;
  esac
  return 1
}

is_protected() {
  case "$1" in
    docs/templates/*) return 1 ;;     # templates/ 配下は除外（同期対象）
    docs/*) return 0 ;;
    domains/_template/*) return 1 ;;
    domains/*) return 0 ;;
    interfaces/_template/*) return 1 ;;
    interfaces/*) return 0 ;;
    tasks/.gitkeep) return 1 ;;
    tasks/*) return 0 ;;
    impl-plans/*) return 0 ;;
    DESIGN_INTENT.md) return 0 ;;
  esac
  return 1
}
```

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

【保護スキップ】N件（ローカルに既存のため上書きしない）
  保護: docs/api/openapi.yaml — プロジェクト固有（保護リスト）
  保護: docs/design/architecture.md — プロジェクト固有（保護リスト）
  保護: docs/requirements/overview.md — プロジェクト固有（保護リスト）
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

**適用後に必ず全件検証を行う。**

同期対象ファイル（除外・保護スキップ以外）がテンプレートと一致することを確認する。保護パスでスキップしたファイルは「元のローカル内容が保持されている」だけ確認（テンプレとの差分は当然発生するので DIFF として数えない）:

```bash
cat /tmp/tpl_files.txt | while read f; do
  # 除外リストはスキップ
  case "$f" in
    CLAUDE.md|.claude/settings.json|.claude/settings.local.json|mkdocs.yml|README.md|spec-map.yml|CHANGELOG.md) continue ;;
    .github/workflows/ci.yml|.github/demo-screenshots/*) continue ;;
  esac
  [ "$f" = ".claude/CLAUDE.md" ] && continue
  [ "$f" = ".claude/skills/sync-template/SKILL.md" ] && continue

  # 保護リスト該当で、ローカルに元々存在したファイルはスキップ（上書きしない想定）
  if is_protected "$f" && [ -f "$f" ] && grep -qxF "$f" /tmp/local_files.txt; then
    continue
  fi

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

**保護パスの検証:** 保護スキップしたファイルは、同期前後で md5 が変わらないことを別途確認する:

```bash
# 同期前に /tmp/local_hashes.txt を作っておく（手順1の直後推奨）
# md5 `cat "$f"` > /tmp/local_hashes.txt  …など
# 同期後、保護スキップ対象が変わっていないことを確認
```

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
- 除外パスは完全にスキップする
- 保護パスはローカルに既存なら上書きしない（新規ファイルなら取り込む）
- それ以外はすべて上書きで取り込む
- 保護リストに該当しないファイルを独自判断でスキップしてはいけない
- 判断に迷ったら保護側に倒す（プロジェクト固有コンテンツ破壊を優先的に避ける）

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
