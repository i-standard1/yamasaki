---
name: review-mark
description: レビューマーカーの一覧・承認・除去を行う。「未承認一覧見せて」「r-XXXX を承認して」「このファイルのレビュー全部承認して」「レビューマーカー一覧」「要確認一覧」等のリクエストで発火する。
argument-hint: "[list | approve <id|--all> [file] | todos]"
---

# review-mark スキル

`docs/**/*.md` の `<!-- review:pending id=... -->` ... `<!-- /review -->` を CLI から操作する。
画面から承認できない時・一括承認したい時のフォールバック。

## 引数

```
/review-mark                           # = list
/review-mark list
/review-mark approve <review-id>
/review-mark approve --all <file>
/review-mark approve --all
/review-mark todos                     # ※ 要確認 平文マーカー一覧
```

## 動作

### list モード（引数なし or `list`）

1. `grep -rn '<!-- review:pending id=' docs/ --include='*.md'` で全未承認マーカーを取得
2. 各ヒットから `id` ・ファイルパス・抜粋（マーカー内の最初の 80 文字）を抽出
3. Markdown の表形式で一覧を返す

出力例:
```
未承認 3 件

| ID                   | ファイル                                       | 抜粋                  |
|----------------------|-----------------------------------------------|----------------------|
| r-20260413-001       | requirements/features/auth.md                  | パスワードは…       |
| r-20260413-002       | design/feature-logic.md                        | 認証ロジックを…     |
```

### approve `<id>` モード

1. 全 `docs/**/*.md` を走査して該当 ID を含むファイルを特定
2. ファイルを Read
3. 正規表現で該当マーカーペアを検出:
   ```
   <!--\s*review:pending\s+id=<ID>\s*-->\s*\n?(.*?)\n?\s*<!--\s*/review\s*-->
   ```
4. Edit で **マーカー行のみ削除**（中身はそのまま）
5. 完了メッセージで「1件承認しました: <id> in <file>」を返す
6. 該当 ID が見つからなければエラーで終了

### approve `--all <file>` モード

1. 指定ファイルを Read
2. 上記の正規表現で**全マーカー**を検出
3. 全て除去して Write
4. 「N 件承認しました: <file>」を返す

### approve `--all` モード（file 省略）

1. まず list モードと同じ処理で件数を算出
2. ユーザーに「○件の未承認マーカーを全て除去します。よろしいですか？」と確認
3. 承認されたら全ファイルから全マーカーを除去
4. 処理したファイル数と件数を返す

### todos モード（キーワード残存一覧）

`review-keywords.yml`（プロジェクト直下）で定義された全キーワードを `docs/` 配下から
走査し、キーワードごとに該当行を一覧する。HTML コメントマーカーとは別物で `approve` では除去できない。

辞書は `<id, label, icon, pattern, severity, description>` の形。代表例:
- `※ 要確認`（info・意図的残存OK）
- `!!! info "確定:`（warn・再発防止対象）
- `TODO` / `FIXME` / `TBD`（info）

新しい検知対象を増やしたい時はスキルではなく `review-keywords.yml` にエントリを1つ追加するだけで良い。

手順:

1. `review-keywords.yml` を読み込んで各キーワード定義を取得
2. 各キーワードの `pattern`（Python 正規表現）で `grep -rnP 'パターン' docs --include='*.md'` を実行
3. キーワードごとに Markdown 表で一覧表示し、件数・severity・説明を併記

出力例:
```
## ❓ 要確認（3 件・info）
仕様未確定の箇所。内容を確定したら該当行を削除する。

| ファイル                 | 行  | 抜粋                 |
|-------------------------|----:|---------------------|
| design/non-functional.md | 214 | ...                 |

## 🏷 確定タグ残存（0 件・warn）
✅ 該当なし。

## 📝 TODO（5 件・info）
...
```

自動除去は行わない（内容を確定した上で人が消す必要があるため）。
ブラウザで見たい場合は `/review-pending/` にも同じ一覧が生成されている。

## 承認時の本文の扱い（3 種のマーカー別）

マーカーは 3 種類ある。承認時の挙動が異なる:

| 種別 | 書式 | 承認で残るもの |
|------|------|---------------|
| 追加 | `<!-- review:pending id=X -->本文<!-- /review -->` | 本文 |
| 変更 | `<!-- review:pending id=X --><!-- review:was -->旧<!-- review:now -->新<!-- /review -->` | 新のみ |
| 削除 | `<!-- review:pending id=X type=delete -->本文<!-- /review -->` | なし（丸ごと消える） |

## 実装上の注意

- **追加・変更の場合は段落本文（変更は「新」の方）を必ず残す**
- **削除の場合はマーカー＋中身を全て消す**
- 除去後、連続する空行が 3 行以上になったら 2 行に圧縮する（任意、ファイルが汚くなるのを防ぐ）
- 実行後はユーザーに git diff を確認してもらうよう促す（自動コミットはしない）
- 複数ファイルを編集する場合、Edit を各ファイルごとに実行

## マッチング用正規表現

```python
MARKER = r"<!--\s*review:pending\s+id=(<ID>)(?:\s+type=(\w+))?\s*-->\s*\n?(.*?)\n?\s*<!--\s*/review\s*-->"
WAS_NOW = r"\s*<!--\s*review:was\s*-->\s*\n?(.*?)\n?\s*<!--\s*review:now\s*-->\s*\n?(.*?)\s*$"
```

## 承認以外のオペレーション

マーカーを付与する（新規）のは `review-mark.md` ルールが自動で行うため、このスキルでは扱わない。
