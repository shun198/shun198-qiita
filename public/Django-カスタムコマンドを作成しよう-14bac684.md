---
title: '[Django] カスタムコマンドを作成しよう！'
tags:
  - Django
private: false
updated_at: '2024-02-05T07:32:07+09:00'
id: 14bac6843a2459b34a34
organization_url_name: null
slide: false
---
## 概要
Djangoのカスタムコマンドの作成方法について解説します
今回は指定したシステムユーザの数分データを生成するカスタムコマンドを作成します

## 前提
- Djangoのプロジェクトを作成済み

## ディレクトリ構成
```
tree
・
└── application
　　   │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── management
    │   │   └── commands
    │   │       └── seed.py
    │   ├── migrations
    │   │   ├── 0001_initial.py
    │   │   └── __init__.py
    │   └── models.py
    └── manage.py
```

## 実装
今回は
- models.py
- seed.py

の順に実装していきます

### models.py
システムユーザのmodelを作成します
AbstractUserについて詳細に知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```application/models.py
from django.contrib.auth.models import AbstractUser, Group
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


class User(AbstractUser):
    """システムユーザ"""

    username_validator = UnicodeUsernameValidator()

    # 不要なフィールドはNoneにすることができる
    first_name = None
    last_name = None
    date_joined = None
    id = models.AutoField(
        primary_key=True,
        db_comment="ID",
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
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日",
    )
    groups = models.ForeignKey(
        Group,
        on_delete=models.PROTECT,
        related_name="users",
        db_comment="社員権限テーブル外部キー",
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

### seed.py
指定したシステムユーザの数分データを生成するカスタムコマンドを作成します
Djangoでカスタムコマンドを作成する際は`management/commands`配下にPythonファイルを作成します
作成したファイル名がそのままコマンドになります
また、ディレクトリ配下のファイルの先頭に`_`を入れるとカスタムコマンドとして認識されなくなります

```application/management/commands/seed.py
from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand

from application.models import User


class Command(BaseCommand):
    help = "Seeds the database with initial data"

    def add_arguments(self, parser):
        """システムユーザの数を指定するオプション

        Args:
            parser : オプションを追加するためのparser
        """
        parser.add_argument(
            "--users",
            type=int,
            help="Specify the amount of users. The default amount of users will be 10",
        )

    def handle(self, *args, **options):
        """システムユーザを作成するコマンド"""
        Group.objects.update_or_create(
            id=1,
            name="管理者",
        )
        Group.objects.update_or_create(
            id=2,
            name="一般",
        )
        users = options["users"]
        if not users:
            users = 10
        print(f"Creating {users} users")
        for id in range(1, users + 1):
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    id=id,
                    username=f"テストユーザ{id}",
                    employee_number=str(id).zfill(8),
                    email=f"example{id}.com",
                    groups=Group.objects.get(name="管理者"),
                )
            user.set_password("test")
            user.save()
            print(f"Created {user}")
        print(f"Successfully created {users} users")

```

一つずつ解説します

#### add_arguments
今回はコマンドに作成するユーザの数を指定するオプションを付与します
オプション名、型、ヘルパーテキストを指定できます

```python
    def add_arguments(self, parser):
        """システムユーザの数を指定するオプション

        Args:
            parser : オプションを追加するためのparser
        """
        parser.add_argument(
            "--users",
            type=int,
            help="Specify the amount of users. The default amount of users will be 10",
        )
```

#### handle
handle内に実際の処理を記載します
**options内に使用したオプションの値が配列として格納されているのでhandle内で使用できます
今回はオプションを指定しなかったらデフォルトでユーザを10人作成し、オプションを指定したら指定した分だけユーザを作成する処理を記載します

```python
    def handle(self, *args, **options):
        """システムユーザを作成するコマンド"""
        Group.objects.update_or_create(
            id=1,
            name="管理者",
        )
        Group.objects.update_or_create(
            id=2,
            name="一般",
        )
        users = options["users"]
        if not users:
            users = 10
        print(f"Creating {users} users")
        for id in range(1, users + 1):
            try:
                user = User.objects.get(id=id)
            except User.DoesNotExist:
                user = User.objects.create_user(
                    id=id,
                    username=f"テストユーザ{id}",
                    employee_number=str(id).zfill(8),
                    email=f"example{id}.com",
                    groups=Group.objects.get(name="管理者"),
                )
            user.set_password("test")
            user.save()
            print(f"Created {user}")
        print(f"Successfully created {users} users")
```

## コマンドを実行してみよう！
作成したカスタムコマンドのhelpを見てみましょう

```
python manage.py seed --help
```

以下のようにコマンドとオプションのヘルパーテキストが表示されていることが確認できました

```
usage: manage.py seed [-h] [--users USERS] [--version] [-v {0,1,2,3}] [--settings SETTINGS] [--pythonpath PYTHONPATH] [--traceback] [--no-color] [--force-color] [--skip-checks]

Seeds the database with initial data

options:
  -h, --help            show this help message and exit
  --users USERS         Specify the amount of users. The default amount of users will be 10
  --version             Show program's version number and exit.
  -v {0,1,2,3}, --verbosity {0,1,2,3}
                        Verbosity level; 0=minimal output, 1=normal output, 2=verbose output, 3=very verbose output
  --settings SETTINGS   The Python path to a settings module, e.g. "myproject.settings.main". If this isn't provided, the DJANGO_SETTINGS_MODULE environment variable will be used.
  --pythonpath PYTHONPATH
                        A directory to add to the Python path, e.g. "/home/djangoprojects/myproject".
  --traceback           Raise on CommandError exceptions.
  --no-color            Don't colorize the command output.
  --force-color         Force colorization of the command output.
  --skip-checks         Skip system checks.
```

コマンドを実行します
以下のようにログが出力され、システムユーザが作成されたら成功です

```
python manage.py seed --users 20
Creating 20 users
Created テストユーザ1
Created テストユーザ2
Created テストユーザ3
Created テストユーザ4
Created テストユーザ5
Created テストユーザ6
Created テストユーザ7
Created テストユーザ8
Created テストユーザ9
Created テストユーザ10
Created テストユーザ11
Created テストユーザ12
Created テストユーザ13
Created テストユーザ14
Created テストユーザ15
Created テストユーザ16
Created テストユーザ17
Created テストユーザ18
Created テストユーザ19
Created テストユーザ20
Successfully created 20 users
```

Userテーブルの中は以下の通りです

```
django=# SELECT * FROM "User" order by id;
                                         password                                         | last_login | is_superuser | is_staff | is_active | id | employee_number |    username    |     emai
l     |          created_at           |          updated_at           | groups_id 
------------------------------------------------------------------------------------------+------------+--------------+----------+-----------+----+-----------------+----------------+---------
------+-------------------------------+-------------------------------+-----------
 pbkdf2_sha256$600000$N70GCTI2t5PvPv1iPh7IgB$n2NVOLXuxvSj29381p9DSvptAPIZSjKzPocQ3VKY2BA= |            | f            | f        | t         |  1 | 00000001        | テストユーザ1  | example1
.com  | 2024-02-04 10:42:05.67779+00  | 2024-02-04 10:42:06.031773+00 |         1
 pbkdf2_sha256$600000$N3fBdPCRjXLOBD2k3toyUt$gkYgtUTqsF6Ck5+AD6IApL83/NvQWFmVJlrxLEkEv/E= |            | f            | f        | t         |  2 | 00000002        | テストユーザ2  | example2
.com  | 2024-02-04 10:42:06.052773+00 | 2024-02-04 10:42:06.441644+00 |         1
 pbkdf2_sha256$600000$a9pkl6ZoaWvyr2xjb6njOQ$581cVCTfw4sVp0w9sbnBe5zMrnaLgIdZ3vE+8TZb+ME= |            | f            | f        | t         |  3 | 00000003        | テストユーザ3  | example3
.com  | 2024-02-04 10:42:06.451707+00 | 2024-02-04 10:42:06.826803+00 |         1
 pbkdf2_sha256$600000$mkfQol0fUYFyYfVLeQfjjX$0oEiSuhOnYPnIHRwhupbwOVMxmFMXsWJwAdmc3Q+qDs= |            | f            | f        | t         |  4 | 00000004        | テストユーザ4  | example4
.com  | 2024-02-04 10:42:06.835912+00 | 2024-02-04 10:42:07.272309+00 |         1
 pbkdf2_sha256$600000$84yicBdzakaQcBKaxXspdJ$0WcDga1WTUZVEQuWlwERoErqIYnBFoqThw9LEhwqr0g= |            | f            | f        | t         |  5 | 00000005        | テストユーザ5  | example5
.com  | 2024-02-04 10:42:07.279547+00 | 2024-02-04 10:42:07.619245+00 |         1
 pbkdf2_sha256$600000$iiUhfF22vlJem5zsq2LQ9W$Jespi8m5ekf7xamLJF5s8e4OKNCjZSalgE6LFpXn4/w= |            | f            | f        | t         |  6 | 00000006        | テストユーザ6  | example6
.com  | 2024-02-04 10:42:07.628706+00 | 2024-02-04 10:42:07.993764+00 |         1
 pbkdf2_sha256$600000$VUNr6RgiBd9kN9SbPMYO1i$dOmYRBHzfo7+F4YTh8drmKb4WKkLPiALymsd/ZzXKlw= |            | f            | f        | t         |  7 | 00000007        | テストユーザ7  | example7
.com  | 2024-02-04 10:42:08.003249+00 | 2024-02-04 10:42:08.351413+00 |         1
 pbkdf2_sha256$600000$rE0Y1GWkpDwWCUbOnhI3OU$YaDCdQVUZCkIxpbsd3bUJWkLyLT7NlNIJF8mBRFzhCk= |            | f            | f        | t         |  8 | 00000008        | テストユーザ8  | example8
.com  | 2024-02-04 10:42:08.358768+00 | 2024-02-04 10:42:08.688046+00 |         1
 pbkdf2_sha256$600000$XeB3OaXr9UPCtNxYkeuGcW$d0Rv3mwnWYeDMniN6t3L6GZWhUs7wvXovNadRpIVSPo= |            | f            | f        | t         |  9 | 00000009        | テストユーザ9  | example9
.com  | 2024-02-04 10:42:08.696455+00 | 2024-02-04 10:42:09.036743+00 |         1
 pbkdf2_sha256$600000$ScENbjJGpqiyi59gd3fhOC$FsDD9cwnJBFkO4ZSn9UqoNmWj041A8tSqQsg3WXBujw= |            | f            | f        | t         | 10 | 00000010        | テストユーザ10 | example1
0.com | 2024-02-04 10:42:09.046133+00 | 2024-02-04 10:42:09.486939+00 |         1
 pbkdf2_sha256$600000$bILciKYVYW44L9aoQMnDae$4hNdrPVl2wplKIhUiwbOBc88QTQc3zFCkbDvBCUiZ8w= |            | f            | f        | t         | 11 | 00000011        | テストユーザ11 | example1
1.com | 2024-02-04 10:42:09.497018+00 | 2024-02-04 10:42:10.017096+00 |         1
 pbkdf2_sha256$600000$638VoeGyOVpTIBPXgtDovq$fvzUy9Y/wU89znr1tEdL6oaZ64oty4B1t8lHpok8w3U= |            | f            | f        | t         | 12 | 00000012        | テストユーザ12 | example1
2.com | 2024-02-04 10:42:10.027721+00 | 2024-02-04 10:42:10.476937+00 |         1
 pbkdf2_sha256$600000$Jcm1530zHbIc5rJAJsZZAX$kDlFDNi5+NJtPWhHnGE76GyRG8xMcIM1GHiUgYnMSoA= |            | f            | f        | t         | 13 | 00000013        | テストユーザ13 | example1
3.com | 2024-02-04 10:42:10.485936+00 | 2024-02-04 10:42:10.90018+00  |         1
 pbkdf2_sha256$600000$AwTHyMTCCAh5autJc8zbBw$LUmDNCo0AAS/3FvDs9UDD2WIv7wAKShsra4iDhiOjxo= |            | f            | f        | t         | 14 | 00000014        | テストユーザ14 | example1
4.com | 2024-02-04 10:42:10.909085+00 | 2024-02-04 10:42:11.293215+00 |         1
 pbkdf2_sha256$600000$aUMjLRU5mm5yxWRL9iCMiX$a5CzTJ+2ieR+fGtesWtD/qkgfeXZzoHTaxzaxUld7ZE= |            | f            | f        | t         | 15 | 00000015        | テストユーザ15 | example1
5.com | 2024-02-04 10:42:11.302117+00 | 2024-02-04 10:42:11.681076+00 |         1
 pbkdf2_sha256$600000$tZMApEQgW92UhSnUYf3qmG$y+DtjW6iWuvZK75B018UJnokGy6mf6JqiMUiA5/yqiQ= |            | f            | f        | t         | 16 | 00000016        | テストユーザ16 | example1
6.com | 2024-02-04 10:42:11.690464+00 | 2024-02-04 10:42:12.143705+00 |         1
 pbkdf2_sha256$600000$UP2BS5Jy6Ypc8y96A7Ugwc$o1WVEXX78fpPbeMRPEAH/ShVYAKZhJv2saJXl7CeeNQ= |            | f            | f        | t         | 17 | 00000017        | テストユーザ17 | example1
7.com | 2024-02-04 10:42:12.153523+00 | 2024-02-04 10:42:12.50654+00  |         1
 pbkdf2_sha256$600000$r1KShSqKn6NRV1fV32hNQW$sfdxcC36lC+FwUSklCewsfIEkFy0LjAAJrN47RT7IgI= |            | f            | f        | t         | 18 | 00000018        | テストユーザ18 | example1
8.com | 2024-02-04 10:42:12.5147+00   | 2024-02-04 10:42:12.863796+00 |         1
 pbkdf2_sha256$600000$XS97oafQ3iujXqWYpKsVWF$JpCrzogirBtDZpRUBEjvYdqiUq7ToydKuz6gICj7Q40= |            | f            | f        | t         | 19 | 00000019        | テストユーザ19 | example1
9.com | 2024-02-04 10:42:12.871577+00 | 2024-02-04 10:42:13.228192+00 |         1
 pbkdf2_sha256$600000$wUOAM4OuTngr5uSV6UT6GC$hd5tpKPdFFkdNSnhXRwxWJ1MIgj85ms+qBIg2jiWU3I= |            | f            | f        | t         | 20 | 00000020        | テストユーザ20 | example2
0.com | 2024-02-04 10:42:13.23653+00  | 2024-02-04 10:42:13.622156+00 |         1
(20 rows)
```

## 参考
https://docs.djangoproject.com/en/5.0/howto/custom-management-commands/
