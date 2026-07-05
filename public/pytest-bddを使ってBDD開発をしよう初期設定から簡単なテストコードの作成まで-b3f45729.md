---
title: pytest-bddを使ってBDD開発をしよう！(初期設定から簡単なテストコードの作成まで)
tags:
  - Django
  - bdd
  - pytest
  - django-rest-framework
  - pytest-bdd
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: b3f45729f1ed1e7b4167
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Pytestにはpytest-bddというBDDを実装するためのプラグインがあります
今回はpytest-bddを使ったテストの書き方について説明していきます

## そもそもBDDって何？
BDDは振る舞い駆動開発(Behavior-Driven Development)という開発手法の略です
名前に振る舞いという文字がある通り、コード自体の振る舞いやアプリケーションの振る舞いを焦点にテストコードを書いていく開発手法です
ちなみにBDDとともによく挙げられるTDD(テスト駆動開発、Test-Driven Development)は
テストコードを書いてから実装用のコードを書く開発手法です

## 前提
- WebフレームワークはDjangoを使用
- 本来であればテストコードを書いてから実装しますが説明の都合上、実装したコードをお見せしてからテストコードを記載していきます
    - テストコードだけみたい方は`BDDの設定`から読んでください
- 今回はヘルスチェックのテストをpytest-bddを使って実装していきます

## ファイル構成
```
tree
・
├── project
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings
│   ├── urls
│   └── wsgi.py
└── application
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── migrations
   ├── models.py
   ├── tests
   |   ├── features
   |   |   └── health_check.feature
   |   ├── views
   |   |   ├── __init__.py
   |   |   └── test_health_check.py
   |   └── conftest.py
   ├── urls.py
   └── views.py
       ├── __init__.py
       └── health_check.py
```

## 初期設定
pytest-bddをインストールします
```
pip install pytest_bdd
```

### 実装イメージ
ヘルスチェックのテストをするには
- project/settings.py
- application/views/health_check.py
- project/urls.py
- application/urls.py

が必要になってきます

### ヘルスチェックの実装

```application/views/health_check.py
from django.http import JsonResponse
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny


@api_view(["GET"])
@permission_classes([AllowAny])
def health_check(request):
    """ヘルスチェック"""
    return JsonResponse(data={"msg": "pass"}, status=status.HTTP_200_OK)
```

```projects/urls.py
from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("application.urls")),
]
```

```application/urls.py
from django.urls import include, path

from application.views.health_check import health_check


urlpatterns = [
    path(r"", include(router.urls)),
    path(r"health/", health_check, name="health_check"),
]
```

## BDDの設定に必要なファイル
pytest-bddでテストを作成する際は
- テストケースを記載するfeatureファイル
    - featureファイルをtests/フォルダの直下に作成します
- 実際のテストコードを記載するPythonファイル

の2つを用意する必要があります
では、今から実装していきましょう

## BDDの実装
### featureファイルの作成
今回作成するfeatureファイルは以下の通りです

```application/tests/features/health_check.feature
Feature: ヘルスチェックAPI
    Background:
        Given APIClientを生成
        And ヘルスチェックAPIのURL

    Scenario Outline: 正常系のテスト
        Given ヘルスチェック成功時のJSONを設定
        When GET通信を実施
        Then レスポンスのステータスが200
        And 期待通りのJSONが返却されていること
```

### Feature
まず、冒頭に
```application/tests/features/health_check.feature
Feature: ヘルスチェックAPI
```

という風にこのFeatureファイル内にはどんな機能の振る舞いがあるのか記載します
今回はヘルスチェックのAPIの振る舞いをFeatureファイルに書きたいので上記のように記載しています
1つのFeatureファイル内ではFeatureは1つしか使えません

### Background
```application/tests/features/health_check.feature
Feature: ヘルスチェックAPI
    Background:
        Given APIClientを生成
        And ヘルスチェックAPIのURL
```

Backgroundは後述するシナリオで共通の前提条件を定義するために使用されます
複数のシナリオで同じ前提条件を持つ時に使用すると前提条件が自動的に使用され、コード量を減らすことができます
今回はAPIと通信する時のAPIClientとヘルスチェックのURLをBackgroundとして定義しています
例えばログインする前提で使用するAPIのテストをするのであればログイン処理をBackgroundとして定義するのが良いかと思います
GivenとAndについてはScenario Outline以降で説明します

### Scenario Outline
```application/tests/features/health_check.feature
    Scenario Outline: 正常系のテスト
        Given ヘルスチェック成功時のJSONを設定
        When GET通信を実施
        Then レスポンスのステータスが200
        And 期待通りのJSONが返却されていること
```
Scenario Outlineにテストケース名(今回だと正常系テスト)を記載します
その下にステップと呼ばれるものを設定します

### Given
テストの前提条件を記載します
ヘルスチェックの正常系テストであり、成功時に期待通りのJSONが返却されていることを確認したいため、
Givenにヘルスチェック成功時のJSONを設定、と記載します

### When
テストを実行するときの振る舞いを指定します
今回はヘルスチェックのAPIへGETリクエストをする、という振る舞いを行いたいので
GET通信を実施、と記載します

### Then
テストが実行された時の結果(振る舞い)を記載します
ヘルスチェックのAPIへGETリクエストをする、という振る舞いを受けて200のレスポンスを返すことを期待しているので
レスポンスのステータスが200、と記載します

### And
Given、When、Thenに追加のステップを行いたいときに記載します
今回はThen(テストの結果)の下に書いているので
- レスポンスのステータスが200

の他に

- 期待通りのJSONが返却されていること

というThenのステップが追加されます

### ヘルスチェックのテスト
今回作成するヘルスチェックのテストは以下の通りです

```application/tests/views/test_health_check.py
from pytest_bdd import given, scenarios, then, when
from rest_framework import status
from rest_framework.test import APIClient


scenarios(
    "./features/health_check.feature",
)


@given("APIClientを生成", target_fixture="client")
def client(db):
    return APIClient()


@given("ヘルスチェックAPIのURL", target_fixture="url")
def health_check_url():
    return "/api/health/"


@given("ヘルスチェック成功時のJSONを設定", target_fixture="expected")
def health_check_expected():
    return {"msg": "pass"}


@when("GET通信を実施", target_fixture="response")
def get(client, url):
    return client.get(url, format="json")


@then("レスポンスのステータスが200")
def response_status_code_200(response):
    assert response.status_code == status.HTTP_200_OK


@then("期待通りのJSONが返却されていること")
def json(response, expected):
    assert response.json() == expected
```

### scenario
まず、下記のようにimportするfeatureファイルのパスを定義します
```
scenarios(
    "./features/health_check.feature",
)
```

### ステップ
- Given
- When
- Then

の3ステップにはそれぞれのデコレータが存在するため、
```python
@given("APIClientを生成", target_fixture="client")
def client(db):
    return APIClient()
```
という風に`@given`デコレータの引数にfeatureファイルに記載したステップの内容と別のステップで使う際にtarget_fixtureを定義します

### target_fixture
```python
@given("APIClientを生成", target_fixture="client")
def client(db):
    return APIClient()


@given("ヘルスチェックAPIのURL", target_fixture="url")
def health_check_url():
    return "/api/health/"
```

に`target_fixture="client"`や`target_fixture="url"`
と記載されていますが別のステップでclientを引数に入れるとその戻り値を使用することができます

以下のようにwhenのステップでtest実行時の振る舞いを記載するときにgivenで定義したfixtureを利用することができます
```python
@when("GET通信を実施", target_fixture="response")
def get(client, url):
    return client.get(url, format="json")
```

`"/api/health/"`へGETリクエストを実施すると
`@then`で記載したテスト実行後の振る舞いは
- `response.status_code == status.HTTP_200_OK`
- `response.json() == expected`

になればテストが成功します

```python
@given("ヘルスチェック成功時のJSONを設定", target_fixture="expected")
def health_check_expected():
    return {"msg": "pass"}


@when("GET通信を実施", target_fixture="response")
def get(client, url):
    return client.get(url, format="json")


@then("レスポンスのステータスが200")
def response_status_code_200(response):
    assert response.status_code == status.HTTP_200_OK


@then("期待通りのJSONが返却されていること")
def json(response, expected):
    assert response.json() == expected
```

pytest-bddを使ったヘルスチェックのテストの解説は以上です

## conftest.py
conftest.pyに他のテストでも使用するシナリオを記載することができます
- ステータスコード
- HTTPメソッド

などがよいかと思います

```application/tests/conftest.py
from pytest_bdd import given, then, when
from rest_framework import status
from rest_framework.test import APIClient


@given("APIClientを生成", target_fixture="client")
def client(db):
    return APIClient()


@then("レスポンスのステータスが200")
def response_status_code_200(response):
    assert response.status_code == status.HTTP_200_OK


@then("レスポンスのステータスが201")
def response_status_code_201(response):
    assert response.status_code == status.HTTP_201_CREATED


@then("レスポンスのステータスが400")
def response_status_code_400(response):
    assert response.status_code == status.HTTP_400_BAD_REQUEST


@when("GET通信を実施", target_fixture="response")
def get(client, url):
    return client.get(url, format="json")


@when("POST通信を実施", target_fixture="response")
def patch(client, url, data):
    return client.post(url, data=data, format="json")


@when("PATCH通信を実施", target_fixture="response")
def patch(client, url, data):
    return client.patch(url, data=data, format="json")


@when("DELETE通信を実施", target_fixture="response")
def delete(client, url, data):
    return client.delete(url, data=data, format="json")


@then("期待通りのJSONが返却されていること")
def json(response, expected):
    assert response.json() == expected
```

と記載することでヘルスチェックのテストコードはもっと少なくなります

```application/tests/views/test_health_check.py
from pytest_bdd import given, scenarios

scenarios(
    "./features/health_check.feature",
)


@given("ヘルスチェックAPIのURL", target_fixture="url")
def health_check_url():
    return "/api/health/"


@given("ヘルスチェック成功時のJSONを設定", target_fixture="expected")
def health_check_expected():
    return {"msg": "pass"}
```

このようにAPIのパスとAPIへのリクエスト成功時のJSONを記載するだけでテストを書くことができてしまいます

## まとめ
初めて使った時はかなりクセが強くて慣れるのに時間がかかりましたが理屈がわかればとても楽しいですね
公式ドキュメントを読んでいてもまだまだ学ばないといけないことが多いので今後もアウトプットしていきたいと思います

## 参考
https://pytest-bdd.readthedocs.io/en/stable/
