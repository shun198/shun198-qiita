---
title: ECS Execを使って作成したECS Fargate内にアクセスする方法について徹底解説！
tags:
  - AWS
  - PostgreSQL
  - ECS
  - SSM
  - Fargate
private: false
updated_at: '2024-07-05T10:30:07+09:00'
id: 8856a40912d1bb74f2a6
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
ECS Execコマンドを使うことでコンテナ内にアクセスすることができますので解説します

## 前提
- ECSについてある程度知識がある
- AWS Fargateを使用している場合、プラットフォームバージョンが1.4.0 以上 (Linux)である
- DBはPostgresを使用

## CLI
aws cliがインストールされているか確認します
以下のようにバージョンが表示されていたら成功です

```
aws --version
aws-cli/2.11.2 Python/3.11.2 Darwin/23.2.0 exe/x86_64 prompt/off
```

まだインストールしていない場合は以下のリンクの手順に従ってインストールしてください

https://docs.aws.amazon.com/ja_jp/cli/latest/userguide/getting-started-install.html

次にsession-manager-pluginがインストールされているか確認します
以下のように表示されていたら成功です

```
session-manager-plugin

The Session Manager plugin was installed successfully. Use the AWS CLI to start a session.
```

まだインストールしていない場合は以下のリンクの手順に従ってインストールしてください

https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/session-manager-working-with-install-plugin.html

## SSM用のロール
> ECS Exec は、AWS Systems Manager (SSM) セッションマネージャーを使用して実行中のコンテナとの接続を確立し、AWS Identity and Access Management (IAM) ポリシーを使用して実行中のコンテナで実行中のコマンドへのアクセスを制御します

と記載されているとおり、ECSTaskRoleにSSMのポリシーが必要になります

```json:AmazonSSMManagedInstanceCore
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "ssm:DescribeAssociation",
                "ssm:GetDeployablePatchSnapshotForInstance",
                "ssm:GetDocument",
                "ssm:DescribeDocument",
                "ssm:GetManifest",
                "ssm:GetParameter",
                "ssm:GetParameters",
                "ssm:ListAssociations",
                "ssm:ListInstanceAssociations",
                "ssm:PutInventory",
                "ssm:PutComplianceItems",
                "ssm:PutConfigurePackageResult",
                "ssm:UpdateAssociationStatus",
                "ssm:UpdateInstanceAssociationStatus",
                "ssm:UpdateInstanceInformation"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ssmmessages:CreateControlChannel",
                "ssmmessages:CreateDataChannel",
                "ssmmessages:OpenControlChannel",
                "ssmmessages:OpenDataChannel"
            ],
            "Resource": "*"
        },
        {
            "Effect": "Allow",
            "Action": [
                "ec2messages:AcknowledgeMessage",
                "ec2messages:DeleteMessage",
                "ec2messages:FailMessage",
                "ec2messages:GetEndpoint",
                "ec2messages:GetMessages",
                "ec2messages:SendReply"
            ],
            "Resource": "*"
        }
    ]
}
```

##  ECS Execコマンド
以下のようにECS Execコマンドを実行します
```
aws ecs execute-command \
    --profile <プロファイル名> \
    --cluster <クラスター名> \
    --task <タスクID> \
    --container app \
    --interactive \
    --command "/bin/sh"
```

aws-vaultを使うときは以下のように実行します
```
aws-vault exec <プロファイル名> -- aws ecs execute-command \
    --cluster <クラスター名> \
    --task <タスクID> \
    --container app \
    --interactive \
    --command "/bin/sh"
```

以下のようにコンテナ内にアクセスできたら成功です

```
The Session Manager plugin was installed successfully. Use the AWS CLI to start a session.


Starting session with SessionId: ecs-execute-command-08e47e1083fc2dcd9
```

## The execute command failed due to an internal error. Try again later.
と表示されたとき

- ECS Fargateのプラットフォームバージョンが1.4より下の時
- AmazonSSMManagedInstanceCoreがECSTaskRoleに付与されていない時
    - 　付与した場合はもう一度ECSタスクを作り直す必要がある
- 　EnableExecuteCommandをTrueにしていない
    - 　CLIかCloudFormationで設定する必要がある

のいずれかなのでもう一度設定をよく確認しましょう


今回はDBにPostgresを使っているので以下のようにクライアントをインストールします
```
# apt-get update && apt-get install postgresql          
```

以下のようにバージョンが表示されたら成功です
```
# psql --version
psql (PostgreSQL) 15.5 (Debian 15.5-0+deb12u1)
```

Postgresのホスト名とユーザを指定し、パスワードを入力します
以下のようにRDSにアクセスできたら成功です

```
# psql -h<ホスト名> -Upostgres
Password for user postgres: 
psql (15.5 (Debian 15.5-0+deb12u1), server 15.2)
SSL connection (protocol: TLSv1.2, cipher: ECDHE-RSA-AES256-GCM-SHA384, compression: off)
Type "help" for help.

postgres=> 
```

## 参考
https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/userguide/ecs-exec.html

https://qiita.com/okubot55/items/b1fb07b2de08c354275b

https://qiita.com/michihito_t/items/d3e1ccee561b6574ddeb
