---
title: django-rest-knoxを使ったトークン認証機能を実装しよう！
tags:
  - Django
  - django-rest-framework
  - django-rest-knox
private: false
updated_at: '2024-01-23T15:42:57+09:00'
id: 0c235b90df96c894b5f0
organization_url_name: null
slide: false
---
## 概要
django-rest-frameworkでトークン認証を実装する際はdjango-rest-knoxを使うと便利なので実装方法について解説します

## 前提
- Djangoのプロジェクトを作成済み


## django-rest-knoxについて
django-rest-knoxはDRFのデフォルトのTokenAuthenticationと似ていますがいくつか違いがあります
違いは以下のとおりです

||従来のトークン認証|django-rest-knoxを使ったトークン認証|
|--|--|--|
|作成時|1ユーザについて1トークンしか生成されず、複数デバイスで同じトークンを使ってログインできてしまう|ログインビューへの呼び出しごとにトークンが生成されるのでクライアントごとにトークンが生成される|
|暗号化|平文のまま|ハッシュ化されるのでトークンが流出してもログインできない|
|有効期限の管理|有効期間に関して設定できない|有効期限を設定できる(デフォルトで10時間|

このようにDRFのデフォルトのトークン認証の
- 作成時
- 暗号化
- 有効期限の管理

の欠点を克服したものになっているのでトークン認証する際はdjango-rest-knoxを使うことを推奨しています

## ディレクトリ構成
```
tree
・
├── .gitignore
├── README.md
├── application
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
└── docker-compose.yml

```

## 初期設定
まず、django-rest-knoxをインストールします
```
pip install django-rest-knox
```

### settings.py
settings.pyにknoxの設定を行います

```settings.py
INSTALLED_APPS = (
  ...
  'rest_framework',
  'knox',
  ...
)


REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": [
        "knox.auth.TokenAuthentication",
    ],
    ...
}

KNOX_TOKEN_MODEL = "knox.AuthToken"

# REST_KNOX内で独自の設定を記載
REST_KNOX = {
    # トークンの有効期限を2時間に設定する
    "TOKEN_TTL": timedelta(hours=2),
}

```

マイグレーションを適用させてトークンを管理するknox_authtokenテーブルを作成します
```
python manage.py migrate
```

## 実装
- models.py
- fixtures.json
- serializers.py
- views.py
- urls.py

を作成します

### Modelの作成
User用のModelを作成します

```models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """システムユーザ"""

    username_validator = UnicodeUsernameValidator()

    class Role(models.IntegerChoices):
        """システムユーザのロール

        Args:
            MANAGEMENT(0): 管理者
            GENERAL(1):    一般
            PART_TIME(2):  アルバイト
        """

        MANAGEMENT = 0
        GENERAL = 1
        PART_TIME = 2

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    groups = None
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
    role = models.PositiveIntegerField(
        choices=Role.choices,
        default=Role.PART_TIME,
        db_comment="システムユーザのロール",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日",
    )

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"
        db_table_comment = "システムユーザ"

    def __str__(self):
        return self.username
```

### Fixtureの作成
Userのテストデータを作成します
パスワードは全てtestです

```fixture.json
[
    {
        "model": "application.User",
        "pk": 1,
        "fields": {
            "employee_number": "00000001",
            "username": "test01",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test01@example.com",
            "role": 0,
            "is_superuser": 0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 2,
        "fields": {
            "employee_number": "00000002",
            "username": "test02",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test02@example.com",
            "role": 1,
            "is_superuser": 0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 3,
        "fields": {
            "employee_number": "00000003",
            "username": "test03",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test03@example.com",
            "role": 2,
            "is_superuser": 0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 4,
        "fields": {
            "employee_number": "00000004",
            "username": "test04",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test04@example.com",
            "role": 0,
            "is_superuser": 1,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    }
]
```

### Serializerの作成
ログイン用のSerializerを作成します

```serializers.py
from rest_framework import serializers

from application.models import User


class LoginSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField()

    class Meta:
        model = User
        fields = ["employee_number", "password"]
```

### Viewの作成
ログイン用のViewを作成します

```views.py
from django.contrib.auth import authenticate, login
from django.http import JsonResponse
from knox.models import AuthToken
from knox.views import LoginView as KnoxLoginView
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from application.serializers import LoginSerializer


class LoginView(KnoxLoginView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data["employee_number"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return JsonResponse(
                data={"msg": "社員番号またはパスワードが間違っています"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
            token_ttl = self.get_token_ttl()
            user = request.user
            _, token = AuthToken.objects.create(user, token_ttl)
            return Response(
                {
                    "user": user.username,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )

```

一つずつ解説します
### django-rest-knoxのLoginViewをオーバーライド
LoginView内にpostメソッドがあるのでこちらをオーバーライドする形でログイン機能を実装します
先ほど作成したLoginSerializerでemployee_numberとパスワードのバリデーションを行います
バリデーションに成功したらauthenticateメソッドを実行し、該当するユーザが存在する場合はuserのobjectが返されます
userが存在することが確認できたらloginメソッドを実行します

```python
class LoginView(KnoxLoginView):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = authenticate(
            request=request,
            username=serializer.validated_data["employee_number"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return JsonResponse(
                data={"msg": "社員番号またはパスワードが間違っています"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
```

### トークンの生成
get_token_ttl()メソッドを使ってトークンの有効期限を設定します
settings.pyにTOKEN_LIMIT_PER_USERを設定したのでAuthTokenのオブジェクトを作成する時に適用されます

```knox.views.py
    def get_token_ttl(self):
        return knox_settings.TOKEN_TTL
```

トークンを生成します
```python
_, token = AuthToken.objects.create(user, token_ttl)
```

生成したトークンをレスポンス内に入れます
```python
            return Response(
                {
                    "user": user.username,
                    "token": token,
                },
                status=status.HTTP_200_OK,
            )
```

## 実際にログインしてみよう！
- 社員番号:00000001
- パスワード：test

のユーザでログインします
以下のようにレスポンスが帰ってきたら成功です

![スクリーンショット 2024-01-23 15.20.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cf833a95-d325-e674-f7ba-bfd8aa42328a.png)

以下のようにDB内にトークン情報が作成されていることも確認できました

```
django=# SELECT * FROM "knox_authtoken";
                                                              digest                                                              |            created            |               user_id                |    
        expiry             | token_key 
----------------------------------------------------------------------------------------------------------------------------------+-------------------------------+--------------------------------------+----
---------------------------+-----------
 64bc9e3b11607855d491dfb2d54b800033f617a714e5c1b77fc953056f90a190c5b7e8dcac1f85082e3397b09c7f9b5a118edcd5e1bd0a561c8d5f3b677e1ec7 | 2024-01-23 06:13:34.181444+00 | 00000000-0000-0000-0000-000000000001 | 202
4-01-23 08:13:34.181241+00 | 3fc620c4
(1 row)
```

## トークンを使ってAPIを実行しよう！
認証が必要なAPIのHeader内にトークンを付与した状態で実行できたら成功です

![スクリーンショット 2024-01-23 15.19.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c85fcc6a-b954-7301-93da-07e270a03376.png)

有効期限が切れたら以下のようなレスポンスが返ってきたら成功です

![スクリーンショット 2024-01-23 15.25.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/46d87c09-c2ad-32be-08ae-3292b661706e.png)

## まとめ
django-rest-knoxを使ってトークン認証を実装することができました
今後は例えばアカウントロック機能をaxesを使って実装する記事などを書きたいと思います

## 参考
https://www.django-rest-framework.org/api-guide/authentication/

https://github.com/jazzband/django-rest-knox

https://dev.to/billy_de_cartel/api-authentication-with-django-rest-knox-13go

https://dev.to/bhuma08/django-user-authentication-using-knox-5f17

https://blog.devgenius.io/django-rest-knox-token-authentication-f134760a4a7b

