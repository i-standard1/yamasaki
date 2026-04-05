# Output Contract: Review Report（レビュー指摘レポート）

## イテレーション間の追跡

イテレーション2以降では、前回の finding_id リストを参照し:
- **resolved**: 修正済みの指摘（finding_id + "resolved" と記載）
- **persists**: 未修正の指摘（同じ finding_id を再利用）
- **new**: 新規発見の指摘（新しい finding_id を付与）

## レポート構成

```markdown
## レビュー結果（イテレーション N/3）

### 修正必須（信頼度80以上）
[CRITICAL/MAJOR の指摘を深刻度順に列挙]

### 修正推奨（MINOR、信頼度80以上）
[MINOR の指摘を列挙]

### 参考情報（信頼度80未満）
[記録のみ。修正依頼しない]

### Finding Timeline（イテレーション2以降）
| finding_id | 前回 | 今回 |
|------------|------|------|
| SEC-auth-42-a3f1 | new | resolved |
| BUG-user-88-c7d2 | new | persists |

### 判定
- [DONE] 指摘なし、または全て INFO レベル
- [NEEDS_FIX] 信頼度80以上の CRITICAL/MAJOR/MINOR あり
```
