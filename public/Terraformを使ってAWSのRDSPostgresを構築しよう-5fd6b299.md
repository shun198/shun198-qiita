---
title: Terraformを使ってAWSのRDS(Postgres)を構築しよう！
tags:
  - AWS
  - PostgreSQL
  - RDS
  - Terraform
private: false
updated_at: '2023-07-16T14:30:37+09:00'
id: 5fd6b29962a8c259ae56
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はTerraformを使ってRDS(Postgres)を構築する方法について解説していきたいと思います

構成は下記の通りです
![RDS-ページ1.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/49904714-eb51-5862-1e9c-d3fce39aa94d.png)

## 前提
- Terraformのmain.tfを作成済み
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- 今回はPostgresのDBインスタンスを作成します

main.tfをまだ作成していない方は下記の記事を参考にしてください

https://qiita.com/shun198/items/c13529253cea5b4f41d3

Terraformを使ってネットワークを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/a3bc837d8a8af5831323

また、コンテナ経由でTerraformを使用すると複数ブロジェクトで使用する際にバージョンによる違いを意識せずに済みます
コンテナを使用したい方はこちらの記事も参考にしてみてください

https://qiita.com/shun198/items/09081dd299490f13ef03

## ディレクトリ構成
構成は以下の通りです
```
tree 
.
├── database.tf
├── main.tf
├── network.tf
└── variables.tf
```

- variables.tf
- database.tf

の順にRDSの設定を記載していきます

## variables.tf
RDSインスタンスを作成する際に
- ユーザ名
- パスワード

を指定できますので設定を記載します

```variables.tf
# ------------------------------
# Variables
# ------------------------------

# プリフィックスを設定
variable "prefix" {
  default = "tf-pg"
}

# プロジェクトを識別する一意の識別子を設定
variable "project" {
  default = "terraform-playground"
}

# プロジェクトのオーナーを設定
variable "owner" {
  default = "shun198"
}

# DBのユーザ名を設定
variable "db_username" {
  description = "Username for the RDS postgres instance"
}

# DBのパスワードを設定
variable "db_password" {
  description = "Password for the RDS postgres instance"
}
```

## database.tf
RDSの
- ネットワーク関連
- RDSのインスタンス

の設定を記載します

```database.tf
# ------------------------------
# Database Configuration
# ------------------------------
resource "aws_db_subnet_group" "main" {
  name = "${local.prefix}-main"
  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_c.id,
  ]


  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-main" })
  )
}

resource "aws_security_group" "rds" {
  description = "Allow access to RDS"
  name        = "${local.prefix}-rds-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol    = "tcp"
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-rds-sg" })
  )
}

resource "aws_db_instance" "main" {
  identifier              = "${local.prefix}-db"
  db_name                 = "postgres"
  allocated_storage       = 20
  storage_type            = "gp2"
  engine                  = "postgres"
  engine_version          = "15.2"
  instance_class          = "db.t3.small"
  db_subnet_group_name    = aws_db_subnet_group.main.name
  password                = var.db_password
  username                = var.db_username
  backup_retention_period = 0
  multi_az                = false
  skip_final_snapshot     = true
  vpc_security_group_ids  = [aws_security_group.rds.id]

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-main" })
  )
}
```

### ネットワーク関連の設定
- サブネット
- セキュリティグループ

の設定を記載します
RDSをプライベートサブネットに配置したいので今回はsubnet_ids内に

- プライベートサブネットA
- プライベートサブネットC

に配置するよう設定します

```database.tf
# ------------------------------
# Database Configuration
# ------------------------------
resource "aws_db_subnet_group" "main" {
  name = "${local.prefix}-main"
  subnet_ids = [
    aws_subnet.private_a.id,
    aws_subnet.private_c.id,
  ]


  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-main" })
  )
}
```

セキュリティグループに関しましては以下のようにインバウンドルールとアウトバウンドルールを設定します
インバウンドルールはTCPの5432ポート(Postgres)のみ許可し、
アウトバウンドルールは今回は全てのトラフィックを許可しています
プロジェクトの要件に応じて柔軟に決めていただけたらと思います

```database.tf
resource "aws_security_group" "rds" {
  description = "Allow access to RDS"
  name        = "${local.prefix}-rds-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol    = "tcp"
    from_port   = 5432
    to_port     = 5432
    cidr_blocks = ["10.0.0.0/16"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-rds-sg" })
  )
}
```

### RDSの設定
RDSの設定を行います
各項目の詳細は以下の通りです
|項目|説明|
|------|-----|
|identifier|RDSインスタンスを識別する一意の名前|
|db_name|DB名|
|allocated_storage|RDSに割り当てるストレージの量|
|storage_type|ストレージの種類|
|engine|DBの種類|
|engine_version|DBのバージョン|
|instance_class|インスタンスの種類|
|db_subnet_group_name|RDSを配置するサブネット|
|username|RDSのユーザ名<br>今回はインスタンス作成時に入力するよう設定します|
|password|RDSのパスワード<br>今回はインスタンス作成時に入力するよう設定します|
|backup_retention_period|自動バックアップの保持期間<br>今回は検証用で作成するため0(バックアップを作成しない)に設定します|
|multi_az|複数のAZでインスタンスを生成するかどうか|
|skip_final_snapshot|インスタンスを削除する前にDBのスナップショットを作成するかどうか<br>今回は検証用で作成するためfalseに設定します|
|vpc_security_group_ids|RDSに設定するセキュリティグループ|

```database.tf
resource "aws_db_instance" "main" {
  identifier              = "${local.prefix}-db"
  db_name                 = "postgres"
  allocated_storage       = 20
  storage_type            = "gp2"
  engine                  = "postgres"
  engine_version          = "15.2"
  instance_class          = "db.t3.small"
  db_subnet_group_name    = aws_db_subnet_group.main.name
  username                = var.db_username
  password                = var.db_password
  backup_retention_period = 0
  multi_az                = true
  skip_final_snapshot     = true
  vpc_security_group_ids  = [aws_security_group.rds.id]

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-main" })
  )
}
```

## tagの作成
こちらに関しては任意です
ハードコーディングしてもいいのですが今回はmain.tfで定義した変数を使用します
mergeを使ってmain.tfにあるlocal.common_tags変数に任意の変数を追加します
共通部分は繰り返し使用でき、なおかつ独自の変数を追加できるのでおすすめです

<details>


前述のvarialbes.tfから
- var.prefix
- var.project
- var.owner

を取得します

```main.tf
# ------------------------------
# Locals
# ------------------------------
locals {
  # variables.tfから変数を取得
  # terraformのworkspaceの一覧から該当するworkspace(dev,stg,prdなど)を取得
  prefix = "${var.prefix}-${terraform.workspace}"
  common_tags = {
    Environmnet = terraform.workspace
    Project     = var.project
    Owner       = var.owner
    ManagedBy   = "Terraform"
  }
}
```

</details>

## 実際に作成してみよう!
フォーマットの修正、validateやplanによる確認が終わったら以下のコマンドで適用します
```
terraform apply -auto-approve
```

上記のコマンドを実行後、RDSのユーザ名とパスワードの入力が要求されます
今回ユーザ名をshun198にします
```
var.db_password
  Password for the RDS postgres instance

  Enter a value: password

var.db_username
  Username for the RDS postgres instance

  Enter a value: shun198 
```

ただし、パスワードに関しましては以下の制約を守る必要があります

> 制約事項: 表示可能な ASCII 文字で 8 文字以上で入力してください次の文字を含めることはできません: / (スラッシュ)、'(単一引用符)、" (二重引用符)、および @ (アットマーク)。

### ユーザ名・パスワードの入力を自動化したいときは？
terraform.tfvarsファイルに記載することで自動入力させることができます
```
tree 
.
tree 
.
├── database.tf
├── main.tf
├── network.tf
├── terraform.tfvars # 新たに追加
├── variables.tf
└── .gitignore　　　　　　　　　　　　　　# 新たに追加
```

今回は
- db_username
- db_password

の2つを追加します
```terraform.tfvars
db_username = "shun198"
db_password = "password"
```

上記の情報は秘匿情報なので.gitignoreに追加しましょう
```.gitignore
terraform.tfvars
```

## 作成されたか確認してみよう！
RDSの作成および該当するタグが付けられていることを確認します

- RDSインスタンス
- RDSのセキュリティグループ

が作成および該当するタグが付けられていることを確認します

### RDS
![スクリーンショット 2023-04-01 17.52.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9bb3cfba-831d-2f8c-e065-02978238d22b.png)

![スクリーンショット 2023-04-01 17.59.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f2e3eeff-0a3d-14b6-de7f-cdf7509a2814.png)

![スクリーンショット 2023-04-01 17.43.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d119494b-ce30-cae6-e352-2b8d3b1015be.png)

### セキュリティグループ
![スクリーンショット 2023-04-01 18.06.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c7b615ae-0f1e-d898-8b0b-a42c1ef82184.png)

![スクリーンショット 2023-04-01 18.06.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/52ce42f4-59b4-14a5-a3d5-ac66887c37cf.png)

## リソースの削除
使用しないリソースは以下のコマンドで削除しましょう
```
terraform destroy
```

## まとめ
RDSを手動で構築すると入力項目が多かったりネットワークの設定もしないといけなくてめんどくさかったのですがたった1コマンドで作成できるのはいいですね
今後ALB、Route53、ECSなどのマネージドサービスについての記事も書きたいと考えてます

## 参考
https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/db_instance

https://github.com/hashicorp/terraform-provider-aws/issues/9655

https://zenn.dev/suganuma/articles/fe14451aeda28f
