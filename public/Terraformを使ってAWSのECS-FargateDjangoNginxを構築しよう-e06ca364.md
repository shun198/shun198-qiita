---
title: Terraformを使ってAWSのECS Fargate(Django+Nginx)を構築しよう！
tags:
  - Django
  - nginx
  - AWS
  - Terraform
  - ECS
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: e06ca36464cc054a6278
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はTerraformを使ってECS Fargateを構築します
かなり長い記事になっていて難易度が高いですが一緒に頑張っていきましょう
構成は下記の通りです

![ecs構成図.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a8e10c15-8bdb-26f6-2219-6bc138592628.png)

## 前提
- Terraformのmain.tfを作成済み
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- RDSを構築済み
- Djangoのプロジェクトを作成済み
- パッケージ管理はPoetryを使って行います
- アプリケーションサーバはGunicornを使用します

main.tfをまだ作成していない方は下記の記事を参考にしてください

https://qiita.com/shun198/items/c13529253cea5b4f41d3

Terraformを使ってネットワークを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/a3bc837d8a8af5831323

Terraformを使ってRDSを構築する方法について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/5fd6b29962a8c259ae56

また、コンテナ経由でTerraformを使用すると複数ブロジェクトで使用する際にバージョンによる違いを意識せずに済みます
コンテナを使用したい方はこちらの記事も参考にしてみてください

https://qiita.com/shun198/items/09081dd299490f13ef03

## ディレクトリ構成
構成は以下の通りです

```
tree 
.
├── application
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── tests.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── project
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings
│   │   │   ├── __init__.py
│   │   │   ├── base.py
│   │   │   ├── dev.py
│   │   │   ├── environment.py
│   │   │   └── local.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   ├── manage.py
│   ├── poetry.lock
│   └── pyproject.toml
├── containers
│   ├── django
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── nginx
│       ├── Dockerfile
│       └── nginx.conf
└── infra
    ├── cloudwatch.tf
    ├── database.tf
    ├── ecs.tf
    ├── main.tf
    ├── network.tf
    ├── templates
    │   └── ecs
    │       └── taskdef.json.tpl
    ├── terraform.tfvars
    └── variables.tf
```
まずは、

- variables.tf
- database.tf
- ecs.tf
- templates.json.tpl
- terraform.tfvars

の順にTerraformの設定を記載していきます

その後
- Dockerfileの作成
- 手動でECRとIAMロール作成と設定

をします
最後に実際にTerraformを実行し、自動デプロイしていきます

## variables
必要な変数の設定を行います
- ecr_image_app
- ecr_image_web

に関しましては後述するタスク定義とECRリポジトリの作成でも登場します

```variables.tf
# ------------------------------
# Variables
# ------------------------------

# プロジェクトを識別する一意の識別子
variable "prefix" {
  default = "tf-pg"
}

variable "project" {
  default = "terraform-playground"
}

variable "owner" {
  default = "shun198"
}

variable "db_username" {
  description = "Username for RDB MySQL Instance"
}

variable "db_password" {
  description = "Password for RDB MySQL Instance"
}

variable "ecr_image_app" {
  description = "ECR Image URI for Django App"
  default = "XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/django"
}

variable "ecr_image_web" {
  description = "ECR Image URI for Nginx"
  default = "XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/nginx"
}
```

## cloudwatch.tf
ECS内のCloudWatchの設定を行います
- Django
- Nginx

の2種類のロググループを作成します

```cloudwatch.tf
# Django
resource "aws_cloudwatch_log_group" "app" {
  name = "${local.prefix}-app"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-cloudwatch-logs" })
  )
}

# Nginx
resource "aws_cloudwatch_log_group" "web" {
  name = "${local.prefix}-web"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-cloudwatch-logs" })
  )
}
```

## database.tf
RDSのセキュリティグループのインバウンドルールに後ほど作成するECSのセキュリティグループを追加します

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
    tomap({ "Name" = "${local.prefix}-rds-subnet-group" })
  )
}

resource "aws_security_group" "rds" {
  description = "Allow access to RDS"
  name        = "${local.prefix}-rds-sg"
  vpc_id      = aws_vpc.main.id

  ingress {
    protocol  = "tcp"
    from_port = 5432
    to_port   = 5432
    security_groups = [
      # ECSからRDSへのアクセスを許可する
      aws_security_group.ecs_sg.id
    ]

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
    tomap({ "Name" = "${local.prefix}-rds-instance" })
  )
}
```

## ecs.tf
ecs.tf内で
- クラスター
- タスク定義ファイル
- タスク定義
- セキュリティグループ

の設定を行います

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

# ECSのタスク定義用のtplファイルの設定
data "template_file" "app_container_definitions" {
  template = file("./templates/ecs/taskdef.json.tpl")

  vars = {
    log_group_name_app = aws_cloudwatch_log_group.app.name
    log_group_name_web = aws_cloudwatch_log_group.web.name
    ecr_image_app = var.ecr_image_app
    ecr_image_web = var.ecr_image_web
  }
}

# タスク定義
resource "aws_ecs_task_definition" "app" {
  family                   = "${local.prefix}-app"
  container_definitions    = data.template_file.app_container_definitions.rendered
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn = "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-exec-role"
  task_role_arn =  "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-role"
  container_definitions    = data.template_file.app_container_definitions.rendered

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

  # ECSからPostgresへのアウトバウンドアクセスを許可
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
    cidr_blocks = [
      "0.0.0.0/0"
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
  # 今回は検証用のためタスクを1つだけ実行させる
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_c.id,
    ]
    security_groups  = [aws_security_group.ecs_sg.id]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-service" })
  )
}
```

一つずつ解説します
### クラスター
クラスターを以下のように作成します

```tf
resource "aws_ecs_cluster" "main" {
  name = "${local.prefix}-cluster"

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-cluster" })
  )
}
```

### タスク定義ファイル
コンテナの設定を記載するタスク定義ファイルを作成します
また、コンテナを起動させる際に環境変数が必要になるので今回はAWSのパラメータストアに環境変数を格納していきます

#### 環境変数の作成
作成する環境変数は以下のとおりです
今回作成するパスは/tf-pg/dev/{環境変数名}にします
|環境変数|説明|
|--|--|
|DJANGO_SETTINGS_MODULE|Djangoの設定ファイルを指定するための環境変数<br>今回はdev環境をデプロイするのでproject.settings.devを指定します|
|SECRET_KEY|Djangoのシークレットキー|
|ALLOWED_HOSTS|Djangoのアプリケーションへのアクセスを許可するオリジン<br>今回は*(ワイルドカード)を指定します|
|POSTGRES_NAME|PostgresのDB名|
|POSTGRES_USER|Postgresのユーザ名|
|POSTGRES_PASSWORD|Postgresのパスワード|
|POSTGRES_HOST|Postgresのホスト名|
|POSTGRES_PORT|Postgresのポート番号|

タスク定義を作成する際はパラメータストアに格納された各環境変数のarnが必要になってくるので
```
aws ssm get-parameters-by-path --path "/tf-pg/dev/"  
```
を実行するとパラメータのarnを含む詳細を取得できます
```
        {
            "Name": "/tf-pg/dev/ALLOWED_HOSTS",
            "Type": "String",
            "Value": "*",
            "Version": 1,
            "LastModifiedDate": 1692970086.203,
            "ARN": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/ALLOWED_HOSTS",
            "DataType": "text"
        },
        {
            "Name": "/tf-pg/dev/DJANGO_SETTINGS_MODULE",
            "Type": "String",
            "Value": "project.settings.dev",
            "Version": 1,
            "LastModifiedDate": 1692969979.44,
            "ARN": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/DJANGO_SETTINGS_MODULE",
            "DataType": "text"
        },
        {
            "Name": "/tf-pg/dev/POSTGRES_HOST",
            "Type": "SecureString",
            "Value": "AQICAHi9FCyTN3Cx9X97OrqEYX75d2ri/mNsGlu32o4ATI7IIgGG0EZgiE2FFsuhXbOgzkfAAAAAnDCBmQYJKoZIhvcNAQcGoIGLMIGIAgEAMIGCBgkqhkiG9w0BBwEwHgYJYIZIAWUDBAEuMBEEDCCdXbyl84z4/eHMMgIBEIBVptSBcKfw8E6zRA+FcMYruM7OtEpDPmLLgjjRr6xWCeT8D66cCQDrpO+nJOlozWdRk1sPCuoP8B+oaYCTcJdGgm0D+84fKnEqS+OrZaSGnomjG2fxFw==",
            "Version": 1,
            "LastModifiedDate": 1692970064.661,
            "ARN": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_HOST",
            "DataType": "text"
        },
(略)
```

#### taskdef.json.tpl
タスク定義を作成します
先ほど作成した環境変数のarnをsecretsのvalueFromに記載します
containerPathに関しましては今回は/code/tmpにします
Dockerfileの作成でも後ほど説明します

```json
[
    {
        "name" : "app",
        "image" : "${ecr_image_app}",
        "cpu" : 0,
        "portMappings" : [
            {
                "containerPort" : 8000,
                "hostPort" : 8000,
                "protocol" : "tcp",
                "appProtocol" : "http"
            }
        ],
        "essential" : true,
        "secrets": [
            {
                "name" : "POSTGRES_USER",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_USER"
            },
            {
                "name" : "DJANGO_SETTINGS_MODULE",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/DJANGO_SETTINGS_MODULE"
            },
            {
                "name" : "POSTGRES_HOST",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_HOST"
            },
            {
                "name" : "ALLOWED_HOSTS",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/ALLOWED_HOSTS"
            },
            {
                "name" : "SECRET_KEY",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/SECRET_KEY"
            },
            {
                "name" : "POSTGRES_PASSWORD",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_PASSWORD"
            },
            {
                "name" : "POSTGRES_PORT",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_PORT"
            },
            {
                "name" : "POSTGRES_NAME",
                "valueFrom" : "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/tf-pg/dev/POSTGRES_NAME"
            }
        ],
        "entryPoint" : [
            "/usr/local/bin/entrypoint.sh"
        ],
        "mountPoints" : [
        {
            "sourceVolume" : "tmp-data",
            "containerPath" : "/code/tmp"
        }
        ],
        "logConfiguration" : {
            "logDriver" : "awslogs",
            "options" : {
                "awslogs-group" : "${log_group_name_app}",
                "awslogs-region" : "ap-northeast-1",
                "awslogs-stream-prefix" : "app"
            }
        }
    },
    {
        "name" : "web",
        "image" : "${ecr_image_web}",
        "essential" : true,
        "portMappings" : [
        {
            "containerPort" : 80,
            "hostPort"      : 80,
            "protocol"      : "tcp"
        }
        ],
        "dependsOn" : [{
            "containerName" : "app",
            "condition"     : "START"
        }],
        "mountPoints" : [
        {
            "sourceVolume" : "tmp-data",
            "containerPath" : "/code/tmp"
        }
        ],
        "logConfiguration" : {
        "logDriver" : "awslogs",
        "options" : {
            "awslogs-group" : "${log_group_name_web}",
            "awslogs-region" : "ap-northeast-1",
            "awslogs-stream-prefix" : "web"
        }
        }
    }
]
```

### タスク定義
タスク定義の設定を行います
template_fileには先ほど作成したtaskdef.json.tpl、varsには環境変数化したログとECRのパスを指定します
また、後述するタスクロールとタスク実行ロールも指定します

```tf
data "template_file" "app_container_definitions" {
  template = file("./templates/ecs/taskdef.json.tpl")

  vars = {
    log_group_name_app = aws_cloudwatch_log_group.app.name
    log_group_name_web = aws_cloudwatch_log_group.web.name
    ecr_image_app = var.ecr_image_app
    ecr_image_web = var.ecr_image_web
    
  }
}


# タスク定義
resource "aws_ecs_task_definition" "app" {
  family                   = "${local.prefix}-app"
  requires_compatibilities = ["FARGATE"]
  network_mode             = "awsvpc"
  cpu                      = 256
  memory                   = 512
  execution_role_arn = "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-exec-role"
  task_role_arn =  "arn:aws:iam::XXXXXXXXXXXX:role/tf-pg-dev-task-role"
  container_definitions    = data.template_file.app_container_definitions.rendered

  volume {
    name = "tmp-data"
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-task-def" })
  )
}
```


### セキュリティグループ
ECSのセキュリティの設定を行います
HTTPのインバウンドアクセスに関しましては本来はALBからのアクセスのみ許可しないといけませんが未作成なので一旦全てのアクセスを許可します

|プロトコル/サービス|in/out|ポート番号|CIDR|
|--|--|--|--|
|HTTP|inbound|80|全てのアクセス|
|RDS(Postgres)|outbound|5432|プライベートサブネットAとCのCIDRブロック内|
|HTTP|outbound|80|全てのアクセス|
|HTTPS|outbound|443|全てのアクセス|

```tf
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


  # ECSからPostgresへのアウトバウンドアクセスを許可
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
    cidr_blocks = [
      "0.0.0.0/0"
    ]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-sg" })
  )
}
```

### ECSの設定について
ECSの設定のために以下を記載します
- クラスター
- タスク定義
- タスク数
- 起動タイプ(今回はFargate)
- バージョン

```tf
resource "aws_ecs_service" "app" {
  name            = "${local.prefix}-app"
  cluster         = aws_ecs_cluster.main.name
  task_definition = aws_ecs_task_definition.app.family
  # 今回は検証用のためタスクを1つだけ実行させる
  desired_count    = 1
  launch_type      = "FARGATE"
  platform_version = "1.4.0"

  network_configuration {
    subnets = [
      aws_subnet.private_a.id,
      aws_subnet.private_c.id,
    ]
    security_groups  = [aws_security_group.ecs_sg.id]
  }

  tags = merge(
    local.common_tags,
    tomap({ "Name" = "${local.prefix}-ecs-service" })
  )
```

## DjangoとNginxの設定
Terraformの設定を終えた後は
- ECRリポジトリの作成
- Dockerfileの作成、ビルド、プッシュ

を行います

### ECRリポジトリの作成
まずはDjangoのECRリポジトリを作成します
パスはvariables.tfにも記載してあるとおり、今回はtf-pg/djangoにします
![スクリーンショット 2023-07-17 8.11.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d64370e1-dd3f-3355-7524-8bb0862c8c9a.png)

今回はイメージスキャンを有効化します
リポジトリを作成ボタンを押したら作成完了です

![スクリーンショット 2023-07-17 8.11.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cac32456-5992-6958-3490-dc35e9ac0fbc.png)

Nginxも同様にECRリポジトリを作成します
今回はtf-pg/nginxにします
![スクリーンショット 2023-07-17 8.12.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/564a7ea3-e176-8189-fab2-7fb3dbcf2230.png)

### Dockerfileの作成
- Django
- Nginx

の2種類のDockerfileを作成します
#### Django
Terraformのタスク定義にも記載しましたがentrypoint.shを使ってコンテナを起動させます
また、コンテナのVolumeは`/code/tmp`に設定します
タスク定義に記載されている内容と統一しないとECSが起動しないので注意です

```Dockerfile:containers/django/Dockerfile
FROM --platform=linux/x86_64 python:3.14

# 公開するポートを明示的に定義
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV APP_ROOT=/code

WORKDIR ${APP_ROOT}

COPY application/ ${APP_ROOT}/
RUN pip install --upgrade pip && pip install poetry
RUN poetry install --without dev

# コンテナ起動時に必ず実行したいコマンドを定義した entrypoint.sh をコピー
COPY ./containers/django/entrypoint.prd.sh /usr/local/bin/entrypoint.prd.sh
# 実行権限を付与
RUN chmod +x /usr/local/bin/entrypoint.prd.sh
ENTRYPOINT ["entrypoint.prd.sh"]

VOLUME ["${APP_ROOT}/tmp"]
```

続いてentrypoint.shを作成します
通常のDjangoの開発では開発用のサーバーのrunserverを使いますが
今回は本番用の想定で有名なアプリケーションサーバであるGunicornを使って起動させます

```shell:containers/django/entrypoint.sh
#!/bin/sh
set -eu

mkdir -p ${APP_ROOT}/tmp/gunicorn_sockets

# Execute migration
poetry run python manage.py migrate

# Run Django application
poetry run gunicorn project.wsgi:application --bind=unix://${APP_ROOT}/tmp/gunicorn_socket

exec "$@"
```

#### Nginx
NginxのDockerfileとnginx.confファイルを作成します
その際に注意しておくべきことが2つあります
- プラットフォームの指定
    - M1MacでDockerfileをbuildする場合はArmのアーキテクチャになってしまいます
    - ECSのコンテナがx86_64で実行されるのでimageとECSのアーキテクチャが違うことによって実行されなくなってしまいます
    - そこで`--platform=linux/x86_64`と指定する必要があります
- フォアグラウンドモードで実行させる
    - Nginxはデフォルトでバックグラウンド(daemon)モードで実行されます
    - CloudWatch内でログを見れるようにするにはバックグラウンドモードをoffにする必要があります

```Dockerfile:containers/nginx/Dockerfile
FROM --platform=linux/x86_64 nginx:stable-alpine

RUN rm -f /etc/nginx/conf.d/*
COPY ./containers/nginx/nginx.prd.conf /etc/nginx/conf.d/

CMD /usr/sbin/nginx -g 'daemon off;' -c /etc/nginx/nginx.conf
```

Nginxの設定ファイルです
```containers/nginx/nginx.conf
upstream gunicorn {
    # Unixドメインソケットを通じてGunicornにリクエストを転送する
    # NginxがリバースプロキシとしてGunicornと連携
    server unix:///code/tmp/gunicorn_socket;
}

server {
    listen 80;
    # Nginxのバージョン情報を非表示にする
    # サーバ情報を隠すことでセキュリティ上のリスクを軽減させる
    server_tokens off;

    # ファイルサイズの変更、デフォルト値は1M
    client_max_body_size 5M;

    # HTTP レスポンスヘッダの Content_Type に付与する文字コード
    charset utf-8;

    # ログ設定
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # API 通信
    location /api {
        # X-Real-IPヘッダにクライアントのIPアドレスを設定
        proxy_set_header X-Real-IP $remote_addr;
        # X-Forwarded-Forヘッダにリクエストを送ったクライアントまたはプロキシのIPアドレスの履歴(リスト)を設定
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # Hostヘッダにクライアントのホスト名を設定
        proxy_set_header Host $http_host;
        # タイムアウトの設定(3600s)
        proxy_read_timeout 3600;
        # 上記のヘッダの情報がGunicornに転送される
        proxy_pass http://gunicorn;
    }

    # ヘルスチェック
    location /api/health {
        empty_gif;
        access_log off;
        break;
    }

    # HTTP 通信をタイムアウトせずに待つ秒数
    keepalive_timeout 60;
}
```

### DockerfileのbuildからECRへpushするまで
aws cliがDockerを使ってpushコマンドを実行できるよう認証トークンを以下のコマンドで取得します
```
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com
```

ログインに成功後、
- Dockerfileのbuild
- buildしたDockerfileのタグづけ
- タグづけしたDockerfileをECRへpush

を順番に行います
```
docker build -t tf-pg/django -f containers/django/Dockerfile .
docker tag tf-pg/django:latest XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/django:latest
docker push XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/django:latest
```

Nginxも同様に行います
```
docker build -t tf-pg/nginx -f containers/nginx/Dockerfile .
docker tag tf-pg/nginx:latest XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/django:latest
docker push XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/tf-pg/nginx:latest
```

以下のように作成したDockerfileをECRリポジトリにpushできたら成功です

![スクリーンショット 2023-07-17 8.23.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/01a3abe4-1aea-277d-a154-ddfe63b4b41b.png)

![スクリーンショット 2023-07-17 8.24.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/474707ca-bb8c-18d1-f2c8-e4007e391e1c.png)

## IAMRoleの作成と設定
ECSをデプロイする際は
- タスクロール
- タスク実行ロール

の2つが必要になります

### タスクロールとタスク実行ロールの違い
- タスクロール
    - コンテナの中のアプリケーションからAWSのサービスを利用する場合に設定するロール
    - 例えばコンテナ内にメール送信機能があればSES、画像をS3にアップロードする機能があればS3のポリシーをアタッチします
- タスク実行ロール
    - 　ECS(タスク)を実行させる場合に設定するロール
    - 　例えばECR内のイメージをpullしたりCloudWatchにログを保存したりパラメータストア内の環境変数を使うときのポリシーをアタッチします

今回はSESやS3を使うロジックを作成してないのでタスク実行ロールのみ作成し、必要な
タスク実行ロールに
- ECRとECSの実行
- CloudWatch
- パラメータストア

用のポリシーをアタッチします

### タスク実行ロール用のポリシー
今回はAWS側ですでに用意しているポリシーである
- AmazonECSTaskExecutionRolePolicy
- CloudWatchAgentServerPolicy

とパラメータストア用のカスタムポリシー(名前はSSMForECSPolicyとします)を作成します

```json:AmazonECSTaskExecutionRolePolicy
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ecr:GetAuthorizationToken",
                "ecr:BatchCheckLayerAvailability",
                "ecr:GetDownloadUrlForLayer",
                "ecr:BatchGetImage",
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "*"
        }
    ]
}
```

```json:CloudWatchAgentServerPolicy
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "cloudwatch:PutMetricData",
                "ec2:DescribeVolumes",
                "ec2:DescribeTags",
                "logs:PutLogEvents",
                "logs:DescribeLogStreams",
                "logs:DescribeLogGroups",
                "logs:CreateLogStream",
                "logs:CreateLogGroup"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter"
            ],
            "Resource": "arn:aws:ssm:*:*:parameter/AmazonCloudWatch-*"
        }
    ]
}
```

パラメータストアからSecureStringとして登録されている値も含めて取得するには
- ssm:GetParameters

以外に
- secretsmanager:GetSecretValue
- kms:Decrypt(Secure Stringを復号化する)

も設定する必要があります

```json:SSMForECSPolicy
{
    "Statement": [
        {
            "Action": [
                "ssm:GetParameters",
                "secretsmanager:GetSecretValue",
                "kms:Decrypt"
            ],
            "Effect": "Allow",
            "Resource": [
                "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/*"
            ]
        }
    ],
    "Version": "2012-10-17"
}
```

信頼されたエンティティもSSMForECSPolicyに忘れずにアタッチしましょう
```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "ecs-tasks.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
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

## 実際に作成してみよう!
フォーマットの修正、validateやplanによる確認が終わったら以下のコマンドで適用します
```
terraform apply -auto-approve
```

## 作成されたか確認してみよう！
以下のようにクラスターが作成され、クラスター内のタスクが実行されていたら成功です
![スクリーンショット 2023-08-26 12.36.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9b68b71d-d515-b859-f989-ed26f4aa5e63.png)

Gunicornの起動とMigrationが正常に実行されていることも確認できました

![スクリーンショット 2023-08-26 11.51.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2c093fc4-b094-8a93-89fc-9ad14b7a1422.png)
![スクリーンショット 2023-08-26 12.37.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c2ac8f95-c705-898a-f412-d660881c5bb5.png)

## リソースの削除

使用しないリソースは以下のコマンドで削除しましょう

```
terraform destroy
```

## まとめ
- ECS
- Dockerfile
- Django
- Nginx
- パラメータストア
- AWS CLI
- IAMロールの適切な権限の設定
- ネットワーク
- Terraform

とある程度の知識の深さを幅広く要求されるのでかなり難しい内容になっているかと思います
今後一人でインフラを構築するのであれば避けては通れない箇所なので難しそうであれば数日かけて読んでいただけると幸いです

## 参考
https://docs.aws.amazon.com/ecs/index.html

https://zenn.dev/sugay0519/articles/88f13ca589fcba

https://dev.classmethod.jp/articles/aws-cli-all-ssm-parameter-get/

https://docs.aws.amazon.com/ja_jp/aws-managed-policy/latest/reference/AmazonEC2ContainerServiceEventsRole.html

https://stackoverflow.com/questions/67361936/exec-user-process-caused-exec-format-error-in-aws-fargate-service

https://docs.aws.amazon.com/systems-manager/latest/APIReference/Welcome.html

https://docs.aws.amazon.com/ja_jp/AmazonECR/latest/userguide/ECR_on_ECS.html

https://docs.aws.amazon.com/ja_jp/AmazonECR/latest/userguide/repository-policy-examples.html
