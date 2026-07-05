---
title: Django Rest Frameworkとdjango_filterを使ってCSVを出力しよう！
tags:
  - Python
  - Django
  - django-rest-framework
  - django-filter
private: false
updated_at: '2023-12-19T09:10:00+09:00'
id: 2dfcbad319775715cfe7
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Django Rest Frameworkを使ってCSVを出力する方法について解説します

## 前提
- Djangoのプロジェクトを作成済み
- django_filterについて一定の知識を有している

## ディレクトリ構成
```
tree
・
└── application
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── filters.py
    ├── fixtures
    │   └── fixture.json
    ├── models.py
    ├── urls.py
    └── views.py

```

## 必要なファイルの作成
実装の際に以下のファイルを作成します
- models.py
- fixture.json
- filters.py
- views.py

### Modelの作成
今回は
- User
- Customer
- Address

の3種類のModelを作成します
UserのModelについてはDjangoのAbstractUserを継承して作成します
詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

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

        MANAGEMENT = 0, "管理者"
        GENERAL = 1, "一般"
        PART_TIME = 2, "アルバイト"

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
    is_verified = models.BooleanField(
        default=False,
        db_comment="有効化有無",
    )

    USERNAME_FIELD = "employee_number"
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"
        db_table_comment = "システムユーザ"

    def __str__(self):
        return self.username


class Customer(models.Model):
    """お客様"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    kana = models.CharField(
        max_length=255,
        db_comment="カナ氏名",
    )
    name = models.CharField(
        max_length=255,
        db_comment="氏名",
    )
    birthday = models.DateField(
        db_comment="誕生日",
    )
    email = models.EmailField(
        db_comment="メールアドレス",
    )
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
        db_comment="電話番号",
    )
    address = models.OneToOneField(
        "Address",
        on_delete=models.CASCADE,
        related_name="address",
        db_comment="住所のFK",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        db_comment="更新日時",
    )
    created_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_created_by",
        db_comment="作成者ID",
    )
    updated_by = models.ForeignKey(
        User,
        on_delete=models.DO_NOTHING,
        related_name="%(class)s_updated_by",
        db_comment="更新者ID",
    )

    class Meta:
        db_table = "Customer"


class Address(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    prefecture = models.CharField(
        max_length=255,
        db_comment="都道府県",
    )
    municipalities = models.CharField(
        max_length=255,
        db_comment="市区町村",
    )
    house_no = models.CharField(
        max_length=255,
        db_comment="丁・番地",
    )
    other = models.CharField(
        max_length=255,
        blank=True,
        db_comment="その他(マンション名など)",
    )
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
        db_comment="郵便番号",
    )

    class Meta:
        db_table = "Address"

```

### Fixtureの作成
作成したmodelのfixture(テストデータ)を作成します

```fixutures.json
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
            "is_verified": true,
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
            "is_verified": true,
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
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.User",
        "pk": 4,
        "fields": {
            "employee_number": "00000004",
            "username": "test04",
            "password": "pbkdf2_sha256$390000$KF4YHJxvWjSODaXdxLBg6S$U5XDh8mR77kMMUtlRcBZS/bkaxdpjNR/P4zyy25g3/I=",
            "email": "test04@example.com",
            "role": 0,
            "is_superuser": 1,
            "is_verified": true,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z"
        }
    },
    {
        "model": "application.Customer",
        "pk": 1,
        "fields": {
            "kana": "オオサカタロウ",
            "name": "大阪太郎",
            "birthday": "1992-01-06",
            "email":"osaka@example.com",
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
            "email":"kyoto@example.com",
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
            "email":"hyogo@example.com",
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

### filterの作成
django_filtersを使ったFilterを作成します
filterで条件を絞り込んで出力する際に使用します
今回作成するfilterは以下の通りです

|model|field|絞り込み|
|--|--|--|
|Customer|name|部分一致|
||address|部分一致|
||birthday|完全一致|
||email|部分一致|
||phone_no|部分一致(前方一致)|

```filters.py
import django_filters
from django.db.models import Q
from django.db.models.functions import Concat

from application.models import Customer


class CustomerFilter(django_filters.FilterSet):
    """お客様のfilter"""

    name = django_filters.CharFilter(method="search_name")
    address = django_filters.CharFilter(method="search_address")

    class Meta:
        model = Customer
        fields = {
            "birthday": ["exact"],
            "email": ["contains"],
            "phone_no": ["startswith"],
        }

    def search_name(self, queryset, name, value):
        """

        Args:
            queryset
            name
            value

        Returns:
            queryset: customerから取得したnameもしくはkanaに該当するqueryset
        """
        return queryset.filter(
            Q(name__contains=value) | Q(kana__contains=value)
        )

    def search_address(self, queryset, address, value):
        """address_queryで取得した住所に該当するquerysetを取得
        Args:
            queryset
            address
        Returns:
            queryset: addressから取得した都道府県・市区町村・番地・その他に該当するqueryset
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

### Serializerの

### Viewの作成
Customer用のviewsetを作成し、CSV出力用のAPIを作成します
Filterを適用させるためにGETにしています

```views.py
import csv
import tempfile

from django.db import DatabaseError, transaction
from django.http import FileResponse
from django.utils import timezone
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from application.filters import CustomerFilter
from application.models import Address, Customer
from application.serializers.customer import (
    ImportCsvSerializer,
)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("address")
    serializer_class = None
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = CustomerFilter

                
    @action(methods=["get"], detail=False)
    def csv_export(self, request):
        """お客様一覧のCSVをエクスポートする用のAPI

        CSV形式でお客様一覧をエクスポートする

        Returns:
            CSVファイル
        """
        queryset = self.filter_queryset(self.get_queryset())
        file = self._create_export_customer_csv(queryset)
        filename = (
            "お客様データ＿" + timezone.localdate().strftime("%Y-%m-%d") + ".csv"
        )
        response = FileResponse(
            open(file.name, "rb"),
            as_attachment=True,
            content_type="application/csv",
            filename=filename,
        )
        return response

    def _create_export_customer_csv(self, customers):
        """エクスポートするCSVを作成するプライベートメソッド

        Args:
            customers : Customerのqueryset

        Returns:
            file: CSVファイル
        """
        file = tempfile.NamedTemporaryFile(delete=False)
        with open(file.name, "w") as csvfile:
            fieldnames = [
                "氏名",
                "カナ氏名",
                "誕生日",
                "メールアドレス",
                "電話番号",
                "作成日",
                "担当者",
                "都道府県",
                "市区町村",
                "丁・番地",
                "その他(マンション名など)",
                "郵便番号",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for customer in customers:
                writer.writerow(
                    {
                        "氏名": customer.name,
                        "カナ氏名": customer.kana,
                        "誕生日": customer.birthday,
                        "メールアドレス": customer.email,
                        "電話番号": customer.phone_no,
                        "作成日": customer.created_at.strftime("%Y/%m/%d"),
                        "担当者": customer.updated_by.username,
                        "都道府県": customer.address.prefecture,
                        "市区町村": customer.address.municipalities,
                        "丁・番地": customer.address.house_no,
                        "その他(マンション名など)": customer.address.other,
                        "郵便番号": customer.address.post_no,
                    }
                )
        # ファイルの読み取り/書き込み位置をファイルの先頭に戻す
        file.seek(0)
        return file

```

一つずつ解説してきます
まず、作成したCustomerFilterを使って以下のquerysetから絞り込んだQuerysetオブジェクトを取得します
```python
Customer.objects.select_related("address")
```

その後、 querysetという変数に代入し、_create_export_customer_csvメソッドを実行します
```python
queryset = queryset = self.filter_queryset(self.get_queryset())
file = self._create_export_customer_csv(queryset)
```

ファイルを作成し、openメソッドでwriteモードで開きます
定義したヘッダをCSVのヘッダとして記載し、for文とwriterowメソッドを使ってひたすらCSVファイルへの書き込みを行います
書き込みが終わったらCSVファイル内のポインタを先頭まで戻した上でfileをreturnします

```python
        file = tempfile.NamedTemporaryFile(delete=False)
        with open(file.name, "w") as csvfile:
            fieldnames = [
                "氏名",
                "カナ氏名",
                "誕生日",
                "メールアドレス",
                "電話番号",
                "作成日",
                "担当者",
                "都道府県",
                "市区町村",
                "丁・番地",
                "その他(マンション名など)",
                "郵便番号",
            ]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            for customer in customers:
                writer.writerow(
                    {
                        "氏名": customer.name,
                        "カナ氏名": customer.kana,
                        "誕生日": customer.birthday,
                        "メールアドレス": customer.email,
                        "電話番号": customer.phone_no,
                        "作成日": customer.created_at.strftime("%Y/%m/%d"),
                        "担当者": customer.updated_by.username,
                        "都道府県": customer.address.prefecture,
                        "市区町村": customer.address.municipalities,
                        "丁・番地": customer.address.house_no,
                        "その他(マンション名など)": customer.address.other,
                        "郵便番号": customer.address.post_no,
                    }
                )
        # ファイルの読み取り/書き込み位置をファイルの先頭に戻す
        file.seek(0)
        return file
```

DjangoのFileResponseを使ってレスポンスからCSVファイルを受け取れるようにします
```python        
        filename = (
            "お客様データ＿" + timezone.localdate().strftime("%Y-%m-%d") + ".csv"
        )
        response = FileResponse(
            open(file.name, "rb"),
            as_attachment=True,
            content_type="application/csv",
            filename=filename,
        )
        return response
```

## 実際に出力してみよう！
以下のようにヘッダとお客様情報を出力できていれば成功です

![スクリーンショット 2023-12-18 10.08.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ad6fc5ad-a07f-ec10-fcf9-397a29565490.png)

また、以下のようにqueryパラメータで絞り込んだ状態で出力できていれば成功です

![スクリーンショット 2023-12-18 10.24.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f5342713-dcad-e186-7595-1022146d2398.png)

![スクリーンショット 2023-12-18 10.26.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7dc8ec28-3eeb-7939-40e6-b1d9c601ab1a.png)

![スクリーンショット 2023-12-18 10.25.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f67462dc-c47c-d960-7a57-49d1b019cdef.png)

![スクリーンショット 2023-12-18 10.26.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0785ae58-f257-65d3-da92-403b494935dc.png)

## 参考
https://shotanukumizu-1000.hatenablog.com/entry/20210522#%E5%BD%B9%E5%89%B2%E3%82%A2%E3%82%AF%E3%82%BB%E3%82%B9%E4%BD%8D%E7%BD%AE%E3%81%AE%E7%A7%BB%E5%8B%95

