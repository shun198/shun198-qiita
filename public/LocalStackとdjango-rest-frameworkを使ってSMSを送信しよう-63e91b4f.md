---
title: LocalStackとdjango-rest-frameworkを使ってSMSを送信しよう！
tags:
  - AWS
  - SMS
  - django-rest-framework
  - docker-compose
  - LocalStack
private: false
updated_at: '2024-01-17T17:38:47+09:00'
id: 63e91b4f96a2e9b78988
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
AWSのマネージドサービスをローカル上で実行できるLocalStackとdjango-rest-frameworkを使ってSMSを送信する方法について解説していきたいと思います

## 前提
- Djangoのプロジェクトを作成済み

## ディレクトリ構成
```
tree
・
├── .gitignore
├── README.md
├── backend
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── fixture.json
│   │   ├── migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py
│   ├── poetry.lock
│   ├── project
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── pyproject.toml
└── compose.yaml
```

以下のファイルを作成・編集します
- compose.yaml
- settings.py
- models.py
- fixtures.py
- views.py

## LocalStackの設定
まずはローカル上でAWS SNSを使用できるようにLocakStackの設定をしていきます
SERVICESにSNSを追加し、今回は
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

の環境変数をlocalstackにします

```compose.yaml
  localstack:
    image: localstack/localstack
    container_name: localstack
    ports:
      - '4566:4566'
    environment:
      - SERVICES=sns
      - AWS_ACCESS_KEY_ID=localstack
      - AWS_SECRET_ACCESS_KEY=localstack
      - DEBUG=1
    volumes:
      - localstack_data:/tmp/localstack/data
      - localstack_bin:/var/lib/localstack
```

## boto3の設定
Djangoのプロジェクト内でLocalStackとAWS SNSを使えるよう設定をしていきます
LocalStackを使う際はboto3.client内に以下の引数を指定します

|引数|値|説明|
|---|---|---|
|aws_access_key_id|localstack|AWSのアクセスキー<br>LocalStack内の環境変数と同じ値にします|
|aws_secret_access_key|localstack|AWSのシークレットキー<br>LocalStack内の環境変数と同じ値にします|
|region_name|ap-northeast-1|リージョン名|
|endpoint_url|http://localstack:4566|ローカル環境のboto3の接続先<br>今回だとLocalStack|

本番環境ではIAMロールを使った開発が一般的なので
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

は使用しません

```settings.py
import boto3
import os

if DEBUG:
    SNS_CLIENT = boto3.client(
        "sns",
        aws_access_key_id="localstack",
        aws_secret_access_key="localstack",
        region_name=os.environ.get("AWS_DEFAULT_REGION_NAME"),
        endpoint_url=os.environ.get("AWS_SNS_ENDPOINT_URL"),
    )
else:
    SNS_CLIENT = boto3.client(
        "sns",
        region_name=os.environ.get("AWS_DEFAULT_REGION_NAME"),
        endpoint_url=os.environ.get("AWS_SNS_ENDPOINT_URL"),
    )
```

## SMS送信用APIの実装
### Modelの作成
SMSを送信するお客様のModelを作成します

```models.py
import uuid

from django.core.validators import RegexValidator
from django.db import models


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
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日時",
    )

    class Meta:
        db_table = "Customer"
```

### テストデータの作成
お客様用のテストデータを作成します

```fixtures.json
[
    {
        "model": "application.Customer",
        "pk": 1,
        "fields": {
            "kana": "オオサカタロウ",
            "name": "大阪太郎",
            "birthday": "1992-01-06",
            "email":"osaka@example.com",
            "phone_no": "08011112222",
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 2,
        "fields": {
            "kana": "キョウトジロウ",
            "name": "京都二郎",
            "birthday": "1994-01-06",
            "email":"kyoto@example.com",
            "phone_no": "08022223333",
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 3,
        "fields": {
            "kana": "ヒョウゴサブロウ",
            "name": "兵庫三郎",
            "birthday": "1995-03-06",
            "email":"hyogo@example.com",
            "phone_no": "08033334444",
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    }
]
```

### viewの作成
今回はパラメータにお客様のIDを入れてメッセージ名にお客様の氏名が入るので動的に簡易的なメッセージを送るようにします
```
{{customer}}様
問い合わせありがとうございます
```

SMSを送信する際はSNSのClientを作成し、publishメソッドを使って送信します
日本の電話番号にSMSを送信する際は`+81`が必要です
SMS送信が失敗したときのためにtry catchを使ってClientErrorの時にエラーメッセージを返すようにします

https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/publish.html

```views.py
from application.models import Customer
from botocore.exceptions import ClientError
from django.conf import settings
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    permission_classes = [IsAuthenticated]
    serializer_class = None

    @action(methods=["post"], detail=True)
    def send_sms(self, request, pk):
        customer = self.get_object()
        message = f"{customer.name}様\n問い合わせありがとうございます"
        try:
            settings.SNS_CLIENT.publish(
                PhoneNumber="+81" + customer.phone_no, Message=message
            )
            return JsonResponse({"msg": "SMSの送信に成功しました"},)
        except ClientError as e:
            return JsonResponse(
                {"msg": "SMSを送信できませんでした"},
                status=status.HTTP_400_BAD_REQUEST,
            )

```

## 実際に送信してみよう！
先ほど作成したAPIにお客様のPKを入れてPOSTします
以下のようにSMSを送信できたら成功です

![スクリーンショット 2024-01-17 17.37.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d33df554-e69b-2c27-ac26-95a287f47753.png)
![スクリーンショット 2024-01-17 17.37.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6db262e9-0258-978b-f710-aaf234154048.png)

以下のようにLocalStackのlogから送信が成功したことを確認できました

```
2024-01-17 17:36:55 2024-01-17T08:36:55.533 DEBUG --- [   asgi_gw_0] l.services.sns.publisher   : Publishing '66c16f50-ee4f-4c69-b2f6-865385453f57' to phone number '+8108011112222' with protocol 'sms'
2024-01-17 17:36:55 2024-01-17T08:36:55.535  INFO --- [   asgi_gw_0] localstack.request.aws     : AWS sns.Publish => 200
2024-01-17 17:36:55 2024-01-17T08:36:55.535  INFO --- [   sns_pub_0] l.services.sns.publisher   : Delivering SMS message to +8108011112222: 大阪太郎様
2024-01-17 17:36:55 問い合わせありがとうございます
```

## 参考
https://stackoverflow.com/questions/58770299/how-to-send-sms-messages-with-django-and-aws-sns-with-phone-numbers-stored-in-a

https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/sns/client/publish.html

https://docs.localstack.cloud/user-guide/aws/sns/
