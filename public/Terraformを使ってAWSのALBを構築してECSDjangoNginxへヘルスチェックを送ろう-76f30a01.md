---
title: 'Terraformを使ってAWSのALBを構築してECS[Django+Nginx]へヘルスチェックを送ろう！'
tags:
  - Django
  - nginx
  - AWS
  - Terraform
  - ALB
private: false
updated_at: '2023-09-17T10:42:15+09:00'
id: 76f30a010df752b705cb
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はTerraformを使ってALBを構築する方法について解説していきたいと思います
構成は下記の通りです

![ecs-ページ1.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b1c13506-5f35-51b9-c6aa-2ea03701ce24.png)


## 前提
- Terraformのmain.tfを作成済み
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- ECSを構築済み
- ヘルスチェック用のAPIを作成済み
- 今回はHTTPの設定のみ解説します

main.tfをまだ作成していない方は下記の記事を参考にしてください

https://qiita.com/shun198/items/c13529253cea5b4f41d3

Terraformを使ってネットワークを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/a3bc837d8a8af5831323

Terraformを使ってRDSを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/5fd6b29962a8c259ae56

Terraformを使ってECSを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/e06ca36464cc054a6278

また、コンテナ経由でTerraformを使用すると複数ブロジェクトで使用する際にバージョンによる違いを意識せずに済みます
コンテナを使用したい方はこちらの記事も参考にしてみてください

https://qiita.com/shun198/items/09081dd299490f13ef03

## ディレクトリ構成
構成は以下の通りです
```
tree 
.
├── alb.tf
├── ecs.tf
├── main.tf
└── variables.tf
```

- alb.tf

にALBの設定を記載していきます

## alb.tf
ALBの設定を記載します

```alb.tf
# ------------------------------
# Load Balancer Configuration
# ------------------------------
resource "aws_lb" "app" {
  name = "${local.prefix}-main"
  # HTTPレベルでリクエストをハンドリングするALBを使用
  load_balancer_type = "application"
  subnets = [
    aws_subnet.public_a.id,
    aws_subnet.public_c.id
  ]

  security_groups = [aws_security_group.lb.id]

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-app" })
  )
}

# トラフィックを分散する箇所(グループ)
# 指定されたプロトコルとポート番号を使用して、ECSにリクエストをルーティングできる
resource "aws_lb_target_group" "app" {
  name        = "${local.prefix}-app"
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  port        = 80

  health_check {
    path = "/api/health/"
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-target-group" })
  )
}

# ロードバランサーの入り口に当たる
# 設定したプロトコルとポートを使用して接続リクエストをチェック役割を持つ
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  # ターゲットグループへ
  default_action {
    # ALBのリスナーからターゲットグループへforwardする
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-listener" })
  )
}

# Publicな通信からロードバランザーへインバウンドで入る
resource "aws_security_group" "lb" {
  description = "Allow access to ALB"
  name        = "${local.prefix}-lb"
  vpc_id      = aws_vpc.main.id

  # Publicな通信からロードバランザーへインバウンドで入る
  ingress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ロードバランザーからECS(Nginx)へアウトバウンドで出る
  egress {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-sg" })
  )
}
```

## ecs.tf
```ecs.tf
# ------------------------------
# ECS Configuration
# ------------------------------
resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-cluster" })
  )
}

data "template_file" "app_container_definitions" {
  template = file("./templates/ecs/taskdef.json.tpl")

  vars = {
    log_group_name_app = aws_cloudwatch_log_group.app.name
    log_group_name_web = aws_cloudwatch_log_group.web.name
    ecr_image_app      = var.ecr_image_app
    ecr_image_web      = var.ecr_image_web

  }
}


# タスク定義
resource "aws_ecs_task_definition" "app" {
  family                   = "${local.prefix}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn    = "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-exec-role"
  task_role_arn         = "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-role"
  container_definitions = data.template_file.app_container_definitions.rendered

  volume {
    name = "tmp-data"
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-task-def" })
  )
}

# ECSのセキュリテーグループ
resource "aws_security_group" "ecs_sg" {
  description = "Access for the ECS Service"
  name        = "${local.prefix}-ecs-sg"
  vpc_id      = aws_vpc.main.id

  # ECSからPublicな通信へのアウトバウンドアクセスを許可
  egress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port = 5432
    to_port   = 5432
    protocol  = "tcp"
    cidr_blocks = [
      aws_subnet.private_a.cidr_block,
      aws_subnet.private_c.cidr_block,
    ]
  }

  # Publicな通信からNginxへのインバウンドアクセスを許可
  # 全ての通信をNginxを経由させたいのでECSの8000ポートへ直接アクセスさせない
  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    # ALBのセキュリティグループを追加
    security_groups = [
      aws_security_group.lb.id
    ]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-sg" })
  )
}

resource "aws_ecs_service" "app" {
  name            = "${local.prefix}-app"
  cluster         = aws_ecs_cluster.main.name
  task_definition = aws_ecs_task_definition.app.family
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_c.id,
    ]
    security_groups = [aws_security_group.ecs_sg.id]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-service" })
  )

  # ECS側にターゲットグループ内で新規タスクの作成を依頼する
  load_balancer {
    target_group_arn = aws_lb_target_group.app.arn
    container_name   = "web"
    container_port   = 80
  }
}
```

### ALB本体の設定
```alb.tf
resource "aws_lb" "app" {
  name               = "${local.prefix}-main"
  load_balancer_type = "application"
  subnets = [
    aws.subnet.public_a.id,
    aws.subnet.public_c.id
  ]

  security_groups = [aws_security_group.lb.id]

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-app" })
  )
}
```

ALB本体の設定を行います
HTTP通信を扱うので今回はload_balancer_typeをapplicationに指定します
サブネット内にはpublicサブネットを指定します
セキュリティグループには後ほど作成するALBのセキュリティグループを指定します

### ALBのセキュリティグループの設定
ALBのセキュリティグループの設定を行います
ALBを使用するので80番ポートからの全てのアクセスを許可します
また、Nginxをリバースプロキシとして使用するのでアウトバウンドアクセスはNginxの80番ポートからの全てのアクセスを許可します
ECSのセキュリティグループもALBからのセキュリティグループからアクセスするよう修正します

|サービス|プロトコル|in/out|ポート番号|CIDR|
|--|--|--|--|--|
|ALB|HTTP|inbound|80|全てのアクセス|
|ALB|HTTP|outbound|80|全てのアクセス|
|ECS|HTTP|outbound|80|ALBのセキュリティグループからのアクセス|

```alb.tf
resource "aws_security_group" "lb" {
  description = "Allow access to ALB"
  name        = "${local.prefix}-lb"
  vpc_id      = aws_vpc.main.id

  # Publicな通信からロードバランザーへインバウンドで入る
  ingress = {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  # ロードバランザーからECS(Nginx)へアウトバウンドで出る
  egress = {
    protocol    = "tcp"
    from_port   = 80
    to_port     = 80
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-sg" })
  )
}
```

```ecs.tf
  # Publicな通信からNginxへのインバウンドアクセスを許可
  # 全ての通信をNginxを経由させたいのでECSの8000ポートへ直接アクセスさせない
  ingress {
    from_port = 80
    to_port   = 80
    protocol  = "tcp"
    # ALBのセキュリティグループを追加
    security_groups = [
      aws_security_group.lb.id
    ]
  }
```

### ALBのターゲットグループの設定
ターゲットグループの設定を行います
ターゲットグループはリクエストをフォワード先として指定する対象、つまりロードバランシングする対象のことです
作成する際は
- ターゲットグループが所属しているVPC
- ターゲットグループがトラフィックを待ち受けるプロトコル
- ターゲットグループがトラフィックを待ち受けるポート

を指定することで登録済みのターゲット(今回だとECS)ごとにリクエストをルーティングできます
また、ヘルスチェックは/api/health/へ向けて行います
今回はすでにヘルスチェックのパスを作成した上でECSのコンテナを作成しています

```alb.tf
# トラフィックを分散する箇所(グループ)
# 指定されたプロトコルとポート番号を使用して、ECSにリクエストをルーティングできる
resource "aws_lb_target_group" "app" {
  name        = "${local.prefix}-app"
  protocol    = "HTTP"
  vpc_id      = aws_vpc.main.id
  target_type = "ip"
  port        = 80

  health_check {
    path = "/api/health/"
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-target-group" })
  )
}
```

### ALBのリスナー
ALBのリスナーの設定を行います
リスナーは外部(インターネット)からアクセスするロードバランサーの入り口のことです
リスナーを作成する際はどのプロトコル・ポートを許可するか設定します

```alb.tf
# ロードバランサーの入り口に当たる
# 設定したプロトコルとポートを使用して接続リクエストをチェック役割を持つ
resource "aws_lb_listener" "app" {
  load_balancer_arn = aws_lb.app.arn
  port              = 80
  protocol          = "HTTP"

  # ターゲットグループへ
  default_action {
    # ALBのリスナーからターゲットグループへforwardする
    type             = "forward"
    target_group_arn = aws_lb_target_group.app.arn
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-alb-listener" })
  )
}
```

## ALLOWED_HOSTSの変更
ALBのDNSを許可するためにパラメータストア内の環境変数の値を変更します
ALBのDNSはロードバランサーの詳細から確認できます

![スクリーンショット 2023-08-26 14.22.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/84c15654-45a1-de5d-5b10-6b56199dbb15.png)
![スクリーンショット 2023-09-17 7.22.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f1b13ddf-6080-dbcc-e91b-6b55dee0859c.png)
![スクリーンショット 2023-09-17 7.22.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9cf2849d-5c59-f41f-76ed-b9b2b9a2a14c.png)

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

## 実際に作成してみよう!
フォーマットの修正、validateやplanによる確認が終わったら以下のコマンドで適用します
```
terraform apply -auto-approve
```

## 作成されたか確認してみよう！
![スクリーンショット 2023-08-26 14.26.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d5bc8ed0-8eec-9a26-547f-a3b7d0403daa.png)

![スクリーンショット 2023-08-26 14.27.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b0e3154e-12a1-40b6-00a9-c661d1061cad.png)

ECSが正常に動作できていたら成功です
![スクリーンショット 2023-08-26 14.21.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e28a05c8-ba57-96ed-2856-2c81b3058f36.png)

ALBのヘルスチェックが正常に実際されていれば成功です
![スクリーンショット 2023-09-17 7.07.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1533a140-75ae-96e8-4f51-36b71f4ef656.png)
![スクリーンショット 2023-09-17 7.07.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/08d6ee54-0c8b-ffb2-46d9-3bba2edc6cd8.png)

## リソースの削除
使用しないリソースは以下のコマンドで削除しましょう
```
terraform destroy
```

## 参考
https://registry.terraform.io/providers/hashicorp/aws/latest/docs/resources/lb

https://dev.classmethod.jp/articles/elb-explanation-try/

https://www.kanzennirikaisita.com/posts/aws-alb-concepts

https://dev.classmethod.jp/articles/terraform-alb/

https://docs.aws.amazon.com/ja_jp/elasticloadbalancing/latest/application/load-balancer-target-groups.html
