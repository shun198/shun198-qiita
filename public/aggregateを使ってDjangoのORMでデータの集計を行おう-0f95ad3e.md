---
title: aggregateを使ってDjangoのORMでデータの集計を行おう
tags:
  - Django
  - ORM
  - aggregate
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 0f95ad3e106c791fff3b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
SQLの
- MAX
- MIN
- SUM
- AVG
- COUNT

などの集計関数をDjangoのORMでも再現する際はaggregateを使います
今回はaggregateの使い方について解説します

## 前提
- Djangoのプロジェクトを作成済み

## ファイル構成
```
application
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── fixtures
   |   └── fixture.json
   ├── migrations
   └── models.py
```

上記のうち
- models.py
- fixture.json

に必要な設定を記載していきます

### models.py
今回は簡易的な購入履歴のテーブルを作成します

```models.py
class PurchaseInfo(models.Model):
    """購入履歴"""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    product_name = models.CharField(max_length=255)
    """商品名"""
    count = models.SmallIntegerField(default=0)
    """個数"""
    created_at = models.DateTimeField(auto_now_add=True)
    """作成日"""
    
    class Meta:
        db_table = "PurchaseInfo"
```

### fixture.json
Djangoのfixtureを使ってテストデータを作成します

```fixture.json
[
    {
        "model": "application.PurchaseInfo",
        "pk": 1,
        "fields": {
            "product_name": "りんご",
            "count": "3",
            "created_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.PurchaseInfo",
        "pk": 2,
        "fields": {
            "product_name": "椅子",
            "count": "6",
            "created_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.PurchaseInfo",
        "pk": 3,
        "fields": {
            "product_name": "鏡",
            "count": "2",
            "created_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.PurchaseInfo",
        "pk": 4,
        "fields": {
            "product_name": "電球",
            "count": "7",
            "created_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.PurchaseInfo",
        "pk": 5,
        "fields": {
            "product_name": "ネギ",
            "count": "9",
            "created_at": "2022-07-28T00:31:09.732Z"
        }
    }
]
```

### 変更内容の反映
以下のコマンドを実行してDBへのマイグレーションとテストデータの投入を行います

```
python manage.py makemigrations
python manage.py migrate
python manage.py loaddata fixture.json
```

## DjangoのShellを使って実際に集計結果を取ってみよう!
DjangoのORMを使用する際はdjango-debug-toolbarを使うと発行されているSQLがわかるので非常に便利です
詳細は以下の記事を参照してください

https://qiita.com/shun198/items/637c05e0701114ae5b3d

以下のコマンドを実行するとShellが起動します
```
python manage.py debugsqlshell
Python 3.11.2 (main, Mar 14 2023, 02:02:39) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
```
django-debug-toolbarを使用しない場合は以下のコマンドでも実行できます

```
python manage.py shell
```

まずはModelと集計関数をimportします
```
>>> from django.db.models import Avg,Sum,Max,Min,Count
>>> from application.models import PurchaseInfo
```

## aggregate
aggregateを使用することで集計をとることができます
その際は集計結果がdict型で帰ってきます

### Max(最大値)
最大値を取得できます
デフォルトで取得したい最大値の後の`__max`のdictionaryが帰ってきます

```
>>> PurchaseInfo.objects.all().aggregate(Max("count"))
SELECT MAX(`PurchaseInfo`.`count`) AS `count__max`
FROM `PurchaseInfo` [18.19ms]
{'count__max': 9}
```

以下のように戻り値として帰ってくるkeyの値も指定できます
```
>>> PurchaseInfo.objects.all().aggregate(max_count=Max("count"))
SELECT MAX(`PurchaseInfo`.`count`) AS `max_count`
FROM `PurchaseInfo` [9.88ms]
{'max_count': 9}
```

### Min(最小値)
最小値を取得できます

```
>>> PurchaseInfo.objects.all().aggregate(min_count=Min("count"))
SELECT MIN(`PurchaseInfo`.`count`) AS `min_count`
FROM `PurchaseInfo` [9.20ms]
{'min_count': 2}
```

### Sum(合計)
合計値を取得できます

```
>>> PurchaseInfo.objects.all().aggregate(total_count=Sum("count"))
SELECT SUM(`PurchaseInfo`.`count`) AS `total_count`
FROM `PurchaseInfo` [16.21ms]
{'total_count': 27}
```

### Avg(平均)
平均値を取得できます

```
>>> PurchaseInfo.objects.all().aggregate(avg_count=Avg("count"))
SELECT AVG(`PurchaseInfo`.`count`) AS `avg_count`
FROM `PurchaseInfo` [11.18ms]
{'avg_count': 5.4}
```

### Count(個数)
個数を取得できます

```
>>> PurchaseInfo.objects.all().aggregate(num_of_count=Count("count"))
SELECT COUNT(`PurchaseInfo`.`count`) AS `num_of_count`
FROM `PurchaseInfo` [30.80ms]
{'num_of_count': 5}
```

以上です

## 参考
https://docs.djangoproject.com/en/4.2/topics/db/aggregation/

https://note.crohaco.net/2014/django-aggregate/
