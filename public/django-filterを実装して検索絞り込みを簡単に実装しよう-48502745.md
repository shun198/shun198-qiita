---
title: django-filterを実装して検索・絞り込みを簡単に実装しよう！
tags:
  - Django
  - swagger
  - django-rest-framework
  - DRF
  - django-filter
private: false
updated_at: '2022-11-05T20:41:15+09:00'
id: 485027451cb32f4abf0d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Django REST frameworkではdjango-filterを使うと簡単に検索機能を追加できます
今回は
- インストールの方法
- filterの設定方法
- Swaggerでの使い方 

について解説していきたいと思います
デフォルトで使えるBrowzableAPIでもFilterは使えますがSwaggerを使ってみたい方は以下の記事を参考に設定してみてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

## 必要な設定
まずはdjango-filterをインストールします
```
pip install django-filter
```

次にsettings.pyを編集します
```settings.py
INSTALLED_APPS = [
    "rest_framework",
    "drf_spectacular",
    'django_filters',
]

REST_FRAMEWORK = {
    "DEFAULT_SCHEMA_CLASS": "drf_spectacular.openapi.AutoSchema",
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    ),
}
```

## 実際に設定してみよう！
###  Model
今回はCustomerとWorkplaceのModelを作成します
CustomerとWorkplaceとの関係は1対1です
```python:models.py
# お客様
class Customer(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    kana = models.CharField(max_length=50)
    name = models.CharField(max_length=50)
    age = models.IntegerField()
    post_no = models.CharField(
        max_length=7, validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Customer"


# 勤務先
class Workplace(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    customer = models.OneToOneField(Customer, on_delete=models.CASCADE,related_name="workplace")
    kana = models.CharField(max_length=255)
    name = models.CharField(max_length=255)
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{10,11}$","10か11桁の数字を入力してください。")],
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Workplace"
```

### Serilaizer
to_representationについてもっと知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/b1a58a438e3256ab6ec7

```serilaizers.py
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id","kana","name","age","post_no","created_at"]
        read_only_fields = ["id","created_at"]

    def to_representation(self, instance):
        ret = super(CustomerSerializer, self).to_representation(instance)
        # 勤務先インスタンス
        workplace = instance.workplace
        # 勤務先名
        ret["workplace_name"] = workplace.name
        return ret


class WorkplaceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Workplace
        fields = ["id","kana","name", "phone_no","created_at"]
        read_only_fields = ["id","created_at"]

    def to_representation(self, instance):
        ret = super(WorkplaceSerializer, self).to_representation(instance)
        # お客様インスタンス
        customer = instance.customer
        # お客様名
        ret["customer_name"] = customer.name
        return ret
```

### Filter
今回は以下の絞り込み機能を実装します
- お客様一覧
    - お客様名
    - 勤務先名
- 勤務先一覧
    - お客様名
    - 勤務先名
    - データの作成日

```filters.py
import django_filters
from relationships.models import (
    Customer,
    Workplace,
)


# お客様Filter
class CustomerFilter(django_filters.FilterSet):
    name = django_filters.CharFilter(field_name="name",lookup_expr="contains")
    workplace = django_filters.CharFilter(field_name="workplace__name",lookup_expr="contains")

    class Meta:
        model = Customer
        # フィルタを列挙する
        fields = ["name","workplace"]

# 勤務先Filter
class WorkPlaceFilter(django_filters.FilterSet):
    customer = django_filters.CharFilter(field_name="customer__name",lookup_expr="contains")
    name = django_filters.CharFilter(field_name="name",lookup_expr="contains")
    created_at = django_filters.DateTimeFromToRangeFilter()

    class Meta:
        model = Workplace
        fields = ["customer","name","created_at"]
```


### View
今回はCustomerとWorkplaceのViewを作成します
```python:views.py
from rest_framework import viewsets
# settings.pyで定義したDjangoFilterBackendをimport
from django_filters.rest_framework import DjangoFilterBackend
from .models import (
    Customer,
    Workplace,
)
#　先ほど作成したFilterをimport
from .filters import (
    CustomerFilter,
    WorkPlaceFilter,
)


# お客様ViewSet
class CustomerViewSets(viewsets.ModelViewSet):
    queryset = Customer.objects.all()
    serializer_class = CustomerSerializer
    # settings.pyで設定したDjangoFilterBackendを追加
    filter_backends = (filters.DjangoFilterBackend,)
    # 自身で定義したFilterSetクラスを指定
    filterset_class = CustomerFilter


# 勤務先ViewSet
class WorkplaceViewSets(viewsets.ModelViewSet):
    queryset = Workplace.objects.all()
    serializer_class = WorkplaceSerializer
    filter_backends = (DjangoFilterBackend,)
    filterset_class = WorkPlaceFilter
```
## 勤務先一覧を絞り込んでみよう！
テキストボックスに値を指定せずにGETすると以下のように勤務先一覧のレスポンスが帰ってきます
![スクリーンショット 2022-11-05 20.27.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/96c9c480-6793-45ed-951d-9be63d85cfc1.png)

### 勤務先名で絞り込み
ここでnameに`四角`と指定してGETしてみます
![スクリーンショット 2022-11-05 20.19.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/36bd68cd-5285-618c-761f-a12ed9266236.png)

すると、リクエストURLにnameのクエリパラメータが表示され、
```
lookup_expr="contains"
```
をFilterに指定したことでnameが`四角`と部分一致するWorkplaceの一覧をGETすることに成功しました
![スクリーンショット 2022-11-05 20.27.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24a5ae6e-872e-caed-c3a3-d1ddacfbf99a.png)

### お客様名で絞り込み
WorkplaceにはcustomerのForeignKeyも持っています
ForeignKeyでつながっているModelのフィールドは
```
field_name="customer__name"
```
というふうにForeignKeyの後にアンダースコアを2つ(__)書いて、
その後に任意のフィールドを指定すると取得できます

ここでcustomerに`一郎`と指定してGETしてみます
![スクリーンショット 2022-11-05 20.24.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0639d0ed-7cce-4584-adcf-e0cf8fd67cfd.png)

すると、リクエストURLにcustomerのクエリパラメータが表示され、customerが`一郎`と部分一致するWorkplaceの一覧をGETすることに成功しました
![スクリーンショット 2022-11-05 20.25.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b27f2e11-10fb-54eb-362f-e83680ff9206.png)

### 作成日で絞り込み
created_at_beforeに入力するとその日付以前のデータが、
created_at_afterに入力するとその日付以後のデータが表示されます
![スクリーンショット 2022-11-05 20.29.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/55e74e6f-638c-f71a-0daf-4c95b5c8b098.png)

試しに7月10日以前のデータで絞ってみます
![スクリーンショット 2022-11-05 20.32.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9e89a882-d2cf-0a4d-ae5c-b6557aadc7cc.png)

すると、リクエストURLにcreated_atのクエリパラメータが表示され、created_atが`7月10日`以前のWorkplaceの一覧をGETすることに成功しました
![スクリーンショット 2022-11-05 20.32.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8db9a849-2f6c-8500-1962-07a6e1a7a3f6.png)

7月20日以後のデータで絞ってみます
![スクリーンショット 2022-11-05 20.33.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2d8f617d-026f-aebf-8c52-899f9972948f.png)

すると、リクエストURLにcreated_atのクエリパラメータが表示され、created_atが`7月20日`以後のWorkplaceの一覧をGETすることに成功しました
![スクリーンショット 2022-11-05 20.34.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/22da11dc-64c2-42f8-1f55-a6ccdf5494a8.png)

## お客様一覧を絞り込んでみよう！

テキストボックスに値を指定せずにGETすると以下のようにお客様一覧のレスポンスが帰ってきます
![スクリーンショット 2022-11-05 19.00.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c7a36363-a1ab-bc53-334d-394d202dbe77.png)


続いて勤務先名を絞り込んでみましょう
Workplaceと違ってCustomerにはworkplaceのForeignKeyを持っていません
そこで思い出してほしいのですがWorkplaceのModelでrelated_nameを指定したのでCustomerはWorkplaceを逆参照することができます
```python:models.py/Workplace
customer = models.OneToOneField(Customer, on_delete=models.CASCADE,related_name="workplace")
```

逆参照することでworkplaceのインスタンスをWorkplaceSerilaizer内で作成できるようになります
```python:serializers.py/WorkplaceSerilaizer
    def to_representation(self, instance):
        ret = super(CustomerSerializer, self).to_representation(instance)
        # 勤務先インスタンス
        workplace = instance.workplace
        # 勤務先名
        ret["workplace_name"] = workplace.name
        return ret
```
そうすることで
```
field_name="workplace__name"
```
というふうにinstance名の後にアンダースコアを2つ(__)書いて、
その後に任意のフィールドを指定すると取得できます

ここでworkplaceに`丸々`と指定してGETしてみます
![スクリーンショット 2022-11-05 19.07.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b8a0abda-fba6-5952-9eb9-31d284ebd3ef.png)

すると、リクエストURLにworkplaceのクエリパラメータが表示され、workplace_nameが`丸々`と部分一致するCustomerの一覧をGETすることに成功しました
![スクリーンショット 2022-11-05 19.08.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/14ab5bed-362b-d3e6-15c1-b4b5a2441572.png)

## まとめ
django-filterを使うと手軽に検索・絞り込み機能が使えるのでいいですね
Filterの詳細は公式ドキュメントに全て書いてあるので確認してみましょう

https://django-filter.readthedocs.io/en/stable/guide/tips.html


## 参考
https://qiita.com/okoppe8/items/77f7f91f6878e3f324cc

https://stackoverflow.com/questions/57989320/django-filter-foreignkey-related-model-filtering

