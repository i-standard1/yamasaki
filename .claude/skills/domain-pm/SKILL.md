---
name: domain-pm
description: |
  ドメインPMとして、SuperPMから受け取ったタスクをPG単位に分解し実装を指揮する。
  domains/[ドメイン名]/ ディレクトリ内で実行すること。
  orchestrate スキルで起動された場合に自動的に呼ばれる。
  ユーザーが直接呼び出すことはない（orchestrate経由専用）。
context:
  required:
    - _shared/task-decomposition-pattern.md
    - _shared/completion-checklist.md
  on_error:
    - _shared/error-recovery.md
---

# ドメインPM：タスク分解と実装指揮

## 前提確認

1. 作業ディレクトリが `domains/[ドメイン名]/` であることを確認
2. `domains/[ドメイン名]/CLAUDE.md` を読み、このドメインの責務・制約を把握
3. SuperPMから渡されたコンテキスト（`logs/context/pm_[domain]_*.md`）を受領し、以下を検証する：
   - [ ] ファイルが存在し、Markdownとして解析可能か
   - [ ] 「タスク一覧」セクションに REQ-ID が1つ以上含まれているか
   - [ ] 各 REQ-ID が `spec-map.yml` に存在するか
   - [ ] 「実行順序」セクションに依存関係（blocks / blockedBy）が記載されているか
   - [ ] `interfaces/` への参照がある場合、該当ファイルが存在するか
   - **不足がある場合はSuperPMに差し戻す**（不足項目を明示して報告）

## タスク分解と実行

[タスク分解パターン](../_shared/task-decomposition-pattern.md) に従い、受け取ったタスクを機能単位（PG 1人分）に分解・配布・起動する。
- 1タスク = 1 Spec ID = 1 PG が原則
- PGへのコンテキストは `domains/[ドメイン名]/CLAUDE.md` の「PGへ渡すコンテキストのフォーマット」に従う

## PGコンテキストの検証

PGに `logs/context/pg_[機能名]_*.md` を配布する前に、以下を確認する：
- [ ] 対象 REQ-ID の要件定義書（`docs/requirements/features/[REQ-ID].md`）が存在するか
- [ ] `docs/api/openapi.yaml` が存在し、該当エンドポイント定義を含んでいるか（APIを伴う機能の場合）
- [ ] `docs/design/shared-components.md` が存在する場合、コンテキストに参照を含めたか
- [ ] `interfaces/` にこのドメインのIF定義が存在する場合、コンテキストに依存先のIF定義への参照を含めたか
- [ ] `spec-map.yml` で `depends_on` に列挙された依存Specが全て `confirmed == spec_version` か
- **依存Specが未追従の場合:** PGに実装を開始させず、SuperPMに「先に [REQ-XXX] の追従が必要」と報告する

## ドメイン内整合性確認

全PG完了後、[完了確認チェックリスト](../_shared/completion-checklist.md) で確認し、SuperPMに完了報告する（完了タスク一覧、更新したIF定義、未解決の問題）。

## ルール
- `domains/[ドメイン名]/CLAUDE.md` のルールに従う
