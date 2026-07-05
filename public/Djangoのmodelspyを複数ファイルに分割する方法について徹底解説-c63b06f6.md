---
title: Djangoのmodels.pyを複数ファイルに分割する方法について徹底解説
tags:
  - Django
  - MySQL
  - model
private: false
updated_at: '2023-02-20T19:13:59+09:00'
id: c63b06f6d47329844e04
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Modelが肥大化してしまった際は1つのmodels.pyを分割したい場面があるかと思います
今回はmodels.pyを複数のファイルに分割する方法について解説したいと思います

## 前提
- DBはMySQLを使用

## ディレクトリ構成
以下のような構成でModelを分割します
今回はmodelsフォルダ内に
- User(カスタムユーザ)
- Customer(お客様)

のカテゴリ別で作成していきます

```
❯ tree
.
├── application
│   └── models
│       ├── __init__.py
│       ├── customer.py
│       └── user.py
└── project
    └── settings.py
```

## Modelを分割しよう
### User
今回はカスタムユーザ専用のModelをuser.pyとして作成します
カスタムユーザの詳細については本記事では解説しませんので以下を参照してください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```applicaton/models/user.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


# カスタムユーザクラスを定義
class User(AbstractUser):
    username_validator = UnicodeUsernameValidator()

    class Role(models.IntegerChoices):
        MANAGEMENT = 0
        GENERAL = 1
        PART_TIME = 2

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    groups = None
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r"^[0-9]{8}$")],
        max_length=8,
        # 管理者のログイン画面で社員番号と表示される
        verbose_name="社員番号",
    )
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    email = models.EmailField(max_length=254, unique=True)
    role = models.PositiveIntegerField(
        choices=Role.choices, default=Role.PART_TIME
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # デフォルトはusernameだが今回は社員番号を指定
    USERNAME_FIELD = "employee_number"
    # uniqueのemailとusernameを指定
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"

    def __str__(self):
        return self.username
```

カスタムユーザを作成後は以下をsettings.pyに記述します
application内のUserクラスを参照しているのでmodels.pyに記載していて別ファイルに移動させたとしても下記を変更する必要がありません
```settings.py
AUTH_USER_MODEL = "application.User"
```

### Customer
下記のようにCustomerのModelを作成します

```application/models/customer.py
import uuid

from django.db import models

from application.models.user import User


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kana = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    birthday = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="%(class)s_created_by"
    )
    updated_by = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name="%(class)s_updated_by"
    )
    
    class Meta:
        db_table = "Customer"
```

## Migrationの実行
上記のようにModelを作成後に
```
python manage.py makemigrations
```
した場合、下記のように参照エラーが発生してしまいます
```
django.core.exceptions.ImproperlyConfigured: AUTH_USER_MODEL refers to model 'application.User' that has not been installed
```

そのため、modelsフォルダ内に__init__.pyを作成してカスタムユーザのModelをimportする記述が必要になります
また、カスタムユーザ以外に作成したModelも同様にimportしないとMigrationファイルを作成できないので以下のように記述します

```application/models/__init__.py
from application.models.customer import User
from application.models.user import Customer
```

## DB内のテーブルを確認してみよう
まずはMigrationを行います
```
python manage.py makemigrations
python manage.py migrate
```

今回はMySQLを使用しているのでDB内にログインしてテーブルが作成されているか確認します
下記のようにCustomerとUserテーブルが作成されていて定義も例の通りになっていたら成功です

### テーブル一覧
```
mysql> show tables;
+------------------------+
| Tables_in_django-db    |
+------------------------+
| Customer               |
| User                   |
| User_user_permissions  |
| auth_group             |
| auth_group_permissions |
| auth_permission        |
| django_admin_log       |
| django_content_type    |
| django_migrations      |
| django_ses_sesstat     |
| django_session         |
+------------------------+
11 rows in set (0.02 sec)
```

### Customerテーブルの定義
```
mysql> desc Customer;
+---------------+--------------+------+-----+---------+-------+
| Field         | Type         | Null | Key | Default | Extra |
+---------------+--------------+------+-----+---------+-------+
| id            | char(32)     | NO   | PRI | NULL    |       |
| kana          | varchar(255) | NO   |     | NULL    |       |
| name          | varchar(255) | NO   |     | NULL    |       |
| birthday      | date         | NO   |     | NULL    |       |
| created_at    | datetime(6)  | NO   |     | NULL    |       |
| updated_at    | datetime(6)  | NO   |     | NULL    |       |
| created_by_id | char(32)     | NO   | MUL | NULL    |       |
| updated_by_id | char(32)     | NO   | MUL | NULL    |       |
+---------------+--------------+------+-----+---------+-------+
8 rows in set (0.07 sec)
```

### Userテーブルの定義
```
mysql> desc User;
+-----------------+--------------+------+-----+---------+-------+
| Field           | Type         | Null | Key | Default | Extra |
+-----------------+--------------+------+-----+---------+-------+
| password        | varchar(128) | NO   |     | NULL    |       |
| last_login      | datetime(6)  | YES  |     | NULL    |       |
| is_superuser    | tinyint(1)   | NO   |     | NULL    |       |
| is_staff        | tinyint(1)   | NO   |     | NULL    |       |
| is_active       | tinyint(1)   | NO   |     | NULL    |       |
| id              | char(32)     | NO   | PRI | NULL    |       |
| employee_number | varchar(8)   | NO   | UNI | NULL    |       |
| username        | varchar(150) | NO   | UNI | NULL    |       |
| email           | varchar(254) | NO   | UNI | NULL    |       |
| role            | int unsigned | NO   |     | NULL    |       |
| created_at      | datetime(6)  | NO   |     | NULL    |       |
| updated_at      | datetime(6)  | NO   |     | NULL    |       |
+-----------------+--------------+------+-----+---------+-------+
12 rows in set (0.03 sec)
```

以上です

