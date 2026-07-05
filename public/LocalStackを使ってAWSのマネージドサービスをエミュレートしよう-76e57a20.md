---
title: LocalStackを使ってAWSのマネージドサービスをエミュレートしよう！
tags:
  - AWS
  - aws-cli
  - docker-compose
  - LocalStack
private: false
updated_at: '2023-03-11T17:00:41+09:00'
id: 76e57a20e83660cc4a97
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## LocalStackとは
AWSのマネージドサービスをローカル上で実行できるツールです
LocalStackを使うことでAWSのマネージドサービスを使う前に開発・テストができるため、AWSのコストを節約することができます

## LocalStack用のコンテナの準備
LocalStackを使う際は基本的にDockerfileもしくはdocker-compose.ymlでLocalStack用のコンテナを作成し、開発・テストを行います
今回は手軽に使用できるdocker-compose.ymlを使用します

### ファイル構成
```
tree
.
├── .env
└── docker-compose.yml
```

LocalStackを使用するには
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

の環境変数が必要なので.envファイルを作成し、
environmentに上記の環境変数を指定します
ローカルで使うものなので今回はダミー値としてどちらも.env内に`localstack`を指定します

```.env
AWS_ACCESS_KEY_ID=localstack
AWS_SECRET_ACCESS_KEY=localstack
```

```docker-compose.yml
version: "3.9"

services:
  localstack:
    image: localstack/localstack
    container_name: localstack
    ports:
      - "4566:4566"
    environment:
      - AWS_ACCESS_KEY_ID
      - AWS_SECRET_ACCESS_KEY
```

### コンテナを立ち上げよう
LocalStackを使用するのに必要な設定をした後に以下のコマンドを実行します
```
docker-compose up -d
```

以下のようにコンテナが起動したら成功です
```
docker ps -a
CONTAINER ID   IMAGE                    COMMAND                  CREATED             STATUS                    PORTS                                             NAMES
ed41ff90711d   localstack/localstack    "docker-entrypoint.sh"   About an hour ago   Up 48 minutes (healthy)   4510-4559/tcp, 5678/tcp, 0.0.0.0:4566->4566/tcp   localstack
```

### 使用できるサービスの一覧
また、`http://127.0.0.1:4566/health`にアクセスすると使用できるサービスの一覧が表示されます

```json
{
    "features": {
        "initScripts": "initialized"
    },
    "services": {
        "acm": "available",
        "apigateway": "available",
        "cloudformation": "available",
        "cloudwatch": "available",
        "config": "available",
        "dynamodb": "available",
        "dynamodbstreams": "available",
        "ec2": "available",
        "es": "available",
        "events": "available",
        "firehose": "available",
        "iam": "available",
        "kinesis": "available",
        "kms": "available",
        "lambda": "available",
        "logs": "available",
        "opensearch": "available",
        "redshift": "available",
        "resource-groups": "available",
        "resourcegroupstaggingapi": "available",
        "route53": "available",
        "route53resolver": "available",
        "s3": "running",
        "s3control": "available",
        "secretsmanager": "available",
        "ses": "available",
        "sns": "available",
        "sqs": "available",
        "ssm": "available",
        "stepfunctions": "available",
        "sts": "available",
        "support": "available",
        "swf": "available",
        "transcribe": "available"
    },
    "version": "1.4.1.dev"
}
```

## 実際に使用してみよう
今回はLocalStackを使ってS3バケットを作成する簡単なコマンドを実行してみましょう！
S3バケットを作成する際は
```
aws s3 mb
```
コマンドを使います
LocalStackのコンテナ内に作成するのでendpointを以下のように指定します
ホスト名とポートはdocker-composeに記載したサービス名とポート番号になります
```
http://localstack:4566
```

sample-bucketという名前のS3バケットを作成します
```
docker-compose exec localstack aws s3 mb s3://sample-bucket --endpoint-url=http://localstack:4566
make_bucket: sample-bucket
```

その後、以下のコマンドで作成したS3バケットの一覧が表示されたら成功です
```
docker-compose exec localstack aws s3 ls --endpoint-url=http://localstack:4566
2023-03-11 07:01:45 sample-bucket
```

## まとめ
個人でAWSの検証をする際は多少の出費を考慮しないといけなくて気が引けていたのですがLocalStackを有効活用すれば気軽にできるので嬉しいです
今後はboto3やフレームワークと一緒に使った記事を執筆していきたいと思います

## 参考
https://docs.localstack.cloud/overview/

https://aws.taf-jp.com/blog/78562

https://awscli.amazonaws.com/v2/documentation/api/latest/reference/s3/index.html
