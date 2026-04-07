---
name: browse
description: |
  ブラウザで画面を確認する。agent-browser CLI を使って画面のスクリーンショット撮影、
  アクセシビリティツリー取得、フォーム操作、画面遷移などを行う。
  「画面見て」「ブラウザ確認して」「スクショ撮って」「現状把握して」「画面開いて」
  「ログインして確認して」「画面の状態を教えて」「UIを確認して」などのリクエストで使用する。
  E2Eテストの作成・実行には gen-tests（Playwright）を使うこと。本スキルはテスト実行ではなく
  「AIの目」としてブラウザを操作し、画面状態を把握するためのもの。
---

# ブラウザ操作（agent-browser）

## 目的

開発中の画面を素早く確認する「AIの目」。テストではなく、観察・確認・調査に使う。

## gen-tests（Playwright）との棲み分け

| 用途 | スキル |
|------|--------|
| 画面を見て現状把握する | **browse**（本スキル） |
| スクショ撮って状態確認する | **browse** |
| バグ調査で画面を操作してみる | **browse** |
| フォームの挙動を試す | **browse** |
| API通信をキャプチャする | **browse** |
| E2Eテストを作成する | gen-tests |
| Playwrightテストを実行する | gen-tests |
| テストを補強・作り直す | gen-tests |

## 前提条件

- `agent-browser` がグローバルインストール済み
  ```bash
  npm install -g agent-browser
  agent-browser install
  ```
- agent-browser のコマンドは `dangerouslyDisableSandbox: true` で実行する
  （`~/.agent-browser/` への書き込みにサンドボックス制限がかかるため）

## ログイン情報

認証が必要な場合、E2Eテストの認証情報ファイルから読み取る。
**認証情報をスキルファイルやコードにハードコードしない。**
CLAUDE.md の「テスト設定」セクションやプロジェクト内の `.env.test` 等を参照すること。

## 基本操作フロー

### 1. ページを開く
```bash
agent-browser open <URL>
```

### 2. 画面状態を把握する（2つの方法を使い分け）

**方法A: snapshot（テキスト）** — シンプルな画面向き、トークン効率が良い
```bash
agent-browser snapshot -ic    # interactive + compact
```
- 出力: アクセシビリティツリー（`@e1`, `@e2` の参照付き）
- 利点: 要素の参照をそのまま操作に使える（`fill @e6 'text'`）
- 注意: 複雑な画面（テーブル多数など）では30KB超になる → スクショの方が効率的

**方法B: screenshot（画像）** — 複雑な画面向き、視覚的に把握
```bash
agent-browser screenshot
```
- Read ツールで画像ファイルを読み取れば視覚的に確認できる
- ビューポートが狭い場合は先に広げる: `agent-browser set viewport 1920 1080`

**使い分け基準:**
- フォーム入力や要素操作が必要 → snapshot（参照が取れる）
- 全体レイアウトを把握したい → screenshot
- 両方取って損はない（snapshotが巨大でなければ）

### 3. 要素を操作する

snapshot で取得した `@ref` を使って操作する:
```bash
agent-browser fill '@e6' 'input-text'     # テキスト入力
agent-browser click '@e3'                  # クリック
agent-browser hover '@e10'                 # ホバー
agent-browser select '@e5' 'option-value'  # セレクト
```

### 4. 遷移・待機

```bash
agent-browser get url                      # 現在のURL確認
agent-browser wait 3000                    # 3秒待機
agent-browser wait '@e1'                   # 要素の出現を待つ
```

### 5. ネットワーク調査（API通信キャプチャ）

```bash
agent-browser network har start            # HAR記録開始
# ... 画面操作 ...
agent-browser network har stop             # HAR記録停止
agent-browser network requests             # リクエスト一覧
```

### 6. 終了

```bash
agent-browser close
```

## セマンティック検索（ref が不明な場合）

snapshot を取らずに直接要素を探すこともできる:
```bash
agent-browser find role button click --name "送信"
agent-browser find text "メールアドレス" click
agent-browser find label "パスワード" fill "password"
```

## 典型的なシナリオ

### A. 「この画面見て」と言われたとき
```bash
agent-browser open <URL>
agent-browser set viewport 1920 1080
agent-browser screenshot   # → Read で画像確認
agent-browser snapshot -ic  # → テキストで構造確認（巨大なら省略）
# ユーザーに画面の状態を報告
agent-browser close
```

### B. 「ログインして○○画面を確認して」と言われたとき
```bash
# .env.test 等から認証情報を読む
agent-browser open <LOGIN_URL>
agent-browser snapshot -ic
agent-browser fill '@eN' '<email>'     # snapshot の ref を使う
agent-browser fill '@eM' '<password>'
agent-browser click '@eK'              # ログインボタン
agent-browser wait 3000
agent-browser open <TARGET_URL>
agent-browser set viewport 1920 1080
agent-browser screenshot
# 確認後
agent-browser close
```

### C. 「バグを調査して」と言われたとき
```bash
agent-browser open <PROBLEMATIC_URL>
agent-browser set viewport 1920 1080
agent-browser screenshot                # 初期状態
agent-browser snapshot -ic              # DOM構造確認
# 問題を再現する操作
agent-browser fill '@eN' 'test-data'
agent-browser click '@eM'
agent-browser wait 2000
agent-browser screenshot                # 操作後の状態
agent-browser snapshot -ic              # エラーメッセージ等を確認
agent-browser close
```

## 注意事項

- **テストを書くツールではない**: 観察・確認が目的。テストは gen-tests で Playwright を使う
- **ブラウザは使い終わったら閉じる**: `agent-browser close` を忘れない
- **ローディング待ち**: SPA では画面遷移後に `wait 2000`〜`wait 5000` で描画完了を待つ
- **viewport**: デフォルトは狭い。横幅が必要な画面では `set viewport 1920 1080` を先に実行する
- **サンドボックス**: `~/.agent-browser/` への書き込みが必要なため `dangerouslyDisableSandbox: true` で実行する
