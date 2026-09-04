---
title: FastAPIでJWTとOAuthを使った認証機能を作成しよう！
tags:
  - OAuth
  - sqlalchemy
  - JWT
  - Argon2
  - FastAPI
private: false
updated_at: '2025-04-29T11:51:25+09:00'
id: 92c4c8eda8a66e78b400
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要

今回はFastAPIのOAuth2用フォームとJWTを使って、ファーストパーティー向けのログイン機構を作成します。
外部サービスへ認可を委譲するOAuthクライアントでは、パスワードを直接受け取る方式ではなく、Authorization Code FlowとPKCEを利用してください。

## 前提

- サンプルではアクセストークンとリフレッシュトークンを分け、有効期限とトークン種別を検証する。
- 本番環境ではHTTPSを必須にし、リフレッシュトークンのローテーション、失効管理、安全な保存も実装する。
- `SECRET_KEY`には十分な長さの乱数を使い、リポジトリへ記載せずシークレット管理サービスや環境変数から渡す。
- FastAPI 0.141.1、Python 3.14を前提とする。

https://qiita.com/shun198/items/92c4c8eda8a66e78b400

## JWTとは

JSON Web Tokenの略です。JSON形式で記述されたトークンを認証(Authentication)に使用します。
今回は認証用のアクセストークンと、再ログインせずにアクセストークンを更新するためのリフレッシュトークンを作成します。

## OAuthとは

パスワードなどを共有せず、アプリケーションやサービスによるユーザー情報へのアクセスを認可(Authorization)する仕組みです。
このサンプルではOAuth2のパスワード入力用フォームを利用しますが、パスワード検証は自分のAPI内で行います。第三者のOAuthプロバイダーへ認可を委譲する実装とは異なります。

## ディレクトリ構成

```text
tree
.
└── application
    ├── alembic.ini
    ├── database.py
    ├── main.py
    ├── migrations
    ├── models.py
    ├── poetry.lock
    ├── pyproject.toml
    ├── routers
    │   ├── __init__.py
    │   ├── auth.py
    │   └── todos.py
    └── schemas
        ├── __init__.py
        ├── auth.py
        └── todos.py
```

今回は以下のAPIを作成します。

- ログインAPI
- ユーザ作成API
- リフレッシュトークンを使ったアクセストークン更新用API

### Model

```models.py
from database import Base
from sqlalchemy import Boolean, Column, Integer, String


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True)
    username = Column(String, unique=True)
    first_name = Column(String)
    last_name = Column(String)
    password = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    phone_number = Column(String)


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
```

### APIのスキーマの定義

ユーザ作成用のリクエストスキーマと、トークン作成時のレスポンススキーマを作成します。

```schemas/auth.py
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    phone_number: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str


class CurrentUser(BaseModel):
    username: str
    id: int
```

### ユーザ作成用API

ユーザ作成用のAPIを作成します。
管理者権限を指定できないよう、公開APIのリクエストには`is_admin`を含めず、`False`に固定します。
FastAPIの現行ドキュメントに合わせて`pwdlib[argon2]`を使います。`PasswordHash.recommended()`は推奨設定のArgon2でパスワードをハッシュ化します。
既存環境でbcryptのハッシュを保存している場合は、切り替え前に移行方法を設計してください。

```shell
poetry add "fastapi[standard]==0.141.1" pyjwt "pwdlib[argon2]" sqlalchemy
```

```routers/auth.py
@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    hashed_password = password_hash.hash(create_user_request.password)
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_admin=False,
        password=hashed_password,
        phone_number=create_user_request.phone_number,
        is_active=True,
    )
    try:
        db.add(create_user_model)
        db.commit()
        return {"msg": "user created"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )
```

### 認証用API

`form_data: Annotated[OAuth2PasswordRequestForm, Depends()]`
を使ってOAuth2仕様のパスワード入力フォームを受け取ります。
authenticate_userメソッドを使って該当するユーザ名とパスワードを持つユーザを探します。
`password_hash.verify()`を使ってリクエスト内のパスワードとDB内のハッシュが一致するか確認します。
ユーザが存在することを確認したらアクセストークンとリフレッシュトークンを作成します。

```routers/auth.py
@router.post("/login")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_jwt_token(
        user.username,
        user.id,
        "access",
        timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    refresh_token = create_jwt_token(
        user.username,
        user.id,
        "refresh",
        timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS)),
    )

    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def create_jwt_token(
    username: str, user_id: int, token_type: str, expires_delta: timedelta
):
    encode = {"sub": username, "uid": user_id, "token_type": token_type}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db):
    user = db.execute(
        select(Users).where(Users.username == username)
    ).scalar_one_or_none()
    if not user:
        password_hash.verify(password, DUMMY_HASH)
        return False
    if not password_hash.verify(password, user.password):
        return False
    return user
```

### 現在のログインユーザの確認

認証が必要なAPIに対して該当するユーザが存在するか確認するメソッドを作成します。

```routers/auth.py
def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    payload = decode_token(token, "access")
    return CurrentUser(username=str(payload["sub"]), id=int(payload["uid"]))
```

### リフレッシュトークンを使ったアクセストークンの更新

アクセストークン更新用のAPIを作成します。アクセストークンを更新APIへ渡しても受け付けないよう、JWTの`token_type`が`refresh`であることを検証します。

```routers/auth.py
@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token, "refresh")
    new_access_token = create_jwt_token(
        str(payload["sub"]),
        int(payload["uid"]),
        "access",
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_access_token, "token_type": "bearer"}
```

## 実装した内容の一覧

今回作成したAPIやメソッドをまとめると以下のようになります。

```routers/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import jwt
from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jwt.exceptions import InvalidTokenError
from models import Users
from pwdlib import PasswordHash
from schemas.auth import CreateUserRequest, CurrentUser, RefreshTokenRequest, Token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.environ["SECRET_KEY"]
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(
    os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES", "30")
)
REFRESH_TOKEN_EXPIRE_DAYS = int(os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS", "7"))

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")
password_hash = PasswordHash.recommended()
DUMMY_HASH = password_hash.hash("not-the-user-password")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED)
def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    hashed_password = password_hash.hash(create_user_request.password)
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_admin=False,
        password=hashed_password,
        phone_number=create_user_request.phone_number,
        is_active=True,
    )
    try:
        db.add(create_user_model)
        db.commit()
        return {"msg": "user created"}
    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists",
        )


def authenticate_user(username: str, password: str, db):
    user = db.execute(
        select(Users).where(Users.username == username)
    ).scalar_one_or_none()
    if not user:
        password_hash.verify(password, DUMMY_HASH)
        return False
    if not password_hash.verify(password, user.password):
        return False
    return user


def decode_token(token: str, expected_type: str) -> dict:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        if (
            not isinstance(payload.get("sub"), str)
            or not isinstance(payload.get("uid"), int)
            or payload.get("token_type") != expected_type
        ):
            raise InvalidTokenError("Invalid token claims")
        return payload
    except InvalidTokenError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
) -> CurrentUser:
    payload = decode_token(token, "access")
    return CurrentUser(username=str(payload["sub"]), id=int(payload["uid"]))


def create_jwt_token(
    username: str, user_id: int, token_type: str, expires_delta: timedelta
):
    encode = {"sub": username, "uid": user_id, "token_type": token_type}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


@router.post("/login")
def login_for_access_token(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()], db: db_dependency
) -> Token:
    user = authenticate_user(form_data.username, form_data.password, db)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_jwt_token(
        user.username,
        user.id,
        "access",
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    refresh_token = create_jwt_token(
        user.username,
        user.id,
        "refresh",
        timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
def refresh_token(request: RefreshTokenRequest):
    payload = decode_token(request.refresh_token, "refresh")
    new_access_token = create_jwt_token(
        str(payload["sub"]),
        int(payload["uid"]),
        "access",
        timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return {"access_token": new_access_token, "token_type": "bearer"}

```

### 認証時のみAPIを実行できるよう設定する

認証を必要とするAPIにuser_dependencyを適用します。
user_dependencyを設定すると、API実行時にget_current_userメソッドを実行します。
ユーザが存在する場合はAPIを実行し、存在しない場合は401を返します。
APIの作成方法の詳細について知りたい方は以下の記事を参考にしてください。

https://qiita.com/shun198/items/8c45d60254f4338a8650

```routers/todos.py
from typing import Annotated

from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from models import Todos
from routers.auth import get_current_user
from schemas.auth import CurrentUser
from schemas.todos import TodoModel, TodoResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/todos", tags=["todos"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[CurrentUser, Depends(get_current_user)]


@router.get("", response_model=list[TodoResponse])
def read_todos(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todos = db.scalars(select(Todos).order_by(Todos.id)).all()
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
def read_todo(user: user_dependency, db: db_dependency, todo_id: int):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
def create_todo(user: user_dependency, db: db_dependency, todo_model: TodoModel):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = Todos(**todo_model.model_dump())
    db.add(todo)
    db.commit()
    db.refresh(todo)
    return todo


@router.put("/{todo_id}", response_model=TodoResponse)
def update_todo(
    user: user_dependency, db: db_dependency, todo_model: TodoModel, todo_id: int
):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    for key, value in todo_model.model_dump().items():
        setattr(todo, key, value)
    db.commit()
    db.refresh(todo)
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_todo(user: user_dependency, db: db_dependency, todo_id: int):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    db.delete(todo)
    db.commit()

```

## 実際に実行してみよう

### ユーザの作成

ユーザを作成します。

![スクリーンショット 2025-04-26 17.40.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/29c31acb-6908-403f-9c9a-e411c9b122d0.png)

ユーザが作成され、201を返したら成功です。
![スクリーンショット 2025-04-26 17.42.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/da4e8fa1-c30b-4102-8aea-6ca355a279c6.png)

もう一度同じユーザ名もしくはメールアドレスでユーザを新規作成し、400を返したら成功です。

![スクリーンショット 2025-04-26 17.43.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/597ec89f-8554-411e-869c-e56cd5ba69c8.png)

### ログイン

先ほど作成したユーザを使ってログインします。
![スクリーンショット 2025-04-26 18.33.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e079e0e9-e38f-46d5-a4a5-4f0a5b1b1aa8.png)

以下のようにアクセストークンとリフレッシュトークンが発行されたら成功です。
![スクリーンショット 2025-04-26 18.34.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4a3cc605-15f6-4aaa-91cf-a47666e4f507.png)

### ログインした状態で別のAPIを実行

Postmanを使ってヘッダにJWTトークンを入れます。
以下のように認証が完了し、APIを実行できたら成功です。
![スクリーンショット 2025-04-26 17.59.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2bd8f104-e73b-4bfd-bad1-ddd302866363.png)

ヘッダがない状態でAPIを実行し、401が返ってきたら成功です。
![スクリーンショット 2025-04-29 8.39.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f203ff4-8857-4650-a238-80c3c7dd9521.png)

### アクセストークンの更新

以下のようにアクセストークンを更新できたら成功です。

![スクリーンショット 2025-04-26 19.54.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8392ec4b-6e96-4bec-a430-f979a38efe72.png)

## 参考

https://fastapi.tiangolo.com/ja/tutorial/security/oauth2-jwt/

https://cheatsheetseries.owasp.org/cheatsheets/Password_Storage_Cheat_Sheet.html

https://www.rfc-editor.org/rfc/rfc9700.html

https://www.rfc-editor.org/rfc/rfc10017.html

https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
