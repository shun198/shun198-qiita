---
title: Django Rest Frameworkを使ってシステムユーザを有効・無効にするAPIを作成しよう！
tags:
  - Django
  - django-rest-framework
  - AbstractUser
private: false
updated_at: '2023-12-19T13:19:06+09:00'
id: d5276f9dd5d717d3544d
organization_url_name: null
slide: false
---
## 概要
DjangoのAbstractUser内のis_activeフラグをTrue,Falseに切り替えるAPIの作成方法について解説します

## 前提
- Djangoのプロジェクトを作成済み
- DjangoのAbstractUserについてある程度知識がある
- ログイン機能を作成済み

ログイン機能について詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/067e122bb291fed2c839

## ディレクトリ構成
```
tree
・
└── application
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── filters.py
    ├── fixtures
    │   └── fixture.json
    ├── models.py
    ├── urls.py
    └── views.py

```


## 必要なファイルの作成
実装の際に以下のファイルを作成します

- models.py
- fixture.json
- filters.py
- views.py


### Modelの作成

UserのModelについてはDjangoのAbstractUserを継承して作成します
詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

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

        MANAGEMENT = 0, "管理者"
        GENERAL = 1, "一般"
        PART_TIME = 2, "アルバイト"

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
    is_verified = models.BooleanField(
        default=False,
        db_comment="有効化有無",
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

作成したmodelのfixture(テストデータ)を作成します

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
            "is_verified": true,
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
            "is_verified": true,
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
            "is_verified": true,
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
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    }
]


```

### Viewの作成
システムユーザを有効・無効にするAPIを作成します
get_objectメソッドでUserのオブジェクトを取得し、request内のuserと比較します
ログインしているユーザと無効化するユーザが同じならエラーメッセージを出します
無効化するユーザをログインさせないなら例のようなエラーメッセージで大丈夫です
is_activeのフラグを変更した後はuser.save()を忘れずに実行しましょう

```views.py
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from application.models import User


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serilaizer_class = None
    permission_classes = [IsAuthenticated]


    @action(detail=True, methods=["post"])
    def toggle_user_active(self, request, pk):
        """ユーザを有効化/無効化するAPI
        Args:
            request : リクエスト
            pk : ユーザID
        Returns:
            JsonResponse
        """
        user = self.get_object()
        if request.user == user:
            return JsonResponse(
                data={"msg": "自身を無効化することはできません"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        if user.is_active:
            user.is_active = False
        else:
            user.is_active = True
        user.save()
        return JsonResponse(data={"is_active": user.is_active})
```

## 実際に実行してみよう！
以下のようにAPIを実行するとis_activeのフラグが切り替わったら成功です
![スクリーンショット 2023-12-19 13.15.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a80f5f2-3ae9-eca4-5541-be0ac490a7e8.png)

![スクリーンショット 2023-12-19 13.14.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/72383869-1c55-a596-9e9b-4f74afcdccd5.png)

また、自身を無効化しようとした際に以下のエラーメッセージが出たら成功です
![スクリーンショット 2023-12-19 13.12.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6761b193-900d-9941-6481-48f7ff40792f.png)
