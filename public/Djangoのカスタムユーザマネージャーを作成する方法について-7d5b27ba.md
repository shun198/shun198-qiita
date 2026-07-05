---
title: Djangoのカスタムユーザマネージャーを作成する方法について
tags:
  - Django
  - django-rest-framework
private: false
updated_at: '2024-01-09T16:39:13+09:00'
id: 7d5b27ba322cbf39ff23
organization_url_name: null
slide: false
---
## 概要
独自でシステムユーザを作成する際にカスタムユーザマネージャーも作成するのが一般的です
カスタムユーザマネージャーを使うことでユーザ作成時の処理をoverrideできるので便利です
今回はカスタムユーザマネージャーの作成方法について解説します

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
│   ├── managers.py
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   └── views.py
└── project
    └── settings.py

```

## 実装
以下のファイルを作成します
- models.py
- serializers.py
- managers.py

### カスタムユーザModel
カスタムユーザModelを作成します
詳細について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

また、カスタムユーザマネージャーを設定する際は以下の記述が必要です
```
# 作成したカスタムユーザマネージャーのクラス名を指定
objects = UserManager()
```

```models.py
import uuid

from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models

from application.managers import UserManager


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

    objects = UserManager()
    """Userモデルクラスとシステム利用者を作成する為のクラスを紐付ける"""

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

```

### Serializer
今回はユーザ招待用のSerializer内にユーザを作成する処理を追加します
User.objects.create_userメソッドを後ほど作成するカスタムユーザマネージャー内に実装した場合、実行されます

```serializers.py
from django.contrib.auth.models import Group
from rest_framework import serializers

from application.models import User


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
            "group",
            "email",
        ]

    def validate_group(self, value):
        try:
            data = Group.objects.get(name=value)
        except Group.DoesNotExist:
            raise serializers.ValidationError("指定された権限は存在しません。")
        return data
```

### カスタムユーザマネージャー
ここからカスタムユーザマネージャーを作成します
今回はBaseUserManagerを継承し、ユーザを作成したら初回パスワードを社員番号にする独自処理を実装します
まず、リクエスト内のグループ名からグループ名を取得します
userのオブジェクトを作成し、パスワードを社員番号にした後、saveメソッドを実行すれば初回パスワードが社員番号のシステムユーザの完成です

```managers.py
from django.contrib.auth.models import BaseUserManager, Group


class UserManager(BaseUserManager):
    """システム利用者を作成する為のクラス"""

    use_in_migrations = True

    def create_user(
        self,
        username: str,
        employee_number: str,
        group: Group,
        **extra_fields,
    ):
        """システム利用者を作成

        Args:
            name (str): システム利用者名
            employee_number (str): 社員番号
            group (UserGroup): システム利用者権限
        Returns:
            作成したシステム利用者
        """

        group, _ = Group.objects.get_or_create(name=group.name)

        user = self.model(
            username=username,
            employee_number=employee_number,
            group=group,
            **extra_fields,
        )
        # 初期バスワードは社員番号
        user.set_password(employee_number)
        user.save(using=self._db)

        return user

```

## まとめ
view内にユーザを作成するロジックを書くと複雑になるのでカスタムユーザマネージャーを使って処理をマネージャーに任せるようにすると管理が楽だと思うので積極的に使っていいと思います

## 参考
https://github.com/django/django/blob/main/django/contrib/auth/models.py
