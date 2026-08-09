---
title: django-filtersとQオブジェクトを使って複数カラムのうちどちらか該当するデータを絞り込むには
tags:
  - Django
  - swagger
  - django-rest-framework
  - django-filter
private: false
updated_at: '2026-08-10T07:49:18+09:00'
id: 88fc94c6afc8dd37a8ea
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
django-filtersとQオブジェクトを使って今回は
- 名前
- カナ

のうちどちらかに該当するデータを絞り込む方法について解説していきたいと思います
例えば大阪太郎(オオサカタロウ)を名前もしくはカナ検索で絞り込みしようとしても下記のようにnameのクエリパラメータひとつで絞り込みできるようになります
```
'http://127.0.0.1:8080/api/customer/?name=大阪'
'http://127.0.0.1:8080/api/customer/?name=オオサカ'
```

カナ検索もしたい時にわざわざカナ用のクエリパラメータを作成しなくてもいいので楽ですので実装していきたいと思います

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

### そもそもQオブジェクトってなに？
ORやANDを使って複雑なクエリを検索をする際に使用されます
今回はnameとkanaでOR検索をするためfilters.pyで使用します

### models.py
今回はCustomer用のModelを作成し、kanaとnameのカラムを入れます
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

    class Meta:
        db_table = "Customer"
``` 

### serializers/customer.py
今回はModelSerializerを使用します
```serializers/customer.py
from rest_framework import serializers

from application.models import Customer


class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
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
```urls.py
from django.urls import include, path
from rest_framework_nested import routers

from application.views.customer import CustomerViewSet

router = routers.DefaultRouter()
router.register(r"customer", CustomerViewSet, basename="customer")

urlpatterns = [
    path(r"", include(router.urls)),
]
```

### fixtures.json
Customerのテストデータです
データを入れるときは
```
python manage.py loaddata fixtures.json
```
で一括で入れることができます

```fixtures.json
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
    }
]
```

### filters.py
ここてfilterの設定をします
```filters.py
import django_filters
from django.db.models import Q

from application.models import Customer


class CustomerFilter(django_filters.FilterSet):
    """お客様の
    - 氏名・カナ氏

    で絞り込むFilter

    Args:
        django_filters
    """

    name = django_filters.CharFilter(method="search_name", label="name")

    class Meta:
        model = Customer
        fields = ["name"]

    def search_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__contains=value) | Q(kana__contains=value)
        )
```

通常のCharFilterだとnameでしか絞り込みができないため、search_nameという独自の検索用メソッドを作成します
```python
name = django_filters.CharFilter(method="search_name", label="name")
```

ここで前述のQオブジェクトを使って絞り込みします
```python
    def search_name(self, queryset, name, value):
        return queryset.filter(
            Q(name__contains=value) | Q(kana__contains=value)
        )
```

#### search_name()の引数
- querysetの変数内にはCustomerのオブジェクトが入ります
- value内には指定した検索条件が入ります
    - 例えば"大阪"で絞り込もうと思った場合はvalue内に"大阪"が入ります
- search_name()の引数にdjango-filtersで指定したfilter名(今回だとname)も入れないとカスタムメソッドが機能しないので注意です
```
print(queryset)
<QuerySet [<Customer: Customer object (00000000-0000-0000-0000-000000000001)>, <Customer: Customer object (00000000-0000-0000-0000-000000000002)>, <Customer: Customer object (00000000-0000-0000-0000-000000000003)>]>
print(value)
'大阪'
print(name)
'name'
```

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
>>> from django.db.models import Q
>>> Customer.objects.filter(Q(name__contains="大阪") | Q(kana__contains="大阪"))
SELECT `Customer`.`id`,
       `Customer`.`kana`,
       `Customer`.`name`,
       `Customer`.`birthday`,
       `Customer`.`phone_no`,
       `Customer`.`address_id`
FROM `Customer`
WHERE (`Customer`.`name` LIKE BINARY '%大阪%'
       OR `Customer`.`kana` LIKE BINARY '%大阪%')
LIMIT 21 [1.05ms]
<QuerySet [<Customer: Customer object (00000000-0000-0000-0000-000000000001)>]>
```

このようにWHERE文内にORを使ってnameまたはkanaのカラム内で"大阪"が含まれているオブジェクトを絞り込んでいることが確認できました

## Swaggerで検証してみよう
Swaggerを開くと以下のようにname用のfilterが作成されています
![スクリーンショット 2023-05-14 10.38.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d091ef76-b845-489e-56d9-931aa7e4f769.png)

![スクリーンショット 2023-05-14 10.38.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/babc9f1a-bdee-ffef-aa1d-c3fe850b308b.png)

nameに"大阪"を入れても"オオサカ"を入れても該当するお客様を絞り込みできていることが確認できました
![スクリーンショット 2023-05-14 10.39.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f427aee6-d4e9-d22a-2ff6-de74522f8f77.png)

![スクリーンショット 2023-05-14 10.40.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c985a0b7-9aed-c37b-5365-28f1dc84db74.png)

![スクリーンショット 2023-05-14 10.40.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/60beac2e-4ab9-5be2-4626-5af8bada9f2c.png)

![スクリーンショット 2023-05-14 10.41.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/04a6308e-d8e0-ac33-1696-1cdfb0138e0d.png)

## 参考
https://stackoverflow.com/questions/57270470/django-filter-how-to-make-multiple-fields-search-with-django-filter

https://docs.djangoproject.com/en/4.2/topics/db/queries/
