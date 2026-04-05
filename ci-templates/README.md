# CI テンプレート

## 自動生成（推奨）

CLAUDE.md の技術スタック設定から CI ワークフローを自動生成する。

```bash
python3 ci-templates/generate-ci.py \
  --claude-md CLAUDE.md \
  --output .github/workflows/ci.yml \
  --repo-structure auto
```

### 対応技術スタック

| カテゴリ | 対応値 |
|---------|--------|
| backend | express, nestjs, django, fastapi, rails, go, spring-boot |
| frontend | next.js, nuxt, vue, react, none |
| test_unit | jest, vitest, pytest, rspec, go-test |
| test_e2e | playwright, cypress, none |

### リポ構成オプション

| 値 | 用途 |
|----|------|
| `auto` | ディレクトリ構造から自動判定 |
| `monorepo` | apps/web + apps/api 等のモノレポ |
| `separated-front` | 分離リポ・フロントエンド（E2E時にバックエンドを自動checkout） |
| `separated-back` | 分離リポ・バックエンド（E2Eなし） |
| `single` | 単体アプリ |

### パイプラインフロー

```
PR → Lint → Type check → Unit test → E2E test → AI review → Summary
```

構成によって自動的にジョブ依存が調整される：
- **monorepo**: unit-front / unit-back を並列実行 → E2E
- **separated-front**: unit → E2E（バックエンド自動checkout）
- **separated-back**: unit → AI review（E2Eなし）
- **single**: unit → E2E → AI review

## セットアップ手順

1. `python3 ci-templates/generate-ci.py` を実行
2. `ci-templates/review-prompt.md` → `.github/review-prompt.md` にコピー
3. GitHub Settings → Secrets に `ANTHROPIC_API_KEY` を設定
4. 必要に応じて生成されたymlのポート・パス・環境変数を調整

## 固定テンプレート（リファレンス用）

自動生成ではなく、手動でコピーして使いたい場合：

| 構成 | テンプレート |
|------|------------|
| モノレポ (Next.js + NestJS) | `ci-monorepo.yml` |
| 分離リポ・フロント (Next.js) | `ci-front.yml` |
| 分離リポ・バック (NestJS) | `ci-back.yml` |
| **共通ジョブ定義** | `_shared/common-jobs.yml` |

これらは Jest + Playwright + Node.js 固定。他の技術スタックでは `generate-ci.py` を使うこと。

### 共通ジョブ（`_shared/common-jobs.yml`）

3つのバリアントで共通する以下のジョブは `_shared/common-jobs.yml` に正規版を集約している：

- **spec-health** — spec-map.yml の整合性チェック（完全に同一）
- **ai-review** — Claude API によるPRレビュー（`needs:` のみバリアント別）
- **summary** — CI結果のPRコメント集約（`needs:` と `results` がバリアント別）

各 `ci-*.yml` にはバリアント固有のジョブ（lint, unit, e2e）のみ残し、共通ジョブは `_shared/common-jobs.yml` からコピーして `NEEDS_PLACEHOLDER` を置換すること。各ファイル末尾のコメントに具体的な設定値を記載している。
