---
title: '[Django Rest Framework] Pytestを使ってdjango-filterのテストを作成しよう！'
tags:
  - Django
  - pytest
  - django-rest-framework
  - django-filter
  - FactoryBoy
private: false
updated_at: '2024-08-21T08:54:04+09:00'
id: 9d5eaa9de90a429fa455
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
pytestを使ってdjango-filterのテストコードを書く方法について解説します

## 前提
- Django Rest Frameworkのプロジェクトを作成済み
- django-filterをインストール済み

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
    ├── serializers.py
    ├── tests
    │   ├── __init__.py
    │   ├── factories
    │   │   └── factory.py
    │   └── test_filters.py
    ├── urls.py
    └── views.py
```

## はじめに
テストコードを作成する前に以下を作成します
- model
- fixture
- factoryboy
- filter
- serializer
- view

### modelの作成
今回は
- User
- Customer
- Address

のmodelを作成します

```application/models.py
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

### fixtureの作成
作成したmodelのfixture(テストデータ)を作成します

```application/fixtures/fixture.json
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

### factoryの作成
```application/tests/factories/factory.py
from datetime import datetime, timedelta

from factory import Faker, PostGenerationMethodCall, Sequence, SubFactory
from factory.django import DjangoModelFactory

from application.models import Address, Customer, User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    username = Sequence(lambda n: "テスト利用者{}".format(n))
    employee_number = Sequence(lambda n: "{0:08}".format(n + 100))
    password = PostGenerationMethodCall("set_password", "test")
    email = Faker("email")
    role = Faker(
        "random_int",
        min=0,
        max=2,
    )
    created_at = Faker(
        "date_between_dates",
        date_start=(datetime.now() - timedelta(days=20)).date(),
        date_end=datetime.now(),
    )
    updated_at = Faker(
        "date_between_dates",
        date_start=(datetime.now() - timedelta(days=20)).date(),
        date_end=datetime.now(),
    )
    is_verified = True


class AddressFactory(DjangoModelFactory):
    class Meta:
        model = Address

    prefecture = Faker("administrative_unit", locale="ja_JP")
    municipalities = Faker("city", locale="ja_JP")
    house_no = str(Faker("ban", locale="ja_JP")) + str(
        Faker("gou", locale="ja_JP")
    )
    other = str(Faker("building_name", locale="ja_JP")) + str(
        Faker("building_number", locale="ja_JP")
    )
    post_no = Faker("random_number", digits=7)


class CustomerFactory(DjangoModelFactory):
    class Meta:
        model = Customer

    kana = Sequence(lambda n: "テストコキャク{}".format(n))
    name = Sequence(lambda n: "テスト顧客{}".format(n))
    birthday = Faker(
        "date_between_dates",
        date_start=(datetime.now().date() - timedelta(days=365 * 50)),
        date_end=(datetime.now().date() - timedelta(days=365 * 20)),
    )
    email = Faker("email")
    phone_no = Sequence(lambda n: f"080" + "{0:08}".format(n + 100))
    address = SubFactory(AddressFactory)

```

### filterの作成
django_filtersを使ったFilterを作成します
今回作成するfilterは以下の通りです

|model|field|絞り込み|
|--|--|--|
|User|created_at|範囲指定|
||username|部分一致|
||email|部分一致|
||role|複数選択|
|Customer|name|部分一致|
||address|部分一致|
||birthday|完全一致|
||email|部分一致|
||phone_no|部分一致(前方一致)|

```application/filters.py
import django_filters
from application.models import Customer, User
from django.db.models import Q
from django.db.models.functions import Concat


class UserFilter(django_filters.FilterSet):
    """システムユーザのfilter"""
    
    created_at = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = User
        fields = {
            "username": ["contains"],
            "email": ["contains"],
            "role": ["in"],
        }


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
        """取得した名前に該当するquerysetを取得
        
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
        """取得した住所に該当するquerysetを取得
        
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

### serializerの作成
- User
- Customer

のSerializerを作成します

```application/serializers.py
from rest_framework import serializers

from application.models import Customer, User


class UserSerializer(serializers.ModelSerializer):
    """ユーザ用シリアライザ"""

    class Meta:
        model = User
        fields = [
            "id",
            "employee_number",
            "username",
            "email",
            "role",
            "is_verified",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        rep = super(UserSerializer, self).to_representation(instance)
        rep["role"] = instance.get_role_display()
        return rep


class CustomerSerializer(serializers.ModelSerializer):
    """ユーザ用シリアライザ"""

    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["id"]

    def to_representation(self, instance):
        rep = super(CustomerSerializer, self).to_representation(instance)
        rep["address"] = (
            instance.address.prefecture
            + instance.address.municipalities
            + instance.address.house_no
            + instance.address.other
        )
        rep["post_no"] = instance.address.post_no
        return rep
```

### viewの作成
- User
- Customer

のViewSetを作成します

```application/views.py
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ModelViewSet

from application.filters import CustomerFilter, UserFilter
from application.models import Customer
from application.serializers.customer import CustomerSerializer, UserSerializer


class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = UserFilter    


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("address")
    serializer_class = CustomerSerializer
    permission_classes = [AllowAny]
    filter_backends = [
        DjangoFilterBackend,
    ]
    filterset_class = CustomerFilter

```

## filterのテストを作成してみよう！
ここからfilterのテストを行います

### 完全一致
Filter内にfieldと項目名を入れます
```python
customer_filter = CustomerFilter({"name": "降田絞込"})
```

### 複数一致
`{field}__in`と書くと複数一致でfilterできます
```python
    user_filter = UserFilter(
        {"role__in": f"{User.Role.MANAGEMENT},{User.Role.GENERAL}"}
    )
```

### 前方一致
`{field}__startswith`と書くと前方一致でfilterできます
```python
customer_filter = CustomerFilter({"phone_no": "01202018"})
```

### test_filters.py
filterのinstance内にqs(queryset)という配列があり、qsのcountや配列の順番を使ってテストコードを作成しています
ソースコードは以下の通りです

```application/tests/test_filters.py
from datetime import timedelta

import pytest
from application.filters import CustomerFilter, UserFilter
from application.models import User
from application.tests.factories.customer import AddressFactory, CustomerFactory
from application.tests.factories.user import UserFactory
from django.utils import timezone
from freezegun import freeze_time


@pytest.mark.django_db
def test_user_filter_email_contains():
    """システムユーザ名を部分一致でフィルターできる事を確認する"""

    user = UserFactory(username="テストフィルターユーザ")
    user_filter = UserFilter({"email__contains": "テストフィルター"})
    assert user_filter.qs.count() == 1
    assert user_filter.qs[0] == user


@pytest.mark.django_db
def test_user_filter_email_contains():
    """メールアドレスを部分一致でフィルターできる事を確認する"""

    user = UserFactory(email="test_filter@test.com")
    user_filter = UserFilter({"email__contains": "test_filter"})
    assert user_filter.qs.count() == 1
    assert user_filter.qs[0] == user


@pytest.mark.django_db
def test_user_filter_role_in():
    """ロールを複数フィルターできる事を確認する"""

    User.objects.all().update(role=User.Role.PART_TIME)
    management_user = UserFactory(role=User.Role.MANAGEMENT)
    general_user = UserFactory(role=User.Role.MANAGEMENT)
    user_filter = UserFilter(
        {"role__in": f"{User.Role.MANAGEMENT},{User.Role.GENERAL}"}
    )
    assert user_filter.qs.count() == 2
    assert user_filter.qs[0] == management_user
    assert user_filter.qs[1] == general_user


@pytest.mark.django_db
def test_inquiry_application_date_range_filter():
    """作成日をフィルターできることを確認する"""

    today = timezone.now()
    with freeze_time(today):
        first_user = UserFactory()
        second_user = UserFactory()
        inquiry_filter = UserFilter({"created_at_after": today})
        assert inquiry_filter.qs.count() == 2
        assert inquiry_filter.qs[0] == first_user
        assert inquiry_filter.qs[1] == second_user


@pytest.mark.django_db
def test_customer_name_kana_filter_contains():
    """氏名・カナ氏名でフィルターできる事を確認する"""

    customer = CustomerFactory(
        name="降田絞込",
        kana="フィルタシボリコミ",
    )
    customer_filter = CustomerFilter({"name": "降田絞込"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer
    customer_filter = CustomerFilter({"name": "フィルタシボリコミ"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer


@pytest.mark.django_db
def test_customer_address_filter_contains():
    """住所でフィルターできる事を確認する"""

    address = AddressFactory()
    customer = CustomerFactory(address=address)
    customer_filter = CustomerFilter({"address": f"{address.prefecture}"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer
    customer_filter = CustomerFilter({"address": f"{address.municipalities}"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer
    customer_filter = CustomerFilter({"address": f"{address.house_no}"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer
    customer_filter = CustomerFilter({"address": f"{address.other}"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer


@pytest.mark.django_db
def test_customer_birthday_filter_exact():
    """誕生日を完全一致でフィルターできる事を確認する"""

    customer = CustomerFactory(birthday="1955-01-01")
    customer_filter = CustomerFilter({"birthday": "1955-01-01"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer


@pytest.mark.django_db
def test_customer_filter_email_contains():
    """メールアドレスを部分一致でフィルターできる事を確認する"""

    customer = CustomerFactory(email="test_filter@test.com")
    customer_filter = CustomerFilter({"email__contains": "test_filter"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer


@pytest.mark.django_db
def test_customer_phone_no_filter_starts_with():
    """電話番号を前方一致でフィルターできる事を確認する"""

    customer = CustomerFactory(phone_no="0120201810")
    customer_filter = CustomerFilter({"phone_no__startswith": "01202018"})
    assert customer_filter.qs.count() == 1
    assert customer_filter.qs[0] == customer

```

## まとめ
実際にrequestを送ってテストしてもいいですがdjango-filterを使って書くとコード量が少なく、直感的に書けるのでおすすめです
