---
paths:
  - "docs/requirements/**"
  - "docs/design/**"
  - "spec-map.yml"
  - "docs/templates/**"
  - "docs/api/**"
---

# Spec・設計書管理ルール

## ID体系
- 要件: REQ-[機能]-[連番]
- IDは一度振ったら変更しない
- OVERVIEW（サービス概要）は予約カテゴリ: REQ-OVERVIEW-001 をシステム全体の共通仕様に使用する
  - OVERVIEWに含めるべき内容: システムの目的・背景、ターゲットユーザー、技術スタック、インフラ構成、非機能要件（パフォーマンス・可用性・スケーラビリティ・セキュリティ）、外部サービス依存、法的・コンプライアンス要件、共通の制約事項
  - 個別Specには機能固有の要件のみ記載し、上記の共通仕様はOVERVIEWに集約して重複させないこと
  - 個別Spec作成・更新時にOVERVIEWに追記すべき共通要件が見つかった場合は、OVERVIEWも同時に更新すること
  - **OVERVIEW Spec の作成タイミング（全スキル共通）:** OVERVIEW が未存在の場合、個別機能のSpec作成より先に作成する

### OVERVIEW 同期トリガー（判定基準）
個別Spec作成・更新時に以下のいずれかに該当する変更があれば、OVERVIEWも同じコミットで更新する：
- **外部サービス依存の追加・変更:** 新しい外部API（決済、メール送信、地図、ストレージ等）の導入
- **認証・認可方式の変更:** OAuth追加、SSO導入、ロール体系の変更
- **技術スタックの追加・変更:** 新しいフレームワーク、DB、キャッシュ層の導入
- **非機能要件の追加・強化:** SLA変更、新しいパフォーマンス目標、可用性要件
- **法的・コンプライアンス要件:** 個人情報保護、GDPR、特定業法への対応
- **インフラ構成の変更:** 新しいサーバー、CDN、キュー等のインフラ追加
- **共通の制約事項:** ブラウザサポート範囲、対応デバイス、文字コード等の変更

該当しない例（OVERVIEW更新不要）: 個別機能のバリデーション変更、画面内UIの変更、機能固有のビジネスロジック修正

## glossary.md（用語辞書）ルール
- 全スキル共通: `docs/requirements/glossary.md` が存在しない場合、**最初のSpec執筆と同時に作成する**
- glossary.md が既に存在する場合、Spec 執筆前に必ず読み、定義済みの用語を使う
- 新しい概念が出てきた場合は glossary.md に追記してから Spec に書く
- spec-all の場合はフェーズ0で事前にコードのモデル名から一括作成する

### glossary.md 排他制御（並行実行時）
- glossary.md を新規作成する前に、**まず `docs/requirements/glossary.md` の存在を再確認する**（他のスキルが先に作成している可能性がある）
- 既に存在していた場合は新規作成せず、既存ファイルに追記する
- 複数の draft-spec / spec-feature が並行で動く場合、glossary.md の更新は**各スキルの最終コミット時にまとめて行う**（途中段階での部分書き込みを避ける）
- spec-all は フェーズ0 でglossary.mdを確定させるため、並行実行の問題は発生しない

## spec-map.yml スキーマ
```yaml
REQ-[カテゴリ]-[3桁連番]:        # REQ-ID（キー）
  spec_version: <integer>         # Specの改訂番号。初回は1、revise-specで+1
  depends_on:                      # 依存先のREQ-ID一覧（省略可）
    - REQ-XXX-NNN
  implementation:                  # 実装ファイル一覧
    - path: <string>              # 形式: "相対パス:関数名" (例: src/auth/signup.ts:signup)
      confirmed: <integer>        # この実装が確認済みのspec_version
  tests:                           # テストファイル一覧
    - path: <string>
      confirmed: <integer>
```
- `spec_version > confirmed` → Spec変更後の修正・確認が必要
- `depends_on` → dependency-graph.md の自動生成に使用。循環依存検出にも利用
- パスは全てコードリポのルートからの相対パス
- 分離リポ構成ではフロント・バックそれぞれの spec-map.yml に持つ

### spec-map.yml 同期ルール（全スキル共通）

spec_version と confirmed の更新責任を以下に定める。手動同期に頼らない。

| イベント | 更新内容 | 実行スキル |
|---------|---------|-----------|
| Spec新規作成 | spec_version: 1, confirmed: 1（implementation/tests は空） | draft-spec, spec-feature, spec-all |
| Spec修正（動作変更） | spec_version を +1。implementation/tests の confirmed は据え置き | revise-spec |
| Spec修正（見た目のみ） | spec_version 据え置き（CSS・テキスト変更等、動作に影響しない場合） | revise-spec |
| コード実装完了 | implementation にパス追加、confirmed = spec_version | implement-spec |
| コード修正完了 | 変更ファイルの confirmed = spec_version。削除ファイルはエントリ削除 | revise-spec (coder) |
| ドキュメント追従 | spec_version を +1、confirmed も同値に更新（コードが先行しているため） | update-docs |
| ホットフィックス | spec_version 据え置き。Spec同期時に +1 して confirmed も同値に | hotfix |

**不整合検出:** 全スキルの仕上げ時に `spec_version > confirmed` のエントリを検索し、未同期があれば警告する

## Spec依存グラフ
- `docs/design/dependency-graph.md` にSpec間の依存関係をMermaid図で管理する
- draft-spec / spec-all / revise-spec 実行時に自動更新する
- revise-spec 実行時は依存グラフから被依存先（影響を受けるSpec）を特定し、変更影響分析を記載する
- 循環依存は禁止。検出された場合はSpec分割またはイベント駆動への変更で解消する

## 品質ゲート
- フェーズ間の遷移には品質ゲートの通過が必要（`docs/quality-gates.md` 参照）
- AIはゲート項目を自動チェックし、結果を提示する。最終判定は人間が行う
- ホットフィックスはGate 1〜2をスキップ可能（24時間以内にSpec同期が必要）

## ディレクトリ規約
- docs/requirements/ : WHATとWHY（要件定義）
- docs/design/ : HOW（基本設計 - アーキテクチャ、DB、API）

## 画面遷移図の Single Source of Truth
- 画面遷移図は `docs/design/screen-flow.md` に一元管理する
- `docs/requirements/` には画面遷移図を配置しない（要件定義書からは `docs/design/screen-flow.md` を参照する）
- draft-spec / init-spec / revise-spec いずれの場合も `docs/design/screen-flow.md` を更新すること

## API仕様ルール
- CLAUDE.md の `api_style` に応じた仕様書を管理する:
  - `rest`: APIエンドポイントを追加・変更したら `docs/api/openapi.yaml` も同じコミットで更新（OpenAPI 3.1準拠）
  - `graphql`: スキーマ変更時に `docs/api/schema.graphql` も同じコミットで更新
  - `grpc`: `.proto` ファイル変更時に `docs/api/` 配下のProto定義も同じコミットで更新
  - `api_style` が未設定の場合は REST（openapi.yaml）をデフォルトとする

## コード根拠のフォーマット
Spec やドキュメントでコードの場所を参照する際は、以下の形式に統一する：
- **形式:** `相対パス:行番号` （例: `src/auth/signup.ts:42`）
- パスはコードリポのルートからの相対パス
- 行範囲を示す場合は `src/auth/signup.ts:42-58`
- メソッド名で示す場合は `src/auth/signup.ts:signup()` （行番号が頻繁に変わる場合のみ許可）
- インライン方式と表方式の併用可（詳細は `skills/_shared/spec-writing-standard.md`）

## セットアップ検証

init-spec 完了後、ユーザーにセットアップの検証を促す：

```
セットアップ検証チェックリスト:
- [ ] Claude Code で /model を実行 → プランモード: Opus、実行モード: Sonnet が設定されているか
- [ ] mkdocs serve でドキュメントサイトが表示されるか
- [ ] CLAUDE.md の「プロジェクト概要」「技術スタック」が正しく記入されているか
- [ ] CLAUDE.md の「テスト設定」にテストフレームワークと devサーバーURL が記入されているか
- [ ] コードリポで npm run test（または該当コマンド）が実行できるか
```
