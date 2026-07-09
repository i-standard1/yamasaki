---
name: md2excel
description: |
  MarkdownファイルをExcel(.xlsx)に変換する。設計書・要件定義書などのMDをExcelで出力する。
  「Excelにして」「Excelで出力して」「xlsxに変換して」「設計書をExcelで」「納品用Excelを作って」
  「MDをExcelに」などのリクエストで使用する。
argument-hint: "[ファイルパス or ディレクトリ] [--merge] [--no-mermaid]"
---

# Markdown → Excel 変換

`scripts/md2excel.py` を使って Markdown ファイルを Excel (.xlsx) に変換する。

## 変換ツールの場所

```
scripts/md2excel.py
```

## 手順

1. **対象ファイルの特定**
   - ユーザーが具体的なファイルパスを指定した場合 → そのファイルを使う
   - 「設計書を全部」等の指定 → `docs/design/*.md` + `docs/design-detail/*.md` を対象にする
   - 「要件定義を」 → `docs/requirements/**/*.md` を対象にする
   - 「全部」 → `docs/**/*.md`（index.md を除く）を対象にする
   - 不明な場合はユーザーに確認する

2. **出力モードの判定**
   - 単一ファイル指定 → 個別変換（1 MD → 1 XLSX）
   - 複数ファイル指定でユーザーが「1つにまとめて」「1ブックで」と言った場合 → `--merge`
   - 複数ファイル指定でまとめ指示なし → 個別変換（各 MD → 各 XLSX）
   - 迷ったらユーザーに確認する

3. **出力先の決定**
   - ユーザーが指定した場合 → そのパスを使う
   - 指定なし → プロジェクトルート直下の `output/excel/` に出力する

4. **変換の実行**
   ```bash
   # 個別変換
   python scripts/md2excel.py <ファイル...> -o <出力先ディレクトリ>

   # マージ変換
   python scripts/md2excel.py <ファイル...> --merge -o <出力ファイル名.xlsx>

   # Mermaid画像を無効化（高速モード）
   python scripts/md2excel.py <ファイル...> --no-mermaid -o <出力先>
   ```

5. **結果の報告**
   - 生成したファイルのパスを一覧で提示する
   - `open <出力先ディレクトリ>` で Finder を開く（macOS の場合）

## オプション

| オプション | 説明 |
|-----------|------|
| `-o <パス>` | 出力先（ファイル名 or ディレクトリ） |
| `--merge` | 複数MDを1つのExcelブック（シート分割）にまとめる |
| `--no-mermaid` | Mermaid図の画像レンダリングを無効化（テキスト表示、高速） |

## 対応する Markdown 要素

| 要素 | Excel での表現 |
|------|---------------|
| H1 見出し | 濃青背景 + 白太字 14pt |
| H2 見出し | 薄青背景 + 太字 12pt |
| H3 見出し | 極薄青背景 + 太字 11pt |
| テーブル | 罫線付き表（ヘッダー青、交互色） |
| Mermaid図 | PNG画像として埋め込み（--no-mermaidで無効可） |
| コードブロック | グレー背景 + Consolas フォント |
| リスト | 番号付きテキスト |
| 段落 | 折り返しテキスト |

## 依存

- Python 3.10+
- openpyxl（`pip install openpyxl` または `pip install -r scripts/requirements.txt`）
- Mermaid画像: `npx @mermaid-js/mermaid-cli`（Node.js必須、初回自動DL）

## ルール

- 変換前にファイルの存在を確認する
- 出力先ディレクトリが存在しなければ自動作成される
- Mermaid レンダリングに失敗した場合はテキスト表示に自動フォールバックする
- `output/` ディレクトリは `.gitignore` に追加すること（未追加なら追加する）
