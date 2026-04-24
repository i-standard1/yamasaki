# フェーズ 3: mkdocs.yml 更新 & 整合性チェック

## 3.1 mkdocs.yml のナビゲーション更新（親の責務）

**index系ファイルの更新は親が責任を持って実施する**（spec-writer は index系に触らない）。

生成した設計書を `mkdocs.yml` の nav に「詳細設計」カテゴリとして追加する：

```yaml
nav:
  - 基本設計:
    - アーキテクチャ: design/architecture.md
    - 画面遷移図: design/screen-flow.md
    - 外部連携仕様: design/api-spec.md
    - DB設計: design/db-design.md
  - 詳細設計:
    - 横断設計:
      - 性能設計: design/performance-design.md
      - 可用性・スケーラビリティ設計: design/availability-design.md
      - 運用・コンプライアンス設計: design/operations-design.md
      - DB詳細スキーマ: design/db-schema.md
      - マスタデータ定義: design/master-data.md
      - 外部連携仕様: design/external-integration.md
      - セキュリティ設計: design/security-design.md
      - 環境構築手順書: design/setup-guide.md
    - 機能別設計:                          # ← 要件定義書に対応
      - 認証: design/features/auth.md
      - プロフィール: design/features/profile.md
      # ... 要件定義書の数だけ追加
```

フェーズ0.3でスキップした成果物は nav に含めない。

## 3.2 機械的整合性チェック（integrity-checker）

`Agent(subagent_type: integrity-checker)` を起動し、機械的整合性を検証する。

**prompt に渡す情報:**
```
変更ファイルリスト:
  [フェーズ2で生成/更新した全ファイルの絶対パスを列挙]

新規REQ-ID（存在する場合）:
  [今回追加した設計書に対応する REQ-ID リスト]

スコープ: フル検査（チェック項目1〜6を全て実行）
```

**integrity-checker が検証する内容（機械的整合性のみ）:**
1. ビルド検証（`mkdocs build` のエラー/警告）
2. Mermaid構文（変更ファイル内の Mermaid ブロック）
3. 相対リンク検証（リンク先ファイルの実在確認）
4. Markdownフォーマット（表の列数、コードフェンス、見出し飛び）
5. index系完全性（新規ファイルが overview.md / spec-map.yml / mkdocs.yml に登録されているか）
6. 画面遷移リンク実在（screen-flow.md の遷移先が実在するか）

チェック項目の詳細は `.claude/skills/_shared/doc-integrity-check.md` を参照。

**FAIL があれば親が修正 → integrity-checker を再起動（最大3ループ）。**

> **integrity-checker の責務:** 機械的整合性のみ。意味的整合性（用語ゆれ・要件漏れ・REQ-ID整合の妥当性）は対象外。

## 3.3 設計書間の意味的整合性チェック（親が直接実施）

integrity-checker が終わった後、親が以下の**設計書間の意味的整合性**を確認する。
これはドキュメント構造の機械的チェックではなく、設計意図の理解が必要なため親が直接実施する:

| チェック対象 | 検証内容 |
|------------|---------|
| db-schema.md ↔ db-design.md | テーブル・カラムの漏れ/矛盾 |
| features/*.md ↔ openapi.yaml | 機能別設計書のAPI記述とOpenAPIの整合 |
| features/*.md ↔ db-schema.md | 機能別設計書のDB参照が正しいか |
| features/*.md ↔ error-codes.md | エラーコードの漏れ/矛盾（存在する場合） |
| external-integration.md ↔ architecture.md | 外部連携の漏れ/矛盾 |
| setup-guide.md ↔ architecture.md | 技術スタックの漏れ/矛盾 |
| security-design.md ↔ architecture.md | セキュリティ要件の漏れ/矛盾 |
| features/*.md ↔ 各Spec | 要件定義書の受入条件が全て設計に反映されているか |

不整合があればこのフェーズで修正する。

## 3.4 仕様カバレッジレビュー（コード分析モードのみ）

設計書生成とは**別の視点から**、コードに存在する仕様が設計書に漏れなく記載されているかを検証する。
「機械的整合性」ではなく「コードと設計書の意味的な対応」を見るため、integrity-checker とは役割が異なる。

`Agent(subagent_type: spec-writer)` ではなく、**専用のレビューエージェント**を起動する:

```
仕様カバレッジレビュー:
  以下のコードパスと設計書の対応を検証してください。
  [.claude/skills/_shared/spec-coverage-review.md に従い、以下の5観点をチェック]
  1. バリデーション漏れ（CHECK制約・パラメータ検証・フォームバリデーション）
  2. エラーハンドリング漏れ（HTTPステータスコード・エラーメッセージ）
  3. 条件分岐漏れ（権限チェック・状態による分岐）
  4. DBトリガー・関数漏れ
  5. 外部API呼び出し漏れ
  対象設計書: [フェーズ2で生成した features/*.md のリスト]
```

漏れがあれば該当設計書に追記してコミット。再レビューは不要（1回で十分）。

**役割分担の整理:**

| チェック種別 | 担当 | 対象 |
|------------|------|------|
| 機械的整合性（ビルド・リンク・構文・index登録） | integrity-checker | 全モード |
| 設計書間の意味的整合性（矛盾・漏れ） | 親が直接 | 全モード |
| コード↔設計書のカバレッジ（仕様漏れ） | 仕様カバレッジレビューエージェント | コード分析モードのみ |

## 3.5 最終確認

```bash
mkdocs build
```

ビルドエラーがないことを確認する（integrity-checker が既に確認済みのため、最終確認のみ）。

→ コミット: `docs: mkdocs.yml更新 + 整合性修正`
