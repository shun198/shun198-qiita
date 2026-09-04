---
title: Terraformを使ってコンテナ経由でAWSのインフラを構築しよう！
tags:
  - AWS
  - Makefile
  - Docker
  - Terraform
  - docker-compose
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 09081dd299490f13ef03
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- AWSを使用
- AWSのアカウントを作成済み
- AWS Vaultをインストールおよび設定済み

AWS Vaultをまだインストールおよび設定できていない方は以下の公式ドキュメントと記事を参考にしてください

https://github.com/99designs/aws-vault

https://qiita.com/shun198/items/9af6911457ad43a6c237

## なぜコンテナを使うのか？
複数プロジェクトで開発することが想定されるのでプロジェクトによってTerraformのバージョンが違うかと思います
そのため、ローカル上ではなく、プロジェクトごとにterraformのコンテナを作成し、コンテナ経由でTerraformを使う方がいいと考えています
今回はチュートリアルに従ってt2.microのEC2インスタンスを作成します

## ディレクトリ構成
```
tree
.
├── .gitignore
└── infra
    ├── compose.yaml
    └── main.tf
```

### .gitignore
下記公式サイトからterraformの.gitignoreの内容をコピーします

https://github.com/github/gitignore/blob/main/Terraform.gitignore

### infra/compose.yaml
以下のようにcompose.yamlを記載します

Terraform CLIのCommunity版にはLTSチャンネルがないため、公式配布ページの最新安定版である`hashicorp/terraform:1.16.0`を使用します。

https://hub.docker.com/r/hashicorp/terraform/tags

```compose.yaml
services:
  terraform:
    container_name: terraform
    image: hashicorp/terraform:1.16.0
    # M1チップでも動くように
    platform: linux/x86_64
    volumes:
      - .:/infra
    working_dir: /infra
    environment:
      # AWS_ACCESS_KEY_IDとAWS_SECRET_ACCESS_KEYを環境変数として使用
      - AWS_ACCESS_KEY_ID=${AWS_ACCESS_KEY_ID}
      - AWS_SECRET_ACCESS_KEY=${AWS_SECRET_ACCESS_KEY}
      # MFAを使うため、AWS_SESSION_TOKENも環境変数として使用
      - AWS_SESSION_TOKEN=${AWS_SESSION_TOKEN}
# 永続Volumeを作成
volumes:
  infra:
```

### infra/main.tf
今回は公式ドキュメントのチュートリアルに記載していた内容をほぼそのまま使用します
```infra/main.tf
terraform {
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 6.62.0"
    }
  }

  required_version = "~> 1.16.0"
}

provider "aws" {
  #　東京リージョンを使用します
  region = "ap-northeast-1"
}

resource "aws_instance" "app_server" {
  ami           = "ami-0bba69335379e17f8"
  instance_type = "t2.micro"

  tags = {
    Name = "ExampleAppServerInstance"
  }
}

```

## Terraformを使ってインフラを構築してみよう！
### アクセスキーの期限を調整
まだアクセスキーを調整してない方は--durationを実行しましょう
```
aws-vault exec shun198 --duration=12h
```

### Terraformの初期設定
以下のコマンドを実行してTerraformの初期設定を行います
```
docker compose -f infra/compose.yaml run --rm terraform init
```

以下のログが出たら成功です
```
Initializing the backend...

Initializing provider plugins...
- Finding hashicorp/aws versions matching "~> 6.62.0"...
- Installing hashicorp/aws v6.62.0...
- Installed hashicorp/aws v6.62.0 (signed by HashiCorp)

Terraform has created a lock file .terraform.lock.hcl to record the provider
selections it made above. Include this file in your version control repository
so that Terraform can guarantee to make the same selections by default when
you run "terraform init" in the future.

Terraform has been successfully initialized!

You may now begin working with Terraform. Try running "terraform plan" to see
any changes that are required for your infrastructure. All Terraform commands
should now work.

If you ever set or change modules or backend configuration for Terraform,
rerun this command to reinitialize your working directory. If you forget, other
commands will detect it and remind you to do so if necessary.
```

気になる方はterraform fmtコマンドを実行してmain.tfのフォーマットを修正しましょう
```
docker compose -f infra/compose.yaml run --rm terraform fmt
main.tf
```

main.tfが有効かどうかvalidateコマンドで確認します
```
docker compose -f infra/compose.yaml run --rm terraform validate
Success! The configuration is valid.
```

AWSに適用される変更を`plan`コマンドで確認します
```
docker compose -f infra/compose.yaml run --rm terraform plan
Terraform used the selected providers to generate the following execution plan. Resource actions are indicated with the following symbols:
  + create

Terraform will perform the following actions:
```

### EC2インスタンスを作成
AWSに`main.tf`の設定を適用します
今回は`-auto-approve`を実行してyesを自動的に入力します
```
docker compose -f infra/compose.yaml run --rm terraform apply -auto-approve
```

以下のログが出たら成功です
```
Plan: 1 to add, 0 to change, 0 to destroy.
aws_instance.app_server: Creating...
aws_instance.app_server: Still creating... [10s elapsed]
aws_instance.app_server: Still creating... [20s elapsed]
aws_instance.app_server: Still creating... [30s elapsed]
aws_instance.app_server: Creation complete after 32s [id=i-01d6eeab4d9a96cb4]

Apply complete! Resources: 1 added, 0 changed, 0 destroyed.
```

コンソール画面からEC2インスタンスが作成されたことが確認できました
![スクリーンショット 2023-01-03 11.41.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e73bf764-569b-13b3-d69d-0768474dccf3.png)

## 作成したインフラを削除しよう
EC2インスタンスを削除します
```
docker compose -f infra/compose.yaml run --rm terraform destroy
```

yesを入力します
```
Plan: 0 to add, 0 to change, 1 to destroy.

Do you really want to destroy all resources?
  Terraform will destroy all your managed infrastructure, as shown above.
  There is no undo. Only 'yes' will be accepted to confirm.

  Enter a value: yes
```

以下のログが出たら成功です
```
aws_instance.app_server: Destroying... [id=i-01d6eeab4d9a96cb4]
aws_instance.app_server: Still destroying... [id=i-01d6eeab4d9a96cb4, 10s elapsed]
aws_instance.app_server: Still destroying... [id=i-01d6eeab4d9a96cb4, 20s elapsed]
aws_instance.app_server: Destruction complete after 30s

Destroy complete! Resources: 1 destroyed.
```

コンソール画面からEC2インスタンスが削除されたことが確認できました
![スクリーンショット 2023-01-03 11.44.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6936f62e-ff84-a37c-a2dc-c68eee28ec39.png)

## Makefileを使ってコマンドを簡潔にしよう
コマンドが長いのでMakefileを作成します
例えばフォーマットを整えたいときは
```
make fmt
```
と入力するだけで
```
docker compose -f infra/compose.yaml run --rm terraform fmt
```
を打ったことになるのでとても楽になります

```Makefile
RUN_TERRAFORM = docker compose -f infra/compose.yaml run --rm terraform
IAM_USER = shun198
DURATION = 12h

vault:
	aws-vault exec $(IAM_USER) --duration=$(DURATION)

init:
	$(RUN_TERRAFORM) init

fmt:
	$(RUN_TERRAFORM) fmt

validate:
	$(RUN_TERRAFORM) validate

show:
	$(RUN_TERRAFORM) show

apply:
	$(RUN_TERRAFORM) apply -auto-approve

graph:
	$(RUN_TERRAFORM) graph | dot -Tsvg > graph.svg

destroy:
	$(RUN_TERRAFORM) destroy
```

## 記事の紹介
以下の記事も書きましたので興味があれば読んでいただけると幸いです

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/fff4ddc0d7ae53665c2c

https://qiita.com/shun198/items/9e4fcb4479385217c323

https://qiita.com/shun198/items/14cdba2d8e58ab96cf95

https://qiita.com/shun198/items/ab6eca4bbe4d065abb8f

## 参考
https://developer.hashicorp.com/terraform/install

https://support.hashicorp.com/hc/en-us/articles/36257315779219-Subscribe-to-HashiCorp-Release-Updates

https://developer.hashicorp.com/terraform/tutorials/aws-get-started/aws-build

https://londonappdeveloper.com/how-to-use-terraform-via-docker-compose-for-professional-developers/
