---
title: to_representationを使って関連ModelのFieldを表示させよう！
tags:
  - Django
  - swagger
  - django-rest-framework
  - DRF
  - to_representation
private: false
updated_at: '2024-01-07T09:16:03+09:00'
id: b1a58a438e3256ab6ec7
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Modelの一覧を表示させたい時にFKと繋がってる一部Fieldも合わせて表示させたい場面では
`to_representation`を使うと楽に実装できるので解説していきます

## to_representaionとは？
BaseSerilaizerクラスのメソッドです
処理の流れをざっくりと解説すると以下のようになります

1. retというOrderedDict型の変数を定義
1. fields内にSerializer自身のFieldを代入
1. For文で一つずつinstance(Serilaizerで定義したModelのinstance)からfieldの値をattribute(属性)に代入する(例：fieldがnameならModelのinstanceのnameをattributeに代入)
1. If文でattributeがPKのみのObjectだったらPKをそのまま代入し、違ったらattributeをcheck_for_noneに代入
1. If文でcheck_for_noneがNone(attributeがnone、つまりinstanceに該当するfieldがなかったら)の時ret[field.field_name]にNoneが入る。Noneではないのであればattributeの値が入る

```rest_framwork/serializers.py
class Serializer(BaseSerializer, metaclass=SerializerMetaclass):
    def to_representation(self, instance):
        """
        Object instance -> Dict of primitive datatypes.
        """
        ret = OrderedDict()
        fields = self._readable_fields

        for field in fields:
            try:
                attribute = field.get_attribute(instance)
            except SkipField:
                continue

            # We skip `to_representation` for `None` values so that fields do
            # not have to explicitly deal with that case.
            #
            # For related fields with `use_pk_only_optimization` we need to
            # resolve the pk value.
            check_for_none = attribute.pk if isinstance(attribute, PKOnlyObject) else attribute
            if check_for_none is None:
                ret[field.field_name] = None
            else:
                ret[field.field_name] = field.to_representation(attribute)

        return ret
```

## 実際に使ってみよう
ModelとSerilaizerを用意して実際の挙動を確かめてみましょう
### Model
今回使うModelでは
CustomerとWorkplaceが1対1、CustomerとOrderが1対多の関係になります

```models.py
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

# 注文
class Order(models.Model):
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE,related_name="order")
    order_no = models.CharField(
        max_length=8,
        validators=[RegexValidator(r"^[0-9]{8}$","8桁の数字を入力してください。")],
        unique=True
        )
    count = models.SmallIntegerField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "Order"
```

### related_name
WorkplaceとOrderのModelはcustomerのFKからCustomerのModelを参照できますが、逆にCustomerのModelからWorkplaceとOrderのModelを参照(逆参照)できません
このようにrelated_nameを付けることでCustomerのModelからFKを持つ関連性のあるModelをto_representationを使う際に逆参照できるようになります
ただし、related_nameの名前が被るとどのModelを逆参照できるかDjango側がわからなくなるので注意が必要です
```python:Workplace
customer = models.OneToOneField(Customer, on_delete=models.CASCADE,related_name="workplace")
```
```python:Order
customer = models.ForeignKey(Customer, on_delete=models.CASCADE,related_name="order")
```

### Serilaizer
CustomerのModel内にある
- お客様ID
- お客様名

に加え、勤務先と商品番号はそれぞれWorkplace、ItemのModel内にある
- 勤務先名
- 注文番号

をto_representationをオーバーライドすることで表示させます


```serializers.py
class CustomerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Customer
        fields = ["id","name"]

    def to_representation(self, instance):
        rep = super(CustomerSerializer, self).to_representation(instance)
        # 勤務先名
        workplace = instance.workplace.name
        # 商品番号
        order = instance.order.latest("created_at")
        rep["workplace"] = workplace
        rep["order_no"] = order.order_no
        return rep
```

### instanceって何？
Serializerを使う際に参照するModelのinstanceにあたります
今回の例ではCustomerのModelを参照しているのでCustomerのinstanceです
```python
print(type(instance)) # <class '<アプリケーション名>.models.Customer'>
print(instance) # <Customer: 田中一郎>
```

### super()って何？
super()とはPythonでbuilt-in関数で
```python
rep = super(CustomerSerializer, self).to_representation(instance)
```
のようにretに代入することでto_representationの定義でreturnされる戻り値のOrderDict型のretが代入されます
こうすることで
```python
rep["workplace"] = workplace
```
のように任意のkeyとvalueを定義できます

### OneToOneのModelを逆参照する時
CustomerとWorkplaceは1対1の関係です。instance.workplaceの後にworkplaceのfieldを後ろに付けることで
```python
# workplace変数にWorkplaceのnameのfieldの値が入る
workplace = instance.workplace.name
rep["workplace"] = workplace
```
のようにkeyとvalueが定義されます
```python
('workplace', '勤務先01')
```

### OneToManyのModelを逆参照する時
CustomerとOrderは1対1の関係です。
前述のinstance.workplaceはWorkplace型のinstanceです
```python
print(type(instance.workplace)) # <class '<アプリケーション名>.models.Workplace'>
print(type(instance.workplace.name)) # <class 'str'>
```
それに対してinstance.orderはRelatedManager型です
```python
print(type(instance.order)) # <class 'django.db.models.fields.related_descriptors.create_reverse_many_to_one_manager.<locals>.RelatedManager'>
```
Customerに対応するOrderが複数あり、このままではWorkplaceのようにkeyとvalueの関係にならないため、一つのインスタンスにする必要があります
そこで今回は
```python
order = instance.order.latest("created_at")
rep["order_no"] = order.order_no
```
のようにcreated_atの日付が最も新しいinstanceだけを抽出します
```python
print(type(instance.order.latest("created_at"))) # <class '<アプリケーション名>.models.Order'>
print(type(instance.order.latest("created_at").order_no)) # <class 'str'>
```
orderも同様にkeyとvalueが定義されます
```python
 ('order_no', '00011122')
```

### retに何が入ってるの？
fieldsで定義したid,nameのkeyとvalueに加えて自身で定義したretのkeyとvalue(今回だとworkplaceとorder_no)が入っています
```python
print(rep)
# OrderedDict([('id', '00000000-0000-0000-0...0000000001'), ('name', '田中一郎'), ('workplace', '勤務先01'), ('order_no', '00011122')])
```

### Swaggerで見てみよう
実際に一覧をGETすると以下のようになります
![スクリーンショット 2022-10-29 16.21.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/773f68bc-32fb-6ace-48b1-d0659cefdc19.png)

Swaggerを使ってみたい方はこちらの記事を参考にしてみてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

## トラブルシューティング
### raise self.RelatedObjectDoesNotExist
逆参照先のテーブル内にデータがない場合に起こるエラーなのでSQLのInsert文かFixtureを使いましょう
Fixtureの使い方については以下の記事に記載してますので興味があれば読んでみてください

https://qiita.com/shun198/items/29b5c253be6f802403cd

## まとめ
なんとなく使っていてよくわからなかったto_representationですがこうやって定義ファイルをデバッグしながらやるとかなり理解が深まりました

## 記事の紹介
記事を書くにあたってコンテナ環境でVSCodeのリモートデバッグを使いながら検証しています
読むより実際に自分でデバッグしてみた方が理解が深まるのは間違いないのでよかったら読んでみてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/9e4fcb4479385217c323

## 参考
https://www.memory-lovers.blog/entry/2021/02/02/152013

https://www.django-rest-framework.org/api-guide/serializers/#overriding-serialization-and-deserialization-behavior

https://devdocs.io/django_rest_framework/api-guide/serializers/index#baseserializer

https://testdriven.io/blog/drf-serializers/#to_representation

https://djangobrothers.com/blogs/related_name/

