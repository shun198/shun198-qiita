---
title: Django内でパスワードのカスタムバリデーションを作成する方法
tags:
  - Python
  - Django
  - 正規表現
private: false
updated_at: '2024-01-07T09:03:31+09:00'
id: 024afa96657937247313
organization_url_name: null
slide: false
---
## 概要
ユーザのパスワードなどDjango内で独自のバリデーションを作成する方法について解説したいと思います

## ファイル構成
今回作成するファイルの構成は以下の通りです

```
tree
・
└── application
    ├── models.py
    ├── utils
    │   ├── __init__.py
    │   └── password_validator.py
    └── project
        └── settings.py
```

- バリデーションを記載するファイル(今回はpassword_validator.py)
- settings.py
- models.py(カスタムユーザの作成)

に設定を記載していきます

## password_validator.py
re.fullmatch()関数を使って指定した正規表現と完全に一致するかどうかを調べます
```application/password_validator.py
import re

from rest_framework.exceptions import ValidationError


class PasswordValidator:
    def validate(self, password, user=None):
        REX = r"(?=.*\d)(?=.*[a-z])(?=.*[A-Z])(?=.*[~!@#$%^&*_\-+=`|(){}\[\]:;\"\'<>,.?/]).{8,64}"
        result = re.fullmatch(REX, password)
        if not result:
            raise ValidationError("英大小文字、数字、または特殊文字が含まれていません")
```

## 正規表現の書き方
正規表現の書き方は以下の通りです

|正規表現|説明|
|--|--|
|?=.*|一致するかどうか|
|（\d）|少なくとも1つの数字|
|（[a-z]）|少なくとも1つの小文字のアルファベット|
|（[A-Z]）|少なくとも1つの大文字のアルファベット|
|\*[~!@#$%^&*_\-+=`\|(){}\[\]:;\"\'<>,.?/]|少なくとも1つの特殊文字|
|{8,64}|全体で8文字以上、64文字以下（.{8,64}）|


## settings.py
AUTH_PASSWORD_VALIDATORSに該当するクラス名もしくはファイル名を記載します

```project/settings.py
AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
    # 以下にカスタムバリデーションのクラス名を記載
    {
        "NAME": "application.utils.password_validator.PasswordValidator",
    },
]
```

## models.py
システムユーザ用のModelを作成します
詳細については以下の記事を参照してください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```application/models.py
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

## 実際に検証してみよう！
```
python manage.py createsuperuser
```
を実行します

以下のように入力していきます
今回は数字だけのパスワードを入力します
```
社員番号: 00000001
Email: test@gmail.com
Password: 11111111
Password (again): 11111111
```

パスワード内に英大小文字、特殊文字が含まれていないため、以下のようにValidationErrorが表示されたら成功です

```
File "/code/application/utils/password_validator.py", line 51, in validate
    raise ValidationError("英大小文字、数字、または特殊文字が含まれていません")
rest_framework.exceptions.ValidationError: [ErrorDetail(string='英大小文字、数字、または特殊文字が含まれていません', code='invalid')]
```

他のパターンも気になる方は以下のようにテストコードで検証してみましょう

```application/tests/test_password_validation.py
import pytest

from application.utils.validator import PasswordValidator
from rest_framework.exceptions import ValidationError

@pytest.mark.django_db()
class TestPasswordValidator:
    def test_user_password_does_not_contain_non_alphanumeric_characters(self):
        """異常/パスワードに不英数文字が含まれていない"""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(self, password="TestingUsr01")

    def test_user_password_does_not_contain_numbers(self):
        """異常/パスワードに数字が含まれていない"""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(self, password="T@stingUsr")

    def test_user_password_does_not_contain_uppercase_letters(self):
        """異常/パスワードに大文字が含まれていない"""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(self, password="t@stingusr01")

    def test_user_password_is_less_than_7_characters(self):
        """異常/パスワードが7文字以下"""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(self, password="T@stus1")

    def test_user_password_is_65_characters_or_longer(self):
        """異常/パスワードが65文字以上"""
        with pytest.raises(ValidationError):
            PasswordValidator.validate(self, password="a" * 65)
```

## 参考
https://docs.djangoproject.com/en/4.0/topics/auth/passwords/#password-validation

https://sixfeetup.com/blog/custom-password-validators-in-django

https://docs.python.org/ja/3/library/re.html

https://marsquai.com/745ca65e-e38b-4a8e-8d59-55421be50f7e/05f253f8-c11b-4c91-8091-989eb2600a7b/de4d464b-1e55-47f4-b993-85dad837dcab/#h3-cc2798cb-095f-4e6a-8be3-fb9102723878-d8681841-d767-46b5-ad9b-5c608b03478e

https://ai-inter1.com/python-regex/

https://qiita.com/luohao0404/items/7135b2b96f9b0b196bf3
