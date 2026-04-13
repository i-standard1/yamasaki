# スキル間の前提条件・成果物マップ

各スキルの入力（前提ファイル）と出力（生成ファイル）の一覧。
スキル実行前に前提ファイルが揃っているか確認し、不足している場合は先行スキルを提案する。

## スキル実行順序（推奨フロー）

### 新規プロジェクト（グリーンフィールド）
```
draft-spec（全機能分）→ detail-design（+ test-design.md）→ implement-spec（TDD: RED→GREEN）→ gen-tests（補強）
                                                              ↑ test-design.md があればTDD
                                                              ↑ なければ従来フロー（テスト同時生成）
```

### 既存プロジェクト（ブラウンフィールド）
```
[analyze-codebase →] init-spec → spec-all → detail-design（+ test-design.md）→ implement-spec（TDD）→ gen-tests（補強）
```

### 仕様変更
```
revise-spec → gen-tests（テスト更新）
```

### 緊急修正
```
hotfix → [24h以内] revise-spec（Spec同期）
```

## 前提条件・成果物マトリクス

### Phase 0: セットアップ

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **analyze-codebase** | コードリポ（200+ファイル） | `logs/context/analyze_plan.md`, `logs/context/analysis_[domain].md`, `docs/requirements/overview.md`（ドラフト） |
| **init-spec** | コードリポ, CLAUDE.md | CLAUDE.md（プロジェクト固有）, `docs/requirements/overview.md`, `docs/design/architecture.md`, `docs/design/db-design.md`, `docs/design/api-spec.md`（外部連携仕様書。外部連携がある場合のみ）, `docs/design/screen-flow.md`, `docs/api/openapi.yaml`, `spec-map.yml`, `mkdocs.yml`, `.github/workflows/ci.yml`（generate-ci.pyで自動生成） |

### Phase 1: 要件定義

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **draft-spec** | ユーザーの自然言語入力, `docs/requirements/glossary.md`（あれば） | `docs/requirements/features/[機能名].md`, `docs/requirements/glossary.md`, `docs/requirements/overview.md`（更新）, `mkdocs.yml`（nav更新） |
| **spec-feature** | 対象のコード, `docs/requirements/glossary.md`（あれば） | `docs/requirements/features/[機能名].md`, `docs/requirements/glossary.md`, `spec-map.yml`, `mkdocs.yml`（nav更新） |
| **spec-all** | `docs/requirements/overview.md`, コードリポ全体 | `docs/requirements/features/*.md`（全Spec）, `docs/requirements/glossary.md`, `docs/design/` 各ファイル（更新）, `docs/api/openapi.yaml`（更新）, `spec-map.yml`, `mkdocs.yml`（nav再構成） |

### Phase 2-3: 設計

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **detail-design** | `docs/requirements/features/*.md`, `docs/design/architecture.md`, `docs/design/db-design.md`, `docs/api/openapi.yaml` | `docs/design/db-schema.md`, `docs/design/features/*.md`（UI設計）, `docs/design/features/*-logic.md`（ロジック設計）, `docs/design/error-codes.md`, `docs/design/security-design.md`, `docs/design/security-ops.md`, **`docs/design/test-design.md`** 等, `docs/api/openapi.yaml`（完全版に拡充）, `mkdocs.yml`（nav更新） |

### Phase 4: 実装

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **orchestrate** | `docs/requirements/overview.md`, `docs/design/architecture.md`, `interfaces/` | `domains/[ドメイン]/CLAUDE.md`, `logs/context/superpm_plan_*.md`, `logs/context/pm_[domain]_*.md` |
| **domain-pm** | `domains/[ドメイン]/CLAUDE.md`, `logs/context/pm_[domain]_*.md` | 実装コード, テストコード, `spec-map.yml`（更新） |
| **implement-spec** | `docs/requirements/features/[REQ-ID].md`（**必須**）, `docs/design/` 各ファイル, `docs/design/test-design.md`（TDD用）, `docs/api/openapi.yaml` | テストコード（RED→GREEN）, 実装コード, `docs/impact-reports/[Spec ID].md`, `spec-map.yml`（更新）, 設計書（更新） |
| **revise-spec** | `docs/requirements/features/[REQ-ID].md`（**必須**）, 既存コード | 更新されたSpec, 更新されたコード, `spec-map.yml`（spec_version +1）, `docs/impact-reports/[Spec ID].md` |
| **apply-design** | デザインファイル（Figma/スクショ）, 対象Spec | 更新されたHTML/CSS/テンプレート |
| **hotfix** | 障害情報, 対象コード | 修正コード, `hotfix/` ブランチ, `spec-map.yml`（更新） |

### Phase 5: テスト

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **gen-tests** | CLAUDE.md（テスト設定）, 実装コード, 対象Spec | テストファイル（unit + E2E）, `docs/tests/unit-test-spec.md`, `docs/tests/integration-test-spec.md`, `spec-map.yml`（tests更新） |
| **gen-test-specs** | `docs/requirements/features/*.md`, `docs/design/` 各ファイル | `docs/tests/system-test-spec.md`, `docs/tests/uat-spec.md`, `mkdocs.yml`（nav更新） |
| **gen-test-report** | テスト実行結果, `docs/tests/*.md` | `docs/tests/test-report.md` |

### ユーティリティ

| スキル | 前提（入力） | 成果物（出力） |
|--------|-------------|---------------|
| **update-docs** | コード変更（git diff）, `spec-map.yml` | 更新された設計書・Spec |
| **sync-template** | テンプレートリポURL（CLAUDE.md内） | 更新された `.claude/` ファイル群 |
| **feedback-template** | テンプレートリポURL, 修正内容 | テンプレートリポへのPR |

## 前提ファイル不足時のフォールバック

| 不足ファイル | エラーメッセージ例 | 推奨アクション |
|-------------|-----------------|--------------|
| `docs/requirements/overview.md` | 「overview.md が見つかりません」 | init-spec を先に実行 |
| `docs/requirements/features/[REQ-ID].md` | 「対象のSpecが見つかりません」 | draft-spec または spec-feature を先に実行 |
| `docs/requirements/glossary.md` | （自動作成される） | 最初のSpec執筆時に自動生成 |
| `docs/design/architecture.md` | 「基本設計が見つかりません」 | init-spec を先に実行 |
| `docs/api/openapi.yaml` | 「API仕様が見つかりません」 | init-spec を先に実行 |
| `spec-map.yml` | （自動作成される） | init-spec で初期生成 |
| `domains/` | （自動作成される） | orchestrate が自動初期化 |
| CLAUDE.md「テスト設定」が空 | 「テストフレームワークが不明です」 | CLAUDE.md を手動で記入 |
