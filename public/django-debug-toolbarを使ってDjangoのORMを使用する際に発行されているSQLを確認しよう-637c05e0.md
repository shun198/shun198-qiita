---
title: django-debug-toolbarを使ってDjangoのORMを使用する際に発行されているSQLを確認しよう！
tags:
  - Django
  - ORM
private: false
updated_at: '2024-07-04T19:43:22+09:00'
id: 637c05e0701114ae5b3d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
DjangoのORMって便利ですけど中でどんなSQLが発行されてるかよくわからないですよね？
今回は`django-debug-toolbar`という便利なツールを使いながら一つずつ解説していきたいと思います

## ファイル構成
ファイル構成は以下の通りです
```
・
├── application
│   ├── __init__.py
│   ├── __pycache__
│   ├── admin.py
│   ├── apps.py
│   ├── fixtures
│   │   └── fixture.py
│   ├── migrations
│   └── models.py
├── manage.py
└── project
    ├── __init__.py
    ├── asgi.py
    ├── settings
    ├── urls
    └── wsgi.py
```

## django-debug-toolbarのインストール
`django-debug-toolbar`をインストールすることでquerysetのSQLを見ることができます
まずはインストールします
```
pip install django-debug-toolbar
```

次にsettings.pyに必要な設定を記載していきます
```project/settings.py
INSTALLED_APPS = [
    "debug_toolbar",
]

MIDDLEWARE = [
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]
```

```
python manage.py debugsqlshell
```
とコマンドを入力した後に以下のように`Interactive mode`になったら成功です
```
Python 3.10.8 (main, Oct 26 2022, 03:28:14) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
```

## 今回使うModelとFixture
以下にハンズオンで使えるModelとFixtureを記載しておきます

```application/models.py
import uuid

from django.db import models


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kana = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    birthday = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "Customer"
```

```application/fixtures/fixture.json
[
    {
        "model": "application.Customer",
        "pk": 1,
        "fields": {
            "kana": "オオサカタロウ",
            "name": "大阪太郎",
            "birthday": "1992-01-06",
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 2,
        "fields": {
            "kana": "キョウトジロウ",
            "name": "京都二郎",
            "birthday": "1994-01-06",
            "created_at": "2022-08-26T00:31:09.732Z",
            "updated_at": "2022-08-26T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 3,
        "fields": {
            "kana": "ヒョウゴサブロウ",
            "name": "兵庫三郎",
            "birthday": "1995-03-06",
            "created_at": "2022-09-20T00:31:09.732Z",
            "updated_at": "2022-09-20T00:31:09.732Z"
        }
    }
]
```

## 実際にORMを使ってみよう！
まずはCustomerのModelを操作できるようあらかじめimportします
```
>>> from application.models import Customer
```

### get
まずはgetを使って特定のCustomerを取得します
```
>>> Customer.objects.get(id="00000000000000000000000000000001")

SELECT VERSION(), @@sql_mode, @@default_storage_engine, @@sql_auto_is_null, @@lower_case_table_names,
                                                                              CONVERT_TZ('2001-01-01 01:00:00', 'UTC', 'UTC') IS NOT NULL [2.46ms]

SET SESSION TRANSACTION ISOLATION LEVEL READ COMMITTED [0.45ms]
SELECT `Customer`.`id`,
       `Customer`.`kana`,
       `Customer`.`name`,
       `Customer`.`birthday`,
       `Customer`.`created_at`,
       `Customer`.`updated_at`
FROM `Customer`
WHERE `Customer`.`id` = '00000000000000000000000000000001'
LIMIT 21 [4.24ms]
<Customer: Customer object (00000000-0000-0000-0000-000000000001)>
```

```
WHERE `Customer`.`id` = '00000000000000000000000000000001'
```
でCustomerのidで絞り込みを行っているのが確認できます

### latest
最新のcreated_atを持つCustomerを取得します
```
>>> Customer.objects.latest("created_at")
SELECT `Customer`.`id`,
       `Customer`.`kana`,
       `Customer`.`name`,
       `Customer`.`birthday`,
       `Customer`.`created_at`,
       `Customer`.`updated_at`
FROM `Customer`
ORDER BY `Customer`.`created_at` DESC
LIMIT 1 [9.79ms]
<Customer: Customer object (00000000-0000-0000-0000-000000000003)>
```

こちらも同様に
```
ORDER BY `Customer`.`created_at` DESC
```
で並び替えを行っているのがわかります

## まとめ
どんなSQLを発行しているかわかるとORMへの理解が深まりますしデバッグ効率が格段に上がるのでかなり便利ですね
特にORMについての知識が浅いうちはどんどん使っていいと思います

## 参考

https://akiyoko.hatenablog.jp/entry/2016/08/04/232531

https://django-debug-toolbar.readthedocs.io/en/latest/
