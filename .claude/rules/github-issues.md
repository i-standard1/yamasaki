---
paths:
  - ".github/**"
description: GitHub Issue操作ルール（サブイシュー作成・イシュー分割時にロード）
alwaysApply: true
---

# GitHub Issue操作ルール

## サブイシュー作成

「サブイシューに分割して」「サブイシューを作って」等のリクエストでは、GitHub の正式なサブイシュー機能を使うこと。
本文にリンクを貼るだけでは**サブイシューにならない**。

### 手順

1. **サブイシューを個別作成**
   ```bash
   gh issue create --repo {owner}/{repo} --title "..." --label "..." --body "..."
   ```

2. **親イシューと各サブイシューの node ID を取得**
   ```bash
   gh issue view {number} --repo {owner}/{repo} --json id --jq '.id'
   ```

3. **GraphQL `addSubIssue` で親子関係を登録**
   ```bash
   gh api graphql -f query='
     mutation {
       addSubIssue(input: {issueId: "{parent_node_id}", subIssueId: "{child_node_id}"}) {
         issue { id }
       }
     }
   '
   ```

4. **親イシューの本文は変更不要** — サブイシューはGitHub UIで自動表示される

### 注意事項
- `addSubIssue` は必ず全サブイシュー分実行すること（1件でも漏れると親子関係が付かない）
- 親イシューの本文にチェックリストを手動追加する必要はない（GitHub が自動生成する）
- 既存イシューをサブイシュー化する場合も同じ GraphQL mutation を使う
