---
name: drawio
description: Always use when user asks to create, generate, draw, or design a diagram, flowchart, architecture diagram, ER diagram, sequence diagram, class diagram, network diagram, or mentions draw.io, drawio, .drawio files. Use for complex diagrams where Mermaid is insufficient.
---

# Draw.io Diagram Skill

draw.io の `.drawio` ファイルを生成し、MkDocs ドキュメントに埋め込む。
Mermaid では表現しにくい複雑なアーキテクチャ図・詳細ダイアグラムに使用する。

## Mermaid vs draw.io 使い分け基準

| 用途 | ツール | 理由 |
|------|--------|------|
| シンプルなフロー・シーケンス図 | Mermaid | テキストベースで差分追跡しやすい |
| 複雑なアーキテクチャ図 | draw.io | レイアウト自由度・アイコン豊富 |
| ER図（テーブル少数） | Mermaid | 簡潔に書ける |
| ER図（テーブル多数・リレーション複雑） | draw.io | 配置の自由度が必要 |
| ネットワーク構成図・インフラ図 | draw.io | AWS/GCP等のアイコンが使える |
| 画面遷移図（多数ページ） | draw.io | 配置の自由度が必要 |

## 前提条件: mkdocs.yml に drawio プラグインが必要

drawio ファイルを MkDocs で描画するには `mkdocs-drawio` プラグインが必要。
mkdocs.yml の `plugins:` セクションに `- drawio` が含まれていることを確認し、
なければ追加してから図を作成する。

```yaml
plugins:
  - search
  - drawio          # ← これが必要
```

## 図の作成手順

1. **mkdocs.yml の `plugins:` に `- drawio` があるか確認**（なければ追加）
2. **draw.io XML を生成** -- mxGraphModel 形式
3. **Write ツールで `.drawio` ファイルを書き出す**
4. **Markdown で参照** -- `![説明](path/to/diagram.drawio)` （mkdocs-drawio プラグインが描画）

## ファイル配置・命名規則

- **配置先**: 参照するMarkdownと同じディレクトリ、または `docs/images/` 配下
- **命名**: `[内容]-[種別].drawio`（例: `aws-architecture.drawio`, `order-flow-detail.drawio`）
- **小文字ハイフン区切り**

## Markdown での埋め込み

```markdown
![AWSアーキテクチャ図](./aws-architecture.drawio)
![Page-2](./diagram.drawio)                          <!-- ページ名指定 -->
![](./diagram.drawio){ page="Page-2" }               <!-- attr_list でページ指定 -->
```

## XML 基本構造

```xml
<mxGraphModel adaptiveColors="auto">
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <!-- ここに図の要素を配置。parent="1" -->
  </root>
</mxGraphModel>
```

## CRITICAL: XML ルール

- XML コメント (`<!-- -->`) は**絶対に含めない**
- 特殊文字はエスケープ: `&amp;`, `&lt;`, `&gt;`, `&quot;`
- 全ての `mxCell` に一意の `id` を付与
- `id="0"`（ルート）と `id="1"`（デフォルトレイヤー、parent="0"）は必須
- **Edge には必ず子要素として `<mxGeometry relative="1" as="geometry" />` を含める**（自己閉じタグの edge は描画されない）
- **エッジラベルに HTML を使う場合は `html=1;` をスタイルに必ず含める**（ないと `<font>` タグが生テキストで表示される）

## CRITICAL: z-order（描画順）ルール

XML の記述順で前面/背面が決まる（後に書いたものが前面）。以下の順序を厳守:

1. **グループ/コンテナ**（背面 — 枠線・背景のみ）
2. **エッジ（矢印・接続線）**（中間）
3. **アイコン・テキストラベル**（前面 — 最も手前）

アイコンが矢印の裏に隠れると接続関係が見えなくなるため、**アイコンは必ずエッジの後に定義する**。

### アイコンは parent="1" で絶対座標にする

グループの子にするとグループと同じ z-order 層になり、エッジより背面に描画される。
アイコンをエッジより前面に出すには、**parent="1"（ルート直下）に配置し絶対座標を使う**:

```xml
<!-- 1. グループ（背面） -->
<mxCell id="vpc" value="VPC" style="swimlane;..." vertex="1" parent="1">
  <mxGeometry x="50" y="100" width="600" height="400" as="geometry"/>
</mxCell>

<!-- 2. エッジ（中間） -->
<mxCell id="e1" edge="1" parent="1" source="ec2" target="rds" style="...">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>

<!-- 3. アイコン（前面、絶対座標で配置） -->
<mxCell id="ec2" value="EC2" style="shape=mxgraph.aws4.fargate;..." vertex="1" parent="1">
  <mxGeometry x="70" y="160" width="40" height="40" as="geometry"/>
</mxCell>
```

## レイアウト設計の原則

図全体を設計してからXMLを書く。場当たりで要素を配置すると間隔不足・エッジ交差が頻発する。

### グリッドベースレイアウト

列（x座標）と行（y座標）を先に決め、全アイコンをグリッドに配置する:

```
列: Col-1=310, Col-2=560, Col-3=810   （250px 間隔）
行: Row-1=240, Row-2=430, Row-3=630, Row-4=860  （190〜200px 間隔）
```

- **メインフローは中央列で上→下**（ユーザー → CDN → LB → App → DB）
- **補助サービスは右列に縦並び**（監視・ストレージ・設定系）
- **外部サービスは図の右端に独立グループ**

### 複数エッジの右方向分離（段階チャネル方式）

1つのアイコンから右側の複数サービスへ接続する場合、垂直チャネルをずらして並走させる:

```
ECS Back → ECR:            垂直チャネル x=1040
ECS Back → Secrets Manager: 垂直チャネル x=1055
ECS Back → CloudWatch:     垂直チャネル x=1070
ECS Back → S3:             垂直チャネル x=1085
```

各チャネルの間隔は **15px** 以上。これによりエッジ同士が重ならない。

## アイコンサイズ・間隔ルール

### 推奨アイコンサイズ

| 図の用途 | アイコンサイズ | フォントサイズ |
|---------|-------------|-------------|
| 概要図（全体俯瞰） | **50x50** | fontSize=11 |
| 詳細図（要素数が多い） | 40x40 | fontSize=10 |

MkDocs 埋め込みでは図が 40〜50% に縮小表示される。**50x50 + fontSize=11 を標準にする**。

### 間隔ルール

- **縦方向**: アイコン中心間は最低 **190px** 空ける（50pxアイコン + ラベル60px + 余白80px）
- **横方向**: アイコン中心間は最低 **200px** 空ける（ラベル幅を考慮）
- ラベル位置が `verticalLabelPosition=bottom` の場合、下に約 **50px** のテキスト領域を確保
- 10px グリッドに揃える
- **グループ内パディング**: グループ枠からアイコン端まで最低 **30px**

## 重なり禁止ルール（CRITICAL）

draw.io ビューアではアイコンが矢印より前面に描画されるため、矢印がアイコンの上を通ると
**矢印が消えて見えなくなる**。同様に、グループ同士が重なると枠線が混ざって構造が読み取れなくなる。

### ルール 1: エッジは絶対にアイコンを横切らない

エッジの waypoint を使ってアイコン群を**迂回**させる。アイコンの間（隙間）を通すか、外側を回す。

```xml
<!-- NG: source=A, target=Z で直線を引くと B,C,D アイコンの上を通ってしまう -->
<mxCell id="bad" edge="1" source="A" target="Z" style="...">
  <mxGeometry relative="1" as="geometry"/>
</mxCell>

<!-- OK: waypoint で迂回 -->
<mxCell id="good" edge="1" source="A" target="Z" style="edgeStyle=orthogonalEdgeStyle;...">
  <mxGeometry relative="1" as="geometry">
    <Array as="points">
      <mxPoint x="50" y="500"/>     <!-- A の左端から下へ抜ける -->
      <mxPoint x="50" y="800"/>     <!-- 図の左端を回す -->
      <mxPoint x="900" y="800"/>    <!-- 下端を通って Z 方向へ -->
    </Array>
  </mxGeometry>
</mxCell>
```

**チェック方法**: エッジの始点・終点・waypoint で構成される線分が、すべてのアイコンの矩形領域
（アイコン位置 ± 余白 30px）と交差しないこと。交差する場合は waypoint を追加して迂回させる。

### ルール 2: 同レベルの矩形（グループ）は重ねない

親子関係でないグループ（同じ親を持つ兄弟グループ）は、矩形領域が**1pxたりとも重ならない**よう
スペースを空ける。重なっていいのは「親グループ ⊃ 子グループ」の包含関係のみ。

```
NG:                          OK:
+---+                        +---+   +---+
| A +---+                    | A |   | B |
|   | B |                    +---+   +---+
+---+   |
    +---+

OK（親子関係）:
+--------+
| Parent |
| +----+ |
| | A  | |
| +----+ |
+--------+
```

**最低マージン**: 兄弟グループ同士は **30px 以上**空ける。グループ枠線が太い場合（4px〜）は
**40px 以上**空ける。

**チェック方法**: 同じ `parent` を持つ vertex 同士について、座標範囲 (x, y, x+width, y+height)
が交差しないことを確認する。子要素を持つグループ同士も同様。

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

## AWS アイコン（ビューア互換）

### CRITICAL: `productIcon` / `resourceIcon` は使用禁止

`shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.cloudfront` のような複合シェイプは
**mkdocs-drawio ビューアのステンシルレジストリに未登録**のため、ただの黒い四角形になる。

**直接ステンシルを参照する**:
```
shape=mxgraph.aws4.cloudfront     ← OK（ビューアで描画される）
shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.cloudfront  ← NG（黒い四角になる）
```

### AWS サービスアイコンのスタイルテンプレート

```xml
<mxCell id="cf" value="CloudFront" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=none;fillColor=#8C4FFF;labelBackgroundColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;whiteSpace=wrap;fontSize=11;shape=mxgraph.aws4.cloudfront;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="50" height="50" as="geometry"/>
</mxCell>
```

### AWS サービスカテゴリカラー

| カテゴリ | fillColor | 対象サービス例 |
|---------|-----------|-------------|
| ネットワーキング | `#8C4FFF` | CloudFront, ALB/ELB, VPC, Route53 |
| コンピューティング | `#ED7100` | ECS Fargate, EC2, Lambda |
| データベース | `#3B48CC` | RDS, ElastiCache, DynamoDB |
| ストレージ | `#3F8624` | S3, EBS, EFS |
| セキュリティ | `#DD344C` | Secrets Manager, IAM, WAF |
| アプリ統合 | `#E7157B` | SQS, EventBridge, SNS, Step Functions |
| 管理・監視 | `#E7157B` | CloudWatch, CloudTrail |
| メール | `#DD344C` | SES |
| コンテナ | `#ED7100` | ECR, ECS |
| ユーザー | `#232F3E` | mxgraph.aws4.user |

### AWS グループシェイプ（これらはビューア互換OK）

```
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud   ← AWS Cloud
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc          ← VPC
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group ← Subnet
```

### AWS サブネット色分け

| サブネット種別 | strokeColor | fillColor | 用途 |
|-------------|------------|-----------|------|
| Public Subnet | `#248814` | `#E9F3E6` | ALB, NAT GW, IGW |
| Private App Subnet | `#147EBA` | `#E6F2F8` | ECS Fargate, Lambda |
| Private Data Subnet | `#7D2EBA` | `#F1E6F8` | RDS, ElastiCache |

色で3層構造を視覚的に区別する。全て同じ色だと構造が読み取りにくい。

### エッジの太さ目安

図は 40〜50% に縮小表示されるため、細すぎると見えない:
- **メインフロー**: `strokeWidth=3` （縮小後 ≈ 1.2px）
- **サブフロー / データ接続**: `strokeWidth=2` （縮小後 ≈ 0.8px）
- **補助通信（設定・監視）**: `strokeWidth=2;dashed=1` （破線で区別）
- `strokeWidth=1` は縮小すると消えるため非推奨

### エッジ色の使い分け

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

## XML リファレンス

詳細なスタイル・レイアウトリファレンス: https://github.com/jgraph/drawio-mcp/blob/main/shared/xml-reference.md
