---
title: GitHub Actions内でPytestを実行して失敗したテストの詳細をPR内で直接表示させよう！
tags:
  - Django
  - pytest
  - GitHubActions
private: false
updated_at: '2023-06-10T21:58:27+09:00'
id: 880ff25977866c30c1a4
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsを使ってテストを実行する際に失敗したテストはログを見るかと思います
テストが少なければいいですがプロジェクトが大きくなるにつれてどんどん探すのが困難になってくるので
PR内で書いたテストコードに失敗したテストの実行内容が表示されたら便利かと思います
今回はとあるライブラリを使って実現する方法について解説していきます

## 前提
- フレームワークはDjangoを使用
- テストフレームワークはPytestを使用

## pytest-github-actions-annotate-failures
`pytest-github-actions-annotate-failures`を使うと

https://github.com/pytest-dev/pytest-github-actions-annotate-failures

```
pip install pytest-github-actions-annotate-failures
```

## 実際に実行してみよう！
試しにテストを書いてみます
今回はヘルスチェックのテストを例に出します
本来は200を返すべきなのにテストコード内で400を返すテストコードを書きます

```python
from rest_framework import status


def test_health_check_returns_200(client):
    """ヘルスチェックで200を返すことをテスト"""
    url = "/api/health/"
    response = client.get(url, format="json")
    assert response.status_code == status.HTTP_400_BAD_REQUEST
    assert response.json() == {"msg": "pass"}
```

GitHub Actionsを実行すると失敗したログが出ます
![スクリーンショット 2023-06-10 21.45.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/08d4b96d-14c2-edd5-0cb5-6c2e10bf4578.png)

GitHub Actionsが実行された後に以下のようにPR内に失敗した時の詳細が記載され、長いログを見ずに済みます
![スクリーンショット 2023-06-10 21.42.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9c83976f-a98e-3921-1fd7-da71824063fc.png)

## 変更していないテストコードが失敗したらどうなるの？
例えばAPIのurlを変更したのに伴いテストコードを修正するのを忘れることはあるかと思います
変更していないテストコードが失敗しても下記のようにPR内で表示されるのでとても便利です
例えば先ほどのヘルスチェックのテストコードを修正せずにパスを変えます
テストコード内のパスも一緒に変えていないと当然失敗します
```python
urlpatterns = [
    path(r"", include(router.urls)),
    path(r"health/", health_check, name="health_check"),
    path(r"health_check/", health_check, name="health_check"),
]
```

GitHub Actionsを実行すると下記のように変更してないテストコードに対しても失敗していたらPR内で詳細に記載されます
便利ですね！
![スクリーンショット 2023-06-10 21.54.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dc55906d-f260-3d00-25ff-8fe72c1d4223.png)

以上です

## 参考
https://github.com/pytest-dev/pytest-github-actions-annotate-failures
