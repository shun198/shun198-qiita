---
title: Python/FastAPIのアプリケーションをClean Architectureで実装してみた
tags:
  - Python
  - DDD
  - ソフトウェア設計
  - CleanArchitecture
  - FastAPI
private: false
updated_at: '2025-07-20T16:40:58+09:00'
id: 1c9516d02d5d01cbf652
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Python/FastAPIでTODOアプリを作る際にClean Architectureを意識して実装してみました

## Clean Architectureとは？
下記図のように「関心の分離」に基づいてレイヤー構造に分ける設計パターンの一つです
中心にビジネスロジックを据え、外側に技術的な要素を配置するのが特徴です

![スクリーンショット 2025-04-29 10.31.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bc5db4f7-d08c-4855-97d9-d898908e46f5.png)

### 各レイヤーの役割
- Entities（エンティティ）
    - ビジネスロジックを中心に記載
- Use Cases（ユースケース）
    - エンティティと組み合わせて、アプリの振る舞いを記載
- Interface Adapters（インターフェース層）
    - 外部の仕組み（フレームワーク、DBなど）とユースケースの橋渡し方法を記載
- Frameworks & Drivers（フレームワーク・ドライバ）
    - 実際のWebフレームワーク（FastAPIなど）、ORM（SQLAlchemyなど）、DB、外部サービス(メールサーバ、ファイルストレージ)との接続などを記載
    - 最も外側に位置し、アプリのコアには影響を与えないように設計する

Clean Architectureでアプリケーションを設計することで依存関係を円の内側へ向かいように設計することでビジネスロジックを技術的な変更から隔離でき、柔軟性やテスト性が向上し、保守性が上がると言われています

## ディレクトリ構成
今回は以下のようにFastAPIのアプリケーションを作成します

```
.
├── application
│   ├── config
│   │   ├── __init__.py
│   │   ├── dependency.py
│   │   ├── env.py
│   │   └── jwt.py
│   ├── infrastructure
│   │   ├── __init__.py
│   │   ├── database.py
│   │   └── slack.py
│   ├── main.py
│   ├── models
│   │   ├── __init__.py
│   │   ├── todo.py
│   │   └── user.py
│   ├── repositories 
│   │   ├── __init__.py
│   │   ├── todo_repository.py
│   │   └── user_repository.py
│   ├── routers
│   │   ├── __init__.py
│   │   ├── auth.py
│   │   └── todos.py
│   ├── schemas
│   │   ├── __init__.py
│   │   ├── requests
│   │   │   ├── __init__.py
│   │   │   ├── auth_request_schema.py
│   │   │   └── todo_request_schema.py
│   │   └── responses
│   │       ├── __init__.py
│   │       ├── auth_response_schema.py
│   │       └── todo_response_schema.py
│   └── usecases
│       ├── __init__.py
│       ├── todo_usecase.py
│       └── user_usecase.py
```

各レイヤーに対応するフォルダ名は以下のとおりです

|レイヤー|対応するフォルダ名|説明|
|---|---|---|
|Entities|models, repositories|models はドメインモデル（Entity）、repositories はそれに対する操作を定義するため、実質的にEntityに関係する|
|Use Cases|usecases|アプリケーションの振る舞いの中心。依存注入でRepositoryを呼ぶ|
|Interface Adapters|schema, routes|schemas はDTO、routers はAPIのエンドポイント定義（Controllerに相当する）|
|Frameworks & Drivers|infrastructure, config|DB接続やSlack連携などの外部技術依存を実装。config もインフラ寄り|

## 実装例
### Request/Responseのschemaの設定
Request/Response時のバリデーションの設定を行います

```schemas/requests/todo_request_schema.py
from pydantic import BaseModel, Field


class UpdateTodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


class CreateTodoRequest(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
```

```schemas/requests/todo_response_schema.py
from pydantic import BaseModel, Field


class TodoResponse(BaseModel):
    id: int = Field()
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool
    owner_id: int
```

### config/infrastructureファイル群
config内でDBセッションやRepositoryの注入を定義することでテスト容易性を実現します

```config/dependency.py
from typing import Annotated
from fastapi import Depends
from config.jwt import decode_jwt_token
from infrastructure.database import get_db
from fastapi.security import OAuth2PasswordBearer
from repositories.todo_repository import TodoRepository
from repositories.user_repository import UserRepository
from sqlalchemy.orm import Session
from usecases.todo_usecase import TodoUsecase
from usecases.user_usecase import UserUsecase
from schemas.requests.auth_request_schema import CurrentUserRequest


oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")


def get_todo_usecase(db: Session = Depends(get_db)) -> TodoUsecase:
    todo_repository = TodoRepository(db)
    return TodoUsecase(todo_repository)


def get_user_usecase(db: Session = Depends(get_db)) -> UserUsecase:
    user_repository = UserRepository(db)
    return UserUsecase(user_repository)


async def get_current_user(token: str = Depends(oauth2_scheme)) -> CurrentUserRequest:
    try:
        decoded_token = decode_jwt_token(token)
        username: str = decoded_token.get("sub")
        user_id: int = decoded_token.get("iss")
        if not username or not user_id:
            return None
        return CurrentUserRequest(username=username, id=user_id)
    except Exception:
        return None


user_dependency = Annotated[dict, Depends(get_current_user)]

db_dependency = Annotated[Session, Depends(get_db)]
```

実際のDBセッションの定義をしています
```database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### routing
どのusecaseを使用するか、どういったリクエストを受け付け、レスポンスを返すか定義します
人によってはhandler、みたいな命名にします

```routes.py
from typing import List

from config.dependency import get_todo_usecase, user_dependency
from fastapi import APIRouter, Depends, HTTPException, status
from schemas.requests.todo_request_schema import CreateTodoRequest, UpdateTodoRequest
from schemas.responses.todo_response_schema import TodoResponse
from usecases.todo_usecase import TodoUsecase

router = APIRouter(prefix="/api/todos", tags=["todos"])


@router.get("", response_model=List[TodoResponse])
async def read_todos(
    user: user_dependency, todo_usecase: TodoUsecase = Depends(get_todo_usecase)
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    return todo_usecase.get_all_todos(user)


@router.get("/{todo_id}", response_model=TodoResponse)
async def read_todo(
    user: user_dependency,
    todo_id: int,
    todo_usecase: TodoUsecase = Depends(get_todo_usecase),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = todo_usecase.read_todo(user, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@router.post("", response_model=TodoResponse, status_code=status.HTTP_201_CREATED)
async def create_todo(
    user: user_dependency,
    todo_model: CreateTodoRequest,
    todo_usecase: TodoUsecase = Depends(get_todo_usecase),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    return todo_usecase.create_todo(user, todo_model)


@router.put("/{todo_id}", response_model=TodoResponse)
async def update_todo(
    user: user_dependency,
    todo_model: UpdateTodoRequest,
    todo_id: int,
    todo_usecase: TodoUsecase = Depends(get_todo_usecase),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = todo_usecase.read_todo(user, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo_usecase.update_todo(user, todo_model, todo)


@router.delete("/bulk_delete", status_code=status.HTTP_204_NO_CONTENT)
async def bulk_delete_todo(
    user: user_dependency,
    todo_usecase: TodoUsecase = Depends(get_todo_usecase),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo_usecase.bulk_delete_todo(user)


@router.delete("/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(
    user: user_dependency,
    todo_id: int,
    todo_usecase: TodoUsecase = Depends(get_todo_usecase),
):
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authentication Failed"
        )
    todo = todo_usecase.read_todo(user, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    todo_usecase.delete_todo(todo)
```

### usecase
usecaseにビジネスロジックを集約します

```usecases/todo_usecase.py
from models.todo import Todos
from models.user import Users
from repositories.todo_repository import TodoRepository
from schemas.requests.todo_request_schema import CreateTodoRequest, UpdateTodoRequest


class TodoUsecase:
    def __init__(self, todo_repository: TodoRepository):
        self.todo_repository = todo_repository

    def get_all_todos(self, user: Users) -> list[Todos]:
        return self.todo_repository.find_all(user)

    def read_todo(self, user: Users, todo_id: int) -> Todos | None:
        return self.todo_repository.find_one(user, todo_id)

    def create_todo(self, user: Users, todo_request: CreateTodoRequest) -> Todos:
        return self.todo_repository.create(user, todo_request)

    def update_todo(
        self, user: Users, todo_request: UpdateTodoRequest, todo: Todos
    ) -> Todos:
        return self.todo_repository.update(user, todo_request, todo)

    def delete_todo(self, todo_id: Todos):
        return self.todo_repository.delete(todo_id)

    def bulk_delete_todo(self, user: Users):
        return self.todo_repository.bulk_delete(user)
```

### repository
最後に、repository内にDBから必要なデータを取得する方法を記載していきます

```repositories/todo_repository.py
from models.todo import Todos
from models.user import Users
from sqlalchemy import select, update, delete
from sqlalchemy.orm import Session
from schemas.requests.todo_request_schema import (
    CreateTodoRequest,
    UpdateTodoRequest,
)


class TodoRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_all(self, user: Users) -> list[Todos]:
        todos = self.db.scalars(
            select(Todos)
            .filter(Todos.owner_id == user.id, Todos.complete == False)
            .order_by(Todos.id)
        ).all()
        return todos

    def find_one(self, user: Users, todo_id: int) -> Todos | None:
        todo = self.db.scalars(
            select(Todos).filter(
                Todos.id == todo_id, Todos.owner_id == user.id, Todos.complete == False
            )
        ).first()
        return todo

    def create(self, user: Users, todo_request: CreateTodoRequest) -> Todos:
        todo = Todos(**todo_request.model_dump(), owner_id=user.id)
        self.db.add(todo)
        self.db.commit()
        self.db.refresh(todo)
        return todo

    def update(
        self, user: Users, todo_request: UpdateTodoRequest, todo: Todos
    ) -> Todos:
        self.db.execute(
            update(Todos)
            .where(Todos.id == todo_request.id, Todos.owner_id == user.id)
            .values(**todo_request.model_dump())
        )
        self.db.commit()
        return todo

    def delete(self, todo: Todos):
        self.db.delete(todo)
        self.db.commit()

    def bulk_delete(self, user: Users):
        self.db.execute(delete(Todos).where(Todos.owner_id == user.id))
        self.db.commit()

```

## まとめ
Clean Architectureを使って実装してみましたが上記のように必ずしもやる必要がありません
プロジェクトの大きさや依存関係をどこまで切り出すかによって変わってくるのでこういう実装方法もあるんだな、って思っていただけたら幸いです

## 参考
https://zenn.dev/shun1997/articles/understand-clean-architecture

https://zenn.dev/sre_holdings/articles/a57f088e9ca07d
