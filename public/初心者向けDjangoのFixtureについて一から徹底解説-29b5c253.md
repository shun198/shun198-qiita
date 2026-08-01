---
title: 【初心者向け】DjangoのFixtureについて一から徹底解説
tags:
  - Django
  - Fixture
  - MySQL8.0
private: false
updated_at: '2022-10-29T11:38:44+09:00'
id: 29b5c253be6f802403cd
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- DBはMySQLを使用

## fixtureとは？
Djangoに備わっている初期データやテスト用データを用意する機能のことです
fixtureを使うことで
- DjangoのAdmin画面から一つずつ手動で入力せずにコマンド一つでデータを投入できる
- Gitで管理すればチームメンバーも同じデータをすぐに投入できる
- fixtureのデータをテストコードのデータとしても流用できる

などメリットが大きいのでぜひ使いましょう！

## サンプルモデル
fixtureの説明用に簡単なModelを作成しました
- Author1人に対してBookは複数あるのでOneToMany
- Book複数に対してCustomerは複数存在するのでManyToMany

の関係になります
```python:models.py
import uuid
from django.db import models
from django.core.validators import RegexValidator

# 本
class Book(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["title"]
        db_table = "Book"

# 作者
class Author(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    book = models.ForeignKey("Book", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = "Author"

# お客様
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kana = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    age = models.IntegerField()
    post_no = models.CharField(
        max_length=7, validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")]
    )
    book = models.ManyToManyField("Book")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name", "age"]
        db_table = "Customer"
```

## fixture用のディレクトリとファイルを用意
fixturesフォルダをアプリケーションディレクトリ配下に作り、fixtures内にデータを作成していきます

```
└── アプリケーションディレクトリ
    └── fixtures
    　　   └── fixture用ファイル
```

fixtureは
- xml
- yaml
- json

の3種類のいずれかを使用することができます
今回はjsonを使用しますので下記のようにbook.jsonを用意してみました

```
└── アプリケーションディレクトリ
    └── fixtures
    　　   └── book.json
```

## fixtureを作成してみよう！
fixtureを作成する時は1Modelにつきデータは2つまであれば十分です
以下のように
- modelに対応するアプリケーション名とModel
- PrimaryKey
- PrimaryKey以外のカラムと対応するデータ
- 他ModelのPrimaryKeyに対応するForeignKey

を記載していきます
```json:book.json
[
    {
    "model": "<アプリケーション名>.Book",
        "pk":1,
        "fields": {
            "title":"ハリー・ポッターと賢者の石",
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    },
    {
    "model": "<アプリケーション名>.Book",
        "pk":2,
        "fields": {
            "title":"ノルウェーの森",
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    },
    {
    "model": "<アプリケーション名>.Author",
        "pk":1,
        "fields": {
            "book":1,
            "name":"J・K・ローリング",
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    },
    {
    "model": "<アプリケーション名>s.Author",
        "pk":2,
        "fields": {
            "book":2,
            "name":"村上春樹",
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    },
    {
    "model": "<アプリケーション名>.Customer",
        "pk":1,
        "fields": {
            "kana":"タナカイチロウ",
            "name":"田中一郎",
            "age":20,
            "post_no":"6003333",
            "book":[1,2],
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    },
    {
    "model": "r<アプリケーション名>.Customer",
        "pk":2,
        "fields": {
            "kana":"ヤマダハナコ",
            "name":"山田花子",
            "age":20,
            "post_no":"6004444",
            "book":[1,2],
            "created_at":"2022-07-28T00:31:09.732Z"
        }
    }
]

```

### Primarykey及びForeignkey
int型のidおよびuuidは1,2と順番に割り振ることができます

### many to many fieldの時
今回の例みたいにCustomerとBookの関係はManyToManyの関係なのでCustomerのModelのbookのfieldにはCustomerのPrimaryKeyを全て記載する必要があります
そのため、
```
"book":1
```
と記載すると
```
'int' object is not iterable: field_value was '1'
```
というエラーが返ってきてしまうため、例のようにList内にPrimaryKeyを全て記載します
```
"book":[1,2]
```

### timezone
Djangoだとデフォルトでtimezoneが有効になっているため、
例えば
```
"created_at":"2022-07-28 00:31:09.732"
```
という風にdatetime型の表記のまま記載すると
```
RuntimeWarning: DateTimeField Book.date received a naive datetime while time zone support is active.
```
という警告が出ます
```
"created_at":"2022-07-28T00:31:09.732Z"
```
と記載することでtimezoneに対応するdatetimeをDBに入れることができます

## 作成したデータをDBに入れてみよう！
loaddataコマンドを実行するとデータを入れることができます
今回はbook.jsonのfixtureを使っていますがbookの箇所は自身がつけたfixtureの名前に置き換えてください
```
python manage.py loaddata book.json
Installed 6 object(s) from 1 fixture(s)
```

## MySQLのテーブルを確認しましょう
以下のようにデータを入れることができたら成功です
```sql:Book
mysql> select * from Book;
+----------------------------------+-----------------------------------------+----------------------------+
| id                               | title                                   | created_at                 |
+----------------------------------+-----------------------------------------+----------------------------+
| 00000000000000000000000000000001 | ハリー・ポッターと賢者の石                　　　　　　　　　　　| 2022-07-28 00:31:09.732000 |
| 00000000000000000000000000000002 | ノルウェーの森                          　　　　　　　　| 2022-07-28 00:31:09.732000 |
+----------------------------------+-----------------------------------------+----------------------------+
```
```sql:Author
mysql> select * from Author;
+----------------------------------+-------------------------+----------------------------+----------------------------------+
| id                               | name                    | created_at                 | book_id                          |
+----------------------------------+-------------------------+----------------------------+----------------------------------+
| 00000000000000000000000000000001 | J・K・ローリング             | 2022-07-28 00:31:09.732000 | 00000000000000000000000000000001 |
| 00000000000000000000000000000002 | 村上春樹                 | 2022-07-28 00:31:09.732000 | 00000000000000000000000000000002 |
+----------------------------------+-------------------------+----------------------------+----------------------------------+
```
```sql:Customer
+----------------------------------+-----------------------+--------------+-----+---------+----------------------------+
| id                               | kana                  | name         | age | post_no | created_at                 |
+----------------------------------+-----------------------+--------------+-----+---------+----------------------------+
| 00000000000000000000000000000001 | タナカイチロウ            | 田中一郎      |  20 | 6003333 | 2022-07-28 00:31:09.732000 |
| 00000000000000000000000000000002 | ヤマダハナコ             | 山田花子      |  20 | 6004444 | 2022-07-28 00:31:09.732000 |
+----------------------------------+-----------------------+--------------+-----+---------+----------------------------+
```

## 参考
https://stackoverflow.com/questions/8197961/specifying-manytomany-fields-in-django-fixtures

https://qiita.com/acecrc/items/5e1368af4277daccaf63

https://houdoukyokucho.com/2021/01/06/post-2758/

