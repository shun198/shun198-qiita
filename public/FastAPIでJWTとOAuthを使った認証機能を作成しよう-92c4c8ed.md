---
title: FastAPIでJWTとOAuthを使った認証機能を作成しよう！
tags:
  - OAuth
  - sqlalchemy
  - JWT
  - bcrypt
  - FastAPI
private: false
updated_at: '2025-04-29T11:51:25+09:00'
id: 92c4c8eda8a66e78b400
organization_url_name: null
slide: false
---
## 概要
Webアプリケーションでログイン認証する際はJWTとOAuthを使って行うのが一般的です
今回はFastAPI、JWT、OAuthを使ってログイン機構を作成します

## 前提
- 本来は作成したJWTをCookieに入れたり、Middleware使って認証したりと色々考えないといけないですが今回は必要最低限の機能を使って実装したいと思います


https://qiita.com/shun198/items/92c4c8eda8a66e78b400

## JWTとは
JSON Web Tokenの略。JSON形式で記述されたトークンを使用して認証(Authentication)する仕組みです
今回は実際に認証に使うアクセストークンとアクセストークンの有効期限が切れた後でも再度ログインせずに新しいアクセストークンを取得するリフレッシュトークンを作成します

## OAuthとは
パスワードなどを共有することなく、アプリケーションやサービスがユーザーの情報へアクセスすることを認可(Authorization)するための仕組みです
JWTとOAuthを組み合わせることで、パスワードを使わずJWTトークンをヘッダに入れてログインすることが一般的です

## ディレクトリ構成
```
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

今回は以下のAPIを作成します
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
リクエスト送信時のユーザ作成用のスキーマとトークン作成時のレスポンスのスキーマを作成します

```schemas/auth.py
from pydantic import BaseModel


class CreateUserRequest(BaseModel):
    username: str
    email: str
    first_name: str
    last_name: str
    password: str
    is_admin: bool
    phone_number: str


class Token(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str



class CurrentUser(BaseModel):
    username: str
    id: int
```


### ユーザ作成用API
ユーザ作成用のAPIを作成します
公式ドキュメントではbcryptとpasslibを使ってパスワードをハッシュ化していますがbcrypt4.1ではpasslibを使うと正常に動作しないので今回はbcryptのみを使って行います

> This is an issue with how passlib attempts to read a version (for logging only) and fails because it's loading modules that no longer exist in bcrypt 4.1.x. I'd suggest filing an issue against them for this.

一度パスワードをutf-8にエンコードし、saltと一緒にbcryptのhashpwを使ってbyte文字列に変換します
その後、パスワードをDB内にstringとして保存するためにutf-8にデコードします

```routers/auth.py
@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    hashed_password = bcrypt.hashpw(
        create_user_request.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_admin=create_user_request.is_admin,
        password=hashed_password,
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
を使ってOAuth認証を有効にします
authenticate_userメソッドを使って該当するユーザ名とパスワードを持つユーザを探します
bcrypt.checkpwを使ってリクエスト内のパスワードとDB内のハッシュ化されたパスワードが一致するか確認します
ユーザが存在することを確認したらアクセストークンとリフレッシュトークンを作成します

```routers/auth.py
# OAuthを使って認証
@router.post("/login")
async def login_for_access_token(
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
        timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    refresh_token = create_jwt_token(
        user.username,
        user.id,
        timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS)),
    )
    
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


def create_jwt_token(
    username: str, user_id: int, role: str, expires_delta: timedelta
):
    encode = {"sub": username, "iss": user_id, "role": role}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


def authenticate_user(username: str, password: str, db):
    user = db.execute(
        select(Users).where(Users.username == username)
    ).scalar_one_or_none()
    if not user:
        return False
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return False
    return user
```

### 現在のログインユーザの確認
認証が必要なAPIに対して該当するユーザが存在するか確認するメソッドを作成します

```routers/auth.py
async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("iss")
        if not username or not user_id:
            return None
        return CurrentUser(username=username, id=user_id)
    except Exception:
        return None
```

### リフレッシュトークンを使ったアクセストークンの更新
アクセストークン更新用のAPIを作成します

```routers/auth.py
@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("iss")
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        new_access_token = create_jwt_token(
            username,
            user_id,
            timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )
```

## 実装した内容の一覧
今回作成したAPIやメソッドをまとめると以下のようになります
```routers/auth.py
import os
from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt
from jose.exceptions import ExpiredSignatureError
from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError, jwt
from models import Users
from schemas.auth import CreateUserRequest, CurrentUser, Token
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/auth", tags=["auth"])

SECRET_KEY = os.environ.get("SECRET_KEY")
ALGORITHM = os.environ.get("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = os.environ.get("ACCESS_TOKEN_EXPIRE_MINUTES")
REFRESH_TOKEN_EXPIRE_DAYS = os.environ.get("REFRESH_TOKEN_EXPIRE_DAYS")

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/token")


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_user(db: db_dependency, create_user_request: CreateUserRequest):
    hashed_password = bcrypt.hashpw(
        create_user_request.password.encode("utf-8"), bcrypt.gensalt()
    ).decode("utf-8")
    create_user_model = Users(
        email=create_user_request.email,
        username=create_user_request.username,
        first_name=create_user_request.first_name,
        last_name=create_user_request.last_name,
        is_admin=create_user_request.is_admin,
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
        return False
    if not bcrypt.checkpw(password.encode("utf-8"), user.password.encode("utf-8")):
        return False
    return user


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUser:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("iss")
        if not username or not user_id:
            return None
        return CurrentUser(username=username, id=user_id)

    except Exception:
        return None


def create_jwt_token(username: str, user_id: int, expires_delta: timedelta):
    encode = {"sub": username, "iss": user_id}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({"exp": expires})
    return jwt.encode(encode, SECRET_KEY, algorithm=ALGORITHM)


# OAuthを使って認証
@router.post("/login")
async def login_for_access_token(
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
        timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
    )
    refresh_token = create_jwt_token(
        user.username,
        user.id,
        timedelta(days=int(REFRESH_TOKEN_EXPIRE_DAYS)),
    )

    return {
        "access_token": access_token,
        "refresh_token": refresh_token,
        "token_type": "bearer",
    }


@router.post("/refresh")
async def refresh_token(refresh_token: str):
    try:
        payload = jwt.decode(refresh_token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str = payload.get("sub")
        user_id: int = payload.get("iss")
        if not username or not user_id:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token"
            )

        new_access_token = create_jwt_token(
            username,
            user_id,
            timedelta(minutes=int(ACCESS_TOKEN_EXPIRE_MINUTES)),
        )
        return {"access_token": new_access_token, "token_type": "bearer"}
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token"
        )

```

### 認証時のみAPIを実行できるよう設定する
認証を必要とするAPIにuser_dependencyを適用します
user_dependencyを設定することでAPI実行時にget_current_userメソッドを実行します
ユーザが存在する場合はAPIが実行され、存在しない場合は401を返します
APIの作成方法の詳細について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/8c45d60254f4338a8650

```routers/todos.py
from typing import Annotated, List

from database import SessionLocal
from fastapi import APIRouter, Depends, HTTPException, status
from models import Todos
from routers.auth import get_current_user
from schemas.todos import TodoModel, TodoResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/todos", tags=["todos"])


async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


db_dependency = Annotated[Session, Depends(get_db)]
user_dependency = Annotated[dict, Depends(get_current_user)]


@router.get("", response_model=List[TodoResponse])
async def read_todos(user: user_dependency, db: db_dependency):
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todos = db.scalars(select(Todos).order_by(Todos.id)).all()
    return todos


@router.get("/{todo_id}", response_model=TodoResponse)
async def read_todo(user: user_dependency, db: db_dependency, todo_id: int):
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
async def create_todo(user: user_dependency, db: db_dependency, todo_model: TodoModel):
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
async def update_todo(
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
    db.execute(
        update(Todos).where(Todos.id == todo_id).values(**todo_model.model_dump())
    )
    db.commit()
    return todo


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(user: user_dependency, db: db_dependency, todo_id: int):
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

## 実際に実行してみよう！
### ユーザの作成
ユーザを作成します

![スクリーンショット 2025-04-26 17.40.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/29c31acb-6908-403f-9c9a-e411c9b122d0.png)

ユーザが作成され、200を返したら成功です
![スクリーンショット 2025-04-26 17.42.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/da4e8fa1-c30b-4102-8aea-6ca355a279c6.png)

もう一度同じユーザ名もしくメールアドレスでユーザを新規で作成し、400を返したら成功です

![スクリーンショット 2025-04-26 17.43.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/597ec89f-8554-411e-869c-e56cd5ba69c8.png)

### ログイン
先ほど作成したユーザを使ってログインします
![スクリーンショット 2025-04-26 18.33.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e079e0e9-e38f-46d5-a4a5-4f0a5b1b1aa8.png)

以下のようにアクセストークンとリフレッシュトークンが発行されたら成功です
![スクリーンショット 2025-04-26 18.34.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4a3cc605-15f6-4aaa-91cf-a47666e4f507.png)

### ログインした状態で別のAPIを実行
Postmanを使ってヘッダにJWTトークンを入れます
以下のように認証が完了し、APIを実行できたら成功です
![スクリーンショット 2025-04-26 17.59.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2bd8f104-e73b-4bfd-bad1-ddd302866363.png)

ヘッダがない状態でAPIを実行し、401が返ってきたら成功です
![スクリーンショット 2025-04-29 8.39.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f203ff4-8857-4650-a238-80c3c7dd9521.png)

### アクセストークンの更新
以下のようにアクセストークンを更新できたら成功です

![スクリーンショット 2025-04-26 19.54.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8392ec4b-6e96-4bec-a430-f979a38efe72.png)


## 参考
https://fastapi.tiangolo.com/ja/tutorial/security/oauth2-jwt/#passlib

https://github.com/pyca/bcrypt/issues/684

https://docs.sqlalchemy.org/en/20/tutorial/data_select.html
