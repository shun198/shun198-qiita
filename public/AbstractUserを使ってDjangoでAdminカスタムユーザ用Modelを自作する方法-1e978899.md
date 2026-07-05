---
title: AbstractUserを使ってDjangoでAdmin(カスタムユーザ)用Modelを自作する方法
tags:
  - Django
  - MySQL
  - AbstractUser
private: false
updated_at: '2024-02-05T16:25:29+09:00'
id: 1e97889942f5da3bec1e
organization_url_name: null
slide: false
---
## 前提
- Djangoのプロジェクトおよびアプリケーションは作成済み
- DBはMySQL

## どうやって作るの？
自身でAdmin(カスタムユーザ)用Modelを自作する場合は
- AbstractUser
- AbstractBaseUserとPermissionsMixin

を継承する方法のどちらかでやるのが一般的だと言われています
今回はAbstractUserを継承して作成します

## AbstractUserとは
- AbstractBaseUser
- PermissionsMixin

の2つのクラスを継承しているクラスです
AbstractBaseUserには
- password
- last_login

など認証関連のフィールドやメソッドを
PermissionsMixinには
- is_superuser
- groups
- user_permissions

などグループと権限管理のフィールドやメソッドを

また、AbstractUserクラス自身も
- username
- first_name
- last_name
- email
- is_staff
- is_active
- date_joined

などユーザの情報管理に必要最低限なフィールドやメソッドを持ちます
そのため、AbstractUserは
- AbstractBaseUser
- PermissionsMixin
- AbstractUser

のフィールドおよびメソッドを全て使うことができます

![abstractuser.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f17773f3-d0bb-1327-3be3-6a15199bc3f0.jpeg)

## Modelを作成しよう！
では、実際に作成してみましょう
```python:models.py
import uuid
from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator

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
        validators=[RegexValidator(r'^[0-9]{8}$')],
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
    role = models.PositiveIntegerField(choices=Role.choices, default=Role.PART_TIME)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # デフォルトはusernameだが今回は社員番号を指定
    USERNAME_FIELD = "employee_number"
    # uniqueのemailとusernameを指定
    REQUIRED_FIELDS = ["email","username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"

    def __str__(self):
        return self.username
```


### USERNAME_FIELDって何？
ユーザーを一意に識別するためのフィールドです
デフォルトでusernameが設定されています
今回はemployee_number(社員番号)でログインしたいのでUSERNAME_FIELDの値を
employee_numberに変更することで実現できます
USERNAME_FIELDを上書きしないとdjango.contrib.auth内のauthenticateメソッドを使ってログインできなくなるので注意が必要です

### REQUIRED_FIELDSって何？
createsuperuserコマンドからもユーザーを追加できるようにするためには
- email
- username

などのuniqueなフィールドをREQUIRED_FIELDSに設定して入力を受け付けるようにする必要があります
今回の場合だと指定しないとemailとusernameは必須なので例えばemailを指定し忘れると
```
django.db.utils.IntegrityError: (1048, "Column 'email' cannot be null")
```
みたいな感じでemailは必須なのに入力してないよ！と怒られます
もちろん、uniqueなフィールドである必要はありませんが、uniqueなフィールドを指定するのが一般的です
ただし、USERNAME_FIELDに指定したフィールドとパスワードはREQUIRED_FILEDSに含まれていなくてもcreatesuperuser実行時に要求されます
そのため、REQUIRED_FILEDSに指定するとエラーになってしまうので注意です

## 認証にカスタムユーザを設定しよう
カスタムユーザーを定義した際は、INSTALLED_APPSにアプリケーションを追加した後に認証用に使用するユーザー管理モデルとしてカスタムユーザーを設定する必要があります
今回はapplication.apps.ApplicationConfigを追加します
```apps.py
from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application"
```

```diff
+++settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
++++"application.apps.ApplicationConfig"
    ]

+++AUTH_USER_MODEL = 'application.User'
```

設定をせずにMigrationをしてしまうと以下のエラーが出ます

```
auth.User.user_permissions: (fields.E304) Reverse accessor 'Permission.user_set' for 'auth.User.user_permissions' clashes with reverse accessor for 'application.User.user_permissions'.
        HINT: Add or change a related_name argument to the definition for 'auth.User.user_permissions' or 'application.User.user_permissions'.
```

## Migrationを行おう
Migrationする際に
```
Migration admin.0001_initial is applied before its dependency
```
というエラーが表示されると思いますがDjangoのデフォルトのadminユーザのModelとカスタムユーザのModelが衝突してしまうために起こるエラーです
Dockerを使っている場合は以下の記事を参考に永続Volumeとmigrationファイルを消してからDockerを立ち上げ直すととても簡単に解決できます

https://qiita.com/shun198/items/38503195637b2c33fde3


## ログを確認してみよう!
以上の設定を完了させた後にMigrationを行うと以下のようなlogが表示されるかと思います
```text:terminal
Migrations for 'application':
  application/migrations/0001_initial.py
    - Create model User
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, sessions, user
Running migrations:
Applying contenttypes.0001_initial... OK
Applying contenttypes.0002_remove_content_type_name... OK
Applying auth.0001_initial... OK
Applying auth.0002_alter_permission_name_max_length... OK
Applying auth.0003_alter_user_email_max_length... OK
Applying auth.0004_alter_user_username_opts... OK
Applying auth.0005_alter_user_last_login_null... OK
Applying auth.0006_require_contenttypes_0002... OK
Applying auth.0007_alter_validators_add_error_messages... OK
Applying auth.0008_alter_user_username_max_length... OK
Applying auth.0009_alter_user_last_name_max_length... OK
Applying auth.0010_alter_group_name_max_length... OK
Applying auth.0011_update_proxy_permissions... OK
Applying auth.0012_alter_user_first_name_max_length... OK
Applying application.0001_initial... OK
Applying admin.0001_initial... OK
Applying admin.0002_logentry_remove_auto_add... OK
Applying admin.0003_logentry_add_action_flag_choices... OK
Applying sessions.0001_initial... OK
165 static files copied to '/static'.
Watching for file changes with StatReloader
Performing system checks...

System check identified no issues (0 silenced).
October 22, 2022 - 16:51:50
Django version 4.1.2, using settings 'project.settings'
Starting development server at http://0.0.0.0:8000/
Quit the server with CONTROL-C.
```

## createsuperuserコマンドを実行
必要な情報を入力していきます
今回はパスワードをtestにしました
以下のようになったら成功です
```
python manage.py createsuperuser
Employee number: 00000001
Email: test01@example.com
Username: test01
Password: 
Password (again): 
このパスワードは username と似すぎています。
このパスワードは短すぎます。最低 8 文字以上必要です。
このパスワードは一般的すぎます。
Bypass password validation and create user anyway? [y/N]: y
Superuser created successfully.
```

## DBも確認してみよう
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
11 rows in set (0.05 sec)
```
```
mysql> select * from User;
+------------------------------------------------------------------------------------------+------------+--------------+----------+-----------+----------------------------------+-----------------+----------+--------------------+------+----------------------------+----------------------------+
| password                                                                                 | last_login | is_superuser | is_staff | is_active | id                               | employee_number | username | email              | role | created_at                 | updated_at                 |
+------------------------------------------------------------------------------------------+------------+--------------+----------+-----------+----------------------------------+-----------------+----------+--------------------+------+----------------------------+----------------------------+
| pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I= | NULL       |            0 |        0 |         1 | 00000000000000000000000000000001 | 00000001        | test01   | test01@example.com |    0 | 2022-07-28 00:31:09.732000 | 2022-07-28 00:31:09.732000 |
+------------------------------------------------------------------------------------------+------------+--------------+----------+-----------+----------------------------------+-----------------+----------+--------------------+------+----------------------------+----------------------------+
1 row in set (0.08 sec)
```

## 管理者画面を開いてみよう
`USERNAME_FIELD = "employee_number"`と指定したことで社員番号でログインできるようになりました
![スクリーンショット 2022-11-05 17.52.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/07e03508-1e6b-ba12-b778-fa17b7c2082a.png)

すでに私の方でいくつかModelを作成しており、admin.pyにも設定していますがこのようにログインできたら成功です
![スクリーンショット 2022-11-05 17.58.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/11aeaa7c-fc1d-b322-b237-cd10bb509770.png)

## 記事の紹介
以下の記事も書いたのでよかったら読んでみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/29b5c253be6f802403cd

https://qiita.com/shun198/items/a79a17db571a461309ea

## 参考
https://docs.djangoproject.com/en/3.2/ref/settings/#auth-user-model

https://docs.djangoproject.com/en/3.2/topics/auth/customizing/

https://daeudaeu.com/django-abstractuser/

https://qiita.com/okoppe8/items/10ae61808dc3056f9c8e
