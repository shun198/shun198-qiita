---
title: FastAPIのアプリケーションでJWTトークンをCookieにセットするには
tags:
  - cookie
  - JWT
  - FastAPI
private: false
updated_at: '2025-05-06T15:46:19+09:00'
id: c26677d7722b1390f6c4
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
FastAPIでJWTを使った認証機能を作成する際に、JWTをCookieへ保存・削除したいニーズがあるかと思いますので解説します

## 前提
JWTトークンを使った認証機能をすでに作成している前提で話を進めますので未作成の方は下記の記事を参考にしてみてください

https://qiita.com/shun198/items/92c4c8eda8a66e78b400

## JWTをCookie に保存するメリット
以下がメリットになるかと思います
- HttpOnly属性を使ってXSS対策ができる
    - JavaScriptを使ってCookieにアクセスできなくなる
- クライアント側の実装がシンプルに
    - `Authorization: Bearer {token}`をヘッダーに毎回設定する必要がなくなる

## 実装
- ログイン
- ログアウト
- アクセストークン更新

用のAPIを作成します

FastAPIのResponseにset_cookieメソッドがあるので以下のようにアクセストークンの値をCookieにセットします

```python
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=1800,
    )
```

詳細は下記公式ドキュメントを参照してください

https://fastapi.tiangolo.com/advanced/response-cookies/#use-a-response-parameter

以下のように
- ログイン
- アクセストークン更新

ではCookieへアクセストークン、リフレッシュトークンをセットする処理を

- ログアウト

ではCookieからアクセストークン、リフレッシュトークンを削除する処理を記載しました

```application/routers/auth.py
from datetime import timedelta
from typing import Annotated

from config.dependency import get_user_usecase
from config.env import app_settings
from config.jwt import check_password, create_jwt_token, decode_jwt_token, hash_password
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from infrastructure.emails.email import send_email
from jose import JWTError
from schemas.requests.auth_request_schema import CreateUserRequest
from usecases.user_usecase import UserUsecase

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _authenticate_user(username: str, password: str, user_usecase: UserUsecase):
    user = user_usecase.get_user_by_username(username)
    if not user:
        return False
    if not check_password(password, user.password):
        return False
    return user


# OAuthを使って認証
@router.post("/login")
async def login_for_access_token(
    response: Response,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> Response:
    user = _authenticate_user(form_data.username, form_data.password, user_usecase)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_jwt_token(
        user.username,
        user.id,
        timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_jwt_token(
        user.username,
        user.id,
        timedelta(days=app_settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    # https://fastapi.tiangolo.com/advanced/response-cookies/#use-a-response-parameter
    response.set_cookie(
        key="access_token",
        value=f"Bearer {access_token}",
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=1800,
    )
    response.set_cookie(
        key="refresh_token",
        value=f"Bearer {refresh_token}",
        httponly=False,
        secure=True,
        samesite="lax",
        max_age=86400,
    )
    response.status_code = status.HTTP_200_OK
    return response


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token")
    response.delete_cookie(key="refresh_token")
    return {"msg": "Logged out"}


@router.post("/refresh")
async def refresh_token(
    request: Request,
    response: Response,
    user_usecase: UserUsecase = Depends(get_user_usecase),
) -> Response:
    try:
        decoded_token = decode_jwt_token(
            request.cookies.get("refresh_token").split("Bearer ")[1]
        )
        username: str = decoded_token.get("sub")
        user_id: int = decoded_token.get("iss")
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )
        user = user_usecase.get_user_by_username(username)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found"
            )
        new_access_token = create_jwt_token(
            user.username,
            user.id,
            timedelta(minutes=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        )
        response.set_cookie(
            key="access_token",
            value=f"Bearer {new_access_token}",
            httponly=False,
            secure=True,
            samesite="lax",
            max_age=1800,
        )
        response.status_code = status.HTTP_200_OK
        return response
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

```

続いてdependency.pyではHeader内にJWTトークンがあるか確認するカスタムクラス(OAuth2PasswordBearerWithCookie)とJWTトークンの値を確認するget_current_user_from_cookieメソッドを作成します

```dependency.py
from typing import Annotated, Optional

from config.jwt import decode_jwt_token
from fastapi import Depends, Request, status
from fastapi.exceptions import HTTPException
from fastapi.openapi.models import OAuthFlows as OAuthFlowsModel
from fastapi.security import OAuth2
from fastapi.security.utils import get_authorization_scheme_param
from infrastructure.database import get_db
from repositories.todo_repository import TodoRepository
from repositories.user_repository import UserRepository
from schemas.requests.auth_request_schema import CurrentUserRequest
from sqlalchemy.orm import Session
from usecases.todo_usecase import TodoUsecase
from usecases.user_usecase import UserUsecase


# https://zenn.dev/noknmgc/articles/fastapi-jwt-cookie
# https://github.com/fastapi/fastapi/issues/480
class OAuth2PasswordBearerWithCookie(OAuth2):
    def __init__(
        self,
        tokenUrl: str,
        scheme_name: str = None,
        scopes: dict = None,
        auto_error: bool = True,
    ):
        if not scopes:
            scopes = {}
        flows = OAuthFlowsModel(password={"tokenUrl": tokenUrl, "scopes": scopes})
        super().__init__(flows=flows, scheme_name=scheme_name, auto_error=auto_error)

    async def __call__(self, request: Request) -> Optional[str]:
        authorization: str = request.headers.get("Authorization")
        if not authorization:
            authorization: str = request.cookies.get("access_token")
        scheme, param = get_authorization_scheme_param(authorization)
        if not authorization or scheme.lower() != "bearer":
            if self.auto_error:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Not authenticated",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            else:
                return None
        return param


oauth2_scheme = OAuth2PasswordBearerWithCookie(tokenUrl="/api/auth/login")


def get_todo_usecase(db: Session = Depends(get_db)) -> TodoUsecase:
    todo_repository = TodoRepository(db)
    return TodoUsecase(todo_repository)


def get_user_usecase(db: Session = Depends(get_db)) -> UserUsecase:
    user_repository = UserRepository(db)
    return UserUsecase(user_repository)


async def get_current_user_from_cookie(
    token: str = Depends(oauth2_scheme),
) -> CurrentUserRequest:
    try:
        decoded_token = decode_jwt_token(token)
        username: str = decoded_token.get("sub")
        user_id: int = decoded_token.get("iss")
        if not username or not user_id:
            return None
        return CurrentUserRequest(username=username, id=user_id)
    except Exception:
        return None


user_dependency = Annotated[dict, Depends(get_current_user_from_cookie)]

db_dependency = Annotated[Session, Depends(get_db)]

```

OAuth2PasswordBearerWithCookieクラスはOAuth2クラスの__call__メソッドをOverrideしています
```fastapi/security/oauth2.py
class OAuth2(SecurityBase):
    """
    This is the base class for OAuth2 authentication, an instance of it would be used
    as a dependency. All other OAuth2 classes inherit from it and customize it for
    each OAuth2 flow.

    You normally would not create a new class inheriting from it but use one of the
    existing subclasses, and maybe compose them if you want to support multiple flows.

    Read more about it in the
    [FastAPI docs for Security](https://fastapi.tiangolo.com/tutorial/security/).
    """

    def __init__(
        self,
        *,
        flows: Annotated[
            Union[OAuthFlowsModel, Dict[str, Dict[str, Any]]],
            Doc(
                """
                The dictionary of OAuth2 flows.
                """
            ),
        ] = OAuthFlowsModel(),
        scheme_name: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme name.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        description: Annotated[
            Optional[str],
            Doc(
                """
                Security scheme description.

                It will be included in the generated OpenAPI (e.g. visible at `/docs`).
                """
            ),
        ] = None,
        auto_error: Annotated[
            bool,
            Doc(
                """
                By default, if no HTTP Authorization header is provided, required for
                OAuth2 authentication, it will automatically cancel the request and
                send the client an error.

                If `auto_error` is set to `False`, when the HTTP Authorization header
                is not available, instead of erroring out, the dependency result will
                be `None`.

                This is useful when you want to have optional authentication.

                It is also useful when you want to have authentication that can be
                provided in one of multiple optional ways (for example, with OAuth2
                or in a cookie).
                """
            ),
        ] = True,
    ):
        self.model = OAuth2Model(
            flows=cast(OAuthFlowsModel, flows), description=description
        )
        self.scheme_name = scheme_name or self.__class__.__name__
        self.auto_error = auto_error

    async def __call__(self, request: Request) -> Optional[str]:
        authorization = request.headers.get("Authorization")
        if not authorization:
            if self.auto_error:
                raise HTTPException(
                    status_code=HTTP_403_FORBIDDEN, detail="Not authenticated"
                )
            else:
                return None
        return authorization
```

## 実際に認証してみよう！
ログインAPIを実行し、アクセストークンとリフレッシュトークンがCookieにセットされていることを確認できました

![スクリーンショット 2025-05-06 15.43.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8e3d0f17-a924-4ae2-9544-d0be134fb805.png)

Cookie内にトークンがあることで認証に成功しています
![スクリーンショット 2025-05-06 15.44.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/290113b8-d4e9-4120-adb2-aa8576434b5f.png)

![スクリーンショット 2025-05-06 15.45.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/001ee067-724c-45ab-8e01-6ef2de40c9d2.png)

ログアウトすることでトークンが削除されていることが確認できました
![スクリーンショット 2025-05-06 15.45.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cc46865a-4365-4ff5-bc33-e188f3406131.png)

## 参考
https://fastapi.tiangolo.com/advanced/response-cookies/#use-a-response-parameter

https://zenn.dev/noknmgc/articles/fastapi-jwt-cookie

https://github.com/fastapi/fastapi/issues/480

https://developer.mozilla.org/ja/docs/Web/HTTP/Cookies

https://blog.flatt.tech/entry/samesite_csrf_hsts
