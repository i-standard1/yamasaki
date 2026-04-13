---
name: detail-design
description: |
  詳細設計書の一括生成。2つのモードを自動判定する:
  (A) コード分析モード: 既存コードから詳細設計書を逆生成する（init-spec + spec-all 完了後）
  (B) 設計書ファーストモード: 要件定義書から詳細設計書を新規作成する（コードなし）
  「詳細設計を作って」「設計書を完成させて」「実装に必要な設計書を全部作って」
  「他のエンジニアに渡せる設計書にして」などのリクエストで使用する。
context:
  required:
    - _shared/subagent-task-format.md
    - _shared/tech-stack-guide.md
    - detail-design/formats.md
    - _shared/spec-coverage-review.md
    - _shared/screen-transition-diagram.md
---

# 詳細設計書一括生成（PM オーケストレーション）

PM オーケストレーション共通パターン（`.claude/rules/pm-orchestration.md` で自動ロード） に従い、
メインエージェントが PM として設計書を一元執筆する。

## モード判定

以下の条件で自動判定する：

| 条件 | モード |
|------|--------|
| `CLAUDE.md`「プロジェクト構成」にコードリポのパスが記載されており、そのパスにソースコードが存在する | **コード分析モード** |
| 上記以外（コードリポの記載がない、またはコードが存在しない） | **設計書ファーストモード** |

判定結果をユーザーに提示して確認する：
```
モード判定: コード分析モード
  コードリポ: ../atengineer-backend/, ../atengineer-frontend/
  既存コードを分析して詳細設計書を生成します。
```
または
```
モード判定: 設計書ファーストモード
  コードリポが見つかりません。
  要件定義書と基本設計をもとに詳細設計書を新規作成します。
  不足情報はユーザーに質問して補完します。
```

---

## 前提条件

### 共通（両モード）

| 前提ファイル | 生成スキル | 用途 |
|------------|-----------|------|
| `docs/requirements/features/*.md` | spec-all / draft-spec | 要件定義書（機能仕様の源泉） |
| `docs/design/architecture.md` | init-spec / draft-spec | アーキテクチャ概要 |
| `docs/design/db-design.md` | init-spec / draft-spec | 既存DB設計（精緻化の起点） |
| `docs/design/api-spec.md` | init-spec / draft-spec | 外部連携仕様書（外部サービス連携がある場合のみ） |
| `docs/design/screen-flow.md` | init-spec / draft-spec | 画面遷移図 |
| `docs/api/openapi.yaml` | init-spec / draft-spec | 既存OpenAPI仕様 |

### コード分析モードのみ

| 前提ファイル | 用途 |
|------------|------|
| `CLAUDE.md`「プロジェクト構成」 | コードリポのパス |
| コードリポのソースコード | 分析対象 |

---

## テンプレート参照

以下のテンプレートを参照し、生成する文書のセクション構成を合わせる：

| テンプレート | 用途 |
|------------|------|
| `docs/templates/phase3/db-schema.md` | DB詳細スキーマの構成 |
| `docs/templates/phase3/module-design.md` | モジュール設計書の構成（複雑なプロジェクトのみ。レイヤー構成・モジュール依存関係が必要な場合） |
| `docs/templates/phase3/batch-design.md` | バッチ設計書の構成 |
| `docs/templates/phase3/error-codes.md` | エラーコード定義書の構成 |
| `docs/templates/phase3/security-design.md` | セキュリティ設計書の構成 |
| `docs/templates/phase2/report-design.md` | 帳票設計書の構成 |
| `docs/templates/phase2/feature-design.md` | 機能別設計書の構成（画面レイアウト・コンポーネント設計を含む） |

テンプレートが存在しない場合は、従来の手順でそのまま生成する（テンプレート不在でブロックしない）。

## 成果物一覧

詳細設計書は **横断設計書** と **機能別設計書** の2層で構成する。
**1情報=1箇所の原則** を徹底し、二重管理を防止する。

### 横断設計書（全機能共通で参照する性質のもの）

| # | ファイル | 内容 | 要否判定 |
|---|---------|------|---------|
| 1 | docs/design/performance-design.md, availability-design.md, operations-design.md | 非機能要件（性能・可用性・スケーラビリティ・運用・コスト）※ テンプレート `non-functional.md` のインデックスに従い分割管理 | 常に必須 |
| 2 | docs/design/db-schema.md | DB詳細スキーマ（全カラム・型・制約・インデックス）。**DBの正** | 常に必須 |
| 3 | docs/api/openapi.yaml | OpenAPI完全版（request body/response定義）。**APIの正** | 常に必須 |
| 4 | docs/design/master-data.md | マスタデータ定義（初期データ・Enum・定数）。**Enumの正** | 判定ロジック参照 |
| 5 | docs/design/external-integration.md | 外部連携詳細仕様。**外部APIの正** | 判定ロジック参照 |
| 6 | docs/design/mail-templates.md | メール・通知テンプレート仕様 | 判定ロジック参照 |
| 7 | docs/design/setup-guide.md | 環境構築手順書 | 常に必須 |
| 8 | docs/design/security-design.md | セキュリティ設計書 | 常に必須 |
| 9 | docs/design/report-design.md | 帳票設計書 | 判定ロジック参照 |
| 10 | docs/design/data-migration.md | データマイグレーション設計書 | 判定ロジック参照 |

### 機能別設計書（各機能の処理フロー・画面構成・ビジネスロジックを1ファイルに集約）

| # | ファイル | 内容 | 要否判定 |
|---|---------|------|---------|
| 11 | docs/design/features/[REQ-ID]-logic.md | API・DB・バリデーション・権限・ビジネスロジック | 常に必須（要件定義書1つにつき1ファイル） |
| 12 | docs/design/features/[REQ-ID]-design.md | 画面構成・UIコンポーネント・レイアウト（UIを含む機能のみ） | UIを含む機能のみ |
| 13 | docs/design/test-design.md | TDD用テスト設計書（テストケース・前提条件・期待結果）。implement-spec のテスト先行フェーズで使用 | 常に必須 |

### ファイル命名規則（implement-spec の必須読取リストと対応）

機能別設計書は以下の規則に従い命名する。implement-spec がこの命名でファイルを検索するため、厳守すること：
- `docs/design/features/[REQ-ID]-logic.md` — API・DB・バリデーション・権限（implement-spec で★必須）
- `docs/design/features/[REQ-ID]-design.md` — 画面構成・UIコンポーネント（implement-spec で推奨）
- 例: REQ-AUTH-001 → `REQ-AUTH-001-logic.md` + `REQ-AUTH-001-design.md`

### 1情報=1箇所の原則（二重管理禁止）

| 情報 | 正の場所（Single Source of Truth） | 他の場所での扱い |
|------|----------------------------------|----------------|
| APIエンドポイント定義（リクエスト/レスポンス/エラー） | **openapi.yaml** | features/*.md では使用するエンドポイント一覧（メソッド+パス+概要）のみ記載し、詳細はSwagger参照 |
| テーブル全カラム定義 | **db-schema.md** | features/*.md では使用するテーブル名のみ記載し、カラム詳細はdb-schema.md参照 |
| Enum/定数の許容値 | **master-data.md** | db-schema.md ではCHECK制約として型情報のみ記載。許容値リストはmaster-data.md参照 |
| エラーコード体系 | **openapi.yaml**（各エンドポイントのresponses） | features/*.md では使用エンドポイント一覧から参照 |
| 外部API仕様 | **external-integration.md** | features/*.md では「外部連携あり」とリンクのみ |
| バッチ処理フロー | **features/*.md**（該当機能の設計書） | 機能に紐付くため横断設計書には含めない |

---

## フェーズ 0: 現状把握と計画

前提ファイルチェック、既存ドキュメント読み込み、成果物の要否判定、統一基盤確認を行う。

詳細手順は [references/phase0-planning.md](references/phase0-planning.md) を参照。

---

## フェーズ 1: 情報収集

モードによって動作が異なる。コード分析モードは並列サブエージェントでコード分析（1A）、設計書ファーストモードは要件定義書からの情報抽出と不足情報の質問（1B）を行う。

詳細手順は [references/phase1-analysis.md](references/phase1-analysis.md) を参照。

---

## フェーズ 2: 設計書執筆（メインが一元管理）

フェーズ1の情報収集結果をもとに、メインエージェントが設計書を執筆する。モード別ルール（コード根拠・値の出典・バリデーション）に従う。

詳細手順は [references/phase2-writing.md](references/phase2-writing.md) を参照。

---

## フェーズ 3: mkdocs.yml 更新 & 整合性チェック

mkdocs.yml 更新、整合性チェックサブエージェント、仕様カバレッジレビュー（コード分析モードのみ）、mkdocs build 確認を行う。

詳細手順は [references/phase3-review.md](references/phase3-review.md) を参照。

---

## フェーズ 4: 完了

1. 成果サマリーを提示：
   ```
   詳細設計書の生成が完了しました:
   横断設計:
   - DB詳細スキーマ: XX テーブル定義
   - OpenAPI完全版: requestBody/response スキーマ追加
   - エラーコード定義: XX エラーコード
   - セキュリティ設計: 認証/認可/OWASP対策
   - 環境構築手順書: セットアップ XX ステップ
   機能別設計:
   - XX 機能の統合設計書（API詳細・処理フロー・画面構成・ロジック含む）
   整合性チェック: XX 件の不整合を修正済み
   ```
2. 次のステップを提案（「実装に入りますか？」「テストを作りますか？」等）

---

## セッション中断時の再開

詳細手順は [references/session-resume.md](references/session-resume.md) を参照。

---

## ルール

### 共通ルール（両モード）
- PM オーケストレーション共通パターン（`.claude/rules/pm-orchestration.md` で自動ロード） の全ルールに従う
- **既存設計書との整合性を保つ。** 矛盾が見つかったら既存側も修正する
- 既存コードは一切変更しない

### コード分析モード固有
- **実装に書いていないことは書かない。** コードに存在しない機能を設計書に記載してはならない
- .claude/rules/doc-accuracy.md「ドキュメント生成の正確性ルール」を厳守すること

### 設計書ファーストモード固有
- **要件定義書に書いていないことは推測で書かない。** 不足情報はユーザーに質問する
- デフォルト値を仮採用した箇所は必ず「※ 未確定」と注記する
- 一般的なベストプラクティスを採用する場合は、その旨を明記する（例: 「REST API設計のベストプラクティスに基づく」）
- 設計書ファーストモードで生成した設計書は、実装後に `update-docs` で実コードと整合させることを前提とする
