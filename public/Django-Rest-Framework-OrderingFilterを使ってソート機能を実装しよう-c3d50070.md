---
title: '[Django Rest Framework] OrderingFilterを使ってソート機能を実装しよう！'
tags:
  - Django
  - django-rest-framework
private: false
updated_at: '2023-11-12T13:30:07+09:00'
id: c3d500701acf0d34fae6
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Django Rest Frameworkを使って一覧のAPIにソート機能を実装する方法について解説します

## 前提
- Djangoのプロジェクトを作成済み

## OrderingFilter
Django Rest Frameworkを使ってソート機能を実装する際はOrderingFilterを使うのが一般的です
以下のようにfilter_backendsにOrderingFilterを指定することで実装できます

```python
from rest_framework.viewsets import ModelViewSet

from application.models import Product
from application.serializers.product import ProductSerializer
from rest_framework.filters import OrderingFilter


class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [OrderingFilter]
```

実装したAPIを確認します

![スクリーンショット 2023-11-12 13.18.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4cf61ffe-8e0b-2f74-173b-fe3c09fbc035.png)

Filterの箇所を押すと以下のように適用したいソート条件を入力できます
![スクリーンショット 2023-11-12 13.19.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3913f532-1845-bb29-a13c-a1743b434607.png)

## ソートしてみよう
試しに`Price - 昇順`を押すと以下のように昇順に値段がソートされます
その際は
```
?ordering=price
```
というふうにソートパラメータがAPIのパスの後ろに適用されます

![スクリーンショット 2023-11-12 13.20.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/39218bc8-fba9-2618-cfba-83ba1954ee24.png)

逆にソート順を降順にする際は
```
?ordering=-price
```
というふうにソートパラメータに`-`が適用されます

![スクリーンショット 2023-11-12 13.22.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4b34e5a4-d056-fc38-2fcc-8909fca70ee4.png)

## デフォルトのソート
また、ordering_fieldsにパラメータを設定するとデフォルトのソート順を指定できます
以下のように設定すればpriceのソートパラメータなしで値段の昇順にソートされます
ただし、一般的にバックエンド側ではなく、フロントエンド側でデフォルトのソート順を保持しておいてフロントエンドから送られたソートパラメータに従ってソートするケースが多いので参考程度に認識していただければと思います

```python
class ProductViewSet(ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    filter_backends = [OrderingFilter]
    ordering_fields = "price"
```

![スクリーンショット 2023-11-12 13.27.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2780e298-9582-9a85-f210-e1808b60244e.png)


## 参考
https://www.django-rest-framework.org/api-guide/filtering/#orderingfilter
