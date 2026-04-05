# spec-map.yml 操作ガイド

spec-map.yml はコードと Spec の対応関係を管理する Single Source of Truth。
各スキルが spec-map.yml を更新する際は、以下のルールに従う。

## エントリの構造

```yaml
REQ-XXX-NNN:
  spec_version: 1          # Spec（要件定義書）が更新されるたびにインクリメント
  depends_on: []            # 依存先の REQ-ID リスト
  implementation:
    - path: "src/auth/signup.ts:signup()"   # ファイルパス:関数名 形式
      confirmed: 1          # この実装が確認済みの spec_version
  tests:
    - path: "tests/auth/signup.test.ts"
      confirmed: 1
```

## スキル別の操作ルール

| スキル | spec_version | confirmed | 備考 |
|--------|-------------|-----------|------|
| **spec-feature** | 1 で初期化 | 1 で初期化 | 新規エントリ追加。パスは「ファイルパス:関数名」形式 |
| **draft-spec** | 1 で初期化 | — | implementation/tests はまだ存在しない |
| **implement-spec** | 未登録なら 1 で初期化 | spec_version と同値 | implementation + tests エントリを追加 |
| **revise-spec** | +1 インクリメント | 実装確認後に spec_version と同値に更新 | 「見た目のみ」変更ではインクリメント不要 |
| **update-docs** | +1 インクリメント | spec_version と同値（コード変更が先行しているため） | 新規ファイルがあれば implementation/tests に追加 |
| **gen-tests** | 変更なし | spec_version と同値 | tests エントリを追加 |
| **hotfix** | +1 インクリメント | spec_version と同値 | Spec 同期時に更新 |

## タイミング別チェックリスト

### Spec新規作成時（draft-spec）
- [ ] REQ-ID をキーとして新規エントリを追加
- [ ] `spec_version: 1` で初期化
- [ ] `depends_on` を設定（依存Specがある場合）
- [ ] implementation/tests は空（コードがまだない）

### 既存コードのSpec化時（spec-feature）
- [ ] REQ-ID をキーとして新規エントリを追加
- [ ] `spec_version: 1` で初期化
- [ ] implementation に既存の実装ファイルパスを「ファイルパス:関数名」形式で追加
- [ ] tests に既存のテストファイルパスを追加
- [ ] `confirmed: 1` で初期化（コードとSpecが一致している状態）

### コード実装時（implement-spec）
- [ ] implementation セクションに実装ファイルを「ファイルパス:関数名」形式で追加
- [ ] tests セクションにテストファイルパスを追加
- [ ] confirmed を `spec_version` と同値に設定
- [ ] エントリが未登録の場合は `spec_version: 1` で新規作成

### Spec修正時（revise-spec）
- [ ] 変更種別を判定:
  - **動作変更**（バリデーション、ロジック、API）→ `spec_version` を +1
  - **見た目のみ**（CSS、テキスト）→ `spec_version` 据え置き
- [ ] 実装修正完了後、変更ファイルの `confirmed` を `spec_version` と同値に更新
- [ ] 削除したファイルのエントリを削除

### ドキュメント追従時（update-docs）
- [ ] `spec_version` を +1（コード変更が先行しているため）
- [ ] `confirmed` も `spec_version` と同値に更新
- [ ] 新規ファイルがあれば implementation/tests に追加

### テスト追加時（gen-tests）
- [ ] tests セクションにテストファイルパスを追加
- [ ] `confirmed` を `spec_version` と同値に設定
- [ ] `spec_version` は変更しない

### ホットフィックス時（hotfix）
- [ ] Spec同期時に `spec_version` を +1
- [ ] `confirmed` も `spec_version` と同値に更新

## 共通ルール

- **ファイル追加時:** implementation または tests セクションにエントリを追加する
- **ファイル削除時:** 対応するエントリを削除する
- **confirmed の意味:** その実装/テストファイルが、どの spec_version の時点で確認済みかを示す。confirmed < spec_version のファイルは「Spec 変更に未追従」を意味する
