---
title: 'factory_boyを使ってテストコードを作成しよう！ '
tags:
  - Django
  - pytest
  - django-rest-framework
  - Faker
private: false
updated_at: '2023-11-23T15:05:24+09:00'
id: 80bd2a79e483e7a72c6d
organization_url_name: null
slide: false
---
## 概要
Pythonでテストコードを書く際にfactory_boyを使うとテスト用のデータの作成と管理を簡単にすることができます
factory_boyの使い方について解説していきます

## 前提
- WebフレークワークはDjangoを使用
- テストフレームワークはPytestを使用
- Model、Serializer、Viewのテストを作成しまs

## ファイル構成
```
application
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── migrations
   ├── models.py
   ├── serializers.py
   ├── tests
   |   ├── factories
   |   |   ├── __init__.py
   |   |   ├── customer.py
   |   |   └── user.py
   |   ├── models
   |   |   ├── __init__.py
   |   |   ├── customer.py
   |   |   └── user.py
   |   ├── serializers
   |   |   ├── __init__.py
   |   |   └── user.py
   |   └── views
   |       ├── __init__.py
   |       └── user.py
   ├── views.py
   └── urls.py
```

## 初期設定
### factory_boyのインストール
factory_boyをインストールしましょう

```
pip install factory_boy
```

### modelの作成
今回は
- システムユーザ
- お客様
- お客様の住所

のmodelを作成していきます
今回は独自でシステムユーザを作成しているので詳細について気になる方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

```application/models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models


# カスタムユーザクラスを定義
class User(AbstractUser):
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
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    employee_number = models.CharField(
        unique=True,
        validators=[RegexValidator(r"^[0-9]{8}$")],
        max_length=8,
        # 管理者のログイン画面で社員番号と表示される
        verbose_name="社員番号",
    )
    """社員番号"""
    username = models.CharField(
        max_length=150,
        unique=True,
        validators=[username_validator],
    )
    """ユーザ名"""
    email = models.EmailField(max_length=254, unique=True)
    """メールアドレス"""
    role = models.PositiveIntegerField(
        choices=Role.choices, default=Role.PART_TIME
    )
    """ロール"""
    created_at = models.DateTimeField(auto_now_add=True)
    """作成日"""
    updated_at = models.DateTimeField(auto_now=True)
    """更新日"""

    # デフォルトはusernameだが今回は社員番号を指定
    USERNAME_FIELD = "employee_number"
    # uniqueのemailとusernameを指定
    REQUIRED_FIELDS = ["email", "username"]

    class Meta:
        ordering = ["employee_number"]
        db_table = "User"

    def __str__(self):
        return self.username


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
    address = models.ForeignKey(
        "Address",
        on_delete=models.CASCADE,
        related_name="address",
    )
    """住所"""

    class Meta:
        db_table = "Customer"


class Address(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    prefecture = models.CharField(max_length=255)
    """都道府県"""
    municipalities = models.CharField(max_length=255)
    """市区町村"""
    house_no = models.CharField(max_length=255)
    """丁・番地"""
    other = models.CharField(max_length=255, blank=True)
    """その他(マンション名など)"""
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
    )
    """郵便番号"""

    class Meta:
        db_table = "Address"
```

## factory_boyの作成方法
factoriesフォルダの配下に
- user.py
- customer.py

を作成し、必要な設定を記載していきます

### user.py
Djangoでfactory_boyを使用する際はDjangoModelFactoryクラスを継承させてテストデータ用のクラスを定義します
passwordの生成に関してはPostGenerationMethodCallを使ってDjangoのset_password関数を実行しており、
テストデータのパスワードを`test`にして暗号化させた上で保存しています

```application/tests/factories/user.py
from datetime import datetime, timedelta

from factory import Faker, PostGenerationMethodCall, Sequence
from factory.django import DjangoModelFactory

from application.models import User


class UserFactory(DjangoModelFactory):
    class Meta:
        model = User

    # ユニーク制約があるのでオートインクリメント
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

```

#### Fakerクラス
Fakerを使うとランダムなテストデータを生成することができます
今回はFactoryBoyのFakerクラスを使用します
また、後述する住所に関してですが`locale="ja_JP"`と指定することで日本独自のテストデータ(例えば都道府県など)を生成できます
以下がFakerクラスのソースコードです

```factory_boy/factory/faker.py
class Faker(declarations.BaseDeclaration):
    """Wrapper for 'faker' values.

    Args:
        provider (str): the name of the Faker field
        locale (str): the locale to use for the faker

        All other kwargs will be passed to the underlying provider
        (e.g ``factory.Faker('ean', length=10)``
        calls ``faker.Faker.ean(length=10)``)

    Usage:
        >>> foo = factory.Faker('name')
    """
    def __init__(self, provider, **kwargs):
        locale = kwargs.pop('locale', None)
        self.provider = provider
        super().__init__(
            locale=locale,
            **kwargs)
```

詳細は以下の公式ドキュメントを参照してください

https://faker.readthedocs.io/en/master/

### customer.py
SubFactoryを使うことでFKに他のFactoryのオブジェクトを指定することができます

```application/tests/factories/customer.py
from datetime import datetime, timedelta

import factory
from factory import Faker, Sequence, SubFactory

from application.models import Address, Customer


class AddressFactory(factory.django.DjangoModelFactory):
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


class CustomerFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Customer

    kana = Sequence(lambda n: "テストコキャク{}".format(n))
    name = Sequence(lambda n: "テスト顧客{}".format(n))
    birthday = Faker(
        "date_between_dates",
        date_start=(datetime.now().date() - timedelta(days=365 * 50)),
        date_end=(datetime.now().date() - timedelta(days=365 * 20)),
    )
    phone_no = Sequence(lambda n: f"080" + "{0:08}".format(n + 100))
    address = SubFactory(AddressFactory)
```

## Modelのテスト
### test_user.py
ユーザのテストを作成します
```python
user = UserFactory()
```
と記述するだけで簡単にシステムユーザのテストデータを作成することができます
また、

```python
def get_user(id):
    return User.objects.get(pk=id)
```
で作成したテストデータを取得し、各Fieldに対してassertで一致するかどうかテストします
一致しなかった場合はpytest.raisesを使ってどんなエラーが出るか判定します
```python
    employee_number = "1" * 9
    with pytest.raises(DataError):
        UserFactory(employee_number=employee_number)
```

テストコードは以下の通りです
データベースにアクセスするため`@pytest.mark.django_db`のデコレータを忘れず入れましょう
```application/tests/models/test_user.py
import pytest
from django.db.utils import DataError, IntegrityError

from application.models import User
from application.tests.factories.user import UserFactory


def get_user(id):
    return User.objects.get(pk=id)


@pytest.mark.django_db
def test_employee_number_length_can_be_8():
    """employee_numberの長さの最大値が8文字"""
    employee_number = "1" * 8
    user = UserFactory(employee_number=employee_number)
    assert get_user(user.id).employee_number == employee_number


@pytest.mark.django_db
def test_employee_number_length_cannot_be_9_or_longer():
    """employee_numberの長さが9文字以上にならない"""
    employee_number = "1" * 9
    with pytest.raises(DataError):
        UserFactory(employee_number=employee_number)


@pytest.mark.django_db
def test_employee_number_length_cannot_be_null():
    """employee_numberはnullにならない"""
    with pytest.raises(IntegrityError):
        UserFactory(employee_number=None)


@pytest.mark.django_db
def test_employee_number_length_must_be_unique():
    """employee_numberはuniqueでなければならない"""
    employee_number = "1" * 8
    UserFactory(employee_number=employee_number)
    with pytest.raises(IntegrityError):
        UserFactory(employee_number=employee_number)


@pytest.mark.django_db
def test_username_length_can_be_150():
    """usernameの長さの最大値が150文字"""
    username = "a" * 150
    user = UserFactory(username=username)
    assert get_user(user.id).username == username


@pytest.mark.django_db
def test_username_length_cannot_be_151_or_longer():
    """usernameの長さの最大値が151文字以上にならない"""
    username = "a" * 151
    with pytest.raises(DataError):
        UserFactory(username=username)


@pytest.mark.django_db
def test_username_cannot_be_null():
    """usernameはnullにできない"""
    with pytest.raises(IntegrityError):
        UserFactory(username=None)


@pytest.mark.django_db
def test_username_must_be_unique():
    """usernameはuniqueでなければならない"""
    username = "a" * 150
    UserFactory(username=username)
    with pytest.raises(IntegrityError):
        UserFactory(username=username)


@pytest.mark.django_db
def test_email_length_can_be_254():
    """emailの長さの最大値が254文字"""
    email = "a" * 245 + "@test.com"
    user = UserFactory(email=email)
    assert get_user(user.id).email == email


@pytest.mark.django_db
def test_email_length_cannot_be_255_or_longer():
    """emailの長さの最大値が255文字以上にならない"""
    email = "a" * 246 + "@test.com"
    with pytest.raises(DataError):
        UserFactory(email=email)


@pytest.mark.django_db
def test_email_cannot_be_null():
    """emailはnullにできない"""
    with pytest.raises(IntegrityError):
        UserFactory(email=None)


@pytest.mark.django_db
def test_email_must_be_unique():
    """emailはuniqueでなければならない"""
    email = "a" * 245 + "@test.com"
    UserFactory(email=email)
    with pytest.raises(IntegrityError):
        UserFactory(email=email)


@pytest.mark.django_db
def test_role_can_be_management():
    """管理者のロール"""
    role = User.Role.MANAGEMENT
    user = UserFactory(role=role)
    assert get_user(user.id).role == role


@pytest.mark.django_db
def test_role_can_be_general():
    """一般のロール"""
    role = User.Role.GENERAL
    user = UserFactory(role=role)
    assert get_user(user.id).role == role


@pytest.mark.django_db
def test_role_can_be_part_time():
    """アルバイトのロール"""
    role = User.Role.PART_TIME
    user = UserFactory(role=role)
    assert get_user(user.id).role == role

```

#### テストデータには何が入ってるの？

では、実際にテストデータの中を見てみましょう
```python
@pytest.mark.django_db
def test_employee_number_length_can_be_8():
    """employee_numberの長さの最大値が8文字"""
    employee_number = "1" * 8
    user = UserFactory(employee_number=employee_number)
    print(user.__dict__)
    assert get_user(user.id).employee_number == employee_number
```

userの中は以下のようにランダムに生成されていることが確認できます
```
'password':'pbkdf2_sha256$600000$AsfCb2R6rRgu3Kmpbf7aff$elbjshRXzE4DYAuvc/bOWwptY+fn7y4iVbnlVywAXJQ='
'last_login':None
'is_superuser':False
'is_staff':False
'is_active':True
'id':UUID('9a0a7b4b-c7ec-4579-8e71-e6efc8daf567')
'employee_number':'11111111'
'username':'テスト利用者0'
'email':'gford@example.com'
'role':2
'created_at':datetime.datetime(2023, 5, 22, 0, 52, 55, 980457, tzinfo=datetime.timezone.utc)
'updated_at':datetime.datetime(2023, 5, 22, 0, 52, 56, 167401, tzinfo=datetime.timezone.utc)
```

### test_customer.py
Customerのテストも同様です

```application/tests/models/test_customer.py
from datetime import datetime, timedelta

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import DataError, IntegrityError

from application.models import Address, Customer
from application.tests.factories.customer import AddressFactory, CustomerFactory


def get_customer(id):
    return Customer.objects.get(pk=id)


def get_address(id):
    return Address.objects.get(pk=id)


@pytest.mark.django_db
def test_kana_length_can_be_255():
    """カナ氏名の長さの最大値が255文字"""
    kana = "a" * 255
    customer = CustomerFactory(kana=kana)
    assert get_customer(customer.id).kana == kana


@pytest.mark.django_db
def test_name_length_can_be_255():
    """カナ氏名の長さの最大値が255文字"""
    name = "a" * 255
    customer = CustomerFactory(name=name)
    assert get_customer(customer.id).name == name


@pytest.mark.django_db
def test_birthday_can_be_date():
    """誕生日が日付のフォーマット"""
    birthday = datetime.now().date() - timedelta(days=365 * 20)
    customer = CustomerFactory(birthday=birthday)
    assert get_customer(customer.id).birthday == birthday


@pytest.mark.django_db
def test_birthday_is_not_date():
    """誕生日が日付以外のフォーマット"""
    birthday = "1995-09-1-8"
    with pytest.raises(ValidationError):
        CustomerFactory(birthday=birthday)


@pytest.mark.django_db
def test_birthday_cannot_be_null():
    """誕生日nullにできない"""
    with pytest.raises(IntegrityError):
        CustomerFactory(birthday=None)


@pytest.mark.django_db
def test_phone_length_can_be_11():
    """phone_numberの長さの最大値が11文字"""
    phone_no = "080" + "1" * 8
    customer = CustomerFactory(phone_no=phone_no)
    assert get_customer(customer.id).phone_no == phone_no


@pytest.mark.django_db
def test_phone_length_cannot_be_12_or_longer():
    """phone_numberの長さが12文字以上にならない"""
    phone_no = "080" + "1" * 9
    with pytest.raises(DataError):
        CustomerFactory(phone_no=phone_no)


@pytest.mark.django_db
def test_phone_length_cannot_be_null():
    """phone_numberはnullにならない"""
    with pytest.raises(IntegrityError):
        CustomerFactory(phone_no=None)


@pytest.mark.django_db
def test_prefecture_length_can_be_255():
    """都道府県の長さの最大値が255文字"""
    prefecture = "a" * 255
    address = AddressFactory(prefecture=prefecture)
    assert get_address(address.id).prefecture == prefecture


@pytest.mark.django_db
def test_municipalities_length_can_be_255():
    """市区町村の長さの最大値が255文字"""
    municipalities = "a" * 255
    address = AddressFactory(municipalities=municipalities)
    assert get_address(address.id).municipalities == municipalities


@pytest.mark.django_db
def test_house_no_length_can_be_255():
    """丁・番地の長さの最大値が255文字"""
    house_no = "a" * 255
    address = AddressFactory(house_no=house_no)
    assert get_address(address.id).house_no == house_no


@pytest.mark.django_db
def test_other_length_can_be_255():
    """その他の長さの最大値が255文字"""
    other = "a" * 255
    address = AddressFactory(other=other)
    assert get_address(address.id).other == other


@pytest.mark.django_db
def test_post_no_length_can_be_7():
    """郵便番号の長さの最大値が7文字"""
    post_no = "1" * 7
    address = AddressFactory(post_no=post_no)
    assert get_address(address.id).post_no == post_no


@pytest.mark.django_db
def test_post_no_length_can_be_8_or_longer():
    """郵便番号の長さが8文字以上にならない"""
    post_no = "1" * 8
    with pytest.raises(DataError):
        AddressFactory(post_no=post_no)
```

## conftest
conftest内にもFactoryBoyを使うことができます
今回は
- Serilaizer
- View

のテストで使用するので作成します
```conftest.py
import pytest
from django.core.management import call_command
from rest_framework.test import APIClient

from application.models.user import User
from application.tests.factories.user import UserFactory


@pytest.fixture(scope="session")
def django_db_setup(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        call_command("loaddata", "fixture.json")


@pytest.fixture
def client(scope="session"):
    return APIClient()


@pytest.fixture
def management_user(user_password):
    return UserFactory(
        password=user_password,
        role=User.Role.MANAGEMENT,
    )


@pytest.fixture
def general_user(user_password):
    return UserFactory(
        password=user_password,
        role=User.Role.GENERAL,
    )


@pytest.fixture
def part_time_user(user_password):
    return UserFactory(
        password=user_password,
        role=User.Role.PART_TIME,
    )


@pytest.fixture
def user_password():
    return "test"

```


## Serializerのテスト
今回はUserSerializerのテストを例に作成します
Serializerのテストを行うときは
- validate、to_representationなどSerializerのメソッドの動作確認
- Modelだけではテストできない文字数制限

の時などです
今回はvalidateメソッドを使用していないので正常系と社員番号が7文字以下のときの異常系テストを追加します

```application/serializers.py
from rest_framework import serializers

from application.models import User


class UserSerializer(serializers.ModelSerializer):
    """ユーザ用シリアライザ"""

    class Meta:
        model = User
        fields = ["id", "employee_number", "username", "email", "role"]
        read_only_fields = ["id", "created_at", "updated_at"]

    def to_representation(self, instance):
        rep = super(UserSerializer, self).to_representation(instance)
        rep["role"] = instance.get_role_display()
        return rep
```

```application/tests/serializers/test_user.py
from collections import OrderedDict

import pytest

from application.models import User
from application.serializers.user import UserSerializer


@pytest.mark.django_db
def test_user_serializer_to_representation(management_user):
    """to_representationで設定した形式で取得できる事を確認する"""

    serializer = UserSerializer(instance=management_user)
    expected = OrderedDict(
        [
            ("id", str(management_user.id)),
            ("employee_number", management_user.employee_number),
            ("username", management_user.username),
            ("email", management_user.email),
            ("role", management_user.get_role_display()),
        ]
    )

    assert serializer.to_representation(serializer.instance) == expected


@pytest.fixture
def user_data():
    """システムユーザのインプットデータ"""

    return {
        "employee_number": "1" * 8,
        "username": "テストユーザ01",
        "email": "test@example.com",
        "role": User.Role.GENERAL,
    }


@pytest.mark.django_db
def test_validate_user_data(user_data):
    """userのデータがバリデーションエラーにならない"""
    serializer = UserSerializer(data=user_data)
    assert serializer.is_valid()


@pytest.mark.django_db
def test_employee_number_length_cannot_be_7_or_shorter(user_data):
    """userのemployee_numberが7文字以下のためバリデーションエラーになる"""
    user_data["employee_number"] = "1" * 7
    serializer = UserSerializer(data=user_data)
    assert not serializer.is_valid()
```

## Viewのテスト
今回はテストケース数が多いのでUserのCRUDのテストのみに絞ってテストコードを書きます

```application/views.py
from django.http import JsonResponse
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from application.models.user import User
from application.serializers import (
    UserSerializer,
)

class UserViewSet(ModelViewSet):
    queryset = User.objects.all()
    serilaizer_class = UserSerializer

    def get_permissions(self):
        if self.action in {
            "create",
            "update",
            "destroy",
            "partial_update",
        }:
            permission_classes = [IsManagementUser]
        else:
            permission_classes = [IsAuthenticated]
        return [permission() for permission in permission_classes]

    def destroy(self, request, *args, **kwargs):
        """システムユーザを削除するAPI

        Args:
            request : リクエスト

        Returns:
            Union[
                Response,
                JsonResponse
            ]
        """
        instance = self.get_object()
        if request.user == instance:
            return JsonResponse(
                data={"msg": "自身を削除する事は出来ません"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        instance.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)
```

```application/tests/views/test_user.py
import pytest
from rest_framework import status

from application.models.user import User
from application.tests.factories.user import UserFactory


@pytest.fixture
def get_user_url():
    return "/api/users/"


def get_user_details_url(id):
    return f"/api/users/{id}/"


@pytest.fixture
def user_data():
    return {
        "employee_number": "11111111",
        "username": "テストユーザ01",
        "email": "test_user_01@test.com",
        "role": User.Role.MANAGEMENT,
    }


@pytest.mark.django_db
def test_management_user_can_list_users(
    client, management_user, user_password, get_user_url
):
    """管理者ユーザでユーザの一覧を表示できるテスト"""
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.get(get_user_url, format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_general_user_can_list_users(
    client, general_user, user_password, get_user_url
):
    """一般ユーザでユーザの一覧を表示できるテスト"""
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.get(get_user_url, format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_sales_user_can_list_users(
    client, part_time_user, user_password, get_user_url
):
    """アルバイトユーザでユーザの一覧を表示できるテスト"""
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.get(get_user_url, format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_user_cannot_list_users_without_login(client, get_user_url):
    """ログインなしでユーザの一覧を表示できないテスト"""
    response = client.get(get_user_url, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_management_user_can_list_user_details(
    client, management_user, user_password
):
    """管理者ユーザでユーザの詳細を表示できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.get(get_user_details_url(user.id), format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_general_user_can_list_user_details(
    client, general_user, user_password
):
    """一般ユーザでユーザの詳細を表示できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.get(get_user_details_url(user.id), format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_part_time_user_can_list_user_details(
    client, part_time_user, user_password
):
    """アルバイトユーザでユーザの詳細を表示できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.get(get_user_details_url(user.id), format="json")
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_management_user_can_create_user(
    client, management_user, user_password, get_user_url, user_data
):
    """管理者ユーザでユーザを作成できるテスト"""
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.post(get_user_url, user_data, format="json")
    assert response.status_code == status.HTTP_201_CREATED


@pytest.mark.django_db
def test_general_user_cannot_create_user(
    client, general_user, user_password, get_user_url, user_data
):
    """一般ユーザでユーザを作成できないテスト"""
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.post(get_user_url, user_data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_general_user_cannot_create_user(
    client, part_time_user, user_password, get_user_url, user_data
):
    """アルバイトユーザでユーザを作成できないテスト"""
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.post(get_user_url, user_data, format="json")
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_management_user_can_update_user(
    client, management_user, user_password, user_data
):
    """管理者ユーザでユーザを更新できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.put(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_general_user_cannot_update_user(
    client, general_user, user_password, user_data
):
    """一般ユーザでユーザを更新できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.put(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_general_user_cannot_update_user(
    client, part_time_user, user_password, user_data
):
    """アルバイトユーザでユーザを更新できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.put(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_management_user_can_partial_update_user(
    client, management_user, user_password, user_data
):
    """管理者ユーザでユーザを一部更新できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.patch(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_200_OK


@pytest.mark.django_db
def test_general_user_cannot_partial_update_user(
    client, general_user, user_password, user_data
):
    """一般ユーザでユーザを一部更新できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.patch(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_general_user_cannot_partial_update_user(
    client, part_time_user, user_password, user_data
):
    """アルバイトユーザでユーザを一部更新できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.patch(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_management_user_can_delete_user(
    client, management_user, user_password, user_data
):
    """管理者ユーザでユーザを削除できるテスト"""
    user = UserFactory()
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.delete(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_204_NO_CONTENT


@pytest.mark.django_db
def test_general_user_cannot_delete_user(
    client, general_user, user_password, user_data
):
    """一般ユーザでユーザを削除できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=general_user.employee_number, password=user_password
    )
    response = client.delete(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_general_user_cannot_delete_user(
    client, part_time_user, user_password, user_data
):
    """アルバイトユーザでユーザを削除できないテスト"""
    user = UserFactory()
    client.login(
        employee_number=part_time_user.employee_number, password=user_password
    )
    response = client.delete(
        get_user_details_url(user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
def test_user_cannot_delete_yourself(
    client, management_user, user_password, user_data
):
    """自身を削除できないテスト"""
    client.login(
        employee_number=management_user.employee_number, password=user_password
    )
    response = client.delete(
        get_user_details_url(management_user.id), user_data, format="json"
    )
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"msg": "自身を削除する事は出来ません"}
    
```

## まとめ
factory_boyを使うとテストコードの可読性が上がるので書いていて楽しくなりました
テストコードはプログラムの品質を担保する上でとても重要な一方、
それなりの労力がかかるので今みたいにfactory_boyを使って効率化していきたいですね

## 参考
https://pytest-factoryboy.readthedocs.io/en/latest/

https://qiita.com/AJIKING/items/ba53d215014989be311c

https://faker.readthedocs.io/en/master/
