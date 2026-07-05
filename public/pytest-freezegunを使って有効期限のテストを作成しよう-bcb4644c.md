---
title: pytest-freezegunを使って有効期限のテストを作成しよう！
tags:
  - Django
  - pytest
  - pytest-freezegun
private: false
updated_at: '2023-11-23T18:25:55+09:00'
id: bcb4644c54946a62d8d9
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
pytest-freezegunを使うと特定の日付や時間に設定してテストを実行することができます
今回は有効期限のテストを例に使い方について解説します

## 前提
- フレームワークはDjangoを使用

## freezegunのインストール
まずはfreezegunをインストールします
```
pip install freezegun
```

## freezegunの使い方
以下のように
```
    with freeze_time("2012-01-14"):
```
と使うことで指定した日付もしくは日時でテストを実行することができます

```python
from freezegun import freeze_time

def test():
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
    with freeze_time("2012-01-14"):
        assert datetime.datetime.now() == datetime.datetime(2012, 1, 14)
    assert datetime.datetime.now() != datetime.datetime(2012, 1, 14)
```


## pytest-freezegunを使ってみよう！
今回はパスワード再設定用トークンの有効期限が30分なのでパスワード再設定トークンを生成してから31分後にパスワード再設定用APIを実行すると失敗するテストを作成します
テストコードは以下の通りです
今回はDjangoのtimezoneを使って現在の時刻の31分後の日時でテストを実行します

```test_views.py
from datetime import timedelta

import pytest
from django.utils import timezone
from freezegun import freeze_time
from rest_framework import status

from application.tests.factories.user import UserFactory
from application.tests.factories.user_reset_password import UserResetPasswordFactory


@pytest.mark.django_db
def test_reset_password_token_is_invalid(
    client,
    get_reset_password_url,
):
    """パスワード再設定用トークンの有効期限が切れているため、パスワードを再設定できないことを確認"""
    user = UserFactory()
    reset_password = UserResetPasswordFactory(user=user)
    post_reset_password = {
        "token": reset_password.token,
        "new_password": "Test@123",
        "confirm_password": "Test@123",
    }
    expiry_time = timezone.localtime() + timedelta(minutes=31)
    with freeze_time(expiry_time):
        response = client.post(
            get_reset_password_url,
            post_reset_password,
            format="json",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json() == {"msg": "こちらのURLは有効期限切れです"}
```

以下のようにテストが正常に実行されたら成功です
```
application/tests/views/test_reset_password.py::test_reset_password_token_is_invalid ✓ 
```

## 参考
https://pypi.org/project/pytest-freezegun/

https://github.com/spulec/freezegun
