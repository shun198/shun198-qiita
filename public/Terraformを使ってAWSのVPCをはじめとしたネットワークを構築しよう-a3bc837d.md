---
title: Terraformを使ってAWSのVPCをはじめとしたネットワークを構築しよう！
tags:
  - AWS
  - vpc
  - Terraform
private: false
updated_at: '2023-08-25T21:07:08+09:00'
id: a3bc837d8a8af5831323
organization_url_name: null
slide: false
---
## 概要
今回はTerraformを使って
- VPC
- パブリックサブネットとプライベートサブネット
- IGW
- ルートテーブルおよびルーティングの設定
- Elastic IP
- NATゲートウェイ

を構築したいと思います
今回作成するインフラ構成は下記の図のようになります
![terraform-vpc.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62055136-58cc-2ca6-8eec-c43e8fdc4f5f.png)

## 前提
- 東京リージョンを使用
- AWSを使用
- main.tfとvariables.tfを設定済み
- ネットワークに関する基本的な知識をある程度持っている

上記のファイルをまだ作成していない方は下記の記事を参考にしてください

https://qiita.com/shun198/items/c13529253cea5b4f41d3

AWSにおけるネットワークの概要について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/06d2c9cb6eb553278ff3

また、コンテナ経由でTerraformを使用すると複数ブロジェクトで使用する際にバージョンによる違いを意識せずに済みます
コンテナを使用したい方はこちらの記事も参考にしてみてください

https://qiita.com/shun198/items/09081dd299490f13ef03

## ディレクトリ構成
構成は以下の通りです
```
tree 
.
├── main.tf
├── network.tf
└── variables.tf
```

network.tfにネットワーク関連の設定を記載していきます

## network.tf
```network.tf
# ------------------------------
# VPC Configuration
# ------------------------------
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # DNSによる名前解決をサポートする
  enable_dns_support = true
  # パブリックIPアドレスを持つインスタンスが対応するDNSホスト名を取得できるよう明示する
  enable_dns_hostnames = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-vpc" })
  )
}

# ------------------------------
# Internert Gateway Configuration
# ------------------------------
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-igw" })
  )
}

# ------------------------------
# Public Subnet Configuration
# ------------------------------
resource "aws_subnet" "public_a" {
  cidr_block = "10.0.1.0/24"
  # サブネットに配置されたインスタンスにパブリックIPアドレスが付与される
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.main.id
  availability_zone       = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a" })
  )
}

# ルートテーブルの設定
resource "aws_route_table" "public_a" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-rt" })
  )
}

# ルートテーブルをパブリックサブネットaと紐付ける
# タグをサポートしてないのでつけない
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_a.id
}

# IGWへのルーティングを設定
# タグをサポートしてないのでつけない
resource "aws_route" "public_internet_access_a" {
  route_table_id = aws_route_table.public_a.id
  # インターネット(0.0.0.0/0)へのアクセスを許可
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

# NATゲートウェイ用のElasticIPをpublic_a内に作成
resource "aws_eip" "public_a" {
  # EIPはVPC内に存在する
  vpc = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-eip" })
  )
}

# NATゲートウェイ
resource "aws_nat_gateway" "public_a" {
  # パブリックサブネットaに作成したElasticIPをNATに割り当てる(allocateする)
  allocation_id = aws_eip.public_a.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-ngw" })
  )
}

resource "aws_subnet" "public_c" {
  cidr_block = "10.0.2.0/24"
  # サブネットに配置されたインスタンスにパブリックIPアドレスが付与される
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.main.id
  availability_zone       = "${data.aws_region.current.name}c"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-c" })
  )
}
resource "aws_route_table" "public_c" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-c-rt" })
  )
}

resource "aws_route_table_association" "public_c" {
  subnet_id      = aws_subnet.public_c.id
  route_table_id = aws_route_table.public_c.id
}

resource "aws_route" "public_internet_access_c" {
  route_table_id         = aws_route_table.public_c.id
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
}

resource "aws_eip" "public_c" {
  vpc = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-c-eip" })
  )
}

resource "aws_nat_gateway" "public_c" {
  allocation_id = aws_eip.public_c.id
  subnet_id     = aws_subnet.public_c.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-c-ngw" })
  )
}
# ------------------------------
# Private Subnet Configuration
# ------------------------------
resource "aws_subnet" "private_a" {
  cidr_block        = "10.0.11.0/24"
  vpc_id            = aws_vpc.main.id
  availability_zone = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-a" })
  )
}

resource "aws_route_table" "private_a" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-a-rt" })
  )
}

resource "aws_route_table_association" "private_a" {
  subnet_id      = aws_subnet.private_a.id
  route_table_id = aws_route_table.private_a.id
}

resource "aws_route" "private_a_internet_out" {
  route_table_id = aws_route_table.private_a.id
  # インターネットへのアウトバウンドアクセスを可能にするためにNATの設定を行う
  nat_gateway_id         = aws_nat_gateway.public_a.id
  destination_cidr_block = "0.0.0.0/0"
}

resource "aws_subnet" "private_c" {
  cidr_block        = "10.0.12.0/24"
  vpc_id            = aws_vpc.main.id
  availability_zone = "${data.aws_region.current.name}c"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-c" })
  )
}

resource "aws_route_table" "private_c" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-private-c-rt" })
  )
}

resource "aws_route_table_association" "private_c" {
  subnet_id      = aws_subnet.private_c.id
  route_table_id = aws_route_table.private_c.id
}

resource "aws_route" "private_c_internet_out" {
  route_table_id = aws_route_table.private_c.id
  # インターネットへのアウトバウンドアクセスを可能にするためにNATの設定を行う
  nat_gateway_id         = aws_nat_gateway.public_c.id
  destination_cidr_block = "0.0.0.0/0"
}
```

##  VPC
VPCには`10.0.0.0/16`を割り当てます
また、
- DNSによる名前解決
- パブリックIPアドレスを持つインスタンスが対応するDNSホスト名を取得

する設定を有効化します

```terraform:network.tf
resource "aws_vpc" "main" {
  cidr_block = "10.0.0.0/16"
  # DNSによる名前解決をサポートする
  enable_dns_support = true
  # パブリックIPアドレスを持つインスタンスが対応するDNSホスト名を取得できるよう明示する
  enable_dns_hostnames = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-vpc" })
  )
}

```

## インターネットゲートウェイ
VPC内にインターネットゲートウェイがないとパブリックサブネットからインターネットへアクセスできないので作成します
その際にVPCのIDと紐付けます
```terraform:network.tf
resource "aws_internet_gateway" "main" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-igw" })
  )
}
```

## パブリックサブネット
今回は
- public_a
- public_c

の2種類のサブネットを作成します
構成は以下の通りです

|パブリックサブネット|public_a|public_c|
|------|------|------|
|IPレンジ|10.0.1.0/24|10.0.2.0/24|
|AZ|ap-northeast-1a|ap-northeast-1c|


AZ内にパブリックサブネットを作成し、サブネットをVPCのIDと紐付けます
```terraform
resource "aws_subnet" "public_a" {
  cidr_block = "10.0.1.0/24"
  # サブネットに配置されたインスタンスにパブリックIPアドレスが付与される
  map_public_ip_on_launch = true
  vpc_id                  = aws_vpc.main.id
  availability_zone       = "${data.aws_region.current.name}a"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a" })
  )
}
```

### パブリックサブネットのルーティングの設定
- aws_route_table
- aws_route_table_association
- aws_route

を設定します

ルートテーブルをどの
- サブネット
- VPC
- インタネットゲートウェイ

と紐づけるかと
- ルーティング(パブリックなのですべてのIPアドレスを許可)

を設定する必要があります

```terraform
# ルートテーブルの設定
resource "aws_route_table" "public_a" {
  vpc_id = aws_vpc.main.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-rt" })
  )
}

# ルートテーブルをパブリックサブネットaと紐付ける
# タグをサポートしてないのでつけない
resource "aws_route_table_association" "public_a" {
  subnet_id      = aws_subnet.public_a.id
  route_table_id = aws_route_table.public_a.id
}

# IGWへのルーティングを設定
# タグをサポートしてないのでつけない
resource "aws_route" "public_internet_access_a" {
  route_table_id = aws_route_table.public_a.id
  # インターネット(0.0.0.0/0)へのアクセスを許可
  destination_cidr_block = "0.0.0.0/0"
  gateway_id             = aws_internet_gateway.main.id
```
### NATの設定
NATゲートウェイはブライベートサブネットのインスタンスが使用するのでパブリックサブネット側で設定をします
パブリックサブネット内にNATゲートウェイとNATゲートウェイに割り当てるElasticIPを作成します

```terraform
# NATゲートウェイ用のElasticIPをpublic_a内に作成
resource "aws_eip" "public_a" {
  # EIPはVPC内に存在する
  vpc = true

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-eip" })
  )
}

# NATゲートウェイ
resource "aws_nat_gateway" "public_a" {
  # パブリックサブネットaに作成したElasticIPをNATに割り当てる(allocateする)
  allocation_id = aws_eip.public_a.id
  subnet_id     = aws_subnet.public_a.id

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-public-a-ngw" })
  )
}
```
## プライベートサブネット
今回は
- private_a
- private_c

の2種類のサブネットを作成します
プライベートサブネットのホスト部を11からにしたのは今後パブリックサブネットを追加する際に
ホスト部の1から10までをパブリックサブネットにできて管理しやすいと思ったからです
構成は以下の通りです

|プライベートサブネット|private_a|private_c|
|------|------|------|
|IPレンジ|10.0.11.0/24|10.0.12.0/24|
|AZ|ap-northeast-1a|ap-northeast-1c|

パブリックサブネットでの設定を被る箇所が多いので違うところのみ解説します

### プライベートサブネットのルーティングの設定
NATゲートウェイを通じたインターネットへのアウトバウンドアクセスのみ許可します
```terraform
resource "aws_route" "private_a_internet_out" {
  route_table_id = aws_route_table.private_a.id
  # インターネットへのアウトバウンドアクセスを可能にするためにNATの設定を行う
  nat_gateway_id         = aws_nat_gateway.public_a.id
  destination_cidr_block = "0.0.0.0/24"
}
```

## tagの作成
こちらに関しては任意です
ハードコーディングしてもいいのですが今回はmain.tfで定義した変数を使用します
mergeを使ってmain.tfにあるlocal.common_tags変数に任意の変数を追加します
共通部分は繰り返し使用でき、なおかつ独自の変数を追加できるのでおすすめです

<details>

```terraform:variables.tf
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
```

```terraform:main.tf
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

## 実際に作成してみよう！
フォーマットの修正、validateやplanによる確認が終わったら以下のコマンドで適用します
```
terraform apply -auto-approve
```

## 作成されたか確認してみよう！
- VPC
- パブリックとサブネット
- インターネットげードウェイ
- ルートテーブル
- NATゲートウェイ

が作成および該当するタグが付けられていることを確認します

### VPC
![スクリーンショット 2023-01-08 9.50.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3a3cab91-2b99-0ea7-6e8b-f87cc8b2e257.png)


### サブネット
![スクリーンショット 2023-01-08 9.41.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dfd94599-0a54-f384-7515-c79c9573f161.png)

### インターネットゲートウェイ
![スクリーンショット 2023-01-08 9.49.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/36291b75-9c52-de20-7c6a-5db202006bb9.png)

### ルートテーブル
![スクリーンショット 2023-01-08 9.53.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a968064f-0fd2-be51-e63e-d79c057c805b.png)
![スクリーンショット 2023-01-08 9.53.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/07604d58-99ff-0402-5927-d2dd1bfec452.png)

### ElasticIP
![スクリーンショット 2023-01-08 10.08.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eb9877de-2393-8565-c397-05584332f3fd.png)


### NATゲートウェイ
![スクリーンショット 2023-01-08 9.47.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/20e9ea41-ff2a-9b1f-3fa4-05e66fbc863d.png)

![スクリーンショット 2023-01-08 9.47.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c35d158b-792f-c737-fc07-d9c47c4f0231.png)

## リソースの削除
使用しないリソースは以下のコマンドで削除しましょう
```
terraform destroy
```

## まとめ
VPCをはじめとしてネットワークの設定をたった1コマンドで作成できるのは楽でいいですね
ただし、NACLやALBの設定などをしてなくて心もとないので別記事で作成したいと思います

## 参考
https://dev.classmethod.jp/articles/about-terraform-version-required-constraints/

https://registry.terraform.io/providers/hashicorp/aws/latest/docs


