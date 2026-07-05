---
title: Django Rest Frameworkでログイン/ログアウト機能を実装してみよう！
tags:
  - Django
  - swagger
  - django-rest-framework
private: false
updated_at: '2024-01-19T15:52:15+09:00'
id: 067e122bb291fed2c839
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
カスタムユーザで
- 社員番号
- パスワード

を使ってログイン/ログアウトを行います
実際の挙動はSwaggerを使って確認します

## 必要な設定ファイルを記述
- models.py
- settings.py
- serilaizers.py
- views.py
- urls.py

に必要な情報を記載します
 - models.py
 - settings.py

は下記の記事を参考に作成してください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```serializers.py
from django.core.validators import RegexValidator
from rest_framework import serializers

from .models import User


class UserSerilaizer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ["id","employee_number","username", "email", "role"]
        read_only_fields = ["id", "created_at","updated_at"]


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

```views.py
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ViewSet

from .models import User
from .serializers import LoginSerializer, UserSerilaizer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerilaizer


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
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
            return JsonResponse(data={"role": user.Role(user.role).name})

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        logout(request)
        return HttpResponse()
```

```アプリケーション/urls.py
from django.urls import path, include
from rest_framework_nested import routers

from application.views import (
    UserViewSet,
)

router = routers.DefaultRouter()
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path(r'', include(router.urls)),
]
```

プロジェクトのurlとSwaggerの設定をしたい場合は下記の記事を参考にしてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

では、一つずつ解説していきます

## serilaizers.py
今回は
- 社員番号
- パスワード

でログインするため、LoginSerilaizerを新規で作成し、
- employee_number
- password

のみを対象にします

### どうしてemployee_numberをオーバーライドするの？
employee_numberはuniqueな値です
loginする際はPOSTリクエストを送るのでデータベースにすでにそのユーザが存在するエラーが発生するのを防ぐために行います
仮にオーバーライドしないと以下のようなエラーが表示されます
```エラー文
{
  "employee_number": [
    "この 社員番号 を持った user が既に存在します。"
  ]
}
```

## views.py
### login
今回は
- 社員番号:00000001
- パスワード:test

のユーザでログインを行います

ご自身でもユーザを入れて検証してみたい方はcreatesuperuserでデータを入れるかfixtureを使ってください

```views.py
from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ViewSet

from .models import User
from .serializers import LoginSerializer, UserSerilaizer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerilaizer


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
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
            return JsonResponse(data={"role": user.Role(user.role).name})
```

今回はPOSTのみを実装したいので`@action`デコレータを使用します
ログインする際はrequest内の情報だけで十分なのでdetail=Falseにします
```python:views.py
@action(detail=False, methods=["POST"])
```
requestのdata内の情報は以下の通りです
```python
print(request.data) # {'employee_number': '00000001', 'password': 'test'}
```
LoginSerializerにrequest.dataが入り、serilaizerの変数に代入されます
```python:views.py
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
```
```python
serializer.is_valid()
```
でバリデーションを行います。これを行わないと以下のエラーが表示されます
```
When a serializer is passed a `data` keyword argument you must call `.is_valid()` before attempting to access the serialized `.data` representation.
You should either call `.is_valid()` first, or access `.initial_data` instead.
```

今回はModelで社員番号は8桁でバリデーションをかけているので例えば
8桁を超える社員番号を入れたとするとバリデーションエラーが発生し、400のレスポンスが返ってきます

![スクリーンショット 2022-11-06 14.28.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1663af26-cdfe-f541-929b-b836f2fb8dcf.png)

![スクリーンショット 2023-12-30 8.55.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2bc91518-f084-dbde-795e-c9fc835b3cae.png)


```python:views.py
        user = authenticate(
            request=request,
            username=serializer.validated_data["employee_number"],
            password=serializer.validated_data["password"],
        )
        if not user:
            return JsonResponse(data={"msg": "社員番号またはパスワードが間違っています"}, status=status.HTTP_400_BAD_REQUEST)
        else:
            login(request, user)
            return JsonResponse(data={"role": user.Role(user.role).name})
```
serializer.dataの中身は以下の通りになっています
```python
print(serializer.data) # {'employee_number': '00000001', 'password': 'test'}
```
`employee_number`と`password`の変数に代入していきます
Djangoには`authenticate`というメソッドでユーザの認証を行うことができます
データベース内にuserが存在しない場合は400とエラーメッセージを返します
![スクリーンショット 2022-11-06 14.48.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/394b5b97-9d0c-27c3-27f2-a889f84ebc47.png)

userが存在する場合はDjangoの`login`メソッドが実行され、`login`が成功します

![スクリーンショット 2022-11-06 14.56.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3ea5d540-6c24-17cf-e3b2-308423d1ff03.png)

今回はJsonResponseとしてroleが返ってくるよう設定します

## authenticationメソッドについて詳しく知りたい方へ
今回は自身で作成した管理者ユーザで認証しているのでModelBackendクラスのauthenticationメソッドを実行しています
usernameとpasswordからユーザを特定し、ユーザが存在したらuserオブジェクトを返します
ユーザが存在しない場合はNoneを返します
また、今回はAbstractUserを継承したUserを作成しているため、AbstractUserで用意しているis_activeがFalseの場合もNoneを返します

```django.contrib.auth.backends.py
class BaseBackend:
    def authenticate(self, request, **kwargs):
        return None


class ModelBackend(BaseBackend):
    """
    Authenticates against settings.AUTH_USER_MODEL.
    """

    def authenticate(self, request, username=None, password=None, **kwargs):
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        if username is None or password is None:
            return
        try:
            user = UserModel._default_manager.get_by_natural_key(username)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
        else:
            if user.check_password(password) and self.user_can_authenticate(user):
                return user

    def user_can_authenticate(self, user):
        """
        Reject users with is_active=False. Custom user models that don't have
        that attribute are allowed.
        """
        return getattr(user, "is_active", True)
```

### is_active=Falseの時もログイン処理を行いたい場合は？
例えば下記みたいにis_active=Falseの時は別のエラーメッセージを出したいケースがあるかと思います

```views.py
class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]

    @action(detail=False, methods=["POST"])
    def login(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # authenticateはUserモデルのis_activeがFalseの場合、Noneを返却する
        user = authenticate(
            request=request,
            username=serializer.validated_data["employee_number"],
            password=serializer.validated_data["password"],
        )

        if user is None:
            return JsonResponse(
                data={"msg": "社員番号、またはパスワードが間違っています。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not user.is_active:
            return JsonResponse(
                data={"msg": "管理者に問い合わせてください。"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        login(request, user)
        return JsonResponse(data={"role": user.Role(user.role).name})
```

その場合はDjangoのAllowAllUsersModelBackendクラスを使用します
このクラスを使用することでuser_can_authenticateメソッドが実行する際にis_active=Falseでもuserオブジェクトを返します
```django.contrib.auth.backends.py
class AllowAllUsersModelBackend(ModelBackend):
    def user_can_authenticate(self, user):
        return True
```

AllowAllUsersModelBackendを使用する際はsettings.pyに以下のように記載します
```settings.py
AUTHENTICATION_BACKENDS = ["django.contrib.auth.backends.AllowAllUsersModelBackend"]
```


## logout
```python:views.py
    @action(methods=["POST"], detail=False)
    def logout(self, request):
        logout(request)
        return HttpResponse()
```
`logout`は`login`と比べると簡単でDjangoの`logout`メソッドを使って実装します
![スクリーンショット 2022-11-06 14.59.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a25e72e1-91cd-fee6-2408-9a18969a380a.png)

## まとめ
Djangoの
- is_valid
- authenticate
- login
- logout

メソッドを使うと楽に実装できました
しかし、現状の実装だけではログインしてもしなくてもAPIを使用できてしまっているので
下記のようにPermissionを実装するとログインしたユーザ以外はAPIを使うことができなくなります
興味がある方は見ていただけると幸いです

https://qiita.com/shun198/items/e3349860ce10e3bba15a

## 記事の紹介
以下の記事も書いたのでよかったら読んでみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/9e4fcb4479385217c323

https://qiita.com/shun198/items/cdc8eaa457c1dc202e1b

## 参考

https://docs.djangoproject.com/en/4.1/topics/auth/default/

https://github.com/django/django/blob/main/django/contrib/auth/backends.py


