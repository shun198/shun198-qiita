---
title: Django Rest FrameworkでPermissionを実装しよう！
tags:
  - Django
  - swagger
  - django-rest-framework
private: false
updated_at: '2024-01-19T15:52:04+09:00'
id: e3349860ce10e3bba15a
organization_url_name: null
slide: false
---
## 概要
今回はログインしたユーザのロール別でPermissionを実装する方法について解説していきます

## はじめに
以下のファイルに必要な記述を記載していきます
- settings.py
- models.py
- fixtures.json
- serializers.py
- permissons.py
- views.py
- urls.py

また、Swaggerを使って実際にPermissionが機能しているか検証するので興味がある方はこちらの記事を見て設定してみてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

## Permissionの設定
### settings.py
認証できたユーザ別にPermissionを付与するのでsettings.pyに以下を記載します
```settings.py
REST_FRAMEWORK = {
    "DEFAULT_PERMISSION_CLASSES": [
        'rest_framework.permissions.IsAuthenticated'
    ],
}

# カスタムユーザの設定
AUTH_USER_MODEL = 'application.User'
```

### models.py
今回はカスタムユーザを作成して認証します
また、superuserを使っての認証も行うのでUserのModelにis_superuserのfieldを追加します
カスタムユーザの作成方法について詳しく知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```models.py
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator


class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    class Role(models.IntegerChoices):
        MANAGEMENT = 0
        GENERAL = 1
        PART_TIME = 2

    first_name = None
    last_name = None
    date_joined = None
    groups = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r'^[0-9]{8}$')],
        max_length=8,
        verbose_name="社員番号",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(max_length=254, unique=True)
    role = models.PositiveIntegerField(choices=Role.choices, default=Role.PART_TIME)
    is_superuser = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email","username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"

    def __str__(self):
        return self.username
```

### fixtures.json
fixtureを使うとカスタムユーザのデータを楽に入れることができます
パスワードが暗号化されていますが全て`test`です
fixtureの使い方について詳しく知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/29b5c253be6f802403cd

```fixtures.json
[
    {
        "model": "relationships.User",
        "pk": 1,
        "fields": {
            "employee_number": "00000001",
            "username":"test01",
            "password":"pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email":"test01@example.com",
            "role":0,
            "is_superuser":0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "relationships.User",
        "pk": 2,
        "fields": {
            "employee_number": "00000002",
            "username":"test02",
            "password":"pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email":"test02@example.com",
            "role":1,
            "is_superuser":0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "relationships.User",
        "pk": 3,
        "fields": {
            "employee_number": "00000003",
            "username":"test03",
            "password":"pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email":"test03@example.com",
            "role":2,
            "is_superuser":0,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "relationships.User",
        "pk": 4,
        "fields": {
            "employee_number": "00000004",
            "username":"test04",
            "password":"pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email":"test04@example.com",
            "role":0,
            "is_superuser":1,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
]
```

#### 自分で暗号化(ハッシュ化)されたパスワードを作成するには？
Djangoのshellを使います
make_password関数の引数に任意のパスワードを入れると作成できます
```
# poetry run python manage.py shell
Python 3.10.9 (main, Dec 21 2022, 18:59:22) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from django.contrib.auth.hashers import make_password
>>> password = make_password("password")
>>> print(password)
pbkdf2_sha256$390000$K8JpO5A4iDOSSxZVpu8VBC$qJPNKobtP7+2HCUv8KUJ7GvpU3ZMiY/FlHOUjYSPf1g=
```

### serializers.py
今回は簡単なUserとLoginのエンドポイントを実装します
```serializers.py
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import User


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "id","employee_number","username","email","role","is_superuser"
        read_only_fields = ["created_at","updated_at","created_by","updated_by"]


class LoginSerializer(serializers.ModelSerializer):
    employee_number = serializers.CharField(
        max_length=8,
        min_length=8,
        validators=[RegexValidator(r"^[0-9]{8}$")],
    )

    class Meta:
        model = User
        fields = ["employee_number","password"]
```

### permissions.py
views.pyを作成する前に権限用のファイル(permissions.py)を作成します
今回は
- superuser(スーパーユーザ)
- management(管理ユーザ)
- general(一般ユーザ)
- part_time(アルバイト)

の4つのロール別のPermissionを作成します
権限の構成は以下の表の通りにします

|  role  |  list  |  retrieve  |  create  |  update  |  partial_update  |  destroy  |
|-----|-----|-----|-----|-----|-----|-----|
|  superuser  |  ○  |  ○  |  ○  |  ○  |  ○  |  ○  |
|  management  |  ○  |  ○  |  ○  |  ○  |  ○  |  -  |
|  general  |  ○  |  ○  |  ○  |  -  |  -  |  -  |
|  part_time  |  ○  |  ○  |  -  |  -  |  -  |  -  |

このようにsuperuserの順で権限が強く、例えばgeneral(一般ユーザ)ができることはmanagement(管理ユーザ)とsuperuserは全てできるようになっています
それをpermissions.pyにコードとして落とし込んでいきます

```permissions.py
"""
権限用のモジュール
"""
from rest_framework.permissions import BasePermission
from .models import User


class IsPartTimeUser(BasePermission):
    def has_permission(self, request, view):
        """アルバイトユーザかどうか判定

        Args:
            request: リクエスト
            view: ビュー

        Returns:
            アルバイトユーザならTrue
            それ以外はFalse
        """
        if request.user.is_superuser:
            return True

        if request.user.is_authenticated:
            # アルバイトユーザーにできて一般ユーザーと管理ユーザーにできないことはないので管理ユーザーもTrue
            if request.user.role in [
                User.Role.PART_TIME,
                User.Role.GENERAL,
                User.Role.MANAGEMENT,
            ]:
                return True
        return False


class IsGeneralUser(BasePermission):
    def has_permission(self, request, view):
        """一般ユーザかどうか判定

        Args:
            request: リクエスト
            view: ビュー

        Returns:
            一般ユーザならTrue
            それ以外はFalse
        """
        if request.user.is_superuser:
            return True

        if request.user.is_authenticated:
            # 一般ユーザー、管理ユーザーともにTrueになるよう設定
            if request.user.role in [
                User.Role.GENERAL,
                User.Role.MANAGEMENT,
            ]:
                return True
        return False


class IsManagementUser(BasePermission):
    def has_permission(self, request, view):
        """管理ユーザかどうか判定

        Args:
            request: リクエスト
            view: ビュー

        Returns:
            管理ユーザならTrue
            それ以外はFalse
        """
        if request.user.is_superuser:
            return True

        if request.user.is_authenticated:
            if request.user.role == User.Role.MANAGEMENT:
                return True
        return False


class IsSuperUser(BasePermission):
    def has_permission(self, request, view):
        """スーパーユーザかどうか判定

        Args:
            request: リクエスト
            view: ビュー

        Returns:
            スーパーユーザならTrue
            それ以外はFalse
        """
        return request.user.is_superuser

```

### views.py
permissions.pyで作成したクラスと`get_permissions`メソッドを使ってログインしたユーザ別に権限を付与していきます
ログイン機能の作成方法について詳しく知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/067e122bb291fed2c839

```views.py
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ViewSet

from .models import User
from .permissions import IsGeneralUser, IsManagementUser, IsPartTimeUser, IsSuperUser
from .serializers import LoginSerializer, UserSerilaizer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerilaizer

    # get_permissionsメソッドを使えば前述の表に従って権限を付与できる
    def get_permissions(self):
        if self.action in ["update", "partial_update"]:
            permission_classes = [IsManagementUser]
        elif self.action == "create":
            permission_classes = [IsGeneralUser]
        elif self.action == "destroy":
            permission_classes = [IsSuperUser]
        elif self.action in ["list", "retrieve"]:
            permission_classes = [IsPartTimeUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        """ユーザのログイン"""
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        employee_number = serializer.validated_data.get("employee_number")
        password = serializer.validated_data.get("password")
        user = authenticate(employee_number=employee_number, password=password)
        if not user:
            return JsonResponse(
                data={"msg": "社員番号またはパスワードが間違っています"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
            return JsonResponse(data={"role": user.Role(user.role).name})

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        logout(request)
        return HttpResponse()
```

## urls.py
アプリケーションのurls.pyは以下のようになります
```urls.py
from django.urls import path, include
from rest_framework_nested import routers

from application.views import UserViewSet, LoginViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")
router.register(r"", LoginViewSet, basename="login")

urlpatterns = [
    path(r"", include(router.urls)),
]

```

## 実際に権限別の挙動を確認してみよう！
まずはログインせずにエンドポイントを操作すると以下のように
```json
{
  "detail": "認証情報が含まれていません。"
}
```
と表示されるのでログイン認証に関してはうまく実装できていることが確認できます
![スクリーンショット 2022-11-27 10.22.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7ee58197-d3bc-43d9-5457-dee73188cac6.png)

今回はfixtureで作成したアルバイトユーザでログインしてみましょう
![スクリーンショット 2022-11-27 10.26.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c7a08246-8d5b-b96b-006d-c4976480c118.png)

今回はログインに成功できたらroleを返すようにしているので成功です
![スクリーンショット 2022-11-27 10.30.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4cf8bccb-229c-e599-3a01-148bb1929ea1.png)

ログインした後にもう一度userのGETを行うと成功です
![スクリーンショット 2022-11-27 10.39.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9b91fd67-0505-0c3f-102a-0264c5ee3820.png)

あたらめてもう一度表を確認します
|  role  |  list  |  retrieve  |  create  |  update  |  partial_update  |  destroy  |
|-----|-----|-----|-----|-----|-----|-----|
|  superuser  |  ○  |  ○  |  ○  |  ○  |  ○  |  ○  |
|  management  |  ○  |  ○  |  ○  |  ○  |  ○  |  -  |
|  general  |  ○  |  ○  |  ○  |  -  |  -  |  -  |
|  part_time  |  ○  |  ○  |  -  |  -  |  -  |  -  |

今回はアルバイトユーザはlistとretrieve(GET、詳細GET)しかできません
実際はcreate(POST)してみると、以下のように権限がなくてできないことが確認できます
![スクリーンショット 2022-11-27 10.41.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/53403fb9-8a1b-1895-f16e-c01a1dc36326.png)
![スクリーンショット 2022-11-27 10.43.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0416e0bd-b15b-f8c2-3ecf-3474dccd16a3.png)

以上のようにロール別で権限を変えることができることが確認できました！

## 記事の紹介
以下の記事も書きましたのでよかったら読んでみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/35c97c95079ecbe80e9d

https://qiita.com/shun198/items/9e4fcb4479385217c323

## 参考

https://dev.classmethod.jp/articles/django-user-org-permission/

https://kamatimaru.hatenablog.com/entry/2020/05/14/220340

https://man.plustar.jp/django/topics/auth/default.html

https://qiita.com/KueharX/items/64e7ae589522687a766b

https://racchai.hatenablog.com/entry/2016/05/27/070000

