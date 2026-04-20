# ドキュメント機械的整合性チェック

ドキュメント生成・更新後のコミット前ゲートで実行する機械的整合性チェックの SSOT。
`integrity-checker` エージェントと各SKILLが参照する。

## 対象

- `docs/requirements/**/*.md`
- `docs/design/**/*.md`
- `docs/api/openapi.yaml`
- `mkdocs.yml`
- `spec-map.yml`

## チェック項目

### 1. ビルド検証

**目的**: MkDocs でレンダリング可能か、nav/参照に抜けがないか。

```bash
mkdocs build 2>&1 | tee /tmp/mkdocs-build.log
```

**判定基準**:
- `ERROR` 行が1つでもあれば FAIL
- `WARNING` 行が変更ファイルに関連するものだけ要確認（既存の既知警告は許容）
- 新規ファイルが nav に含まれていない警告（`is not included in the "nav" configuration`）は FAIL

### 2. Mermaid構文検証

**目的**: Mermaid ブロックの構文エラーでグラフが表示されないことを防ぐ。

**手順**:
1. 変更ファイルから ` ```mermaid` ブロックを抽出
2. 各ブロックで以下の基本パターンを検証:
   - `graph TD` / `graph LR` / `flowchart TD` / `sequenceDiagram` / `erDiagram` / `classDiagram` のいずれかで始まる
   - ノード定義の括弧が閉じている（`[...]`, `(...)`, `{...}`）
   - 矢印構文が有効（`-->`, `---`, `-.->`, `==>`, `-- text -->`）
   - 閉じ ` ``` ` がある

**より厳密に検証する場合（mermaid-cli があれば）**:
```bash
npx -y @mermaid-js/mermaid-cli -i /tmp/mermaid-block.mmd -o /tmp/out.svg 2>&1
```

**判定基準**:
- 構文エラーのブロックがあれば FAIL（ファイル:行番号 + エラー内容を報告）

### 3. 相対リンク検証

**目的**: `[text](./path/file.md)` のリンク先ファイルが実在するか。

**手順**:
1. 変更ファイルから Markdown リンクを正規表現で抽出: `\[.+?\]\((?!http)([^)]+)\)`
2. 外部URL（`http://`, `https://`, `mailto:`）は除外
3. アンカー（`#...`）は除外または該当ファイル内セクション存在確認
4. 相対パスを正規化してファイル実在確認

**判定基準**:
- 存在しないファイルへのリンクがあれば FAIL

### 4. Markdownフォーマット

**目的**: 表崩れ・未閉じブロックによる表示崩れを防ぐ。

**チェック項目**:
- **表の列数一致**: ヘッダ行・セパレータ行・データ行の `|` カラム数が揃っているか
- **コードフェンスの閉じ忘れ**: ` ``` ` の開閉がペアになっているか
- **見出しレベル飛び**: `#` → `###` のような2レベル以上の飛びがないか（警告レベル）

**判定基準**:
- 列数不一致・フェンス閉じ忘れは FAIL
- 見出し飛びは WARNING（修正推奨だが必須ではない）

### 5. index系完全性

**目的**: 新機能を追加したのに一覧ファイルに登録し忘れるのを防ぐ。

**チェック対象ファイル**:

| ファイル | チェック内容 |
|---------|------------|
| `docs/requirements/overview.md` | 機能一覧テーブルに新規REQ-IDが存在するか |
| `spec-map.yml` | 新規REQ-IDのエントリが存在するか |
| `mkdocs.yml` | 新規Specファイルが nav に含まれるか |
| `docs/design/dependency-graph.md` | 存在する場合、新規REQ-IDが依存関係グラフに登録されているか |
| `docs/design/screen-flow.md` | UI機能の場合、画面一覧に新規画面が含まれるか |

**判定基準**:
- 親から受け取った「新規REQ-ID/画面ID」が index に含まれなければ FAIL

### 6. 画面遷移リンク実在

**目的**: 画面遷移図に記載された遷移先画面が実在するか。

**手順**:
1. `docs/design/screen-flow.md` 内の Mermaid 図からノード一覧を抽出
2. 各画面IDが画面一覧セクションに存在するか確認
3. 個別Specの画面遷移図に記載された遷移先が screen-flow.md に実在するか確認

**判定基準**:
- 遷移先が画面一覧に存在しなければ FAIL

### 7. キーワード残存（辞書ベース）

**目的**: `review-keywords.yml` で定義された各キーワードの残存を可視化する。
辞書エントリの `severity` により扱いを分ける。

**手順**:
1. プロジェクト直下 `review-keywords.yml` を読み込む（なければ本チェックはスキップ）
2. 各キーワードの `pattern` で変更ファイル（または `docs/` 全体）を走査
3. キーワードごとに件数・該当行（ファイル:行 + 抜粋）を収集

**判定基準**:
- `severity: info` → INFO（FAIL にしない）。要確認・TODO など意図的残存が許される系
- `severity: warn` → **FAIL**。場当たり記法の再発防止対象（例: `!!! info "確定:"`）
- レポートにはキーワードごとに件数と箇所を列挙

辞書に新しい検知ワードを足すとチェック対象も自動で増える。

## 軽量セルフチェック（spec-writer 用）

spec-writer が完了時に自己実行する軽量版。高速に終わるチェックのみ:

1. `mkdocs build` を実行し、ERROR/WARNING をカウント
2. 生成した変更ファイル内の Mermaid ブロックを基本パターン検証
3. 変更ファイル内の相対リンクをファイル実在確認
4. 変更ファイル内で `review-keywords.yml` の各パターン残存を集計（`info` は INFO、`warn` は FAIL）

結果は親に返す完了報告に含める（例: `mkdocs build: OK (warnings=0), mermaid: OK (3/3), links: OK (5/5), keywords: 要確認=2(info) 確定タグ=0(warn)`）。

## フル検査（integrity-checker 用）

integrity-checker は上記1〜7を全て実行し、構造化レポートを返す。

## 実行環境の前提

- `mkdocs` は Python 環境にインストール済み、または `pipx run mkdocs` で実行可能
- リポジトリルートで `mkdocs.yml` が参照可能な状態
- Mermaid検証は `@mermaid-js/mermaid-cli` があれば使うが、なければパターンマッチで代替

## パフォーマンス考慮

- `mkdocs build` は数秒〜数十秒かかる。チェック全体で最大1分程度
- 並列実行すると `site/` 書き込みで衝突するので、**同時に1つ**が原則
- 並列 worktree では各 worktree 内で独立に実行すれば問題ない
