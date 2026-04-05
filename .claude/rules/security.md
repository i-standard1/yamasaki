---
description: セキュリティ関連の操作時（機密ファイル、認証情報、設定、デプロイ）
paths:
  - ".env*"
  - "**/*.pem"
  - "**/*.key"
  - "**/*credentials*"
  - "**/*secret*"
  - "**/deploy*"
  - "**/Dockerfile*"
  - "**/.ssh/**"
  - ".claude/settings*.json"
  - ".claude/hooks/**"
---

# セキュリティルール

## 絶対禁止事項
- `git push --force` / `git push -f` / `git push --force-with-lease` の実行（deny ルールでブロック済み）
- `git reset --hard` の実行（deny ルールでブロック済み）
- `rm -rf` の実行（deny ルールでブロック済み）
- `sudo` の実行（deny ルールでブロック済み）
- `chmod 777` / `chmod -R 777` の実行（deny ルールでブロック済み）
- `.env`、秘密鍵（`.pem`/`.key`）、クレデンシャルファイルの読み取り（deny + sandbox でブロック済み）
- `curl`/`wget` による外部通信（deny ルールでブロック済み）
- 本番環境への直接接続（hooks でブロック済み）

## セキュリティ設定の構成（settings.json）

### deny と hook の役割分担

| 層 | 役割 | 特徴 | 対象コマンド |
|---|---|---|---|
| **deny ルール** | 汎用的な破壊的コマンドのブロック | allow で上書き不可。パターンマッチでブロック | `rm -rf`, `sudo`, `git push --force`, `git reset --hard`, `curl`, `wget`, `chmod 777` |
| **PreToolUse hook** | コンテキスト依存の検出 | コマンド全体を解析し、意図を判定 | 本番接続パターン, 機密変数出力, SSH/SCP, Docker特権, 危険なgit履歴改変, base64データ持ち出し |
| **sandbox** | OS レベルのファイルシステム・ネットワーク隔離 | 全 Bash コマンドに適用 | ファイル読み取り制限, ネットワークアクセス制限 |

**設計原則:** deny は「このコマンド自体を許可しない」、hook は「このコマンドの使い方が危険」を検出する。deny で防げない文脈依存の危険パターン（例: 正当な `ssh` の使い方 vs 本番への直接接続）を hook が補完する。

### deny ルール（最優先・allow で上書き不可）
deny → ask → allow の順で評価される。deny に入れたコマンドは「Always allow」を連打しても実行されない。

### サンドボックス
- `sandbox.enabled: true` — Bash コマンドを OS レベルで隔離
- `sandbox.enableWeakerNetworkIsolation: true` — macOS TLS 証明書検証サービス (`com.apple.trustd.agent`) へのアクセスを許可。Go 製 CLI ツール（`gh`, `gcloud`, `terraform` 等）がキーチェーン経由で認証する際に必要
- `sandbox.allowUnsandboxedCommands: false` — dangerouslyDisableSandbox による脱出を防止
- `sandbox.filesystem.denyRead` — Bash 経由（cat 等）での機密ファイル読み取りをブロック

#### トラブルシューティング: gh CLI が sandbox 下で認証失敗する場合
**症状**: `gh auth status` で "The token in keyring is invalid" エラー
**原因**: sandbox が macOS キーチェーンアクセスに必要な Mach IPC (`com.apple.trustd.agent`) をブロック
**対処**: `sandbox.enableWeakerNetworkIsolation: true` を settings.json に追加する（sandbox は有効のまま）

### PreToolUse フック
`.claude/hooks/validate-command.sh` が Bash コマンド実行前に以下を検出・ブロック：
- 本番環境接続パターン
- 機密環境変数の出力
- SSH/SCP コマンド
- Docker 特権モード
- ルートディレクトリ配下への再帰的 chmod
- 危険な git 履歴改変（filter-branch、rebase --onto 等）
- base64 エンコードによるデータ持ち出し

## 運用ルール
- `/permissions` で月1回、権限設定を棚卸しする
- 不要な allow ルールが蓄積していないか確認する
- hooks スクリプトの変更時はチームレビュー必須

## チーム開発時の追加設定
組織ポリシーを強制する場合は Managed Settings を使用：
- `allowManagedPermissionRulesOnly: true` — ユーザー独自の allow/deny を無効化
- `allowManagedHooksOnly: true` — 管理者許可の hooks のみ有効
- `allowManagedMcpServersOnly: true` — 管理者許可の MCP サーバーのみ有効
