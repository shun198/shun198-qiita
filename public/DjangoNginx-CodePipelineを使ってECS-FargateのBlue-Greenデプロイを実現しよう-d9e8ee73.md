---
title: '[Django+Nginx] CodePipelineを使ってECS FargateのBlue/Greenデプロイを実現しよう！'
tags:
  - Django
  - nginx
  - AWS
  - ECS
  - CodePipeline
private: false
updated_at: '2024-01-31T14:49:01+09:00'
id: d9e8ee7372c3ccaddfeb
organization_url_name: null
slide: false
---
## 概要
AWSのコンソール上でCodePipelineを構築し、ECS FargateをBlue/Greenデプロイを使ってデプロイする方法について解説していきたいと思います

## 前提
- リージョンはap-northeast-1を使用
- VPC、ECS、RDS、ALBを作成済み
- ECRリポジトリ内にNginxとDjangoのDocker imageがあること
- Blue/Greenデプロイ用のターゲットグループとリスナーを設定済み
- DjangoのプロジェクトをECSへデプロイ済み
- 対象プロジェクトのGitHubリポジトリを作成済み


## ディレクトリ構成
```
tree
・
├── backend # バックエンドのソースコード
├── codebuild
│   ├── buildspec_django.yml
│   └── buildspec_nginx.yml
├── codedeploy
│   └── appspec.yml
├── containers
│   ├── django
│   │   ├── Dockerfile.prd
│   │   └── entrypoint.prd.sh
│   └── nginx
│       ├── Dockerfile.prd
│       └── nginx.prd.conf
└── ecs
    └── taskdef.json
```

## Blue/Greenデプロイとは？
同じアプリケーションの異なるバージョンを実行している同一の環境間でトラフィックを移行することでデプロイする手法です
Blue/Greenデプロイをする際は新しい環境(Green)を古い環境(Blue)を一緒に起動させ、トラフィックを新しい環境(Green)に再ルーティングします
Blue/Greenデプロイをすることで問題の検出をロールバックする前に、新しいバージョンを監視およびテストできることに加え、アプリケーションの更新中のダウンタイムを最小限に抑えた上でダウンタイムとロールバックのリスクを軽減できます

https://docs.aws.amazon.com/ja_jp/whitepapers/latest/introduction-devops-aws/blue-green-deployments.html


## CodePipelineの構築
CodePipelineではBlue/Greenデプロイを使用してコンテナをデプロイするパイプラインを構築できるのでその方法について今から解説します

### パイプラインの設定
今回はパイプラインのバージョンをV1にします
また、CodePipelineを新規で作成するのでサービスロールも新規で作成します

![スクリーンショット 2024-01-25 9.43.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a42a8992-849f-8ca0-2648-a321e1cd7b97.png)

### ソースステージを追加
今回はGitHubのソースが対象ブランチにpushされたことをトリガーにCodePipelineを実行するよう設定します
ソースプロバイダはGitHub(バージョン2)を選択します

![スクリーンショット 2024-01-25 9.44.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3dcd6c0f-99cc-55b6-2f82-b1e251c20a00.png)

今回はmainブランチへpushしたらCodePipelineを実行するよう設定します
![スクリーンショット 2024-01-25 9.44.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/87e94097-67a2-bd3d-99bc-a69ac076ecc6.png)

### ビルドステージを追加
Dockerfileをビルドするためのステージを作成します
今回はAWS CodeBuildを選択します
新規でCodePipelineを作成しているのでAWS CodeBuildも同様に新規で作成するのでプロジェクトを作成する、を選択します

![スクリーンショット 2024-01-25 9.45.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4da0f96b-084b-f8dc-4009-7db35918e66e.png)

#### CodeBuildの作成
プロジェクト名を記載します
画像の通りの項目を選択します

![スクリーンショット 2024-01-25 9.47.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/734fd19a-8ffa-366f-979e-40f5141a642a.png)

環境の設定を行います
イメージに関してですがバージョンが古すぎると比較的新しいPythonのバージョンをサポートしてない時があるので今回はstandard:5.0を選択します
イメージのバージョンも常に最新のイメージを使用するようにします

![スクリーンショット 2024-01-25 9.48.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6f486473-56a1-d91d-2e7f-f2d6043167e1.png)

新しいロールを作成します
![スクリーンショット 2024-01-25 9.49.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/088536de-17f2-25ef-3e70-6e59001d7e37.png)

追加設定の箇所で環境変数の設定を行います

![スクリーンショット 2024-01-25 9.54.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/47004e6b-c7b3-cc96-7bee-f8dd797bc760.png)

必要になる環境変数は以下の通りです

|環境変数|値|
|--|--|
|DOCKERHUB_USER|自身のDockerHubのユーザ名|
|DOCKERHUB_TOKEN|自身のDockerHubのトークン|
|DJANGO_DOCKERFILE_PATH|リポジトリ内のDjangoのDockerfileのパス|
|NGINX_DOCKERFILE_PATH|リポジトリ内のNginxのDockerfileのパス|
|ECR_DJANGO_REPOSITORY_URI|DjangoのDockerfileを格納しているECRリポジトリのパス|
|ECR_NGINX_REPOSITORY_URI|NginxのDockerfileを格納しているECRリポジトリのパス|
|AWS_DEFAULT_REGION|リージョン名(ap-northeast-1)|
|AWS_DEFAULT_ACCOUNT|AWSのアカウントID|

DockerHubのアクセストークンの作成方法は以下の公式ドキュメントを参照してください

https://docs.docker.com/security/for-developers/access-tokens/

#### Buildspec
Buildspecを作成します
今回は複数のbuildspecファイルを使ってビルドするのでビルドコマンドの挿入を選択し、エディタに切り替えを選択します

![スクリーンショット 2024-01-25 10.04.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/701d345e-e6f0-b91a-1cfd-387870d796c2.png)

![スクリーンショット 2024-01-25 10.06.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a1b728aa-0331-faf7-adbd-0a6ab36c0575.png)

後ほどCodeDeployの箇所で解説しますがIdentifierを元に入力アーティファクトを選択します
以下のようにbuildspecにDjango用とNginx用のymlファイルのパスを記載します

```yml
version: 0.2
batch:
  build-list:
    - identifier: BuildBackEndDjangoArtifact
      buildspec: codebuild/buildspec_django.yml
    - identifier: BuildBackEndNginxArtifact
      buildspec: codebuild/buildspec_nginx.yml
```

#### バッチ設定
今回は複数のDockerfileを使って同時にBuildするのでバッチ設定を行います
新規でバッチサービスロールを作成します

![スクリーンショット 2024-01-25 10.21.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/722c70c1-d1a1-8c00-bd0c-6058e738a2be.png)

#### ログ
デバッグの際に必要なのでCloudWatchでログが見れるよう設定します

![スクリーンショット 2024-01-25 10.21.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c4aacafa-767d-4d98-93b1-013a5659b5e9.png)

バッチビルドを選択します

![スクリーンショット 2024-01-25 10.26.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/39d3b593-51de-fa45-4da6-54eecb9a113f.png)

### デプロイステージの追加
デプロイプロバイダーをAmazon ECS(ブルー/グリーン)に設定します
新規でCodePipelineを作成しているのでAWS CodeDeployも同様に新規で作成します

#### CodeDeploy
CodeDeployのアプリケーションを作成します

![スクリーンショット 2024-01-25 10.27.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8723e7e1-923a-4d24-d07b-3005085b3999.png)

CodeDeployのアプリケーションを作成後、デプロイグループを作成します

![スクリーンショット 2024-01-27 10.38.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b7b3b566-23c5-3f68-f170-c618d7368e43.png)

デプロイグループ名とサービスロールを設定します
![スクリーンショット 2024-01-27 10.41.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/01484285-62c4-03d2-cac5-f9c92a67e903.png)

CodeDeploy用のロールを作成します
今回私はCodeDeployRoleという名前で作成しています

![スクリーンショット 2024-01-30 9.24.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cda0f4df-4e43-7bfb-a23e-6e60633cd97b.png)

AWSCodeDeployRoleForECSのポリシーをアタッチします
詳細は以下のとおりです

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": [
                "ecs:DescribeServices",
                "ecs:CreateTaskSet",
                "ecs:UpdateServicePrimaryTaskSet",
                "ecs:DeleteTaskSet",
                "elasticloadbalancing:DescribeTargetGroups",
                "elasticloadbalancing:DescribeListeners",
                "elasticloadbalancing:ModifyListener",
                "elasticloadbalancing:DescribeRules",
                "elasticloadbalancing:ModifyRule",
                "lambda:InvokeFunction",
                "cloudwatch:DescribeAlarms",
                "sns:Publish",
                "s3:GetObject",
                "s3:GetObjectVersion"
            ],
            "Resource": "*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "iam:PassRole"
            ],
            "Effect": "Allow",
            "Resource": "*",
            "Condition": {
                "StringLike": {
                    "iam:PassedToService": [
                        "ecs-tasks.amazonaws.com"
                    ]
                }
            }
        }
    ]
}
```

環境設定ではクラスターとサービス名を選択します
LoadBalanceの設定では
- ロードバランサー本体
- 本稼働用とテスト用のリスナーポート
- ターゲットグループ

の選択を行います

![スクリーンショット 2024-01-30 9.26.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0624ef77-f8d1-807a-7c49-a727fdc334a5.png)

デプロイ設定については今回は以下の通りにします
設定が終わったらデプロイグループを作成、ボタンを押します

![スクリーンショット 2024-01-30 9.26.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/19334c4a-6da5-47e9-840d-dbb0c540f121.png)

CodeDeployの設定画面に戻ります
taskdef.jsonとappspec.ymlをまだ作成していないので今はBuildArtifactを選択した状態にします
また、CodePipelineをコンソールで作成するときは複数アーティファクトを指定できないので一旦そのままにします

![スクリーンショット 2024-01-30 9.40.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d9a14b1b-24cd-3b55-8f9f-7295ad221e61.png)

- Source
- Build
- Deploy

ステージの設定が終わったらパイプラインを作成する、ボタンを押してCodePipelineを構築します

![deploy-stage.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a5e605e3-d0c5-f4b6-b5d6-f7178c2f8ccb.png)

## ファイルの作成
- DjangoとNginxのbuildspec.ymlファイル
- appspec.yml
- taskdef.json(タスク定義ファイル)

の3つを作成します

### buildspecの作成
今回はcodebuildフォルダ配下にymlファイルを作成します
buildspecのphaseは
- pre_build
- build
- post_build

の3種類に分類されるので1つずつ説明します

#### pre_build
Dockerfileをbuildする前にECRにログインするフェーズです
ログインする際はCodeBuildで設定した
- DOCKERHUB_USER
- DOCKERHUB_TOKEN

の環境変数を使ってECRにログインします
また、ビルドの解決済みソースバージョンの識別子の前から7文字をIMAGE_TAGの変数に代入します

![image_tag.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/54561ad3-c170-b692-9789-7662c7c57d72.png)

#### build
DJANGO_DOCKERFILE_PATH内にあるDockerfileをbuildし、タグ付けします

#### post_build
buildが完了したDockerfileをECRへpushし、imageDetail.jsonに書き込み処理を行います

```codebuild/buildspec_django.yml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - echo Logging in to Docker Hub...
      - echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USER --password-stdin
      - IMAGE_TAG=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - cd $CODEBUILD_SRC_DIR
      - docker build -f $DJANGO_DOCKERFILE_PATH -t $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG .
      - docker tag $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG
      - echo Writing imageDetail.json...
      - printf '{"Version":"1.0","ImageURI":"%s"}' $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG > imageDetail.json
artifacts:
  files:
    - imageDetail.json
```

Nginx用のbuildspecファイルも同様に作成します

```codebuild/buildspec_nginx.yml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - echo Logging in to Docker Hub...
      - echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USER --password-stdin
      - IMAGE_TAG=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - cd $CODEBUILD_SRC_DIR
      - docker build -f $NGINX_DOCKERFILE_PATH -t $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG .
      - docker tag $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG
      - echo Writing imageDetail.json...
      - printf '{"Version":"1.0","ImageURI":"%s"}' $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG > imageDetail.json
artifacts:
  files:
    - imageDetail.json

```

### appspecの作成
今回はcodedeployフォルダ配下にymlファイルを作成します
TaskDefinitionの箇所に<TASK_DEFINITION>を設定します
CodePipeline実行時にCodeDeployで設定したECSタスクのパスが自動的に代入されます

```codedeploy/appspec.yml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "<TASK_DEFINITION>"
        LoadBalancerInfo:
          ContainerName: "web"
          ContainerPort: "80"
```

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/tutorials-ecs-ecr-codedeploy.html

### taskdefの作成
今回はecsフォルダ配下にjsonファイルを作成します
ECSのタスク定義に以下の変数が入るようにします
- NGINX_IMAGE_NAME
- DJANGO_IMAGE_NAME

appspec.yml同様、CodeDeployの設定に追加します

```ecs/taskdef.json
{
    "taskDefinitionArn": "arn:aws:ecs:ap-northeast-1:XXXXXXXXXXXX:task-definition/my-project-dev-back-taskdef:18",
    "containerDefinitions": [
        {
            "name": "web",
            "image": "<NGINX_IMAGE_NAME>",
            "cpu": 0,
            "links": [],
            "portMappings": [
                {
                    "containerPort": 80,
                    "hostPort": 80,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "entryPoint": [],
            "command": [],
            "environment": [],
            "environmentFiles": [],
            "mountPoints": [
                {
                    "sourceVolume": "tmp-data",
                    "containerPath": "/code/tmp"
                }
            ],
            "volumesFrom": [],
            "secrets": [],
            "dependsOn": [
                {
                    "containerName": "app",
                    "condition": "START"
                }
            ],
            "dnsServers": [],
            "dnsSearchDomains": [],
            "extraHosts": [],
            "dockerSecurityOptions": [],
            "dockerLabels": {},
            "ulimits": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/my-project/dev/back/nginx",
                    "awslogs-region": "ap-northeast-1",
                    "awslogs-stream-prefix": "my-project"
                },
                "secretOptions": []
            },
            "systemControls": []
        },
        {
            "name": "app",
            "image": "<DJANGO_IMAGE_NAME>",
            "cpu": 0,
            "links": [],
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "entryPoint": [
                "/usr/local/bin/entrypoint.prd.sh"
            ],
            "command": [],
            "environment": [],
            "environmentFiles": [],
            "mountPoints": [
                {
                    "sourceVolume": "tmp-data",
                    "containerPath": "/code/tmp"
                }
            ],
            "volumesFrom": [],
            "secrets": [
                {
                    "name": "POSTGRES_NAME",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_NAME"
                },
                {
                    "name": "POSTGRES_USER",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_USER"
                },
                {
                    "name": "POSTGRES_PASSWORD",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_PASSWORD"
                },
                {
                    "name": "POSTGRES_PORT",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_PORT"
                },
                {
                    "name": "POSTGRES_HOST",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_HOST"
                },
                {
                    "name": "SECRET_KEY",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/SECRET_KEY"
                },
                {
                    "name": "ALLOWED_HOSTS",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/ALLOWED_HOSTS"
                },
                {
                    "name": "AWS_DEFAULT_REGION_NAME",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/AWS_DEFAULT_REGION_NAME"
                },
                {
                    "name": "TRUSTED_ORIGINS",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/TRUSTED_ORIGINS"
                },
                {
                    "name": "DJANGO_SETTINGS_MODULE",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/DJANGO_SETTINGS_MODULE"
                }
            ],
            "dnsServers": [],
            "dnsSearchDomains": [],
            "extraHosts": [],
            "dockerSecurityOptions": [],
            "dockerLabels": {},
            "ulimits": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/my-project/dev/back/django",
                    "awslogs-region": "ap-northeast-1",
                    "awslogs-stream-prefix": "my-project"
                },
                "secretOptions": []
            },
            "systemControls": []
        }
    ],
    "family": "my-project-dev-back-taskdef",
    "taskRoleArn": "arn:aws:iam::XXXXXXXXXXXX:role/service-role/ECSTaskRole-my-project-dev",
    "executionRoleArn": "arn:aws:iam::XXXXXXXXXXXX:role/service-role/ECSTaskExecutionRole-my-project-dev",
    "networkMode": "awsvpc",
    "revision": 18,
    "volumes": [
        {
            "name": "tmp-data",
            "host": {}
        }
    ],
    "status": "ACTIVE",
    "requiresAttributes": [
        {
            "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
        },
        {
            "name": "ecs.capability.execution-role-awslogs"
        },
        {
            "name": "com.amazonaws.ecs.capability.ecr-auth"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.17"
        },
        {
            "name": "com.amazonaws.ecs.capability.task-iam-role"
        },
        {
            "name": "ecs.capability.container-ordering"
        },
        {
            "name": "ecs.capability.execution-role-ecr-pull"
        },
        {
            "name": "ecs.capability.secrets.ssm.environment-variables"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
        },
        {
            "name": "ecs.capability.task-eni"
        }
    ],
    "placementConstraints": [],
    "compatibilities": [
        "EC2",
        "FARGATE"
    ],
    "requiresCompatibilities": [
        "FARGATE"
    ],
    "cpu": "512",
    "memory": "1024",
    "registeredAt": "2024-01-05T02:48:18.158Z",
    "registeredBy": "arn:aws:sts::XXXXXXXXXXXX:assumed-role/XXXXXXXXXXXX/XXXXXXXXXXXX",
    "tags": [
        {
            "key": "ProjectName",
            "value": "my-project"
        },
        {
            "key": "Environment",
            "value": "dev"
        }
    ]
}

```

## CodePipeline内のビルドとデプロイステージの修正
作成したCodePipelineへアクセスします
CodePipelineのステージを修正する際は編集する、を押します

![スクリーンショット 2024-01-30 11.45.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5b06c14d-2f0d-4cdc-fcf0-d942660e8115.png)

まずはビルドステージを修正します
![スクリーンショット 2024-01-30 11.47.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a10cea2-5791-96a9-ae9a-99915163ea93.png)

出力アーティファクトに
- BuildBackEndDjangoArtifact
- BuildBackEndNginxArtifact

を指定します
出力アーティファクト名はidentifierと揃える必要があります

```yml
version: 0.2
batch:
  build-list:
    - identifier: BuildBackEndDjangoArtifact
      buildspec: codebuild/buildspec_django.yml
    - identifier: BuildBackEndNginxArtifact
      buildspec: codebuild/buildspec_nginx.yml
```

![スクリーンショット 2024-01-30 14.44.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d27a9f2b-460e-b802-1a45-698a56fe9282.png)

次にデプロイステージを修正します
![スクリーンショット 2024-01-30 11.46.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/56bd3a04-3751-0cb9-3c20-3c34a6bbb5b1.png)

入力アーティファクトはSourceArtifactに加えて
- BuildBackEndDjangoArtifact
- BuildBackEndNginxArtifact

を追加する必要があります

![スクリーンショット 2024-01-30 14.48.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/10628363-5218-6bf1-6e19-7ae14b0bc603.png)

SourceArtifactを選択した上で
- タスク定義
- appspec

ファイルのパスを記載します
また、入力アーティファクトとタスク定義のプレースホルダー文字をDjangoとNginx別でそれぞれ記入したら完了です

![スクリーンショット 2024-01-30 14.49.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dc3c079c-176b-46d4-c809-5478acd324d5.png)

## 実際にデプロイしてみよう！
変更内容をmainブランチにpushするとCodePipelineが実行されます
以下のようにパイプラインが実行できていれば成功です

![スクリーンショット 2024-01-27 10.45.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/664a7d6e-e009-4d9b-eb86-74d3f5e2ef27.png)

![スクリーンショット 2024-01-27 10.46.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3af892e7-8a70-de85-5e1c-3fe2d69e3e56.png)

![スクリーンショット 2024-01-27 10.46.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4ed4d368-453f-d14f-9613-223dc7b934fb.png)


## 参考
https://docs.aws.amazon.com/ja_jp/codebuild/latest/userguide/welcome.html

https://docs.aws.amazon.com/ja_jp/codedeploy/latest/userguide/welcome.html

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/welcome.html

https://dev.classmethod.jp/articles/aws-codebuild-now-supports-parallel-and-coordinated-executions-of-a-build-project/

https://qiita.com/Ichi0124/items/880a509852e0121df1d0

https://qiita.com/ramunauna/items/114ffb3b5532cdb7fd2d

https://gb-j.com/column/codebuild/

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/file-reference.html#file-reference-ecs-bluegreen

https://docs.aws.amazon.com/ja_jp/codebuild/latest/userguide/build-env-ref-env-vars.html
