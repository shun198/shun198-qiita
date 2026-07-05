---
title: Django Rest FrameworkでアップロードしたCSVファイルの内容をDBに保存しよう
tags:
  - Django
  - CSV
  - django-rest-framework
private: false
updated_at: '2022-11-27T12:31:46+09:00'
id: 8e029655a029eb8a8d5a
organization_url_name: null
slide: false
---
## 概要
今回はPOSTする際にrequestの中のCSVファイルのデータをデータベースにINSERTする方法について記載していきます

## はじめに
以下のファイルに必要な設定を記載していきます
- models.py
- serializers.py
- views.py

### models.py
お客様用のModelを作成します
```models.py
import uuid
from django.db import models
from django.core.validators import RegexValidator


class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255)
    kana = models.CharField(max_length=255)
    birthday = models.DateField()
    post_no = models.CharField(
        max_length=7, validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")]
    )
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{10,11}$", "10桁の数字を入力してください。")],
        null=True,
        blank=True,
    )
    email = models.EmailField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_created_by')
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(User, on_delete=models.DO_NOTHING, related_name='%(class)s_updated_by')

    class Meta:
        db_table = "Customer"

    def __str__(self):
        return self.name
```

### serializers.py
ファイルのアップロードをするときはSerializerのFileFieldを使用します
そうすることでPOSTする際のrequest内にCSVファイルを入れることができます
今回はfileという名前のfieldにします
その際はserializers.Serializerクラスを継承させます
```serializers.py
# ファイルアップロード用Serializer
class CreateCustomerSerializer(serializers.Serializer):
    file = serializers.FileField()

# お客様用Serializer
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = "__all__"
        read_only_fields = ["id","created_at","created_by","updated_at","updated_by"]
```

### views.py
views.pyにCSVファイル内のデータをPOSTする処理を記載していきます
```views.py
import csv, io, datetime
from rest_framework import viewsets
from django.http import JsonResponse
from rest_framework import status
from .models import Customer
from .serializers import (
    CustomerSerializer,
    CreateCustomerSerializer,
)


class CustomerViewSet(viewsets.ModelViewSet):
    queryset = Customer.objects.all()


    # POSTの時だけ
    def get_serializer_class(self):
        if self.action == "create":
            return CreateCustomerSerializer
        else:
            return CustomerSerializer


    def create(self, request, *args, **kwargs):
        # request.FILESからSerializerで定義したfileを指定
        # CSVファイルがInMemoryUploadedFile型として格納されている
        csv_file = request.FILES["file"]
        # utf-8に変換
        decoded_file = csv_file.read().decode("utf-8")
        io_string = io.StringIO(decoded_file)
        # header(1行目)を無視
        header = next(csv.reader(io_string))
        # delimiter=","と指定し、CSVファイルを1行ずつ読み込む
        for row in csv.reader(io_string, delimiter=","):
            # CSVファイルの内容はstr型のため、birthdayをdate型にキャストする必要がある
            year = int(row[2].split("/")[0])
            month = int(row[2].split("/")[1])
            day = int(row[2].split("/")[2])
            birthday = datetime.date(year, month, day)
            # Customerに必要なデータ
            csv_data = {
                "name": row[0],
                "kana": row[1],
                "birthday": birthday,
                "post_no": row[3],
                "phone_no": "0" + row[4],
                "email": row[5],
            }
            serializer = CustomerSerializer(data=csv_data)
            if serializer.is_valid():
                serializer.save(created_by=request.user,updated_by=request.user)
            else:
                return JsonResponse({"msg":"CSVファイルのアップロードに失敗しました"},status=status.HTTP_400_CREATED)
        return JsonResponse({"msg":"CSVファイルのアップロードに成功しました"},status=status.HTTP_201_CREATED)
```

## 実際にCSVをPOSTしてみよう！
該当するエンドポイントにアクセスすると下記のようにファイルを添付することができます
![スクリーンショット 2022-11-27 11.39.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/08522ea3-80bc-3332-acde-4ed589e95901.png)

該当するCSVファイルを選択してimportします
![スクリーンショット 2022-11-27 12.21.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/edaa33b3-ee8c-9861-dd24-a73e7cd03650.png)

CSVファイルのアップロードに成功しました
![スクリーンショット 2022-11-27 12.21.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a43feca8-3bd3-ff14-8b0c-8f01d4b52f3d.png)

![スクリーンショット 2022-11-27 12.22.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/787ccbd0-5b95-215f-a365-e8c64c189611.png)

## 参考
https://stackoverflow.com/questions/50638374/expected-str-bytes-or-os-pathlike-object-not-inmemoryuploadedfile

https://docs.djangoproject.com/en/4.1/ref/models/fields/

https://www.django-rest-framework.org/api-guide/fields/#file-upload-fields

https://www.geeksforgeeks.org/appending-a-dictionary-to-a-list-in-python/

https://baronchibuike.medium.com/how-to-read-csv-file-and-save-the-content-to-the-database-in-django-rest-256c254ef722

https://www.techscore.com/blog/2019/12/16/better-way-handling-json-data-in-python/

https://kuma-server.com/djangocsv/

https://zerofromlight.com/blogs/detail/77/
