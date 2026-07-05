---
title: '[Django] LocalStack+SQS+S3+Lambdaを使ったCSVファイルを非同期でimportしよう！'
tags:
  - S3
  - lambda
  - sqs
  - django-rest-framework
  - LocalStack
private: false
updated_at: '2024-08-12T15:49:15+09:00'
id: 83e766724ea5c9731cad
organization_url_name: null
slide: false
---
## 概要
SQSとS3とLambdaを使った非同期処理をローカル上でLocalStackを用いて再現する方法について解説します

## 前提
- Djangoのアプリケーションを作成済み
- SQSとLambdaとS3に関する基本的な知識を有している

## 今回実装する非同期処理の仕組み
①APIを使ってS3にCSVをアップロードします
②アップロードする際にSQSを使ってアップロード履歴のIDを送ります
③SQSのメッセージ送信をトリガーにLambdaを実行し、Lambda内でS3内のCSVのデータをDBにInsertするAPIを実行させます
④SQSのメッセージ内のIDを利用して該当するアップロード履歴テープル内のFileFieldを参照してアップロード処理を実行します

CSVの処理状況についてはアップロード履歴テーブル内にステータスのカラムを作成して履歴一覧から進捗状況を把握できるようにします
処理の流れは下記の画像の通りです

![lambda-s3-sqs.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e707c101-fd62-a8d8-636d-ef939874d626.png)

DjangoのCeleryを使用すれば同様のことができますが
- CeleryとCelery Beat用のECSタスクを常時起動させ続ける必要があるためコストを節約したい
- 1週間に1回あるか、ないか程度の頻度しか使用しない

などのニーズを満たすのであれば今回の非同期処理の採用を検討してもいいのではないかと考えています

## ディレクトリ構成
```
├── backend
│   ├── .vscode
│   │   └── launch.json
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── fixture.json
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── urls.py
│   │   ├── utils
│   │   │   ├── fields.py
│   │   │   ├── sqs.py
│   │   │   └── storages.py
│   │   └── views.py
│   ├── manage.py
│   ├── poetry.lock
│   ├── project
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── upload
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── pyproject.toml
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── localstack
│   │   ├── entrypoint.sh
│   │   ├── function.py
│   │   └── role.json
└── docker-compose.yml
```

## LocalStackの設定
ローカル上で非同期処理を再現するためのLocalStackの設定を行います

### docker-compose.yml
LocalStackではready.d配下にエントリーポイントとなるシェルスクリプトなどを配置すると起動時に実行される仕様なので下記のようにvolumeを定義します

```
./containers/localstack/:/etc/localstack/init/ready.d/
```

詳細は以下の通りです

> LocalStack has four well-known lifecycle phases or stages:
BOOT: the container is running but the LocalStack runtime has not been started
START: the Python process is running and the LocalStack runtime is starting
READY: LocalStack is ready to serve requests
SHUTDOWN: LocalStack is shutting down
You can hook into each of these lifecycle phases using custom shell or Python scripts. Each lifecycle phase has its own directory in /etc/localstack/init. You can mount individual files, stage directories, or the entire init directory from your host into the container.

```
/etc
└── localstack
    └── init
        ├── boot.d           <-- executed in the container before localstack starts
        ├── ready.d          <-- executed when localstack becomes ready
        ├── shutdown.d       <-- executed when localstack shuts down
        └── start.d          <-- executed when localstack starts up
```

```docker-compose.yml
version: '3.9'

services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_NAME
      - POSTGRES_USER
      - POSTGRES_PASSWORD
    ports:
      - '5432:5432' # デバッグ用
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./backend:/code
      - ./static:/static
    ports:
      - '8000:8000'
      # デバッグ用ポート
      - '8080:8080'
    command: sh -c "/usr/local/bin/entrypoint.sh"
    stdin_open: true
    tty: true
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
  nginx:
    container_name: web
    build:
      context: .
      dockerfile: containers/nginx/Dockerfile
    volumes:
      - ./static:/static
    ports:
      - 80:80
    depends_on:
      - app
  localstack:
    container_name: localstack
    image: localstack/localstack:3.0.2
    ports:
      - 4566:4566
    environment:
      - DOCKER_HOST=unix:///var/run/docker.sock
      - AWS_DEFAULT_REGION=ap-northeast-1
      - LAMBDA_TOKEN=test
      - AWS_ACCESS_KEY_ID=localstack
      - AWS_SECRET_ACCESS_KEY=localstack
    volumes:
      - /var/run/docker.sock:/var/run/docker.sock
      - ./containers/localstack/:/etc/localstack/init/ready.d/
volumes:
  db_data:
  static:
  localstack_data:
  localstack_bin:
```

### .env
必要な環境変数を定義します
ALLOWED_HOSTSにappを入れないとLocalStack内でAPIを実行できないので注意しましょう

```.env
POSTGRES_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
ALLOWED_HOSTS=localhost 127.0.0.1 [::1] back web app"
AWS_DEFAULT_REGION_NAME=ap-northeast-1
AWS_SQS_URL=http://sqs.ap-northeast-1.localhost.localstack.cloud:4566/000000000000/queue01.fifo
AWS_SQS_ENDPOINT=http://localstack:4566
AWS_SQS_MESSAGE_GROUP=group
LAMBDA_TOKEN=test
```

### entrypoint.sh
エントリーポイントを記載します
- Lambda用のロールの作成
- LambdaがSQSを実行する用のポリシーの作成
- Lambdaの作成
- SQSの作成
- LambdaとSQSの紐付け(イベントソースマッピング)


を行ってます

下記のコマンドで実行権限を付与しないと起動しないので注意しましょう
```
chmod +x containers/localstack/entrypoint.sh
```

```entrypoint.sh
#!/bin/bash

set -eu

# 設定
LOCALSTACK_HOME=/etc/localstack/init/ready.d
AWSLOCAL_ACCOUNT_ID=000000000000
ROLE_NAME=role01
FUNC_NAME=func01
QUEUE_NAME=queue01.fifo

# 実行ロールを作成
awslocal iam create-role \
--role-name ${ROLE_NAME} \
--assume-role-policy-document file://${LOCALSTACK_HOME}/role.json

awslocal iam attach-role-policy \
--policy-arn arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole \
--role-name ${ROLE_NAME}

# Lambda 関数を作成
cp -p ${LOCALSTACK_HOME}/function.py .
chmod 755 function.py
zip function.zip function.py
awslocal lambda create-function \
    --function-name ${FUNC_NAME} \
    --zip-file fileb://function.zip \
    --handler function.lambda_handler \
    --runtime python3.12 \
    --timeout 900 \
    --memory-size 1024 \
    --role arn:aws:iam::${AWSLOCAL_ACCOUNT_ID}:role/${ROLE_NAME} \
    --environment "Variables={LAMBDA_TOKEN=${LAMBDA_TOKEN}}"

# AmazonSQSキューを作成
awslocal sqs create-queue \
    --queue-name ${QUEUE_NAME} \
    --attributes FifoQueue=true,ContentBasedDeduplication=true

# イベントソースを設定
awslocal lambda create-event-source-mapping \
--function-name ${FUNC_NAME}  \
--batch-size 1 \
--event-source-arn arn:aws:sqs:${AWS_DEFAULT_REGION}:${AWSLOCAL_ACCOUNT_ID}:${QUEUE_NAME}
```

### role.json
Lambdaがentrypoint.shで作成したIAMロールを使って実行できるよう設定します

```role.json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

### function.py
Lambda内に処理を記載します
API作成時に詳細に説明しますがCSVをアップロードするAPIを実行するとSQSからのメッセージをトリガーに下記のLocalStack内のLambdaの処理が自動的に実行されます
実行されるのは冒頭で説明したアップロード履歴用のIDをもとにS3内のCSVファイルをDBにinsertする処理です

```function.py
import json
import os
from pprint import pprint
from urllib import error, request


def lambda_handler(event, context):
    try:
        id = event["Records"][0]["body"]
        lambda_token = os.environ.get("LAMBDA_TOKEN")
        print(id)
        url = f"http://app:8000/api/customers/register_csv"
        data = {"token": lambda_token, "id": id}
        headers = {
            "Content-Type": "application/json",
        }
        req = request.Request(url, json.dumps(data).encode(), headers)
        try:
            with request.urlopen(req) as res:
                body = json.loads(res.read())
                headers = res.getheaders()
                status = res.getcode()
                pprint(headers)
                pprint(status)
                pprint(body)
        except error.HTTPError as e:
            pprint(e)
    except Exception as e:
        print(str(e))
```

### LocalStackの起動
以下のようにLocalStackを起動できれば成功です
```
2024-08-12 10:54:01 LocalStack version: 3.0.2
2024-08-12 10:54:01 LocalStack Docker container id: 1f01e94f935e
2024-08-12 10:54:01 LocalStack build date: 2023-11-29
2024-08-12 10:54:01 LocalStack build git hash: 60518e11
2024-08-12 10:54:01 
2024-08-12 10:54:02 2024-08-12T01:54:02.803  INFO --- [-functhread4] hypercorn.error            : Running on https://0.0.0.0:4566 (CTRL + C to quit)
2024-08-12 10:54:02 2024-08-12T01:54:02.803  INFO --- [-functhread4] hypercorn.error            : Running on https://0.0.0.0:4566 (CTRL + C to quit)
2024-08-12 10:54:03 Ready.
2024-08-12 10:54:03 2024-08-12T01:54:03.602  INFO --- [   asgi_gw_0] localstack.request.aws     : AWS iam.CreateRole => 200
2024-08-12 10:54:03 {
2024-08-12 10:54:03     "Role": {
2024-08-12 10:54:03         "Path": "/",
2024-08-12 10:54:03         "RoleName": "role01",
2024-08-12 10:54:03         "RoleId": "AROAQAAAAAAAONF5D6ACL",
2024-08-12 10:54:03         "Arn": "arn:aws:iam::000000000000:role/role01",
2024-08-12 10:54:03         "CreateDate": "2024-08-12T01:54:03.594000Z",
2024-08-12 10:54:03         "AssumeRolePolicyDocument": {
2024-08-12 10:54:03             "Version": "2012-10-17",
2024-08-12 10:54:03             "Statement": [
2024-08-12 10:54:03                 {
2024-08-12 10:54:03                     "Effect": "Allow",
2024-08-12 10:54:03                     "Principal": {
2024-08-12 10:54:03                         "Service": "lambda.amazonaws.com"
2024-08-12 10:54:03                     },
2024-08-12 10:54:03                     "Action": "sts:AssumeRole"
2024-08-12 10:54:03                 }
2024-08-12 10:54:03             ]
2024-08-12 10:54:03         }
2024-08-12 10:54:03     }
2024-08-12 10:54:03 }
2024-08-12 10:54:04 2024-08-12T01:54:04.075  INFO --- [   asgi_gw_0] localstack.request.aws     : AWS iam.AttachRolePolicy => 200
2024-08-12 10:54:04 updating: function.py (deflated 53%)
2024-08-12 10:54:05 2024-08-12T01:54:05.545  INFO --- [   asgi_gw_0] localstack.request.aws     : AWS lambda.CreateFunction => 201
2024-08-12 10:54:05 {
2024-08-12 10:54:05     "FunctionName": "func01",
2024-08-12 10:54:05     "FunctionArn": "arn:aws:lambda:ap-northeast-1:000000000000:function:func01",
2024-08-12 10:54:05     "Runtime": "python3.12",
2024-08-12 10:54:05     "Role": "arn:aws:iam::000000000000:role/role01",
2024-08-12 10:54:05     "Handler": "function.lambda_handler",
2024-08-12 10:54:05     "CodeSize": 591,
2024-08-12 10:54:05     "Description": "",
2024-08-12 10:54:05     "Timeout": 900,
2024-08-12 10:54:05     "MemorySize": 1024,
2024-08-12 10:54:05     "LastModified": "2024-08-12T01:54:05.542086+0000",
2024-08-12 10:54:05     "CodeSha256": "/jgoYVmWkLStYP+Ml1pxSzWykctciARBv2DiGfAKnA8=",
2024-08-12 10:54:05     "Version": "$LATEST",
2024-08-12 10:54:05     "Environment": {
2024-08-12 10:54:05         "Variables": {
2024-08-12 10:54:05             "LAMBDA_TOKEN": "test"
2024-08-12 10:54:05         }
2024-08-12 10:54:05     },
2024-08-12 10:54:05     "TracingConfig": {
2024-08-12 10:54:05         "Mode": "PassThrough"
2024-08-12 10:54:05     },
2024-08-12 10:54:05     "RevisionId": "11df305b-2c47-4dee-9372-d95c71f1fc41",
2024-08-12 10:54:05     "State": "Pending",
2024-08-12 10:54:05     "StateReason": "The function is being created.",
2024-08-12 10:54:05     "StateReasonCode": "Creating",
2024-08-12 10:54:05     "PackageType": "Zip",
2024-08-12 10:54:05     "Architectures": [
2024-08-12 10:54:05         "x86_64"
2024-08-12 10:54:05     ],
2024-08-12 10:54:05     "EphemeralStorage": {
2024-08-12 10:54:05         "Size": 512
2024-08-12 10:54:05     },
2024-08-12 10:54:05     "SnapStart": {
2024-08-12 10:54:05         "ApplyOn": "None",
2024-08-12 10:54:05         "OptimizationStatus": "Off"
2024-08-12 10:54:05     },
2024-08-12 10:54:05     "RuntimeVersionConfig": {
2024-08-12 10:54:05         "RuntimeVersionArn": "arn:aws:lambda:ap-northeast-1::runtime:8eeff65f6809a3ce81507fe733fe09b835899b99481ba22fd75b5a7338290ec1"
2024-08-12 10:54:05     }
2024-08-12 10:54:05 }
2024-08-12 10:54:06 2024-08-12T01:54:06.169  INFO --- [   asgi_gw_1] localstack.request.aws     : AWS sqs.CreateQueue => 200
2024-08-12 10:54:06 {
2024-08-12 10:54:06     "QueueUrl": "http://sqs.ap-northeast-1.localhost.localstack.cloud:4566/000000000000/queue01.fifo"
2024-08-12 10:54:06 }
2024-08-12 10:54:06 2024-08-12T01:54:06.768  INFO --- [   asgi_gw_1] localstack.request.aws     : AWS lambda.CreateEventSourceMapping => 202
2024-08-12 10:54:06 {
2024-08-12 10:54:06     "UUID": "75266f54-0fd7-4614-9342-699134681836",
2024-08-12 10:54:06     "BatchSize": 1,
2024-08-12 10:54:06     "MaximumBatchingWindowInSeconds": 0,
2024-08-12 10:54:06     "EventSourceArn": "arn:aws:sqs:ap-northeast-1:000000000000:queue01.fifo",
2024-08-12 10:54:06     "FunctionArn": "arn:aws:lambda:ap-northeast-1:000000000000:function:func01",
2024-08-12 10:54:06     "LastModified": 1723427646.764243,
2024-08-12 10:54:06     "State": "Creating",
2024-08-12 10:54:06     "StateTransitionReason": "USER_INITIATED",
2024-08-12 10:54:06     "FunctionResponseTypes": []
2024-08-12 10:54:06 }
```


## Djangoの設定
### settings.py
settings.pyにS3とSQSの設定を行います
LocalStackを使用する際はAWSのシークレットキーとアクセスキーがいるのでdocker-compose.yml内に書いたLocalStackの環境変数と同じものを記載します
逆にAWS上ではシークレットキーとアクセスキーではなく、IAMロールを使って実行するので下記のようにローカルとAWSではSQS_CLIENTの設定が違います

```settings.py
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

MEDIA_URL = "/upload/"
MEDIA_ROOT = os.path.join(BASE_DIR, "upload")

AWS_SQS_URL = os.environ.get("AWS_SQS_URL")
LAMBDA_TOKEN = os.environ.get("LAMBDA_TOKEN")

if DEBUG:
    SQS_CLIENT = boto3.client(
        "sqs",
        endpoint_url=os.environ.get("AWS_SQS_ENDPOINT"),
        aws_access_key_id="localstack",
        aws_secret_access_key="localstack",
        region_name=os.environ.get("AWS_DEFAULT_REGION_NAME"),
    )
else:
    SQS_CLIENT = boto3.client(
        "sqs",
        endpoint_url=os.environ.get("AWS_SQS_ENDPOINT"),
        region_name=os.environ.get("AWS_DEFAULT_REGION_NAME"),
    )
    DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
    STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
    AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
```

### S3の設定
今回はローカル上でDjangoのFileSystemStorageを使用します
CustomStorageクラスを作成してローカル上ではupload/配下に、AWS上ではS3にCSVを保存するよう設定します

```storages.py
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage


if settings.DEBUG:
    storage_class = FileSystemStorage
else:
    storage_class = S3Boto3Storage


class CustomStorage(storage_class):
    file_overwrite = False
    counts = {}

    def get_alternative_name(self, file_root, file_ext):
        if file_root not in self.counts:
            self.counts[file_root] = 1
        new_file_name = (
            file_root + "_" + str(self.counts[file_root]) + file_ext
        )
        self.counts[file_root] += 1
        return new_file_name
```

### SQSへのメッセージ送信
LocalStack、AWSでSQS_CLIENTの設定が違うのでラッパー関数を作成して下記のメソッドを実行するだけで裏側を意識せずにSQSへメッセージを送信できるようにします

```sqs.py
import os

from django.conf import settings


def sqs_send_message(message_body, message_group_id=os.environ.get("AWS_SQS_MESSAGE_GROUP")):
    """AWS SQSへキューを送信する"""
    sqs_client = getattr(settings, "SQS_CLIENT")
    sqs_client.send_message(
        QueueUrl=os.environ.get("AWS_SQS_URL"),
        MessageBody=f"{message_body}",
        MessageGroupId=f"{message_group_id}",
    )

```

## APIの実装
### Modelの実装
下記のようにModelを作成します

```models.py
import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import FileExtensionValidator, RegexValidator
from django.db import models

from application.utils.storages import CustomStorage


class User(AbstractUser):
    """システムユーザ"""

    username_validator = UnicodeUsernameValidator()

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    groups = None
    group = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="users",
        db_comment="システム利用者権限テーブルの外部キー",
    )
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="システムユーザID",
    )
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r"^[0-9]{8}$")],
        max_length=8,
        db_comment="社員番号",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
        db_comment="ユーザ名",
    )
    email = models.EmailField(
        max_length=254,
        unique=True,
        db_comment="メールアドレス",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日",
    )
    is_verified = models.BooleanField(
        default=False,
        db_comment="有効化有無",
    )
    created_by = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        db_comment="作成者",
    )
    updated_by = models.ForeignKey(
        "self",
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_updated_by",
        db_comment="更新者",
    )

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"
        db_table_comment = "システムユーザ"

    def save(self, *args, **kwargs):
        # 既に登録されているシステム利用者情報の保存処理
        if self.id:
            if not "updated_by" in kwargs:
                self.updated_by = self
            else:
                self.updated_by = kwargs.get("updated_by")
                kwargs.pop("updated_by")
        super(User, self).save(*args, **kwargs)

    def __str__(self):
        return self.username


class Customer(models.Model):
    """お客様"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    kana = models.CharField(
        max_length=255,
        db_comment="カナ氏名",
    )
    name = models.CharField(
        max_length=255,
        db_comment="氏名",
    )
    birthday = models.DateField(
        db_comment="誕生日",
    )
    email = models.EmailField(
        db_comment="メールアドレス",
    )
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
        db_comment="電話番号",
    )
    address = models.OneToOneField(
        "Address",
        on_delete=models.CASCADE,
        related_name="address",
        db_comment="住所のFK",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日時",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_created_by",
        db_comment="作成者ID",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_updated_by",
        db_comment="更新者ID",
    )

    class Meta:
        db_table = "Customer"


class Address(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    prefecture = models.CharField(
        max_length=255,
        db_comment="都道府県",
    )
    municipalities = models.CharField(
        max_length=255,
        db_comment="市区町村",
    )
    house_no = models.CharField(
        max_length=255,
        db_comment="丁・番地",
    )
    other = models.CharField(
        max_length=255,
        blank=True,
        db_comment="その他(マンション名など)",
    )
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
        db_comment="郵便番号",
    )

    class Meta:
        db_table = "Address"


class UploadHistory(models.Model):
    class UploadStatus(models.IntegerChoices):
        WAIT = 1, "処理待ち"
        IN_PROGRESS = 2, "処理中"
        COMPLETE = 3, "正常終了"
        ERROR = 4, "エラー終了"

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    csv = models.FileField(
        upload_to="upload_file",
        validators=[
            FileExtensionValidator(
                [
                    "csv",
                ]
            )
        ],
        storage=CustomStorage(),
        db_comment="CSVファイル",
    )
    status = models.IntegerField(
        choices=UploadStatus.choices,
        default=UploadStatus.WAIT,
        db_comment="アップロードステータス",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_created_by",
        db_comment="作成者ID",
    )

    class Meta:
        db_table = "UploadHistory"

```

### Serializer
- CSVをアップロードする用のUploadCSVSerializer
- CSV内のデータを登録するリクエストのバリデーションを行うRegisterCSVSerializer
- CSV内のデータをInsertする際に使用するAddressSerializer,CustomerSerializer
- アップロード履歴一覧用のListUploadHistorySerializer

を作成します
ListUploadHistorySerializerではto_representationを使ったstatusのEnumのLabelの表示とCSVファイルのパスを"/"でsplitして最後の要素のみ表示させるようにします

```serializers.py
from rest_framework import serializers

from application.models import Address, Customer, UploadHistory

class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = "__all__"
        read_only_fields = ["id"]


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = [
            "id",
            "name",
            "kana",
            "email",
            "phone_no",
            "birthday",
        ]
        read_only_fields = ["id"]


class ListUploadHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadHistory
        fields = "__all__"

    def to_representation(self, instance):
        rep = super(ListUploadHistorySerializer, self).to_representation(
            instance
        )
        rep["csv"] = instance.csv.name.split("/")[-1]
        rep["status"] = instance.get_status_display()
        rep["created_by"] = instance.created_by.username
        return rep


class UploadCSVSerializer(serializers.ModelSerializer):
    class Meta:
        model = UploadHistory
        fields = ["id", "csv"]


class RegisterCSVSerializer(serializers.ModelSerializer):
    token = serializers.CharField()

    class Meta:
        model = UploadHistory
        fields = ["id", "token"]
```

### Viewの作成
- CSVアップロード用のAPI
- CSV内のデータをinsertする用のAPI
- 履歴一覧表示用のAPI

の3つについて順番に解説します

```views.py
import csv

import chardet
from django.conf import settings
from django.db import transaction
from django.http import HttpResponseBadRequest, JsonResponse
from rest_framework import mixins, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import GenericViewSet, ModelViewSet

from application.models import Address, Customer, UploadHistory
from application.serializers.customer import (
    AddressSerializer,
    CustomerSerializer,
    ListUploadHistorySerializer,
    RegisterCSVSerializer,
    UploadCSVSerializer,
)
from application.utils.sqs import sqs_send_message


class CustomerViewSet(ModelViewSet):
    queryset = (
        Customer.objects.select_related("address")
        .select_related("created_by")
        .all()
    )

    def get_serializer_class(self):
        match self.action:
            case "upload_csv":
                return UploadCSVSerializer
            case "register_csv":
                return RegisterCSVSerializer

    @action(methods=["post"], detail=False, permission_classes=[IsAuthenticated])
    def upload_csv(self, request):
        """CSVアップロードAPI

        CSVファイルをアップロードする

        Returns:
            JsonResponse
        """
        csv = request.FILES.get("csv")
        encoding = chardet.detect(csv.read())
        csv.seek(0)
        if encoding["encoding"] != "utf-8":
            return JsonResponse(
                data={"msg": "CSVファイルのエンコードをutf-8にしてください"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(
            data={
                "csv": csv,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        id = serializer.data["id"]
        sqs_send_message(id)
        return JsonResponse(
            {"msg": "CSVファイルのアップロードに成功しました", "id": id},
            status=status.HTTP_201_CREATED,
        )

    @transaction.atomic
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def register_csv(self, request, pk):
        """Lambdaを使った非同期でお客様情報を登録するAPI

        CSVファイルを読み込み、お客様を非同期で一括で登録する

        Returns:
            - JsonResponse
            - HttpResponseBadRequest
        """
        if request.data.get("token", "") != settings.LAMBDA_TOKEN:
            # 攻撃者へ情報を与えない為にレスポンスにメッセージを入れない
            return HttpResponseBadRequest()
        try:
            entry = UploadHistory.objects.get(pk=pk)
        except UploadHistory.DoesNotExist:
            return JsonResponse(
                data={"msg": "存在しないIDです"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if entry.status != UploadHistory.UploadStatus.WAIT:
            return JsonResponse(
                data={"msg": "処理対象のIDが無効です。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            entry.status = UploadHistory.UploadStatus.WAIT
            entry.save()
            decoded_file = entry.csv.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)
            for row in reader:
                customer_data = {
                    "name": row[0],
                    "kana": row[1],
                    "birthday": row[2],
                    "email": row[3],
                    "phone_no": "0" + row[4],
                }
                address_data = {
                    "prefecture": row[5],
                    "municipalities": row[6],
                    "house_no": row[7],
                    "other": row[8],
                    "post_no": row[9],
                }
                address_serializer = AddressSerializer(data=address_data)
                address_serializer.is_valid(raise_exception=True)
                customer_serializer = CustomerSerializer(data=customer_data)
                customer_serializer.is_valid(raise_exception=True)
                address = Address.objects.create(
                    **address_data,
                )
                Customer.objects.create(
                    **customer_data,
                    address=address,
                    created_by=request.user,
                    updated_by=request.user,
                )
            entry.status = UploadHistory.UploadStatus.COMPLETE
            entry.save()
        except BaseException as e:
            entry.status = UploadHistory.UploadStatus.ERROR
            entry.save()
            return JsonResponse(
                data={"msg": e},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return JsonResponse(
            data={"msg": "CSVファイルの取り込みに成功しました"},
            status=status.HTTP_201_CREATED,
        )


class ListUploadCSVHistoryViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = UploadHistory.objects.select_related("created_by")
    permission_classes = [IsAuthenticated]
    serializer_class = ListUploadHistorySerializer

    def list(self, request):
        """CSVアップロード履歴

        CSVアップロード履歴を一覧表示する

        Returns:
            Response
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

#### CSVアップロード用のAPI
まず、リクエスト内のCSVがutf-8の文字コードを使用しているか確認します
その後、CSVファイルなのかバリデーションし、serializer.is_validがtrueの時UploadHistoryを作成し、PKの値をSQSへメッセージとして送信します

```python
    @action(methods=["post"], detail=False, permission_classes=[IsAuthenticated])
    def upload_csv(self, request):
        """CSVアップロードAPI

        CSVファイルをアップロードする

        Returns:
            JsonResponse
        """
        csv = request.FILES.get("csv")
        encoding = chardet.detect(csv.read())
        csv.seek(0)
        if encoding["encoding"] != "utf-8":
            return JsonResponse(
                data={"msg": "CSVファイルのエンコードをutf-8にしてください"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        serializer = self.get_serializer(
            data={
                "csv": csv,
            }
        )
        serializer.is_valid(raise_exception=True)
        serializer.save(created_by=request.user)
        id = serializer.data["id"]
        sqs_send_message(id)
        return JsonResponse(
            {"msg": "CSVファイルのアップロードに成功しました", "id": id},
            status=status.HTTP_201_CREATED,
        )
```

#### CSV内のデータをinsertする用のAPI
下記のコードはLambdaで実行するのでpermission_classesをAllowAnyにします
まず、不正アクセス対策のためにtokenの値を確認し、一致しなければ400を返します
次にステータスの値から処理待ち以外だと400を返すようにします
その後、処理中にステータスを変更し、CSV内のデータをinsertします
処理が完了したらステータスをCOMPLETEに変更して終了です

```python
    @transaction.atomic
    @action(detail=True, methods=["post"], permission_classes=[AllowAny])
    def register_csv(self, request, pk):
        """Lambdaを使った非同期でお客様情報を登録するAPI

        CSVファイルを読み込み、お客様を非同期で一括で登録する

        Returns:
            - JsonResponse
            - HttpResponseBadRequest
        """
        if request.data.get("token", "") != settings.LAMBDA_TOKEN:
            # 攻撃者へ情報を与えない為にレスポンスにメッセージを入れない
            return HttpResponseBadRequest()
        try:
            entry = UploadHistory.objects.get(pk=pk)
        except UploadHistory.DoesNotExist:
            return JsonResponse(
                data={"msg": "存在しないIDです"},
                status=status.HTTP_404_NOT_FOUND,
            )
        if entry.status != UploadHistory.UploadStatus.WAIT:
            return JsonResponse(
                data={"msg": "処理対象のIDが無効です。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            entry.status = UploadHistory.UploadStatus.IN_PROGRESS
            entry.save()
            decoded_file = entry.csv.read().decode("utf-8").splitlines()
            reader = csv.reader(decoded_file)
            next(reader)
            for row in reader:
                customer_data = {
                    "name": row[0],
                    "kana": row[1],
                    "birthday": row[2],
                    "email": row[3],
                    "phone_no": "0" + row[4],
                }
                address_data = {
                    "prefecture": row[5],
                    "municipalities": row[6],
                    "house_no": row[7],
                    "other": row[8],
                    "post_no": row[9],
                }
                address_serializer = AddressSerializer(data=address_data)
                address_serializer.is_valid(raise_exception=True)
                customer_serializer = CustomerSerializer(data=customer_data)
                customer_serializer.is_valid(raise_exception=True)
                address = Address.objects.create(
                    **address_data,
                )
                Customer.objects.create(
                    **customer_data,
                    address=address,
                    created_by=request.user,
                    updated_by=request.user,
                )
            entry.status = UploadHistory.UploadStatus.COMPLETE
            entry.save()
        except BaseException as e:
            entry.status = UploadHistory.UploadStatus.ERROR
            entry.save()
            return JsonResponse(
                data={"msg": e},
                status=status.HTTP_400_BAD_REQUEST,
            )
        return JsonResponse(
            data={"msg": "CSVファイルの取り込みに成功しました"},
            status=status.HTTP_201_CREATED,
        )
```

#### 履歴一覧表示用のAPI
表示内容についてはSerializerで制御しているのでrest_frameworkのListModelMixinのコードをそのまま流用します

```python
class ListUploadCSVHistoryViewSet(mixins.ListModelMixin, GenericViewSet):
    queryset = UploadHistory.objects.select_related("created_by")
    permission_classes = [IsAuthenticated]
    serializer_class = ListUploadHistorySerializer

    def list(self, request):
        """CSVアップロード履歴

        CSVアップロード履歴を一覧表示する

        Returns:
            Response
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)
```

## 実際に検証してみよう！
### APIを個別に検証
CSVファイルをアップロードします

![スクリーンショット 2024-08-12 9.18.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e78d2afd-c7e6-a791-70f2-1be20e6c4b5e.png)

以下のようにmsgとidが表示されたら成功です
![スクリーンショット 2024-08-12 9.44.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ed96012f-3ec4-799c-c6ef-98b4d7e8dcd6.png)

CSVのimport処理を検証します
以下のように表示されたら成功です
![スクリーンショット 2024-08-12 9.45.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4374a3ac-98c2-07a0-baab-0b979ddf476a.png)

履歴一覧を表示させます
以下のように表示されたら成功です

![スクリーンショット 2024-08-12 15.30.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3b122369-7f3a-1970-7da8-229c9ae09b04.png)

### Localstackを検証
CSVをアップロードするAPIを実行するとDjangoとLocalStackで下記のようなログが出れば成功です

```Djangoのコンテナ
2024-08-12 10:52:37 [12/Aug/2024 10:52:37] "POST /api/customers/upload_csv HTTP/1.1" 201 168 
2024-08-12 10:52:38 [12/Aug/2024 10:52:38] "POST /api/customers/register_csv HTTP/1.1" 201 110
```

```LocalStackのコンテナ
2024-08-12 10:37:38 time="2024-08-12T01:37:38Z" level=warning msg="Cannot list external agents" func=go.amzn.com/lambda/agents.ListExternalAgentPaths file="/home/runner/work/lambda-runtime-init/lambda-runtime-init/lambda/agents/agent.go:24" error="open /opt/extensions: no such file or directory"
2024-08-12 10:37:38 c23e8b17-ec15-4107-8c35-41d0befe6ca8
2024-08-12 10:37:38 [('Date', 'Mon, 12 Aug 2024 01:37:38 GMT'),
2024-08-12 10:37:38  ('Server', 'WSGIServer/0.2 CPython/3.11.9'),
2024-08-12 10:37:38  ('Content-Type', 'application/json'),
2024-08-12 10:37:38  ('Vary', 'Accept, Cookie, Origin'),
2024-08-12 10:37:38  ('Allow', 'POST, OPTIONS'),
2024-08-12 10:37:38  ('djdt-store-id', 'bbaa2ab2a43e447ab2e16f5b1147b4f1'),
2024-08-12 10:37:38  ('Server-Timing',
2024-08-12 10:37:38   'TimerPanel_utime;dur=63.471000000000274;desc="User CPU time", '
2024-08-12 10:37:38   'TimerPanel_stime;dur=1.6119999999999468;desc="System CPU time", '
2024-08-12 10:37:38   'TimerPanel_total;dur=65.08300000000023;desc="Total CPU time", '
2024-08-12 10:37:38   'TimerPanel_total_time;dur=76.9503116607666;desc="Elapsed time", '
2024-08-12 10:37:38   'SQLPanel_sql_time;dur=6.563425064086914;desc="SQL 9 queries", '
2024-08-12 10:37:38   'CachePanel_total_time;dur=0;desc="Cache 0 Calls"'),
2024-08-12 10:37:38  ('X-Frame-Options', 'DENY'),
2024-08-12 10:37:38  ('Content-Length', '110'),
2024-08-12 10:37:38  ('X-Content-Type-Options', 'nosniff'),
2024-08-12 10:37:38  ('Referrer-Policy', 'same-origin'),
2024-08-12 10:37:38  ('Cross-Origin-Opener-Policy', 'same-origin')]
2024-08-12 10:37:38 201
2024-08-12 10:37:38 {'msg': 'CSVファイルの取り込みに成功しました'}
```

## まとめ
今回はLocalStackを使った非同期処理の実装方法を説明するためにAPIの実装をやや簡素なものにしましたが、CSV内のヘッダのバリデーションやエラーが発生した時にエラ〜メッセージを履歴一覧に表示させるなど顧客のニーズに応じて適宜処理を追加しても面白いのではないかと思います
やるべきことがとても多かったですが非同期処理はとても汎用的なものなので一度作成すればたプロジェクトでも横展開できるので学んだことをしっかり復習して同様の実装を任されても再現できるようにしたいです

## 参考
https://docs.localstack.cloud/user-guide/aws/sqs/

https://github.com/localstack/localstack/issues/9753

https://qiita.com/KWS_0901/items/bb0d3c8319cbb1e64217
