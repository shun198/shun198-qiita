---
title: Terraformにおけるmain.tfやtfstateファイルの作成および運用方法について
tags:
  - AWS
  - S3
  - DynamoDB
  - Terraform
  - main.tf
private: false
updated_at: '2026-08-10T07:49:18+09:00'
id: c13529253cea5b4f41d3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はTerraformを使って
- main.tf
- 変数を格納するvariables.tf

の作成と運用方法について解説したいと思います

## 前提
- 東京リージョンを使用
- AWSを使用
- S3バケットとDynamoDBの作成方法について理解している

コンテナ経由でTerraformを使用すると複数ブロジェクトで使用する際にバージョンによる違いを意識せずに済みます
コンテナを使用したい方はこちらの記事も参考にしてみてください

https://qiita.com/shun198/items/09081dd299490f13ef03

## ディレクトリ構成
構成は以下の通りです
```
├── main.tf
└── variables.tf
```

- variables.tf
- main.tf

の順に作成していきましょう

## variables.tf
variables.tfに共通で使用する変数を記載していきます
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
```

## main.tf
main.tfでは
- tfstateファイルの管理方法
- 使用するプロバイダ(今回はAWS)およびそのプロバイダのバージョン制約
- Terraformのバージョン制約

などを記載していきます

```main.tf
# ------------------------------
# Terraform configuration
# ------------------------------
terraform {
  # tfstateファイルを管理するようbackend(s3)を設定
  backend "s3" {
    bucket         = "terraform-playground-for-cicd"
    key            = "terrafrom-playground.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-playground-tf-state-lock"
  }
  # プロバイダを設定
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 4.16"
    }
  }

  # Terraformのバージョン制約
  required_version = ">= 1.15.0"
}

# ------------------------------
# Provider
# ------------------------------
# プロバイダ(AWS)を指定
provider "aws" {
  region = "ap-northeast-1"
}

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

# ------------------------------
# Current AWS Region(ap-northeast-1)
# ------------------------------
# 現在のAWS Regionの取得方法
data "aws_region" "current" {}
```

### tfstateファイルの管理について
Terraformを使用する際はtfstateファイルを通じてインフラに関する情報を管理します
複数人で開発することが想定されるので
- S3バケット
- DynamoDB

を使ってチームで同じtfstateファイルを共有しながら開発するのが一般的です

#### S3バケット
今回はS3バケット内でtfstateファイルを管理します
私はバケット名を`terraform-playground-for-cicd`にしました
バケット名は一意でなくてはならないのでこの名前以外のS3バケットを作成した後はバケット名を記載してください

:::note warn
バケットを作成する際は非公開にしましょう
:::

![スクリーンショット 2023-01-08 8.10.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ac437e7d-9384-fdc9-15f5-2db2953f8df5.png)

プロパティからバージョニングを有効にすると古いtfstateファイルを復旧できるので便利です
![スクリーンショット 2023-01-08 8.12.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0a710ba6-7223-e4c3-4955-d79f4cc4ed1c.png)

#### DynamoDB
複数人が同時にterraformを実行しtfstateを更新してコンフリクトを起こすことを避けるため、
DynamoDBによって状態にロックをかけることができます
今回はテーブル名を`terraform-playground-tf-state-lock`、
プライマリーキーを`LockID`にします

![スクリーンショット 2023-01-08 8.21.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7915ac81-adbd-0b84-6250-c915b9aa758d.png)

```terraform
  backend "s3" {
    bucket         = "terraform-playground-for-cicd"
    key            = "terrafrom-playground.tfstate"
    region         = "ap-northeast-1"
    encrypt        = true
    dynamodb_table = "terraform-playground-tf-state-lock"
  }
```

https://developer.hashicorp.com/terraform/language/settings/backends/configuration

### locals
variables同様、変数の設定を行うことができます
localsはvariablesと違って下記のように複数の変数を組み合わせて使ったりすることができます
今回は全サービスで共通で使用できるタグを作成します

```terraform
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

Nameに関しては私がパブリックサブネットに独自に追記したタグですがこのようにlocalsで作成したタグをつけると見やすくなります
![スクリーンショット 2023-01-08 9.43.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/738f3c60-f3d1-d669-0a28-868deac14066.png)

#### workspace
Terraformでは同一AWSアカウント上で複数以上の環境を管理する際にworkspaceを使用します
今回はdev環境のworkspaceを作成します
```
terraform workspace new dev
```
でdevのworkspaceを作成します
workspaceが作成され、devに切り替わったことを確認します
```
terraform workspace list
  default
* dev
```

### 現在のAWS Regionの取得方法について
公式ドキュメントに記載の通り
```terraform
data "aws_region" "current" {}
```
と記載することで現在のAWS Regionである東京リージョンを取得できます
AZの設定等でハードコーディングしなくて済むので便利です

https://registry.terraform.io/providers/hashicorp/aws/latest/docs/data-sources/region

### providerで指定してるregionについて
```terraform
provider "aws" {
  region = "ap-northeast-1"
}
```
regionを`data.aws_region.current`にすればいいじゃん！って思うかもしれませんが
Cycleエラー(双方向参照エラー)になってしまうため、ここは残念ながら
```
region = "ap-northeast-1"
```
とハードコーディングする必要があります

## 初期化
以上の設定を終えたら下記のコマンドを実行しましょう
```
terraform init
```

## まとめ
Terraform使って複数人で開発する際に色々準備しないといけないので思ってたより覚えることが多くて大変でした
本記事をチートシートとして使っていただければと思います

## 参考
https://techgrowup.net/2022/04/18/terraform%E3%81%A7tfstate%E3%82%92s3%E3%81%A7%E7%AE%A1%E7%90%86%E3%81%99%E3%82%8B/

https://www.squadcast.com/blog/creating-your-first-module-using-terraform

https://developer.hashicorp.com/terraform/language/settings/backends/s3


