---
name: analyze-codebase
description: |
  既存プロジェクトをサブエージェントで並列分析し、
  精度の高い overview.md を生成する。init-spec の前処理として使う。
  「既存プロジェクトを分析して」「コードベースを理解して設計書を作って」
  「overview.mdを作って」などのリクエストで使用する。
  ファイル数が200を超えるプロジェクトで特に有効。
  200以下の場合は単一エージェントで全体を読む方が精度が高いため、
  init-spec をそのまま実行することを提案する。
context:
  required:
    - _shared/project-scale-thresholds.md
    - _shared/subagent-task-format.md
---

# コードベース並列分析

## 規模チェック

[プロジェクト規模の閾値定義](../_shared/project-scale-thresholds.md) に従い規模を判定する。
200ファイル以下の場合は init-spec をそのまま実行することを提案して終了する。

## 全体スキャン（メインエージェントが実行）

1. プロジェクトの全体像を把握する
   ```bash
   find . -type f -not -path './.git/*' | wc -l
   find . -type d | head -50
   cat package.json
   ```

2. 分析対象ディレクトリを特定し、ドメイン境界になりそうなディレクトリを列挙する

3. 分析計画を `logs/context/analyze_plan.md` に書き出す
   - 特定したドメイン候補、各サブエージェントへの分析指示、横断分析の担当を記載

4. 計画をユーザーに提示して確認する

## 並列サブエージェント分析

5. [サブエージェントタスク指示フォーマット](../_shared/subagent-task-format.md) に従い、各ドメインをサブエージェントに並列で分析させる
   - 出力先: `logs/context/analysis_[ドメイン名].md`
   - レポート内容: 機能一覧、エンドポイント一覧、データモデル、他ドメインとの依存関係、特記事項

6. メインエージェントは以下を並行して分析する
   - DBスキーマ / マイグレーション、ルーティング定義、共通ミドルウェア、環境変数・設定ファイル

## 結果の統合

7. 全サブエージェントの `logs/context/analysis_*.md` が揃っていることを確認する

8. 各レポートを読み込んで `docs/requirements/overview.md` を生成する
   - `> ⚠️ このoverview.mdはコード分析から自動生成されました。` の注記を付与

9. 生成結果のサマリーを提示する（検出ドメイン数、機能総数、要確認事項）

10. 次のステップを提案する
    - 「overview.mdを確認してください。問題なければ init-spec で設計書を生成できます。」
    - domains/ や interfaces/ の初期化が必要な場合は orchestrate スキルが担当する旨を案内

## ルール
- ドメイン境界が曖昧な場合は、ユーザーに確認してから進める

## init-spec との連携
このスキルの完了後、init-spec を実行すると：
- overview.md が既にある → 移行モードで差分補完
- より精度の高い設計書一式が生成される
