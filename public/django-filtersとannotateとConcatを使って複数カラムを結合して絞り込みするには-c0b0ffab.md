---
title: django-filtersとannotateとConcatを使って複数カラムを結合して絞り込みするには？
tags:
  - Django
  - swagger
  - django-rest-framework
  - django-filter
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: c0b0ffab9d04578dd4f0
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
django-filtersを使って複数カラムを結合して絞り込む方法について解説していきたいと思います
今回は住所を例に
- 都道府県
- 市区町村
- 丁・番地
- その他(マンション名など)

を結合させて絞り込みをおこないます
結合するのは例えば都道府県と市区町村を組み合わせて検索した時に
各項目でのみ検索してしまったがために該当する住所を検索できなくなってしまうのを防ぐためです

## 前提
- django-filtersをインストール済み
- django-filtersの基本的な使い方を知っている
- 必須ではないが最後にSwaggerで検証するため、Swaggerを設定済み

## ファイル構成
ファイル構成は以下の通りです
```
application
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── filters.py
   ├── fixtures
   |   └── fixture.json
   ├── migrations
   ├── models.py
   ├── serializers
   |   └── customer.py
   ├── urls.py
   └── views
       └── customer.py
```

上記のうち

- models.py
- serializers/customer.py
- views/customer.py
- urls.py
- fixtures/fixture.json
- filters.py

に必要な設定を記載していきます

### annoateって何？
日本語で翻訳すると注釈の意味です
前述した
- 都道府県
- 市区町村
- 丁・番地
- その他(マンション名など)

を結合して検索する際にannotateを使って結合されたカラムを別カラムとして扱うことができます
この説明だけだといまいちピンとこないかもしれませんのでfilters.pyを作成する際も説明します

### Concatって何？
複数の文字列を連結した文字列を取得する際に使用するクラスです
今回の結合検索で使用します

### models.py
CustomerとAddressのModelを作成します
```models.py
import uuid

from django.core.validators import RegexValidator
from django.db import models


class Customer(models.Model):
    """お客様"""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kana = models.CharField(max_length=255)
    """カナ氏名"""
    name = models.CharField(max_length=255)
    """氏名"""
    birthday = models.DateField()
    """誕生日"""
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
    )
    """電話番号"""
    address = models.OneToOneField("Address", on_delete=models.CASCADE)
    """住所"""

    class Meta:
        db_table = "Customer"


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prefecture = models.CharField(max_length=255, null=True)
    """都道府県"""
    municipalities = models.CharField(max_length=255, null=True)
    """市区町村"""
    house_no = models.CharField(max_length=255, null=True)
    """市区町村"""
    other = models.CharField(max_length=255, null=True)
    """丁・番地"""
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
    )
    """郵便番号"""

    class Meta:
        db_table = "Address"
```

### serializers/customer.py
CustomerSerializerを作成します
その際にto_representationを使ってListする際は住所が結合された状態で表示させます

```serializers/customer.py
from rest_framework import serializers

from application.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["address"]

    def to_representation(self, instance):
        ret = super(CustomerSerializer, self).to_representation(instance)
        address = instance.address
        ret["address"] = (
            address.prefecture
            + address.municipalities
            + address.house_no
            + address.other
        )
        return ret
```

### views/customer.py
CustomerViewSetを作成し、django-filtersの設定をします

```views/customer.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.viewsets import ModelViewSet

from application.filters import CustomerFilter
from application.models import Customer
from application.serializers.customer import CustomerSerializer


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = CustomerFilter
```

### urls.py
Customer用のurlを作成します

```application.urls.py
from django.urls import include, path
from rest_framework_nested import routers

from application.views.customer import CustomerViewSet

router = routers.DefaultRouter()
router.register(r"customer", CustomerViewSet, basename="customer")

urlpatterns = [
    path(r"", include(router.urls)),
]
```

### fixture.json
CustomerとAddressのテストデータです
データを入れるときは
```
python manage.py loaddata fixture.json
```
で一括で入れることができます

```fixture.json
[
    {
        "model": "application.Customer",
        "pk": 1,
        "fields": {
            "kana": "オオサカタロウ",
            "name": "大阪太郎",
            "birthday": "1992-01-06",
            "phone_no": "08011112222",
            "address": 1
        }
    },
    {
        "model": "application.Customer",
        "pk": 2,
        "fields": {
            "kana": "キョウトジロウ",
            "name": "京都二郎",
            "birthday": "1994-01-06",
            "phone_no": "08022223333",
            "address": 2
        }
    },
    {
        "model": "application.Customer",
        "pk": 3,
        "fields": {
            "kana": "ヒョウゴサブロウ",
            "name": "兵庫三郎",
            "birthday": "1995-03-06",
            "phone_no": "08033334444",
            "address": 3
        }
    },
    {
        "model": "application.Address",
        "pk": 1,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "清水",
            "other": "1-294",
            "post_no": "6050862"
        }
    },
    {
        "model": "application.Address",
        "pk": 2,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "北区金閣寺町1",
            "other": "",
            "post_no": "6038361"
        }
    },
    {
        "model": "application.Address",
        "pk": 3,
        "fields": {
            "prefecture": "京都府",
            "municipalities": "京都市東山区",
            "house_no": "左京区銀閣寺町2",
            "other": "",
            "post_no": "6068402"
        }
    }
]
```

### filters.py
ここてfilterの設定をします
```filters.py
import django_filters
from django.db.models import Q
from django.db.models.functions import Concat

from application.models import Customer


class CustomerFilter(django_filters.FilterSet):
    """お客様の
    - 住所

    で絞り込むFilter

    Args:
        django_filters
    """

    address = django_filters.CharFilter(method="search_address")

    class Meta:
        model = Customer
        fields = ["address"]

    def search_address(self, queryset, address, value):
        """address_queryで取得した住所に該当するquerysetを取得
        Args:
            queryset
            address_query
        Returns:
            queryset: address_queryで取得した都道府県・市区町村・番地・その他に該当するqueryset
        """
        return queryset.annotate(
            customer_address=Concat(
                "address__prefecture",
                "address__municipalities",
                "address__house_no",
                "address__post_no",
                "address__other",
            )
        ).filter(customer_address__icontains=value)
```

通常のCharFilterだと1カラムでしか絞り込みができないため、search_nameという独自の検索用メソッドを作成します

```python
address = django_filters.CharFilter(method="search_address")
```

ここでsearch_address()メソッドを呼ぶよう設定します
```python
    def search_address(self, queryset, address, value):
        """address_queryで取得した住所に該当するquerysetを取得
        Args:
            queryset
            address_query
        Returns:
            queryset: address_queryで取得した都道府県・市区町村・番地・その他に該当するqueryset
        """
        return queryset.annotate(
            customer_address=Concat(
                "address__prefecture",
                "address__municipalities",
                "address__house_no",
                "address__post_no",
                "address__other",
            )
        ).filter(customer_address__icontains=value)
```

### search_address()の引数
- querysetの変数内にはCustomerのオブジェクトが入ります
- value内には指定した検索条件が入ります
    - 例えば"京都"で絞り込もうと思った場合はvalue内に"京都"が入ります
- search_address()の引数にdjango-filtersで指定したfilter名(今回だとaddress)も入れないとカスタムメソッドが機能しないので注意です

### annotate
前述のannnotateを使用することで
customer_addressという
- 都道府県
- 市区町村
- 丁・番地
- その他(マンション名など)

をConcatで結合させたカラムで絞り込みすることができます
そのため、上記の4つのカラムの中を見て検索しているかのように感じますが
実際は裏ではcustomer_addressという1つのカラムの中を検索しています
annotationを使う際はModelの既存のカラムと被らないようにしましょう

### 発行されているSQLについて
querysetにCustomerのオブジェクトが入っていることがわかったのでShellで確認してみましょう
django-debug-toolbarを使えばDjangoのORMで発行されたSQLが簡単にわかるので使い方を知らない方は以下の記事を参考にしてください

https://qiita.com/shun198/items/637c05e0701114ae5b3d

```
python manage.py debugsqlshell
Python 3.11.3 (main, Apr 12 2023, 14:31:14) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from application.models import Customer
>>> from django.db.models.functions import Concat
>>> Customer.objects.annotate(customer_address=Concat("address__prefecture","address__municipalities","address__house_no","address__post_no","address__other",)).filter(customer_address__icontains="京都")
SELECT `Customer`.`id`,
       `Customer`.`kana`,
       `Customer`.`name`,
       `Customer`.`birthday`,
       `Customer`.`phone_no`,
       `Customer`.`address_id`,
       CONCAT_WS('', `Address`.`prefecture`, CONCAT_WS('', `Address`.`municipalities`, CONCAT_WS('', `Address`.`house_no`, CONCAT_WS('', `Address`.`post_no`, `Address`.`other`)))) AS `customer_address`
FROM `Customer`
INNER JOIN `Address` ON (`Customer`.`address_id` = `Address`.`id`)
WHERE CONCAT_WS('', `Address`.`prefecture`, CONCAT_WS('', `Address`.`municipalities`, CONCAT_WS('', `Address`.`house_no`, CONCAT_WS('', `Address`.`post_no`, `Address`.`other`)))) LIKE '%京都%'
LIMIT 21 [1.72ms]
<QuerySet [<Customer: Customer object (00000000-0000-0000-0000-000000000001)>, <Customer: Customer object (00000000-0000-0000-0000-000000000002)>, <Customer: Customer object (00000000-0000-0000-0000-000000000003)>]>
```

このように"京都"が含まれているオブジェクトを絞り込んでいることが確認できました

## Swaggerで検証してみよう
Swaggerを開くと以下のようにaddress用のfilterが作成されています

![スクリーンショット 2023-05-14 11.46.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/88d4d5c0-0fce-d91f-9c92-9fb1a28ed2fa.png)

例えば
- 都道府県
- 市区町村
 
のように複数カラムを結合して絞り込むことに成功したことを確認できました

![スクリーンショット 2023-05-14 11.47.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/36865751-e26b-bfbd-7ad2-1df2e6f58f0f.png)

![スクリーンショット 2023-05-14 11.47.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f21b8827-4290-ace0-22bd-81c56ec703d3.png)


## 参考
https://qiita.com/knitbow/items/be26d0406fa922186bf7

https://www.javadrive.jp/mysql/function/index35.html

https://docs.djangoproject.com/en/1.8/ref/models/database-functions/

https://www.northtorch.co.jp/archives/1308
