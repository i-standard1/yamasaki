# Context Logs

このディレクトリはPM of PMs構成でのコンテキスト配布ログを保存します。

## ファイル命名規則
- `superpm_plan_[YYYYMMDD_HHMM].md` : SuperPMの全体計画
- `pm_[domain]_[YYYYMMDD_HHMM].md` : SuperPM → ドメインPM へのコンテキスト
- `pg_[feature]_[YYYYMMDD_HHMM].md` : ドメインPM → PG へのコンテキスト

## 目的
- PMが各エージェントに渡したコンテキストを可視化・検証するため
- 問題発生時のデバッグに使用するため
- **削除禁止**（.gitignore には追加しない）

## 保持ポリシー
- 直近3ヶ月以内のファイル: 常に保持
- 3ヶ月超のファイル: 該当Specが完了済みであれば削除可
- 判断に迷う場合は保持する
