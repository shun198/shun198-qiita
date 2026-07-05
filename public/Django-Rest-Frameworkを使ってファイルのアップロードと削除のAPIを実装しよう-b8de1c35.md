---
title: Django Rest Frameworkを使ってファイルのアップロードと削除のAPIを実装しよう！
tags:
  - Django
  - S3
  - django-rest-framework
  - FileStorage
private: false
updated_at: '2023-12-24T14:23:12+09:00'
id: b8de1c3597a75093f8c0
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Django Rest Frameworkを使ってファイルのアップロードと削除のAPIを実装する方法について解説します
今回はローカル環境ではDjangoのFileSystemStorage、本番環境ではS3Boto3Storageを使用します

## 前提
- Djangoのプロジェクトを作成済み

## ディレクトリ構成
```
tree
・
├── application
│   ├── __init__.py
│   ├── admin.py
│   ├── apps.py
│   ├── fixtures
│   │   └── fixture.json
│   ├── migrations
│   │   ├── 0001_initial.py
│   │   └── __init__.py
│   ├── models.py
│   ├── serializers.py
│   ├── urls.py
│   ├── utils
│   │   ├── fields.py
│   │   └── storages.py
│   └── views.py
└── project
    └── settings.py

```

## 必要なファイルの作成
実装の際に以下のファイルを作成・編集します
- settings.py
- storages.py
- models.py
- fixtures.py
- fields.py
- serializers.py
- views.py

### settings.py
AWS上で使用する際はdjango-storagesを使用するのでインストールします

```
pip install django-storages
```

settings.pyに以下のように追加します
また、アップロードするS3バケットの名前は環境変数化します

```settings.py
INSTALLED_APPS += [
    # django-storagesを追加
    "storages",
]

# ファイルのアップロード先(ローカル)
MEDIA_URL = "/upload/"
MEDIA_ROOT = os.path.join(BASE_DIR, "upload")

# アップロードするファイルサイズの最大値
MAX_FILE_SIZE_LIMIT = 5000000

# AWS S3の設定
DEFAULT_FILE_STORAGE = "storages.backends.s3boto3.S3Boto3Storage"
STATICFILES_STORAGE = "storages.backends.s3boto3.S3StaticStorage"
AWS_STORAGE_BUCKET_NAME = os.environ.get("AWS_STORAGE_BUCKET_NAME")
```

### ストレージの設定ファイルの作成
DEBUG=Trueの時はFileSystemStorage　
DEBUG=Falseの時はS3Boto3Storage
を使うよう設定します
また、後述するStorageクラスのget_alternative_nameをoverrideして同じ名前のファイルが既にアップロードされていたら後ろに_1のサフィックスを追加します

```storages.py
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.s3boto3 import S3Boto3Storage

if settings.DEBUG:
    storage_class = FileSystemStorage
else:
    storage_class = S3Boto3Storage


class CustomStorage(storage_class):
    file_overwrite = False
    counts = {}

    def get_alternative_name(self, file_root, file_ext):
        if file_root not in self.counts:
            self.counts[file_root] = 1
        new_file_name = (
            file_root + "_" + str(self.counts[file_root]) + file_ext
        )
        self.counts[file_root] += 1
        return new_file_name
```

#### FileSystemStorage
FileSystemStorageについて詳細に説明します
このクラスはDjangoのStorageクラスを継承しています

```django.core.files.storage.py
class FileSystemStorage(Storage):
    """
    Standard filesystem storage
    """
```

Storageクラス内にget_alternative_nameメソッドがあり、ファイル名を返しています
ファイル名に独自のロジックを追加するときはこのメソッドをoverrideすることで実現できます

```django.core.files.storage.base.py
class Storage:
    """
    A base storage class, providing some default behaviors that all other
    storage systems can inherit or override, as necessary.
    """

    
    def get_alternative_name(self, file_root, file_ext):
        """
        Return an alternative filename, by adding an underscore and a random 7
        character alphanumeric string (before the file extension, if one
        exists) to the filename.
        """
        return "%s_%s%s" % (file_root, get_random_string(7), file_ext)
```

#### S3Boto3Storage
django-storagesのS3Storageクラスは
django-storagesのBaseStorageクラスを継承しています
また、storages.pyに記載したfile_overwriteフラグがTrueかFalseかで処理が変わります
今回はFalseにしているため、get_available_overwrite_nameではなく、Storageクラスのget_available_nameが実行されます

```storages.backends.s3.py
class S3Storage(CompressStorageMixin, BaseStorage):
    """
    Amazon Simple Storage Service using Boto3

    This storage backend supports opening files in read or write
    mode and supports streaming(buffering) data in chunks to S3
    when writing.
    """


    def get_default_settings(self):
        return {
            "access_key": setting("AWS_S3_ACCESS_KEY_ID", setting("AWS_ACCESS_KEY_ID")),
            "secret_key": setting(
                "AWS_S3_SECRET_ACCESS_KEY", setting("AWS_SECRET_ACCESS_KEY")
            ),
            "security_token": setting(
                "AWS_SESSION_TOKEN", setting("AWS_SECURITY_TOKEN")
            ),
            "session_profile": setting("AWS_S3_SESSION_PROFILE"),
            "file_overwrite": setting("AWS_S3_FILE_OVERWRITE", True),
            "object_parameters": setting("AWS_S3_OBJECT_PARAMETERS", {}),
            "bucket_name": setting("AWS_STORAGE_BUCKET_NAME"),
            "querystring_auth": setting("AWS_QUERYSTRING_AUTH", True),
            "querystring_expire": setting("AWS_QUERYSTRING_EXPIRE", 3600),
            "signature_version": setting("AWS_S3_SIGNATURE_VERSION"),
            "location": setting("AWS_LOCATION", ""),
            "custom_domain": setting("AWS_S3_CUSTOM_DOMAIN"),
            "cloudfront_key_id": setting("AWS_CLOUDFRONT_KEY_ID"),
            "cloudfront_key": setting("AWS_CLOUDFRONT_KEY"),
            "addressing_style": setting("AWS_S3_ADDRESSING_STYLE"),
            "file_name_charset": setting("AWS_S3_FILE_NAME_CHARSET", "utf-8"),
            "gzip": setting("AWS_IS_GZIPPED", False),
            "gzip_content_types": setting(
                "GZIP_CONTENT_TYPES",
                (
                    "text/css",
                    "text/javascript",
                    "application/javascript",
                    "application/x-javascript",
                    "image/svg+xml",
                ),
            ),
            "url_protocol": setting("AWS_S3_URL_PROTOCOL", "https:"),
            "endpoint_url": setting("AWS_S3_ENDPOINT_URL"),
            "proxies": setting("AWS_S3_PROXIES"),
            "region_name": setting("AWS_S3_REGION_NAME"),
            "use_ssl": setting("AWS_S3_USE_SSL", True),
            "verify": setting("AWS_S3_VERIFY", None),
            "max_memory_size": setting("AWS_S3_MAX_MEMORY_SIZE", 0),
            "default_acl": setting("AWS_DEFAULT_ACL", None),
            "use_threads": setting("AWS_S3_USE_THREADS", True),
            "transfer_config": setting("AWS_S3_TRANSFER_CONFIG", None),
        }


    def get_available_name(self, name, max_length=None):
        """Overwrite existing file with the same name."""
        name = clean_name(name)
        if self.file_overwrite:
            return get_available_overwrite_name(name, max_length)
        return super().get_available_name(name, max_length)
```

BaseStorageクラスはStorageクラスを継承しています

```storages.base.py
class BaseStorage(Storage):
    def __init__(self, **settings):
        default_settings = self.get_default_settings()
```

Storageクラスのget_available_name内にget_alternative_nameメソッドがあるため、storages.pyに記載したget_alternative_nameメソッドが実行されます

```django.core.files.storage.base.py
class Storage:
    """
    A base storage class, providing some default behaviors that all other
    storage systems can inherit or override, as necessary.
    """
    
    def get_available_name(self, name, max_length=None):
        """
        Return a filename that's free on the target storage system and
        available for new content to be written to.
        """
        name = str(name).replace("\\", "/")
        dir_name, file_name = os.path.split(name)
        if ".." in pathlib.PurePath(dir_name).parts:
            raise SuspiciousFileOperation(
                "Detected path traversal attempt in '%s'" % dir_name
            )
        validate_file_name(file_name)
        file_root, file_ext = os.path.splitext(file_name)
        # If the filename already exists, generate an alternative filename
        # until it doesn't exist.
        # Truncate original name if required, so the new filename does not
        # exceed the max_length.
        while self.exists(name) or (max_length and len(name) > max_length):
            # file_ext includes the dot.
            # Storageクラスのget_alternative_nameメソッドを実行している
            name = os.path.join(
                dir_name, self.get_alternative_name(file_root, file_ext)
            )
            if max_length is None:
                continue
            # Truncate file_root if max_length exceeded.
            truncation = len(name) - max_length
            if truncation > 0:
                file_root = file_root[:-truncation]
                # Entire file_root was truncated in attempt to find an
                # available filename.
                if not file_root:
                    raise SuspiciousFileOperation(
                        'Storage can not find an available filename for "%s". '
                        "Please make sure that the corresponding file field "
                        'allows sufficient "max_length".' % name
                    )
                name = os.path.join(
                    dir_name, self.get_alternative_name(file_root, file_ext)
                )
        return name
```

### Modelの作成
以下のModelを作成します
- User
- Customer
- Photo

Photoモデルのphotoのstorageに先ほど作成したCustomStorageを適用させます

```models.py
import uuid

from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.validators import RegexValidator
from django.db import models

from application.utils.storages import CustomStorage


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


class Photo(models.Model):
    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="ID",
    )
    customer = models.ForeignKey(
        "Customer",
        on_delete=models.CASCADE,
        related_name="customer_photo",
        db_comment="お客様ID",
    )
    photo = models.FileField(
        upload_to="customer_photo",
        storage=CustomStorage(),
        db_comment="お客様の画像データ",
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        db_comment="作成日時",
    )

    def save(self, *args, **kwargs):
        if self._state.adding and self.pk:
            self.photo.name = "{}/{}".format(self.customer.id, self.photo.name)
        super().save(*args, **kwargs)

    class Meta:
        db_table = "Photo"

```

また、Modelのsaveメソッドをoverrideします
今のままだとファイル名がcustomer_photo/ファイル名になるため、customer/customerのpk/ファイル名にする場合は以下のようにpkが存在するのとself._state.addingがTrueの時にformat関数を実行します
Model._stateはModelがまだDBに保存されていない時にTrueになるため、保存される前に処理を書き換えています

> The ModelState object has two attributes: adding, a flag which is True if the model has not been saved to the database yet,

```python
    def save(self, *args, **kwargs):
        if self._state.adding and self.pk:
            self.photo.name = "{}/{}".format(self.customer.id, self.photo.name)
        super().save(*args, **kwargs)
```

https://docs.djangoproject.com/en/5.0/ref/models/instances/#django.db.models.Model._state

### Fixtureの作成
- User
- Customer

のテストデータを作成します

```fixtures.json
[
    {
        "model": "application.User",
        "pk": 1,
        "fields": {
            "employee_number": "00000001",
            "username": "管理者ユーザユーザ01",
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
            "username": "一般ユーザ01",
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
            "username": "アルバイトユーザ01",
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
            "username": "スーパーユーザ01",
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
            "address": 1,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 1,
            "updated_by": 1
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
            "address": 2,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 2,
            "updated_by": 2
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
            "address": 3,
            "created_at": "2022-07-28T00:31:09.732Z",
            "updated_at": "2022-07-28T00:31:09.732Z",
            "created_by": 1,
            "updated_by": 1
        }
    }
]
```

### カスタムFieldの作成
Serializerに使用するカスタムFieldを作成します
FileFieldを継承し、to_internal_valueをoverrideすることで独自の処理を記載できます
今回はpdf以外をアップロードしたら
```
無効なファイル形式です。指定されたファイル形式を使用してください
```
というエラー文を出力します
また、5MBのファイルをアップロードしたら
```
{max_size}MB 以下のファイルを登録してください
```
と出力します

```application/utils/fields.py
def upload_file_to_internal_value(self, data):
    try:
        file_name = data.name
        file_size = data.size
    except AttributeError:
        self.fail("invalid")

    if not file_name:
        self.fail("no_name")
    if not self.allow_empty_file and not file_size:
        self.fail("empty")
    if self.max_length and len(file_name) > self.max_length:
        self.fail(
            "max_length", max_length=self.max_length, length=len(file_name)
        )
    if file_size > MAX_FILE_SIZE_LIMIT:
        self.fail("file_size_over", max_size=MAX_FILE_SIZE_LIMIT / 1000000)
    return file_name


class CustomFileField(FileField):
    default_error_messages = {
        "required": _("No file was submitted."),
        "invalid": "無効なファイル形式です。指定されたファイル形式を使用してください",
        "no_name": _("No filename could be determined."),
        "empty": _("The submitted file is empty."),
        "max_length": _(
            "Ensure this filename has at most {max_length} characters (it has {length})."
        ),
        "file_size_over": "{max_size}MB 以下のファイルを登録してください",
    }

    def to_internal_value(self, data):
        file_name = upload_file_to_internal_value(self, data)
        if not file_name.lower().endswith(".pdf"):
            self.fail("invalid")
        return data
```

#### fields.py
rest_frameworkのFileFieldです
このようにdefault_error_messagesをoverrideすることでDjangoが出してるエラーメッセージを独自のものに変えることができたりto_internal_valueメソッドの処理を書き換えたりできます

```rest_framework.fields.py
class FileField(Field):
    default_error_messages = {
        'required': _('No file was submitted.'),
        'invalid': _('The submitted data was not a file. Check the encoding type on the form.'),
        'no_name': _('No filename could be determined.'),
        'empty': _('The submitted file is empty.'),
        'max_length': _('Ensure this filename has at most {max_length} characters (it has {length}).'),
    }

    def __init__(self, **kwargs):
        self.max_length = kwargs.pop('max_length', None)
        self.allow_empty_file = kwargs.pop('allow_empty_file', False)
        if 'use_url' in kwargs:
            self.use_url = kwargs.pop('use_url')
        super().__init__(**kwargs)

    def to_internal_value(self, data):
        try:
            # `UploadedFile` objects should have name and size attributes.
            file_name = data.name
            file_size = data.size
        except AttributeError:
            self.fail('invalid')

        if not file_name:
            self.fail('no_name')
        if not self.allow_empty_file and not file_size:
            self.fail('empty')
        if self.max_length and len(file_name) > self.max_length:
            self.fail('max_length', max_length=self.max_length, length=len(file_name))
        return data
```

アップロードに失敗したらrest_frameworkのFieldクラスのfailメソッドが実行されます
```rest_framework.fields.py
class Field:
    def fail(self, key, **kwargs):
        """
        A helper method that simply raises a validation error.
        """
        try:
            msg = self.error_messages[key]
        except KeyError:
            class_name = self.__class__.__name__
            msg = MISSING_ERROR_MESSAGE.format(class_name=class_name, key=key)
            raise AssertionError(msg)
        message_string = msg.format(**kwargs)
        raise ValidationError(message_string, code=key)
```

### Serializerの作成
Serializerの作成を行います
instance.photo.nameの中身が以下のように
```
Modelに定義したupload_to/photoのpk/ファイル名
```
のパスになります
今回はupload_to=customer_photoになるので
```
customer_photo/customerのpk/ファイル名
```
になります

今回はファイル名のみ表示させたいので/で区切られたindexの最後の文字列(ファイル名)を表示させます

```serializers.py
from rest_framework import serializers

from application.models import Photo


class CustomerPhotoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Photo
        fields = ["id", "photo", "created_at", "created_by"]
        read_only_fields = ["id", "created_at", "created_by"]

    def to_representation(self, instance):
        rep = super().to_representation(instance)
        rep["photo"] = instance.photo.name.split("/")[-1]
        rep["created_by"] = instance.created_by.username
        return rep
```

### Viewの作成
ファイルの
- アップロード
- 削除

用のAPIを作成します
今回は複数以上のファイルを一斉にアップロードすることを想定しているので以下のようにfor文を使ってrequest.FILES.getlist("photo")内のファイルを作成していきます

```views.py
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from application.filters import CustomerFilter
from application.models import Photo
from application.serializers.customer import (
    CustomerPhotoSerializer,
    CustomerSerializer,
)


class CustomerViewSet(ModelViewSet):
    queryset = Customer.objects.select_related("address")
    permission_classes = [AllowAny]
    serializer_class = CustomerSerializer


class CustomerPhotoViewSet(ModelViewSet):
    queryset = Photo.objects.select_related("customer")
    permission_classes = [AllowAny]
    serializer_class = CustomerPhotoSerializer

    def create(self, request, *args, **kwargs):
        photo_data = []
        for photo in request.FILES.getlist("photo"):
            serializer = self.get_serializer(data={"photo": photo})
            serializer.is_valid(raise_exception=True)
            photo_data.append(
                Photo.objects.create(
                    customer_id=kwargs["customer_pk"],
                    photo=photo,
                    created_by=request.user,
                )
            )
        response = self.serializer_class(photo_data, many=True).data
        return Response(response, status=status.HTTP_201_CREATED)

    def perform_destroy(self, instance):
        # imageを削除
        instance.photo.delete(save=False)
        # photoインスタンスを削除
        instance.delete()
```

## urlの作成
画像アップロード用のパスを作成します

```urls.py
from django.urls import include, path
from rest_framework_nested import routers

from application.views.customer import CustomerPhotoViewSet, CustomerViewSet
from application.views.health_check import health_check
from application.views.login import LoginViewSet
from application.views.user import UserViewSet

router = routers.DefaultRouter()
router.register(r"", LoginViewSet, basename="login")
router.register(r"users", UserViewSet, basename="user")
router.register(r"customers", CustomerViewSet, basename="customer")
customer_router = routers.NestedDefaultRouter(
    router, "customers", lookup="customer"
)
customer_router.register(r"photos", CustomerPhotoViewSet, basename="photo")


urlpatterns = [
    path(r"", include(router.urls)),
    path(r"", include(customer_router.urls)),
    path(r"health/", health_check, name="health_check"),
]

```

## 実際にファイルをアップロードしてみよう！
今回はPostmanを使って複数ファイルをアップロードします
Keyをtextからfileに変更すると複数以上のファイルのアップロードを実現できます
以下のようにresponseが返ってきたら成功です

![スクリーンショット 2023-12-24 14.01.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b6b76731-c388-4e58-c926-85bdb72d93e8.png)

upload配下は以下のようになれば成功です

![スクリーンショット 2023-12-24 14.01.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9af11fcd-b6eb-4a12-d277-d7d4e99fab58.png)

もう一度アップロードして以下のようにサフィックスがついたら成功です

![スクリーンショット 2023-12-24 14.03.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bd0b806e-f659-662d-04c2-c03bf5bae146.png)

PDF以外アップロードして以下のエラーメッセージが出たら成功です

![スクリーンショット 2023-12-24 14.03.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ffc16e26-30d1-06ec-ca3d-804b674e5c30.png)

5MB超えPDFをアップロードして以下のエラーメッセージが出たら成功です

![スクリーンショット 2023-12-24 14.05.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/31bcf8c9-979c-1a5f-820e-8ac41afb5b75.png)

以下のように削除のAPIを実行し、204が返ってきた上にuploadとPhotoテーブルからデータが削除されたら成功です

![スクリーンショット 2023-12-24 14.13.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62f473a8-769a-af47-a278-c1afc156db5d.png)

## 参考
https://django-storages.readthedocs.io/en/1.5.2/backends/amazon-S3.html

https://docs.djangoproject.com/en/5.0/ref/files/storage/#the-filesystemstorage-class

https://github.com/django/django/blob/main/django/core/files/storage/filesystem.py#L19

https://stackoverflow.com/questions/28185300/how-to-send-multiple-files-in-postman-restful-web-service

https://stackoverflow.com/questions/14666199/how-do-i-create-multiple-model-instances-with-django-rest-framework
