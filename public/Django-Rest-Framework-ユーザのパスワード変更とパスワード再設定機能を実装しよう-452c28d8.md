---
title: '[Django Rest Framework] ユーザのパスワード変更とパスワード再設定機能を実装しよう！'
tags:
  - Django
  - mailcatcher
  - django-rest-framework
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: 452c28d89400e97e1866
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はDjango Rest Frameworkを使って
- パスワードを変更する
- パスワード再設定用メールを送信する
- パスワード再設定を行う

APIの作成を行います

## 前提
- Djangoのプロジェクトを作成済み


## ディレクトリ構成
```
tree
・
├── application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── emails.py
│   ├── fixtures
│   │   └── fixture.json
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── templates
│   │   ├── reset_password_email.html
│   │   └── reset_password_email.txt
│   ├── urls.py
│   └── views.py
└── project
    └── settings.py
```

## メールの設定
### MailCatcherの設定
MailCatcherという仮想のSMTPサーバの設定を行います
詳細は以下の記事を参考にしてください

https://qiita.com/shun198/items/35c97c95079ecbe80e9d

```docker-compose.yml
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

  mail:
    container_name: mail
    image: schickling/mailcatcher
    ports:
      - '1080:1080'
      - '1025:1025'

volumes:
  db_data:
  static:
```

## Djangoの設定
settings.pyにMailCatcherとSESの設定を行います

```settings.py
if DEBUG:
    # メールの設定
    EMAIL_HOST = "mail"
    EMAIL_HOST_USER = ""
    EMAIL_HOST_PASSWORD = ""
    EMAIL_PORT = 1025
    EMAIL_USE_TLS = False
else:
    # SESの設定
    EMAIL_BACKEND = "django_ses.SESBackend"
    AWS_DEFAULT_REGION_NAME = os.environ.get("AWS_DEFAULT_REGION_NAME")
    AWS_SES_REGION_ENDPOINT = os.environ.get("AWS_SES_REGION_ENDPOINT")
    DEFAULT_FROM_EMAIL = os.environ.get("DEFAULT_FROM_EMAIL")
```

.envファイルに必要な環境変数の設定を行います
```.env
AWS_DEFAULT_REGION_NAME=ap-northeast-1
AWS_SES_REGION_ENDPOINT=email.ap-northeast-1.amazonaws.com
DEFAULT_FROM_EMAIL=example.co.jp
BASE_URL=http://localhost
```

## ユーザのパスワード変更機能
### テストデータの作成
パスワード変更APIを検証するために以下のようにユーザのテストデータを作成します
fixture内のパスワードは全て`test`です

```fixtures.json
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
    },
]
```

### Model
- システムユーザ
- システムユーザのパスワード変更用トークンを管理する

用のModelを作成します
システムユーザのModelの詳細は以下の記事を参考にしてください

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


class UserResetPassword(models.Model):
    """ユーザパスワード再設定テーブルに対応するモデルクラス"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="システムユーザID",
    )
    token = models.CharField(
        max_length=255,
        db_comment="パスワード設定メールURL用トークン",
    )
    expiry = models.DateTimeField(
        null=True,
        default=None,
        db_comment="有効期限",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name="user_password_reset",
        db_comment="ユーザテーブル外部キー",
    )
    is_used = models.BooleanField(
        default=False,
        db_comment="使用有無",
    )

    class Meta:
        db_table = "PasswordReset"
        db_table_comment = "ユーザパスワード再設定"
```

### Serializer
- パスワード変更用
- パスワード再設定用
- トークンの有効期限の確認用

のSerializerを作成します
Serializerのvalidateメソッドを作成し、新規パスワードと確認用パスワードが一致するか確認し、
もし一致してなかったらValidationErrorをraiseします
また、Djangoのvalidate_passwordメソッドを使って新規パスワードのバリデーションを行います
独自でValidationを設定していなかったら
```
get_default_password_validators()
```
メソッドからDjangoのデフォルトのパスワードのバリデーションを使用します

```serializers.py
class ChangePasswordSerializer(serializers.Serializer):
    """パスワード変更用Serializer"""

    current_password = serializers.CharField(max_length=255)
    """現在のパスワード"""
    new_password = serializers.CharField(max_length=255)
    """新規パスワード"""
    confirm_password = serializers.CharField(max_length=255)
    """新規パスワード再確認"""

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("新規パスワードと確認パスワードが違います")
        validate_password(data["new_password"])
        return data

        
class ResetPasswordSerializer(serializers.Serializer):
    """パスワード再設定用シリアライザ"""

    token = serializers.CharField(max_length=255)
    """パスワード再設定メールURL用トークン"""
    new_password = serializers.CharField(max_length=255)
    """新規パスワード"""
    confirm_password = serializers.CharField(max_length=255)
    """新規パスワード再確認"""

    def validate(self, data):
        if data["new_password"] != data["confirm_password"]:
            raise serializers.ValidationError("新規パスワードと確認パスワードが違います")
        validate_password(data["new_password"])
        return data


class CheckTokenSerializer(serializers.Serializer):
    """トークンが有効であるか確認するSerializer"""

    token = serializers.CharField(max_length=255)
    """トークン"""
```

```django/contrib/auth/password_validation.py
def validate_password(password, user=None, password_validators=None):
    """
    Validate that the password meets all validator requirements.

    If the password is valid, return ``None``.
    If the password is invalid, raise ValidationError with all error messages.
    """
    errors = []
    if password_validators is None:
        password_validators = get_default_password_validators()
    for validator in password_validators:
        try:
            validator.validate(password, user)
        except ValidationError as error:
            errors.append(error)
    if errors:
        raise ValidationError(errors)
```

### Views
- change_password(パスワード変更)
- check_reset_password_token(パスワード再設定用トークンの有効期限確認)
- reset_password(パスワード再設定)
- send_reset_password_email(パスワード再設定用メール送信)

用のAPIを作成します

```views.py
import os, secrets, logging
from datetime import timedelta

from django.db import DatabaseError
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from application.emails import send_reset_email
from application.models import User, UserResetPassword
from application.serializers import (
    ChangePasswordSerializer,
    CheckTokenSerializer,
    ResetPasswordSerializer,
    SendResetPasswordEmailSerializer,
    UserSerializer,
)


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    logger = logging.getLogger(__name__)

    def get_serializer_class(self):
        match self.action:
            case "change_password":
                return ChangePasswordSerializer
            case "check_reset_password_token":
                return CheckTokenSerializer
            case "reset_password":
                return ResetPasswordSerializer
            case "send_reset_password_email":
                return SendResetPasswordEmailSerializer
            case _:
                return UserSerializer

    @action(methods=["post"], detail=False)
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = request.user

        if not user.check_password(
            serializer.validated_data["current_password"]
        ):
            return JsonResponse(
                data={"msg": "現在のパスワードが違います"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        update_session_auth_hash(request, user)
        return HttpResponse()

    @action(detail=False, methods=["POST"])
    def send_reset_password_email(self, request):
        """指定したメールアドレス宛へパスワード再設定メールを送る

        Args:
            request: リクエスト

        Returns:
            HttpResponse
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
            )
        except User.DoesNotExist as e:
            logger.error(e)
            return JsonResponse(
                data={},
            )
        if not user.is_active or not user.is_verified:
            logger.warning("ユーザは有効化済みまたは認証済みです")
            return JsonResponse(
                data={},
            )
        try:
            token = secrets.token_urlsafe(64)
            expiry = timezone.now() + timedelta(minutes=30)
            UserResetPassword.objects.create(
                token=token,
                user=user,
                expiry=expiry,
            )
        except DatabaseError as e:
            logger.error(e)
            return JsonResponse(
                data={},
            )
        base_url = django_settings.BASE_URL
        # 初回登録用のURLへ遷移
        url = base_url + "/reset-password/" + token
        send_reset_email(
            email=user.email,
            url=url,
        )
        return JsonResponse(
            data={},
        )

    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        """パスワード再設定用API

        Args:
            request: リクエスト

        Returns:
            JsonResponse
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_password = self.check_reset_password(serializer.data["token"])
        if reset_password is None:
            return JsonResponse(
                data={"msg": "有効期限切れのリンクです。管理者に再送信を依頼してください。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = reset_password.user
        user.set_password(serializer.data["password"])
        reset_password.is_used = True
        reset_password.save()
        user.save()
        return JsonResponse(data={"msg": "パスワードの再設定が完了しました"})

    @action(detail=False, methods=["post"])
    def check_reset_password_token(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(data={"check": False})

        check = self._check_reset_password(serializer.data["token"]) != None
        return JsonResponse(data={"check": check})

    def _check_reset_password(self, token):
        """パスワード再設定用トークンを確認する

        Args:
            token : ユーザ認証用トークン

        Returns:
            Union[
                UserResetPasswordオブジェクト,
                None
            ]
        """
        try:
            reset_password = UserResetPassword.objects.select_related(
                "user"
            ).get(
                token=token,
                is_used=False,
            )
        except:
            return None

        if reset_password.expiry < timezone.now() or reset_password.is_used:
            return None
        return reset_password

    def get_permissions(self):
        if self.action == "send_reset_password_email":
            permission_classes = [AllowAny]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]
```

1つずつ解説していきます

### パスワード変更
パスワード変更用のAPIを作成します
現在のパスワードが間違っているかどうかはAbstractBaseUserクラスのcheck_passwordメソッドを使って確認します
パスワードが一致することを確認したらAnonymousUserクラスのset_passwordメソッドを使って更新します
パスワード変更後もセッションIDを変更しつつ、セッションを維持するためにupdate_session_auth_hashメソッドを使います

```views.py
    @action(methods=["post"], detail=False)
    def change_password(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(
            serializer.validated_data["current_password"]
        ):
            return JsonResponse(
                data={"msg": "現在のパスワードが違います"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        user.set_password(serializer.validated_data["new_password"])
        user.save()
        update_session_auth_hash(request, user)
        return HttpResponse()
```

```django/contrib/auth/base_user.py
class AbstractBaseUser(models.Model):
    def check_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])
```

```django/contrib/auth/models.py
class AnonymousUser:
    id = None
    pk = None
    username = ""
    is_staff = False
    is_active = False
    is_superuser = False
    _groups = EmptyManager(Group)
    _user_permissions = EmptyManager(Permission)


    def set_password(self, raw_password):
        raise NotImplementedError(
            "Django doesn't provide a DB representation for AnonymousUser."
        )
```

```django/contrib/auth/__init__.py
def update_session_auth_hash(request, user):
    """
    Updating a user's password logs out all sessions for the user.

    Take the current request and the updated user object from which the new
    session hash will be derived and update the session hash appropriately to
    prevent a password change from logging out the session from which the
    password was changed.
    """
    request.session.cycle_key()
    if hasattr(user, "get_session_auth_hash") and request.user == user:
        request.session[HASH_SESSION_KEY] = user.get_session_auth_hash()
```

### パスワード再設定メール送信
パスワードを再設定する際のメール送信機能を行います
まず、メールアドレスのバリデーションを行います
メールアドレスから該当するユーザを取得し、再設定用のトークンを作成します
今回はトークンの有効期限を30分とします
トークン作成後、再設定用のurlが記載されたメールを送信します
不正アクセスするユーザによってメールアドレスが登録されているか特定されないために今回はあえて200を返します

```views.py
    @action(detail=False, methods=["POST"])
    def send_reset_password_email(self, request):
        """指定したメールアドレス宛へパスワード再設定メールを送る

        Args:
            request: リクエスト

        Returns:
            HttpResponse
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(
                email=serializer.validated_data["email"],
            )
        except User.DoesNotExist as e:
            logger.error(e)
            return JsonResponse(
                data={},
            )
        if not user.is_active or not user.is_verified:
            logger.warning("ユーザは有効化済みまたは認証済みです")
            return JsonResponse(
                data={},
            )
        try:
            token = secrets.token_urlsafe(64)
            expiry = timezone.now() + timedelta(minutes=30)
            UserResetPassword.objects.create(
                token=token,
                user=user,
                expiry=expiry,
            )
        except DatabaseError:
            return JsonResponse(
                data={},
            )
        base_url = django_settings.BASE_URL
        url = base_url + "/reset-password/" + token
        send_reset_email(
            email=user.email,
            url=url,
        )
            return JsonResponse(
                data={},
            )
```

### パスワード再設定用トークンの有効期限の確認
メール内のパスワード再設定URLへアクセスする前にトークンが有効かどうか確認するAPIを作成します
トークンの有効期限、すでに使用されているかを確認し、
有効であれば
```
{"check": True}
```
無効であれば
```
{"check": False}
```
を返します

```views.py
    @action(detail=False, methods=["post"])
    def check_reset_password_token(self, request):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(data={"check": False})

        check = self._check_reset_password(serializer.data["token"]) != None
        return JsonResponse(data={"check": check})

    def _check_reset_password(self, token):
        """パスワード再設定用トークンを確認する

        Args:
            token : パスワード再設定用トークン

        Returns:
            Union[
                UserResetPasswordオブジェクト,
                None
            ]
        """
        try:
            reset_password = UserResetPassword.objects.select_related(
                "user"
            ).get(
                token=token,
                is_used=False,
            )
        except:
            return None

        if reset_password.expiry < timezone.now() or reset_password.is_used:
            return None
        return reset_password
```

### パスワード再設定
メールに添付されたurlへアクセスする際にフロント側からトークンの値を受け取ります
Serializerを使ったバリデーションに成功した後、ユーザを認証する際にトークンが存在するか確認し、なければ404を返します
トークンの有効期限用のAPIを作成したので不要かと思われますが例えば有効期限ギリギリにアクセスし、有効期限が過ぎてから認証しようとしてしまうことなど、有効期限を確認するAPIでは検知できない不備を防ぐために記載しております
トークンが有効であることを確認した後、Userテーブル内に新しいパスワードを設定し、テーブル内の有効化フラグをTrueにします

```views.py
    @action(detail=False, methods=["post"])
    def reset_password(self, request):
        """パスワード再設定用API

        Args:
            request: リクエスト

        Returns:
            JsonResponse
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        reset_password = self.check_reset_password(serializer.data["token"])
        if reset_password is None:
            return JsonResponse(
                data={"msg": "有効期限切れのリンクです。管理者に再送信を依頼してください。"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user = reset_password.user
        user.set_password(serializer.data["password"])
        reset_password.is_used = True
        reset_password.save()
        user.save()
        return JsonResponse(data={"msg": "パスワードの再設定が完了しました"})
```

## メール送信機能
メール送信機能を実装します
メール送信の際はEmailMultiAlternativesクラスを使ってhtmlとtxtの両方のバージョンのメールを送信できるように設定できます

https://docs.djangoproject.com/en/4.2/topics/email/

```emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_reset_email(email, url):
    plaintext = render_to_string(
        "reset_password_email.txt",
        {
            "email": email,
            "url": url,
        },
    )
    html_text = render_to_string(
        "reset_password_email.html",
        {
            "email": email,
            "url": url,
        },
    )
    msg = EmailMultiAlternatives(
        subject="パスワード再設定のお知らせ",
        body=plaintext,
        from_email=None,
        to=[email],
        alternatives=[(html_text, "text/html")],
    )

    # 送信
    msg.send()

```

メールの本文は以下の通りurlを入れます
```templates/invite_user_email.txt
下記URLへ30分以内にアクセスしてパスワードの再設定をお願いします。
▼パスワード再設定URL
{{ url }}
```

```templates/invite_user_email.html
<pre>

下記URLへ30分以内にアクセスしてパスワードの再設定をお願いします。
▼パスワード再設定URL
<a href={{url}}>{{ url }}</a>
        
</pre>
```

### urls.py
APIのパスを作成します

```urls.py
from django.urls import include, path
from rest_framework_nested import routers

from application.views import UserViewSet

router = routers.DefaultRouter()
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    path(r"", include(router.urls)),
]
```

## 実際にパスワードの変更・再設定をしてみよう！
### パスワードの変更
- 現在のパスワード(fixtureのパスワード)
- 新しいパスワード
- 確認用パスワード

をrequestに入れてPOSTします

![スクリーンショット 2023-10-28 20.27.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bedbf75c-5f25-a095-3d8e-6b16cb795a87.png)

以下のようにステータスコードが200になったら成功です

![スクリーンショット 2023-10-28 20.29.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/672c17e0-9400-fa25-c9bf-83c567083f37.png)

### パスワードの再設定
- メールアドレス(fixtureに記載されたもの)

をrequestに入れてPOSTします

![スクリーンショット 2023-10-28 20.33.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ebc21ef7-f43d-99d4-5aef-58e72dedae62.png)

以下のメッセージが表示されたら成功です

![スクリーンショット 2023-10-28 20.36.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b147660e-5745-1cd9-32b7-9f9f638464a1.png)

MailCatcherにTokenが埋め込まれたパスワード再設定メールが受信されていることを確認しました

![スクリーンショット 2024-01-09 9.55.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/44c99e5a-4092-cc84-7e91-c605bfc42f5a.png)

- URL内のトークン
- 新しいパスワード
- 確認用パスワード

をrequestに入れてPOSTします
![スクリーンショット 2023-10-28 20.39.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cd4543e2-e6e6-4ef8-52b0-41ecddea3ca5.png)

以下のメッセージが表示されたら成功です
![スクリーンショット 2023-10-28 20.39.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/841ec6e7-8cbc-30db-29d4-32dd684b5ff9.png)

以上です
