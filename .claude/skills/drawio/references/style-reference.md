# スタイルリファレンス

## コンテナ（グループ化）

アーキテクチャ図では swimlane コンテナを使う:
```xml
<mxCell id="vpc" value="VPC" style="swimlane;startSize=30;fillColor=#dae8fc;strokeColor=#6c8ebf;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="600" height="400" as="geometry"/>
</mxCell>
<mxCell id="ec2" value="EC2" style="rounded=1;whiteSpace=wrap;" vertex="1" parent="vpc">
  <mxGeometry x="20" y="40" width="120" height="60" as="geometry"/>
</mxCell>
```

子要素は `parent="コンテナID"` を設定し、座標はコンテナ内の相対座標。

## エッジ（接続線）

```xml
<mxCell id="e1" edge="1" parent="1" source="a" target="b" style="edgeStyle=orthogonalEdgeStyle;rounded=1;">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>
```

## スタイルプロパティ

| プロパティ | 用途 |
|-----------|------|
| `rounded=1` | 角丸 |
| `whiteSpace=wrap` | テキスト折り返し |
| `fillColor=#dae8fc` | 背景色 |
| `strokeColor=#6c8ebf` | 枠線色 |
| `shape=cylinder3` | DB用シリンダー |
| `swimlane;startSize=30` | タイトル付きコンテナ |
| `edgeStyle=orthogonalEdgeStyle` | 直角コネクタ |
| `dashed=1` | 破線 |

## エッジの太さ目安

図は 40〜50% に縮小表示されるため、細すぎると見えない:
- **メインフロー**: `strokeWidth=3` （縮小後 ≈ 1.2px）
- **サブフロー / データ接続**: `strokeWidth=2` （縮小後 ≈ 0.8px）
- **補助通信（設定・監視）**: `strokeWidth=2;dashed=1` （破線で区別）
- `strokeWidth=1` は縮小すると消えるため非推奨

## エッジ色の使い分け

| 接続種別 | strokeColor | 例 |
|---------|-----------|------|
| ユーザートラフィック | `#232F3E` | User → CF → ALB → ECS |
| DB / キャッシュ | `#3B48CC` | ECS → RDS, ECS → ElastiCache |
| ストレージ | `#3F8624` | ECS → S3 |
| 外部サービス | `#555555` | NAT → CloudLogi, Sentry, SendGrid |
| 設定 / 監視 | `#888888`（dashed） | ECS → Secrets, CloudWatch |

## ダークモード対応

`adaptiveColors="auto"` を mxGraphModel に設定すれば自動対応。
明示指定が必要な場合: `fontColor=light-dark(#333333,#cccccc)`

## エクスポート（オプション）

draw.io Desktop がインストールされている場合、PNG/SVG/PDF にエクスポート可能:
```bash
/Applications/draw.io.app/Contents/MacOS/draw.io -x -f png -e -b 10 -o output.drawio.png input.drawio
```
MkDocs では `.drawio` を直接埋め込めるためエクスポートは通常不要。
