# セッション中断時の再開

セッションが途中で切れた場合、新しいセッションで「spec-all を再開して」と言えば、
以下のファイルから進捗を復元できる：

1. `logs/context/specall_plan_*.md` → ドメイン分割計画・バッチ順序
2. `logs/context/specall_reqid_plan.md` → REQ-ID カテゴリ一覧
3. `docs/requirements/overview.md` → ステータスが「未着手」以外の機能 = 完了済み
4. `docs/requirements/features/` → 既に生成された Spec ファイル
5. `docs/requirements/glossary.md` → 用語辞書

**再開手順:**
1. 上記ファイルを読み、完了済みバッチと未完了バッチを特定する
2. 未完了の最初のバッチからフェーズ3を再開する
3. 分析エージェントの結果が logs/context/ に残っていれば再利用する。なければフェーズ2から再実行する
