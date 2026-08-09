---
title: Django Rest FrameworkでDockerとMailCatcherを使ってメール送信を行おう！
tags:
  - Django
  - Docker
  - mailcatcher
  - django-rest-framework
  - docker-compose
private: false
updated_at: '2026-08-10T07:49:18+09:00'
id: 35c97c95079ecbe80e9d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- docker-compose.ymlを使用
- ある程度Dockerの知識を持っていること
- メール送信する際にSwaggerを使用します

## mailcatcherとは
> MailCatcher runs a super simple SMTP server which catches any message sent to it to display in a web interface. 

公式ドキュメントに記載されている通り簡易的なSMTPサーバでMailCatcherに送信されたメールをWebインターフェイス(Webブラウザ)に表示させることができます
本番環境ではAWSのSESを使うのでローカルでメール送信テストを行いたいときはMailCatcherを使ってみましょう

## SMTP(メール)サーバ用のコンテナを作ろう！
> Run mailcatcher, set your favourite app to deliver to smtp://127.0.0.1:1025 instead of your default SMTP server, then check out http://127.0.0.1:1080 to see the mail that's arrived so far.

公式ドキュメントに記載されている通り
MailCatcherのイメージを指定して
- SMTP用の1025番ポート
- Webブラウザで閲覧する用の1080番ポート
 
の2種類のポートを解放します
```yml:docker-compose.yml
  mail:
    container_name: mail
    image: schickling/mailcatcher
    ports:
      - "1080:1080"
      - "1025:1025"
```

settings.pyに以下の設定を記載します
検証用のため、EMAIL_HOST_USERとEMAIL_HOST_PASSWORDは空白にします
```settings.py
# Djangoのメールの設定
EMAIL_HOST = 'mail'
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''
# SMTPの1025番ポートを指定
EMAIL_PORT = 1025
# 送信中の文章の暗号化をFalseにします
EMAIL_USE_TLS = False
```

## MailCatcherにアクセスしてみよう！
コンテナを起動し、`http://127.0.0.1:1080`にアクセスし、以下のMailCatcherの画面が表示されたら成功です

![スクリーンショット 2022-11-06 17.27.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5b54a536-ce13-6e78-5244-b714a3fff3c3.png)

## メールを送る設定をしてみよう！
今回は新規ユーザに招待メールを送るという簡単な機能を実装します
以下のファイルにコードを記載していきます
- models.py
- serializers.py
- views.py
- emails.py
- templateファイル群

に以下のコードを記載していきます

### models.py
システムユーザのModelを作成します
システムユーザの作成方法について知りたい方は以下の記事を参考にしてください

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
        """

        MANAGEMENT = 0, "管理者"
        GENERAL = 1, "一般"

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
        default=Role.MANAGEMENT,
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


class UserInvitation(models.Model):
    """ユーザ招待用テーブルに対応するモデルクラス"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="システムユーザID",
    )
    token = models.CharField(
        max_length=255,
        db_comment="ユーザ招待用メールURL用トークン",
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
        related_name="user_invitation",
        db_comment="社員テーブル外部キー",
    )
    is_used = models.BooleanField(
        default=False,
        db_comment="使用有無",
    )

    class Meta:
        db_table = "Invitation"
        db_table_comment = "ユーザ招待用"
```

### serializers.py
EmailのSerilaizerを作成します
```serializers.py
from rest_framework import serializers


class LoginSerializer(serializers.ModelSerializer):
    """ログイン用シリアライザ"""

    employee_number = serializers.CharField(max_length=255)

    class Meta:
        model = User
        fields = ["employee_number", "password"]

        
class InviteUserSerializer(serializers.ModelSerializer):
    """ユーザ招待用シリアライザ"""

    def create(self, validated_data, created_by, updated_by):
        return User.objects.create_user(
            created_by=created_by, updated_by=updated_by, **validated_data
        )

    class Meta:
        model = User
        fields = [
            "employee_number",
            "username",
            "role",
            "email",
        ]
```

### views.py
actionデコレータを使ってメール送信機能を実装します

```views.py
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet
from rest_framework.viewsets import ViewSet

from .models import User
from .serializers import LoginSerializer, UserSerilaizer, InviteUserSerializer
from .emails import send_welcome_email


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()

    def get_serializer_class(self):
        if self.action == "invite_user":
            return EmailSerializer
        else:
            return UserSerilaizer

    @action(detail=False, methods=["POST"])
    def invite_user(self, request):
        """指定したメールアドレス宛へユーザの招待メールを送る

        Args:
            request: リクエスト

        Returns:
            HttpResponse
        """
        # Userの新規登録と招待用トークンを作成する
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.create(
            serializer.validated_data,
            created_by=request.user,
            updated_by=request.user,
        )
        token = secrets.token_urlsafe(64)
        expiry = timezone.now() + timedelta(days=1)
        UserInvitation.objects.create(token=token, user=user, expiry=expiry)
        # 今回はフロントエンドのローカル環境のオリジンを指定
        base_url = "localhost:3000"
        # 初回登録用のURLへ遷移
        url = base_url + "/verify-user/" + token
        send_invitation_email(
            email=user.email,
            url=url,
        )
        return JsonResponse(
            data={"msg": "招待メールを送信しました"},
            status=status.HTTP_200_OK,
        )

```

### emails.py
メール送信用のメソッドを作成します
今回はDjangoのEmailMultiAlternativesを使ってメール送信機能を実装します
EmailMultiAlternativesを使うとHTMLとテキスト両方のバージョンでメールを送信することができます

https://docs.djangoproject.com/ja/5.0/topics/email/#sending-alternative-content-types

```emails.py
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string


def send_invitation_email(email, url):
    plaintext = render_to_string(
        "invite_user_email.txt",
        {
            "email": email,
            "url": url,
        },
    )
    html_text = render_to_string(
        "invite_user_email.html",
        {
            "email": email,
            "url": url,
        },
    )
    
    msg = EmailMultiAlternatives(
        subject="アカウント登録のお知らせ",
        body=plaintext,
        from_email=None,
        to=[email],
        alternatives=[(html_text, "text/html")],
    )

    # 送信
    msg.send()
```

### templateファイル群
今回は
- invite_user_email.html
- invite_user_email.txt

の2種類を作成します
```welcome_email.html
<pre>

下記URLへ24時間以内にアクセスしてアカウントの本登録をお願いします。
▼アカウント認証URL
<a href={{url}}>{{ url }}</a>
    
</pre>
```

```welcome_email.txt
下記URLへ24時間以内にアクセスしてアカウントの本登録をお願いします。
▼アカウント認証URL
{{ url }}
```

## メールを送信してみよう！
emailを入力してPOSTします
![スクリーンショット 2024-01-09 9.11.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dad5172b-1094-918d-0d5c-9575a45c51b2.png)

![スクリーンショット 2024-01-09 9.11.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c796be30-60ec-a971-5400-0853f45d3209.png)

`http://127.0.0.1:1080`にアクセスし、メールが受信できたら成功です

![スクリーンショット 2024-01-09 9.10.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/20a8a54d-c6bb-01c1-142e-f99004063943.png)

## メールが送信できたかどうかテストコードを書いてみたい
Pytestでメール送信のテストコードを書きたい方はこちらの記事を書きました

https://qiita.com/shun198/items/318847d7e0be59108f22

## 記事の紹介
以下の記事も書きましたのでよかったら読んでみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/067e122bb291fed2c839

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

## 参考
https://mailcatcher.me/

https://book-reviews.blog/send-email-on-local-development-environment-on-Django/

https://qiita.com/pocari/items/de0436c39ffc65647cf0

https://hub.docker.com/r/sj26/mailcatcher

https://note.com/takuya814/n/n48475f7d9583

https://sendgrid.kke.co.jp/docs/Integrate/Frameworks/django.html

https://kaminashi-developer.hatenablog.jp/entry/mailhog
