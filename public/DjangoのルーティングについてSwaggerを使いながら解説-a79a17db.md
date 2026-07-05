---
title: DjangoのルーティングについてSwaggerを使いながら解説
tags:
  - Django
  - swagger
  - ルーティング
  - django-rest-framework
  - DRF
private: false
updated_at: '2023-01-15T10:40:37+09:00'
id: a79a17db571a461309ea
organization_url_name: null
slide: false
---
## 概要
Djangoのルーティングについて
- Simple Router と Default Routerの概要とその違い
- ルーティングのネスト

の順で解説していきたいと思います


## 前提
- Djangoのプロジェクトとアプリケーションを作成済み
- SwaggerUIを使用
- 今回使用するパッケージは以下の通りです
    - drf-spectacular==0.23.1
    - django-extensions==3.2.0
    - drf-nested-routers==0.93.4

## はじめに
必要なパッケージをインストールします
|  パッケージ  |  概要  |
|-----|-----|
|  drf-spectacular  |  SwaggerUI  |
|  django-extensions  |  今回はルーティングを確認する際に使用  |
|  drf-nested-routers  |  ルーティングのネストに使用  |

### ローカル上で使用する時
```terminal:terminal
pip install drf-spectacular
pip install django-extensions
pip install drf-nested-routers  
```

django-extensionsを使用する際はsettings.pyに以下を追加します
```settings.py
INSTALLED_APPS = [
    # django_extensionsを追加
    "django_extensions",
]
```

### コンテナを使用するとき
一般的にはrequirements.txtに必要なパッケージを書きます
```python:requirements.txt
drf-spectacular==0.23.1
django-extensions==3.2.0
drf-nested-routers==0.93.4
```

### Swaggerの設定方法
Swaggerの導入方法について以下の記事に書いたので使ったことがない方は参考にしてください

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

## Simple Router と Default Routerとは
`Simple Router` または `Default Router`を(`viewsets.ModelViewSet`と組み合わせて)使うことで
- GET(一覧)
- GET(詳細)
- POST
- PUT
- PATCH
- DELETE

の一通りのルーティングを自動的に作成できます
includeでHTTPメソッドごとにurlやviewを作成しなくて済みます
詳しく知りたい方は公式ドキュメントを参照してください

https://www.django-rest-framework.org/tutorial/6-viewsets-and-routers/


どちらも以下のようにrest_framework.routersからimportすれば使用できます
```python:urls.py
from rest_framework.routers import SimpleRouter
from rest_framework.routers import DefaultRouter
```
今回はルーティングのネストも行うのでrest_framework_nestedからimportします
```python:urls.py
from rest_framework_nested import routers
```
```python:urls.py
router = routers.SimpleRouter()
router = routers.DefaultRouter()
```
### Simple RouterとDefault Routerの違いって何？
Defalut RouterはSimple Routerと違ってAPIのデフォルトのルートディレクトリを持ちます。以下のようにルートディレクトリにアクセスすると表示されます。Simple Routerでは表示されません
![スクリーンショット 2022-09-25 14.40.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/faf74978-6724-f9ac-2455-1d533ef088f9.png)


それ以外は特に違いがありません。今回はDefaultRouterを使ってルーティングをします
SimpleRouterを使用されたい方はDefaultRouterをSimpleRouterに置き換えて使用しても同じ挙動になります

## ルーティングをしてみよう
まずはrest_framework_nestedからroutersをimportしてインスタンス化します
今回はrouterという名前のインスタンスを作成します
```python
from rest_framework_nested import routers

router = routers.DefaultRouter()
```
どのようなルーティングにするか設定します
```python
router.register(r'<ディレクトリ名>', <ViewSet名>,basename=<basename名、通常は単数系>)
```

### basename
basenameは自身でviewset内にget_querysetメソッドを定義した場合に使用します

以上を踏まえてルーティングすると以下のようになります
```python:urls.py
from django.urls import path, include
from rest_framework_nested import routers
from .views import CustomerViewSets,BookViewSets

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'customers', CustomerViewSets,basename="customer")

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path(r'', include(router.urls)),
]
```

django-extensionsをインストールできたので
```terminal:terminal
python manage.py show_urls
```
でルーティングを確認できます
今回はCustomerのルーティングを作成したのでadminのルーティングを除くと以下のようになります
```python:terminal
python manage.py show_urls
/       rest_framework.routers.view     api-root
/\.<format>/    rest_framework.routers.view     api-root
/customers/     relationships.views.CustomerViewSets    customer-list
/customers/<pk>/        relationships.views.CustomerViewSets    customer-detail
/customers/<pk>\.<format>/      relationships.views.CustomerViewSets    customer-detail
/customers\.<format>/   relationships.views.CustomerViewSets    customer-list
```

また、Swaggerで確認すると以下のようになります
![スクリーンショット 2022-09-25 15.11.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c1ccda30-cdf0-13a1-2da2-e77cb43a8a5d.png)

## ネスティング
上記のCustomerのルーティングに別のルーティングをネストしたいときはどうすればいいか解説します
今回はCustomerと1対多のリレーションをもつBookのルーティングをネストするとします
rest_framework_nestedのNestedDefaultRouterを使用します
SimpleRouterを使用する際はNestedSimpleRouterを使用することで同じ挙動になります

まずはNestedDefaultRouterをインスタンス化します
```python
<NestedDefalutRouterのインスタンス名> = routers.NestedDefaultRouter(router,r"<ネスト元のurl>",lookup="ネスト元のbasename")
```
次にネストするurlの設定を行います
```python
customer_router.register(r'books', BookViewSets, basename='book')
```
最後にurlspatternsにNestedDefaultRouterのurlを加えます
```python
urlpatterns = [
    path(r'', include(<NestedDefalutRouterのインスタンス名>.urls)),
]
```

以上の設定をすると以下のようになります
```python:urls.py
from django.urls import path, include
from rest_framework_nested import routers
from .views import CustomerViewSets,BookViewSets

# Create a router and register our viewsets with it.
router = routers.DefaultRouter()
router.register(r'customers', CustomerViewSets,basename="customer")
# 今回はcustomer_routerという名前のNestedDefaultRouterのインスタンスを作成
customer_router = routers.NestedDefaultRouter(router,r"customers",lookup="customer")
# customerにネストするbookのルーティング
customer_router.register(r'books', BookViewSets, basename='book')

# The API URLs are now determined automatically by the router.
urlpatterns = [
    path(r'', include(router.urls)),
    # ネストしたurlのルーティングをurlpatternsに指定
    path(r'', include(customer_router.urls)),
]
```

CustomerとBookのルーティングを作成したのでadminのルーティングを除くと以下のようになります
```python:terminal
python manage.py show_urls
/       rest_framework.routers.view     api-root
/\.<format>/    rest_framework.routers.view     api-root
/customers/     relationships.views.CustomerViewSets    customer-list
/customers/<customer_pk>/books/ relationships.views.BookViewSets        book-list
/customers/<customer_pk>/books/<pk>/    relationships.views.BookViewSets        book-detail
/customers/<customer_pk>/books/<pk>\.<format>/  relationships.views.BookViewSets        book-detail
/customers/<customer_pk>/books\.<format>/       relationships.views.BookViewSets        book-list
/customers/<pk>/        relationships.views.CustomerViewSets    customer-detail
/customers/<pk>\.<format>/      relationships.views.CustomerViewSets    customer-detail
/customers\.<format>/   relationships.views.CustomerViewSets    customer-list
```

Swagger上だと以下のようにCustomerのルーティングの後にBookのルーティングが設定されています

![スクリーンショット 2022-09-25 15.27.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5dc7b0d2-a8ea-cc3c-0571-b66c3c20e515.png)

以上でルーティングの説明は終わりです

## 記事の紹介
以下の記事も作成しましたので見ていただけると幸いです

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/9e4fcb4479385217c323

## 参考

https://developpaper.com/difference-between-defaultrouter-and-simplerouter-in-drf/

https://stackoverflow.com/questions/55202454/drf-nested-routers-runtimeerrorparent-registered-resource-not-found

https://zenn.dev/shimakaze_soft/scraps/1e61519eb122e2

https://www.django-rest-framework.org/api-guide/routers/

https://github.com/alanjds/drf-nested-routers



