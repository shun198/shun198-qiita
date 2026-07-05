---
title: DjangoのOuterRefとSubqueryを使ってサブクエリを実行しよう！
tags:
  - Django
  - ORM
private: false
updated_at: '2024-05-21T11:44:44+09:00'
id: d8cad5c46f1761fcee56
organization_url_name: null
slide: false
---
## 概要
サブクエリを使ったデータの取得をDjangoのORMで実現するにはDjangoのOuterRefとSubqueryを使って実現できるのでその方法について解説していきたいと思います

## 前提
- Djangoのプロジェクトを作成済み
- 今回は著者ごとの最新の本のタイトルを取得するクエリを作成します

## modelの作成
- Author
- Book

のModelを作成します

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


class Author(models.Model):
    """作者"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="お客様ID",
    )
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        db_comment="作成者",
    )

    class Meta:
        db_table = "Author"
        db_table_comment = "作者"


class Book(models.Model):
    """本"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="お客様ID",
    )
    title = models.CharField(max_length=255)
    author = models.ForeignKey(
        Author,
        null=True,
        on_delete=models.CASCADE,
        related_name="%(class)s_author",
        db_comment="作者",
    )
    publication_date = models.DateField()
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    created_by = models.ForeignKey(
        User,
        null=True,
        on_delete=models.SET_NULL,
        related_name="%(class)s_created_by",
        db_comment="作成者",
    )

    class Meta:
        db_table = "Book"
        db_table_comment = "本"

```

## fixtureの作成
- Author
- Book

のテストデータを作成します

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
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Author",
        "pk": 1,
        "fields": {
            "name": "J.K. Rowling",
            "created_at": "2022-01-01T00:00:00.000Z",
            "created_by": 1
        }
    },
    {
        "model": "application.Author",
        "pk": 2,
        "fields": {
            "name": "George R.R. Martin",
            "created_at": "2022-02-01T00:00:00.000Z",
            "created_by": 2
        }
    },
    {
        "model": "application.Author",
        "pk": 3,
        "fields": {
            "name": "Agatha Christie",
            "created_at": "2022-03-01T00:00:00.000Z",
            "created_by": 3
        }
    },
    {
        "model": "application.Book",
        "pk": 1,
        "fields": {
            "title": "Harry Potter and the Philosopher's Stone",
            "author": 1,
            "publication_date": "1997-06-26",
            "created_at": "2022-01-01T00:00:00.000Z",
            "created_by": 1
        }
    },
    {
        "model": "application.Book",
        "pk": 2,
        "fields": {
            "title": "Harry Potter and the Chamber of Secrets",
            "author": 1,
            "publication_date": "1998-07-02",
            "created_at": "2022-01-01T00:00:00.000Z",
            "created_by": 1
        }
    },
    {
        "model": "application.Book",
        "pk": 3,
        "fields": {
            "title": "Harry Potter and the Prisoner of Azkaban",
            "author": 1,
            "publication_date": "1999-07-08",
            "created_at": "2022-01-01T00:00:00.000Z",
            "created_by": 1
        }
    },
    {
        "model": "application.Book",
        "pk": 4,
        "fields": {
            "title": "A Game of Thrones",
            "author": 2,
            "publication_date": "1996-08-06",
            "created_at": "2022-02-01T00:00:00.000Z",
            "created_by": 2
        }
    },
    {
        "model": "application.Book",
        "pk": 5,
        "fields": {
            "title": "A Clash of Kings",
            "author": 2,
            "publication_date": "1998-11-16",
            "created_at": "2022-02-01T00:00:00.000Z",
            "created_by": 2
        }
    },
    {
        "model": "application.Book",
        "pk": 6,
        "fields": {
            "title": "A Storm of Swords",
            "author": 2,
            "publication_date": "2000-08-08",
            "created_at": "2022-02-01T00:00:00.000Z",
            "created_by": 2
        }
    },
    {
        "model": "application.Book",
        "pk": 7,
        "fields": {
            "title": "Murder on the Orient Express",
            "author": 3,
            "publication_date": "1934-01-01",
            "created_at": "2022-03-01T00:00:00.000Z",
            "created_by": 3
        }
    },
    {
        "model": "application.Book",
        "pk": 8,
        "fields": {
            "title": "The ABC Murders",
            "author": 3,
            "publication_date": "1936-01-06",
            "created_at": "2022-03-01T00:00:00.000Z",
            "created_by": 3
        }
    },
    {
        "model": "application.Book",
        "pk": 9,
        "fields": {
            "title": "Death on the Nile",
            "author": 3,
            "publication_date": "1937-11-01",
            "created_at": "2022-03-01T00:00:00.000Z",
            "created_by": 3
        }
    }
]

```

## シェルの実行
まず、DjangoのModelとOuterRef、Subqueryをimportします
```
>>> from django.db.models import OuterRef, Subquery
>>> from application.models import Author, Book
```

特定の著書が執筆した本をpublication_dateの降順で取得するサブクエリを作成します
サブクエリを作成する際はOuterRefを使用して絞り込みを行います
今回はAuthorのpkを使用します

```
>>> latest_book = Book.objects.filter(author=OuterRef('pk')).order_by('-publication_date')
```

その後、annotateを使ってauthors_with_latest_bookのfieldを作成し、latest_bookのクエリセット内から最初の要素(最新の著書)を1つだけ取得します

```
>>> authors_with_latest_book = Author.objects.annotate(latest_book_title=Subquery(latest_book.values('title')[:1]))
```

以下のように著者ごとの最新の本を取得できれば成功です
```
>>> for author in authors_with_latest_book:
...     print(f"{author.name}: {author.latest_book_title}")
...
SELECT "Author"."id",
       "Author"."name",
       "Author"."created_at",
       "Author"."created_by_id",

  (SELECT U0."title"
   FROM "Book" U0
   WHERE U0."author_id" = ("Author"."id")
   ORDER BY U0."publication_date" DESC
   LIMIT 1) AS "latest_book_title"
FROM "Author" [19.69ms]
J.K. Rowling: Harry Potter and the Prisoner of Azkaban
George R.R. Martin: A Storm of Swords
Agatha Christie: Death on the Nile
```

## 参考
https://docs.djangoproject.com/en/5.0/ref/models/expressions/#subquery-expressions
