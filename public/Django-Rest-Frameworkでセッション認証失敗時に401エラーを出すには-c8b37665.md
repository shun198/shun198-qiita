---
title: Django Rest Frameworkでセッション認証失敗時に401エラーを出すには
tags:
  - Django
  - django-rest-framework
private: false
updated_at: '2024-09-27T16:23:11+09:00'
id: c8b376657471b7e29f99
organization_url_name: null
slide: false
---
## 概要
Django Rest Frameworkでセッション認証失敗時に403ではなく、401エラーを出す方法について解説します

## 実装
Django Rest Frameworkではセッション認証時はデフォルトで401ではなく、403を返してしまいます
401を返すにはWWW-Authenticateヘッダに有効な値をセットする必要があります
今回はauthenticate_headerメソッドの戻り値に'Session'を指定します

```common.authenticate.py
from rest_framework import authentication


class SessionAuthentication(authentication.SessionAuthentication):
    """
    This class is needed, because REST Framework's default SessionAuthentication does never return 401's,
    because they cannot fill the WWW-Authenticate header with a valid value in the 401 response. As a
    result, we cannot distinguish calls that are not unauthorized (401 unauthorized) and calls for which
    the user does not have permission (403 forbidden). See https://github.com/encode/django-rest-framework/issues/5968
    We do set authenticate_header function in SessionAuthentication, so that a value for the WWW-Authenticate
    header can be retrieved and the response code is automatically set to 401 in case of unauthenticated requests.
    """
    def authenticate_header(self, request):
        return 'Session'
```

以下がDjango RestFrameworkのSessionAuthenticationクラスが継承しているBaseAuthenticationクラスです

```python
class BaseAuthentication:
    """
    All authentication classes should extend BaseAuthentication.
    """

    def authenticate(self, request):
        """
        Authenticate the request and return a two-tuple of (user, token).
        """
        raise NotImplementedError(".authenticate() must be overridden.")

    def authenticate_header(self, request):
        """
        Return a string to be used as the value of the `WWW-Authenticate`
        header in a `401 Unauthenticated` response, or `None` if the
        authentication scheme should return `403 Permission Denied` responses.
        """
        pass
```

## 実際に検証してみよう！
以下のようにAPI実行時に401を返していたら成功です

![スクリーンショット 2024-09-27 16.21.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/358911d5-aad8-e2d0-d05f-ccf7702cc41e.png)

## 参考
https://github.com/encode/django-rest-framework/issues/5968#issuecomment-399352828

https://github.com/encode/django-rest-framework/blob/master/rest_framework/authentication.py#L33
