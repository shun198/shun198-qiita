---
title: FastAPIとSQLAlchemyとPydanticを使ってCRUD用APIを実装しよう！
tags:
  - PostgreSQL
  - sqlalchemy
  - docker-compose
  - FastAPI
  - pydantic
private: false
updated_at: '2025-04-29T01:13:18+09:00'
id: 8c45d60254f4338a8650
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
- FastAPI
- SQLAlchemy
- Pydantic

を使ってCRUD操作のAPIを実装します
今回はタスク管理アプリのCRUD操作を例に説明します

## 前提
- FastAPI、SQLAlchemy、Pydanticともにインストール済み
- 今回はFastAPIとPostgres用のコンテナを使用します
- SQLAlchemyのバージョン2以上を使用
- Pydanticのバージョン2以上を使用
- FastAPIのバージョン0.95.0を使用

## ディレクトリ構成
```
・
├── application
│   ├── __init__.py
│   ├── alembic.ini
│   ├── database.py
│   ├── main.py
│   ├── models.py
│   ├── poetry.lock
│   ├── pyproject.toml
│   ├── schemas.py
├── containers
│   ├── fastapi
│   │   └── Dockerfile
│   └── postgres
│       ├── Dockerfile
│       └── init.sql
└── docker-compose.yml
```

- database.py
- models.py
- schemas.py
- main.py


の順に実装していきます

## 実装
### データベースの設定
FastAPIのアプリケーションとDBを接続する設定をdatabase.pyに記載します

```database.py
import os

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL")

# https://docs.sqlalchemy.org/en/20/core/engines.html#engine-configuration
engine = create_engine(SQLALCHEMY_DATABASE_URL)

# https://docs.sqlalchemy.org/en/20/orm/session_basics.html#session-basics
# DBセッションのオブジェクトを生成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# https://docs.sqlalchemy.org/en/20/orm/mapping_api.html#sqlalchemy.orm.DeclarativeBase
class Base(DeclarativeBase):
    pass
```

順番に解説します
まず、SQLALCHEMY_DATABASE_URLという変数を定義します
変数内にFastAPIとDBが接続できるためのURLを設定し、それを元にDB用エンジンのオブジェクトを生成します

```python
SQLALCHEMY_DATABASE_URL = os.environ.get("SQLALCHEMY_DATABASE_URL")

engine = create_engine(SQLALCHEMY_DATABASE_URL)
```

URLのフォーマットは以下ドキュメントを参考にしてください

https://docs.sqlalchemy.org/en/20/core/engines.html#database-urls

urlは以下のようになります
```
SQLALCHEMY_DATABASE_URL=postgresql://{ユーザ名}:{パスワード}@{ホスト名}:5432/{DB名}
```

その後、DBセッションのオブジェクトを定義します
APIを記載するmain.pyで後ほど使用します
```python
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
```

Baseクラスを元にモデルを定義します
SQLAlchemyのバージョン2以降からdeclarative_baseではなく、DeclarativeBaseクラスを使うことが推奨されています
modelを定義するmodels.pyで使用します

```python
class Base(DeclarativeBase):
    pass
```

### modelの実装
Todosというmodelを実装します
database.pyで定義したBaseクラスを継承することで作成したmodelの定義をDBに反映させることができます
カラムはsqlalchemyのColumnなどを元に定義していきます
カラムの詳細は以下を参考にしてください

https://docs.sqlalchemy.org/en/21/core/metadata.html

```models.py
from database import Base
from sqlalchemy import Boolean, Column, Integer, String


class Todos(Base):
    __tablename__ = "todos"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(String)
    priority = Column(Integer)
    complete = Column(Boolean, default=False)
```

### schemaの実装
schemas.pyバリデーションを定義します
TodoModelはAPIでPostやPutする際のリクエストのバリデーションや型チェックに使用します
TodoResponseはAPIのレスポンスで出力したいフィールドを定義する際に使用します

```schemas.py
from pydantic import BaseModel, Field


class TodoModel(BaseModel):
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool


class TodoResponse(BaseModel):
    id: int = Field()
    title: str = Field(min_length=3)
    description: str = Field(min_length=3, max_length=100)
    priority: int = Field(gt=0, lt=6)
    complete: bool

```

### APIの実装
DBの接続設定、modelの定義、バリデーションの設定が完了したのでAPIの実装に入ります

```main.py
from typing import Annotated, List

from database import SessionLocal, engine
from fastapi import Depends, FastAPI, HTTPException, status
from models import Base, Todos
from schemas import TodoModel, TodoResponse
from sqlalchemy import select, update
from sqlalchemy.orm import Session

app = FastAPI()

# https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData.create_all
# テーブルを作成
Base.metadata.create_all(bind=engine)


# https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/?h=get_db
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-session-dependency
# 依存性注入をすることでget_dbメソッドが自動的に呼ばるので毎回セッションインスタンスの生成やセッションを切る処理を書かずに済む
# Annotatedを使うことでDepends(get_db)がSession型だとわかる
db_dependency = Annotated[Session, Depends(get_db)]

# https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/?h=get_db#sub-dependencies-with-yield
# https://github.com/fastapi/fastapi/pull/9298
# FastAPI0.95.0以降の機能
@app.get("/api/todos", response_model=List[TodoResponse])
def read_todos(db: db_dependency):
    # https://docs.sqlalchemy.org/en/20/orm/quickstart.html#simple-select
    # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.scalars
    # scalarsを使うことでTodosのインスタンスを返す
    todos = db.scalars(select(Todos).order_by(Todos.id)).all()
    return todos


@app.get("/api/todos/{todo_id}", response_model=TodoResponse)
def read_todo(db: db_dependency, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo


@app.post(
    "/api/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED
)
def create_todo(db: db_dependency, todo_model: TodoModel):
    # pydantic2ではdict()ではなく、model_dumpが使用されている
    # https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump
    todo = Todos(**todo_model.model_dump())
    # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.add
    db.add(todo)
    db.commit()
    # # refreshをすることでauto-incrementしたIDやcreated_atが反映されるようになる
    # # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.refresh
    db.refresh(todo)
    return todo


@app.put("/todo/{todo_id}", response_model=TodoResponse)
async def update_todo(db: db_dependency, todo_model: TodoModel, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    # https://docs.sqlalchemy.org/en/20/core/dml.html#sqlalchemy.sql.expression.update
    db.execute(
        update(Todos).where(Todos.id == todo_id).values(**todo_model.model_dump())
    )
    db.commit()
    return todo


@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.delete
    db.delete(todo)
    db.commit()

```

順番に解説します
以下の記述を記載することでdatabase.pyで定義したengineの情報を元にDB内にテーブルを作成します

https://docs.sqlalchemy.org/en/20/core/metadata.html#sqlalchemy.schema.MetaData.create_all

```python
Base.metadata.create_all(bind=engine)
```

get_dbメソッドを使ってDBのセッションを作成し、使用後に接続を閉じるよう定義します
レスポンスを作成する前に実行されるのは以下の箇所です

```python
    db = DBSession()
    try:
        yield db
```

以下の箇所はレスポンスが作成される前とレスポンスを返す前に実行されます

```python
    finally:
        db.close()
```

詳細は以下の通りです

https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/?h=get_db

```python
async def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

下記の記述で依存性を注入しています
依存性注入をするとAPI内でdb_dependencyを定義する際にget_dbメソッドが自動的に呼ばるため、毎回セッションインスタンスの生成(`db = SessionLocal()`)やセッションを切る処理(`db.close()`)を書かずに済みます
また、Annotatedを使うことでDepends(get_db)がSession型だとわかるので便利です

https://fastapi.tiangolo.com/tutorial/sql-databases/#create-a-session-dependency

```
db_dependency = Annotated[Session, Depends(get_db)]
```

まず、一覧表示のAPIを実装します
先ほど定義したdb_dependencyを使って依存性の注入を実現させます
scalarsを使ってTodosのインスタンスをレスポンスとして返します

https://docs.sqlalchemy.org/en/20/orm/quickstart.html#simple-select

https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.scalars
    
```python
@app.get("/api/todos", response_model=List[TodoResponse])
def read_todos(db: db_dependency):
    todos = db.scalars(select(Todos).order_by(Todos.id)).all()
    return todos
```

詳細表示のAPIを実装します
idからTodoを取得し、あればレスポンスとして返し、なければ404を返します

```python
@app.get("/api/todos/{todo_id}", response_model=TodoResponse)
def read_todo(db: db_dependency, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    return todo
```

作成用のAPIを実装します

pydanticのバージョン2以上では`dict()`ではなく、`model_dump()`を使用します
リクエスト内のフィールドを**でdict型に変換してTodosに代入してTodosのインスタンスを生成します
Todoのインスタンスをセッションに`add()`で加えた後に`commit()`でTodoの内容をDBにinsertします

```python
    db.add(todo)
    db.commit()
```

https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.add

refreshをすることでauto-incrementしたIDやcreated_atが反映されるようになります

https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.refresh

https://docs.pydantic.dev/latest/concepts/serialization/#modelmodel_dump

```python
@app.post(
    "/api/todos", response_model=TodoResponse, status_code=status.HTTP_201_CREATED
)
def create_todo(db: db_dependency, todo_model: TodoModel):
    todo = Todos(**todo_model.model_dump())
    db.add(todo)
    db.commit()

    db.refresh(todo)
    return todo
```

更新用のAPIを作成します
該当するidのTodoがなければ404を返します
存在する場合は`model_dump()`で全てのfieldに更新をかけてtodoのインスタンスを返します

```python
@app.put("/todo/{todo_id}", response_model=TodoResponse)
async def update_todo(db: db_dependency, todo_model: TodoModel, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    # https://docs.sqlalchemy.org/en/20/core/dml.html#sqlalchemy.sql.expression.update
    db.execute(
        update(Todos).where(Todos.id == todo_id).values(**todo_model.model_dump())
    )
    db.commit()
    return todo
```

削除用APIを作成します
該当するidのTodoがなければ404を返します
存在する場合はセッション内から削除し、`commit()`でTodoの内容をDBからdeleteしまs

```python
@app.delete("/todo/{todo_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_todo(db: db_dependency, todo_id: int):
    todo = db.get(Todos, todo_id)
    if not todo:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Todo not found"
        )
    # https://docs.sqlalchemy.org/en/20/orm/session_api.html#sqlalchemy.orm.Session.delete
    db.delete(todo)
    db.commit()
```

## 実際に実行してみよう！
`127.0.0.1:8000/docs`へアクセスし、下記のようにAPIの一覧が作成されたら成功です

![スクリーンショット 2025-02-11 8.45.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b0858bb5-41a0-8059-f912-5be6e41b8bf9.png)

Todoを作成してみます
以下のように/api/todosへPOSTし、Todoが作成されたら成功です
![スクリーンショット 2025-02-11 8.46.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/05f2a5d0-c29a-6550-f986-c5b2a53dffe2.png)

![スクリーンショット 2025-02-11 8.46.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ba26a71d-b970-3b1a-56f4-c85d4ede0780.png)

続いてTodoの一覧と詳細を取得します
以下のように一覧と詳細を取得できれば成功です
![スクリーンショット 2025-02-11 8.47.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/db7398af-5c9b-7fe7-959e-3f3cb5b8eb3f.png)

![スクリーンショット 2025-02-11 8.48.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/661ed16f-7a1d-1d0c-8f40-6e78389a910f.png)

Todoを更新します
/api/todosへPUTし、Todoが更新されたら成功です
![スクリーンショット 2025-02-11 8.50.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc409308-a150-e224-45ed-c6313c046c09.png)

![スクリーンショット 2025-02-11 8.51.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9ddcdd5e-025e-2b1f-5cda-d2c5bd5484fb.png)

![スクリーンショット 2025-02-11 8.51.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/242db071-abf7-768f-7bae-7b846fd0e942.png)

最後にTodoを削除します
以下のようにTodoが削除されたら成功です
![スクリーンショット 2025-02-11 8.52.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ac80a152-8f0b-3b81-f33a-f5dcbc22532d.png)

![スクリーンショット 2025-02-11 8.52.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a82aa2b3-e878-c458-b99b-bf756efa5fee.png)

## 参考
https://docs.sqlalchemy.org/en/20/orm/quickstart.html

https://fastapi.tiangolo.com/ja/tutorial/body-nested-models/

https://fastapi.tiangolo.com/tutorial/dependencies/dependencies-with-yield/?h=get_db#sub-dependencies-with-yield

https://github.com/fastapi/fastapi/pull/9298
