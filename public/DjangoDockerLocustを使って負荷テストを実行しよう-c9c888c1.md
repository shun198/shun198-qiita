---
title: '[Django+Docker]Locustを使って負荷テストを実行しよう！'
tags:
  - Django
  - Docker
  - locust
  - docker-compose
private: false
updated_at: '2024-02-14T14:17:52+09:00'
id: c9c888c1261e6015a531
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Pythonのプロジェクトで使えるLocustという負荷検証ツールを使って負荷テストを行う方法について解説したいと思います
今回はお客様登録用APIを作成して検証します

## 前提
- Django、Postgres(DB)用のDockerfileを作成済み

## ディレクトリ構成
```
tree
・
├── application
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── locustfile.py
│   │   ├── management
│   │   │   └── commands
│   │   │       └── seed.py
│   │   ├── migrations
│   │   │   ├── 0001_initial.py
│   │   │   └── __init__.py
│   │   ├── models.py
│   │   ├── permissions.py
│   │   ├── serializers.py
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
├── containers
│   ├── django
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── postgres
│       └── Dockerfile
├── docker-compose.yml
└── static
```

## 実装
以下のファイルを作成します
- docker-compose.yml
- application/models.py
- application/serializers.py
- application/views.py
- application/locust.py

### Docker環境の作成
今回はdocker-compose.ymlを使って負荷テスト用のDocker環境を作成します
locustfile.pyをlocust用のworkerとmaster用コンテナにマウントするよう設定します
また、locustのコンテナ内でDjangoのAPIを実行したいので以下のように
```
-H http://app:8000
```
とホストを設定します
今回は本番を想定してGunicornを使ってアプリケーションを起動します

```docker-compose.yml
services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    # 環境変数
    environment:
      - POSTGRES_NAME
      - POSTGRES_HOST
      - POSTGRES_USER
      - POSTGRES_PASSWORD
    ports:
      - "5432:5432"
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 30s
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./application:/code
      - ./static:/static
    ports:
      - "8000:8000"
      # デバッグ用ポート
      - "8080:8080"
    command: "poetry run gunicorn project.wsgi:application --bind 0.0.0.0:8000"
    stdin_open: true
    tty: true
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
  master:
    container_name: master
    image: locustio/locust
    ports:
      - "8089:8089"
    volumes:
      - ./application/application/locustfile.py:/mnt/locust/locustfile.py
    command: -f /mnt/locust/locustfile.py --master -H http://app:8000
  worker:
    image: locustio/locust
    volumes:
      - ./application/application/locustfile.py:/mnt/locust/locustfile.py
    command: -f /mnt/locust/locustfile.py -H app:8000 --worker --master-host=master
volumes:
  db_data:
  static:

```

### Modelの作成
- User
- Customer

のmodelを作成します
AbstractUserについて詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```models.py
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """システムユーザ"""

    username_validator = UnicodeUsernameValidator()

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    id = models.AutoField(
        primary_key=True,
        db_comment="ID",
    )
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r"^[0-9]{8}$")],
        max_length=8,
        # 管理者のログイン画面で社員番号と表示される
        verbose_name="社員番号",
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
    groups = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="users",
        db_comment="社員権限テーブル外部キー",
    )

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"
        db_table_comment = "システムユーザ"

    def __str__(self):
        return self.username


class Customer(models.Model):
    """お客様"""

    id = models.AutoField(
        primary_key=True,
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
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
        db_comment="電話番号",
    )

    class Meta:
        db_table = "Customer"
        db_table_comment = "お客様"

```

### Serializerの作成
- ログイン用
- お客様用

のSerializerを作成します

```serializers.py
from rest_framework import serializers

from application.models import Customer, User


class LoginSerializer(serializers.ModelSerializer):
    """ログイン用シリアライザ"""

    employee_number = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["employee_number", "password"]


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "employee_number",
            "username",
            "email",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

        
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
```

### Viewの作成
- ログイン
- CSRFトークン取得
- お客様

APIを作成します
今回はログイン認証の詳細について説明しないので気になる方は以下の記事を参考にしてください

https://qiita.com/shun198/items/067e122bb291fed2c839

```views.py
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.viewsets import ModelViewSet, ViewSet

from application.models import Customer, User
from application.serializers import (
    CustomerSerializer,
    LoginSerializer,
    UserSerializer,
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "get_csrf_token":
            return None
        else:
            return UserSerializer

    @action(detail=False, methods=["get"])
    def get_csrf_token(self, request):
        """CSRF Tokenを発行する

        Args:
            request : リクエスト

        Returns:
            JsonResponse
        """
        return JsonResponse({"token": str(get_token(request))})

        
class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    permission_classes = [IsAuthenticated]


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        """ログインAPI

        Args:
            request : リクエスト

        Returns:
            JsonResponse
        """
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee_number = serializer.validated_data.get("employee_number")
        password = serializer.validated_data.get("password")
        user = authenticate(employee_number=employee_number, password=password)
        if not user:
            return JsonResponse(
                data={
                    "msg": "either employee number or password is incorrect"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
            return JsonResponse(
                {
                    "username": user.username,
                    "role": user.groups.name,
                }
            )

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        """ログアウトAPI

        Args:
            request : リクエスト

        Returns:
            HttpResponse
        """
        logout(request)
        return HttpResponse()
```


### locust.pyの作成
負荷テスト用のスクリプト(locust.py)を作成します

```application/locust.py
import random
import time

from locust import HttpUser, between, task


class TestLoad(HttpUser):
    wait_time = between(1, 1)
    id = 1
    csrftoken = None
    headers = None

    def on_start(self):
        self.id = TestLoad.id
        TestLoad.id += 1

    @task
    def test_scenario(self):
        if not self.csrftoken:
            token_res = self.client.get(
                "/api/users/get_csrf_token",
                headers={"Cache-Control": "no-cache"},
            )
            self.csrftoken = token_res.cookies.get("csrftoken")
            self.headers = {
                "X-CSRFToken": self.csrftoken,
            }

        employee_number = str(self.id).zfill(8)
        self.client.post(
            "/api/login",
            json={
                "employee_number": employee_number,
                "password": "test",
            },
            headers=self.headers,
            cookies={"csrftoken": self.csrftoken},
        )

        time.sleep(random.randrange(5, 25))

        response = self.client.post(
            "/api/customer",
            json={
                "kana": "ヤマダタロウ",
                "name": "山田太郎",
                "birthday": "1995-01-01",
                "phone_no": "08011112222",
            },
            headers=self.headers,
            cookies={"csrftoken": self.csrftoken},
        )

        time.sleep(random.randrange(5, 25))

```

locust.pyに記載されている内容について１つずつ解説します

#### 変数
負荷テスト用のスクリプトを作る際はまず、HttpUserクラスを継承したクラスを作成します
変数はクラス内に定義します
wait_time変数を使用するとタスク間のインターバルを設定できます
今回はタスク間の間隔を5秒に設定します
また、ログイン認証を使用するので
- csrttoken
- headers

変数を使用します

```python
class TestLoad(HttpUser):
    wait_time = between(1, 5)
    id = 1
    csrftoken = None
    headers = None
```

#### on_start
タスクが始まるたびに実行されるon_startメソッドを作成します
今回はタスクが実行されるたびにidの変数をauto incrementします

```python
    def on_start(self):
        self.id = TestLoad.id
        TestLoad.id += 1
```

#### タスク
タスク(負荷テストの内容)を記載します
ログイン認証する際にcsrfトークンが必要なのでまずはcsrtトークンを取得するAPIを実行します
トークンを取得したらログインAPIでログイン認証します
最後にお客様登録APIを使ってお客様情報を登録します
APIを実行する際は
```
time.sleep(random.randrange(5, 25))
```
を使って一定時間分実行する間隔を空けます

```python
    @task
    def test_scenario(self):
        if not self.csrftoken:
            token_res = self.client.get(
                "/api/users/get_csrf_token",
                headers={"Cache-Control": "no-cache"},
            )
            self.csrftoken = token_res.cookies.get("csrftoken")
            self.headers = {
                "X-CSRFToken": self.csrftoken,
            }

        employee_number = str(self.id).zfill(8)
        self.client.post(
            "/api/login",
            json={
                "employee_number": employee_number,
                "password": "test",
            },
            headers=self.headers,
            cookies={"csrftoken": self.csrftoken},
        )

        time.sleep(random.randrange(5, 25))

        response = self.client.post(
            "/api/customer",
            json={
                "kana": "ヤマダタロウ",
                "name": "山田太郎",
                "birthday": "1995-01-01",
                "phone_no": "08011112222",
            },
            headers=self.headers,
            cookies={"csrftoken": self.csrftoken},
        )

        time.sleep(random.randrange(5, 25))
```

## 実際に実行してみよう！
今回は10人同時接続テストを行います
まずはシステムユーザを10人作成します
ユーザを作成するカスタムコマンドを作る方法について解説しているので以下の記事を参考にしてください

https://qiita.com/shun198/items/14bac6843a2459b34a34

docker compose upを実行し、`http://127.0.0.1:8089/`にアクセスします
以下の画面が出たら成功です

![スクリーンショット 2024-02-05 16.28.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/44372810-2528-20d1-51b7-2607d5a9fe92.png)

ユーザ数を10にした状態でStart swarmingボタンを押します

![スクリーンショット 2024-02-05 16.28.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b9acd19f-045f-c557-4b57-e10bef262f4a.png)

以下のように実行したAPIのリクエスト数や失敗数などの情報が表示されます

![スクリーンショット 2024-02-05 16.33.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/37a7135a-61cb-f8c0-8167-c3a55c63ac2e.png)

Chartsタブを開くと
- 1秒ごとの合計リクエスト数
- レスポンスにかかった時間(ms)
- ユーザ数

が表示されます

![スクリーンショット 2024-02-05 16.33.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f6be3a7f-a0af-a854-7087-6d8308478794.png)

![スクリーンショット 2024-02-05 16.34.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5675cfaf-49ef-eeec-d1c8-0c2529eea266.png)

![スクリーンショット 2024-02-05 16.34.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d22ece5e-b744-3b8b-e53d-9002c8a6bcef.png)

## Workerを増やすには？
Workerのデフォルトの数は1ですが以下のようにworkerの数を指定することで増やすことができます

```
docker compose up --scale worker=2
```

以下のように指定したWorkerの数で実行できるようになります

![スクリーンショット 2024-02-14 14.16.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/511ada23-0093-64ad-5d9c-37281df991fb.png)

## 参考
https://docs.locust.io/en/stable/writing-a-locustfile.html

https://docs.locust.io/en/stable/running-in-docker.html

https://qiita.com/HirokazuMiyaji/items/ea88f861d3ad5debba78
