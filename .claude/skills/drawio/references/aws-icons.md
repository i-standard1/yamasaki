# AWS アイコン（ビューア互換）

## CRITICAL: `productIcon` / `resourceIcon` は使用禁止

`shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.cloudfront` のような複合シェイプは
**mkdocs-drawio ビューアのステンシルレジストリに未登録**のため、ただの黒い四角形になる。

**直接ステンシルを参照する**:
```
shape=mxgraph.aws4.cloudfront     ← OK（ビューアで描画される）
shape=mxgraph.aws4.productIcon;prIcon=mxgraph.aws4.cloudfront  ← NG（黒い四角になる）
```

## AWS サービスアイコンのスタイルテンプレート

```xml
<mxCell id="cf" value="CloudFront" style="outlineConnect=0;fontColor=#232F3E;gradientColor=none;strokeColor=none;fillColor=#8C4FFF;labelBackgroundColor=#ffffff;verticalLabelPosition=bottom;verticalAlign=top;align=center;html=1;whiteSpace=wrap;fontSize=11;shape=mxgraph.aws4.cloudfront;" vertex="1" parent="1">
  <mxGeometry x="100" y="100" width="50" height="50" as="geometry"/>
</mxCell>
```

## AWS サービスカテゴリカラー

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

## AWS グループシェイプ（これらはビューア互換OK）

```
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_aws_cloud   ← AWS Cloud
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_vpc          ← VPC
shape=mxgraph.aws4.group;grIcon=mxgraph.aws4.group_security_group ← Subnet
```

## AWS サブネット色分け

| サブネット種別 | strokeColor | fillColor | 用途 |
|-------------|------------|-----------|------|
| Public Subnet | `#248814` | `#E9F3E6` | ALB, NAT GW, IGW |
| Private App Subnet | `#147EBA` | `#E6F2F8` | ECS Fargate, Lambda |
| Private Data Subnet | `#7D2EBA` | `#F1E6F8` | RDS, ElastiCache |

色で3層構造を視覚的に区別する。全て同じ色だと構造が読み取りにくい。
