---
title: FastAPIでCSRF対策を行うには？
tags:
  - csrf
  - middleware
  - FastAPI
private: false
updated_at: '2025-05-06T15:27:08+09:00'
id: 17857bea62f873dedf14
organization_url_name: null
slide: false
---
## 概要
starlette-csrfというライブラリを使用するとcsrfトークンの発行やMiddlewareによる認証ができるのでその方法について解説します

## CSRFトークンの発行から認証まで流れ
- CSRFトークン発行用のAPIをフロントエンドに実行してもらう
- クライアントのCookieにcsrftokenというkeyでランダム文字列のトークンが格納される
    - デフォルトがcsrftokenですが設定で変更可能です
- リクエスト毎にクライアントからx-csrftokenというkeyでヘッダをAPI実行時にセットする
    - デフォルトがx-csrftokenですが設定で変更可能です
- Middleware内でヘッダ内のトークンとCookie内のトークンを照合し、問題がなければリクエストを許可する

## 実装
### main.py
main.pyにstarlette_csrfのCSRFMiddlewareを追加します

```main.py
from fastapi import FastAPI
from starlette_csrf import CSRFMiddleware
from routers import auth, todos
from config.csrf import csrf_settings


app = FastAPI()

app.add_middleware(CSRFMiddleware, **csrf_settings)
app.include_router(auth.router)
app.include_router(todos.router)
```

add_middlewareのメソッド内でkwargsを使ってMiddlewareのオプションを追加できるので後述するcsrf_settingsのdictの設定が追加されます

```python
    def add_middleware(
        self,
        middleware_class: _MiddlewareFactory[P],
        *args: P.args,
        **kwargs: P.kwargs,
    ) -> None:
        if self.middleware_stack is not None:  # pragma: no cover
            raise RuntimeError("Cannot add middleware after an application has started")
        self.user_middleware.insert(0, Middleware(middleware_class, *args, **kwargs))
```


### CSRFMiddlewareの設定
CSRFMiddlewareに追加する設定をdictにまとめています
```config/csrf.py
from config.env import app_settings


csrf_settings = {
    "secret": app_settings.SECRET_KEY,
    "exempt_urls": app_settings.EXCLUDED_PATHS,
    "cookie_name": app_settings.CSRF_COOKIE_NAME,
    "cookie_secure": app_settings.COOKIE_SECURE,
    "cookie_httponly": app_settings.COOKIE_HTTP_ONLY,
    "cookie_samesite": app_settings.COOKIE_SAME_SITE,
    "header_name": app_settings.CSRF_HEADER_NAME,
}
```

CSRFMiddlewareクラスには以下の設定ができます
追加したい設定等あれば下記を参考にしてください

```python
class CSRFMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret: str,
        *,
        required_urls: Optional[list[Pattern]] = None,
        exempt_urls: Optional[list[Pattern]] = None,
        sensitive_cookies: Optional[set[str]] = None,
        safe_methods: set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"},
        cookie_name: str = "csrftoken",
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = False,
        cookie_httponly: bool = False,
        cookie_samesite: str = "lax",
        header_name: str = "x-csrftoken",
    ) -> None:
        self.app = app
        self.serializer = URLSafeSerializer(secret, "csrftoken")
        self.secret = secret
        self.required_urls = required_urls
        self.exempt_urls = exempt_urls
        self.sensitive_cookies = sensitive_cookies
        self.safe_methods = safe_methods
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.header_name = header_name
```

READMEにも詳細が記載されていますので下記を参考にしてみてください

https://github.com/frankie567/starlette-csrf?tab=readme-ov-file#arguments

使用する環境変数は以下のとおりです
EXCLUDED_PATHSにCSRFによる認証を適用したくないAPI(ログイン、ログアウト、リフレッシュトークンを使ったアクセストークンの更新)の正規表現の一覧をlistにして記載しています

```config/env.py
import os
import re

from pydantic_settings import BaseSettings


class AppSettings(BaseSettings):
    SECRET_KEY: str = os.environ.get("SECRET_KEY")
    COOKIE_SECURE: bool = os.environ.get("COOKIE_SECURE") == "True"
    COOKIE_HTTP_ONLY: bool = os.environ.get("COOKIE_HTTP_ONLY") == "True"
    COOKIE_SAME_SITE: str = os.environ.get("COOKIE_SAME_SITE")
    CSRF_COOKIE_NAME: str = "csrftoken"
    CSRF_HEADER_NAME: str = "X-CSRF-Token"
    EXCLUDED_PATHS: list = [
        re.compile(r"^/api/auth/login"),
        re.compile(r"^/api/auth/logout"),
        re.compile(r"^/api//auth/refresh"),
    ]


app_settings = AppSettings()
```

## APIの作成
CookieのHttpOnly属性がTrueの場合、Javascriptから取得できないのでget_csrf_tokenを作成してCSRFトークンをレスポンスに表示してフロントエンド側で使用できるようにします
また、ログアウトする場合はdelete_cookieメソッドを使ってトークンをCookieから削除するようにします

```application/routes/auth.py
from fastapi import APIRouter, Request, Response, status
from fastapi.responses import JSONResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.get("/get_csrf_token")
def get_csrf_token(request: Request) -> JSONResponse:
    return JSONResponse(
        content={"csrftoken": request.cookies.get("csrftoken")},
        status_code=status.HTTP_200_OK,
    )


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    response.delete_cookie(key="csrftoken")
    return {"msg": "Logged out"}

```

## CSRFMiddlewareについて
以下がstarlette_csrfのCSRFMiddlewareのソースコードです
はじめにCookieからCSRFトークンを取得します
Middlewareのオプションで指定したrequired_urlsやexempt_urlsを見て該当するエンドポイントかなどを判断します
HeaderとCookie内のCSRFトークンを照合し、一致することが確認できれば完了です

```starlette_csrf/middleware.py
import functools
import http.cookies
import secrets
from re import Pattern
from typing import Dict, List, Optional, Set, cast

from itsdangerous import BadSignature
from itsdangerous.url_safe import URLSafeSerializer
from starlette.datastructures import URL, MutableHeaders
from starlette.requests import Request
from starlette.responses import PlainTextResponse, Response
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class CSRFMiddleware:
    def __init__(
        self,
        app: ASGIApp,
        secret: str,
        *,
        required_urls: Optional[List[Pattern]] = None,
        exempt_urls: Optional[List[Pattern]] = None,
        sensitive_cookies: Optional[Set[str]] = None,
        safe_methods: Set[str] = {"GET", "HEAD", "OPTIONS", "TRACE"},
        cookie_name: str = "csrftoken",
        cookie_path: str = "/",
        cookie_domain: Optional[str] = None,
        cookie_secure: bool = False,
        cookie_httponly: bool = False,
        cookie_samesite: str = "lax",
        header_name: str = "x-csrftoken",
    ) -> None:
        self.app = app
        self.serializer = URLSafeSerializer(secret, "csrftoken")
        self.secret = secret
        self.required_urls = required_urls
        self.exempt_urls = exempt_urls
        self.sensitive_cookies = sensitive_cookies
        self.safe_methods = safe_methods
        self.cookie_name = cookie_name
        self.cookie_path = cookie_path
        self.cookie_domain = cookie_domain
        self.cookie_secure = cookie_secure
        self.cookie_httponly = cookie_httponly
        self.cookie_samesite = cookie_samesite
        self.header_name = header_name

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] not in ("http", "websocket"):  # pragma: no cover
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        csrf_cookie = request.cookies.get(self.cookie_name)

        if self._url_is_required(request.url) or (
            request.method not in self.safe_methods
            and not self._url_is_exempt(request.url)
            and self._has_sensitive_cookies(request.cookies)
        ):
            submitted_csrf_token = await self._get_submitted_csrf_token(request)
            if (
                not csrf_cookie
                or not submitted_csrf_token
                or not self._csrf_tokens_match(csrf_cookie, submitted_csrf_token)
            ):
                response = self._get_error_response(request)
                await response(scope, receive, send)
                return

        send = functools.partial(self.send, send=send, scope=scope)
        await self.app(scope, receive, send)

    async def send(self, message: Message, send: Send, scope: Scope) -> None:
        request = Request(scope)
        csrf_cookie = request.cookies.get(self.cookie_name)

        if csrf_cookie is None:
            message.setdefault("headers", [])
            headers = MutableHeaders(scope=message)

            cookie: http.cookies.BaseCookie = http.cookies.SimpleCookie()
            cookie_name = self.cookie_name
            cookie[cookie_name] = self._generate_csrf_token()
            cookie[cookie_name]["path"] = self.cookie_path
            cookie[cookie_name]["secure"] = self.cookie_secure
            cookie[cookie_name]["httponly"] = self.cookie_httponly
            cookie[cookie_name]["samesite"] = self.cookie_samesite
            if self.cookie_domain is not None:
                cookie[cookie_name]["domain"] = self.cookie_domain  # pragma: no cover
            headers.append("set-cookie", cookie.output(header="").strip())

        await send(message)

    def _has_sensitive_cookies(self, cookies: Dict[str, str]) -> bool:
        if not self.sensitive_cookies:
            return True
        for sensitive_cookie in self.sensitive_cookies:
            if sensitive_cookie in cookies:
                return True
        return False

    def _url_is_required(self, url: URL) -> bool:
        if not self.required_urls:
            return False
        for required_url in self.required_urls:
            if required_url.match(url.path):
                return True
        return False

    def _url_is_exempt(self, url: URL) -> bool:
        if not self.exempt_urls:
            return False
        for exempt_url in self.exempt_urls:
            if exempt_url.match(url.path):
                return True
        return False

    async def _get_submitted_csrf_token(self, request: Request) -> Optional[str]:
        return request.headers.get(self.header_name)

    def _generate_csrf_token(self) -> str:
        return cast(str, self.serializer.dumps(secrets.token_urlsafe(128)))

    def _csrf_tokens_match(self, token1: str, token2: str) -> bool:
        try:
            decoded1: str = self.serializer.loads(token1)
            decoded2: str = self.serializer.loads(token2)
            return secrets.compare_digest(decoded1, decoded2)
        except BadSignature:
            return False

    def _get_error_response(self, request: Request) -> Response:
        return PlainTextResponse(
            content="CSRF token verification failed", status_code=403
        )

```

## 実際に実行してみよう！
CSRFトークンの発行APIを実行し、トークンが発行されたことを確認できました

![スクリーンショット 2025-05-06 13.33.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/219663a8-9e96-4e01-8763-c3bd3fa9c47d.png)

Cookie内にトークンが格納されていることも確認できました
![スクリーンショット 2025-05-06 15.10.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/19d7e52b-6bb3-4ec8-b96b-725fba14843e.png)

以下のようにCSRFトークンをヘッダにセットし、API実行できれば成功です
![スクリーンショット 2025-05-06 13.33.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/57dc8061-b3f2-41a3-b7e4-a8985b27fdb8.png)

トークンがない場合、間違っている場合などは403を返します
![スクリーンショット 2025-05-06 15.19.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/02b1a4e8-9170-426e-9129-a71acd88ac06.png)

ログアウトAPIを実行した後にCSRFトークンが削除されていることを確認できました
![スクリーンショット 2025-05-06 15.13.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/843cedf4-52e0-4f15-9f64-828cf35662c7.png)

## 参考
https://github.com/frankie567/starlette-csrf
