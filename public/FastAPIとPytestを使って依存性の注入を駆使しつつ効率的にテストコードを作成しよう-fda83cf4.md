---
title: FastAPIとPytestを使って依存性の注入を駆使しつつ効率的にテストコードを作成しよう！
tags:
  - DependencyInjection
  - pytest
  - FastAPI
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: fda83cf4e7d3eefe467f
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
FastAPIとPytestを使ってテストする際は依存性の注入(Dependency Injection)を使用するのが一般的です
今回はテストDBを作成しつつ、FastAPIとPytestを依存性の注入を取り入れた状態で作成します

## 前提
- 今回はCRUDのAPIのテストを行います。また、認証はJWTとOAuthを使ってますが本記事では説明しません。詳細についてもっと知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/8c45d60254f4338a8650

https://qiita.com/shun198/items/92c4c8eda8a66e78b400

## テスト用DBの作成
DB用のコンテナを作成し、初回起動時にinit.sqlを実行してテスト用DBとユーザを作成するように設定します

```compose.yaml
services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
      - ./containers/postgres/init.sql:/docker-entrypoint-initdb.d/init.sql
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_NAME
      - POSTGRES_USER
      - POSTGRES_PASSWORD
    ports:
      - "5432:5432" # デバッグ用
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/fastapi/Dockerfile
    volumes:
      - ./application:/code
    ports:
      - 8000:8000
      # デバッグ用ポート
      - 8080:8080
    command: poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
volumes:
  db_data:

```

```init.sql
-- 開発用ユーザとデータベース
CREATE DATABASE dev_db;
GRANT ALL PRIVILEGES ON DATABASE dev_db TO dev_user;

-- テスト用ユーザとデータベース
CREATE DATABASE test_db;
CREATE USER test_user WITH PASSWORD 'password';
GRANT ALL PRIVILEGES ON DATABASE test_db TO test_user;

-- dev_user にスキーマ変更権限を付与
ALTER DATABASE dev_db OWNER TO dev_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO dev_user;

-- test_user にスキーマ変更権限を付与
ALTER DATABASE test_db OWNER TO test_user;
GRANT ALL PRIVILEGES ON SCHEMA public TO test_user;

```

## テストコードの実装
### テスト用Dependencyの設定
テスト用DBセッションとテスト用ログインユーザの設定を行います
テスト用DBのsqlalchemyの設定は間違えないようにしましょう

```tests/utils.py
from database import Base
from models import Users
from pwdlib import PasswordHash
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

TEST_SQLALCHEMY_DATABASE_URL = "postgresql://test_user:password@db:5432/test_db"
password_hash = PasswordHash.recommended()

test_engine = create_engine(TEST_SQLALCHEMY_DATABASE_URL, poolclass=StaticPool)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(bind=test_engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def override_get_current_user():
    user = Users(
        id=123,
        email="test_user_admin_01@example.com",
        username="test_user_admin_01",
        first_name="user_admin_01",
        last_name="test",
        password=password_hash.hash("test"),
        is_active=True,
        is_admin=True,
        phone_number="08011112222",
    )
    return user

```

### conftest.pyの作成
テスト用のClientなど他のテストで使用するfixtureを作成します
FastAPIではdependency_overridesメソッドを使うことで依存性(dependency)を上書きすることができます

> For these cases, your FastAPI application has an attribute app.dependency_overrides, it is a simple dict.
To override a dependency for testing, you put as a key the original dependency (a function), and as the value, your dependency override (another function).
And then FastAPI will call that override instead of the original dependency.

以下のようにテスト用Clientのfixture内に元々のdependencyをkeyにutils.pyで作成したいテスト用の設定に上書きする形で記載します

```conftest.py
import pytest

from datetime import timedelta

from routers.auth import get_current_user, create_jwt_token
from database import get_db
from fastapi.testclient import TestClient
from sqlalchemy import text
from tests.utils import (
    override_get_current_user,
    override_get_db,
    TestingSessionLocal,
    test_engine,
)
from models import Todos, Users
from main import app


@pytest.fixture
def client():
    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_current_user] = override_get_current_user
    client = TestClient(app)
    yield client


@pytest.fixture
def non_existing_user():
    return "99999"


@pytest.fixture
def test_todo_one():
    user = override_get_current_user()
    db = TestingSessionLocal()
    db.add(user)
    db.commit()
    todo = Todos(
        id=1,
        title="test task 01",
        description="description of test task 01",
        priority=1,
        complete=False,
        owner_id=user.id,
    )
    db.add(todo)
    db.commit()
    yield todo
    with test_engine.connect() as connection:
        connection.execute(text("DELETE FROM todos;"))
        connection.commit()
        connection.execute(text("DELETE FROM users;"))
        connection.commit()


@pytest.fixture
def headers():
    user = override_get_current_user()
    jwt_token = create_jwt_token(user.username, user.id, timedelta(minutes=30))
    headers = {"Authorization": f"Bearer {jwt_token}"}
    return headers

```

### APIのテスト
作成したテスト用Clientや認証用ヘッダのfixtureを駆使しながらテストを作成します
例えばログインしてない状態でAPIを実行するテストを書きたいなど、特定の依存性(ログインユーザ)を削除したいケースがあるかと思います
その際は以下のようにdependency_overridesのlistから削除したい依存性をpopすることで再現できます

```python
app.dependency_overrides.pop(get_current_user, None)
```

全ての依存性を削除したい場合はclearメソッドも用意されています

```python
app.dependency_overrides.clear()
```

```tests/test_todo.py
import pytest

from fastapi import status
from routers.auth import get_current_user
from main import app


@pytest.fixture
def create_data():
    return {
        "title": "Created Todo",
        "description": "Created test",
        "priority": 2,
    }


@pytest.fixture
def update_data():
    return {
        "title": "Updated Todo",
        "description": "Updated test",
        "priority": 2,
    }


def test_list_todos(client, headers, test_todo_one):
    response = client.get("/api/todos", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)
    assert response.json() == [
        {
            "id": test_todo_one.id,
            "title": test_todo_one.title,
            "description": test_todo_one.description,
            "priority": test_todo_one.priority,
            "complete": test_todo_one.complete,
            "owner_id": test_todo_one.owner_id,
        }
    ]


def test_list_todos_unauthorized(client):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get("/api/todos")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_read_todo(client, headers, test_todo_one):
    response = client.get(f"/api/todos/{test_todo_one.id}", headers=headers)
    assert response.status_code == status.HTTP_200_OK
    assert response.json() == {
        "id": test_todo_one.id,
        "title": test_todo_one.title,
        "description": test_todo_one.description,
        "priority": test_todo_one.priority,
        "complete": test_todo_one.complete,
        "owner_id": test_todo_one.owner_id,
    }


def test_read_todo_not_found(client, headers, non_existing_user):
    response = client.get(f"/api/todos/{non_existing_user}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


def test_read_todos_unauthorized(client, test_todo_one):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.get(f"/api/todos/{test_todo_one.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_create_todo(client, headers, create_data, test_todo_one):
    response = client.post("/api/todos", json=create_data, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["title"] == create_data["title"]
    assert response.json()["description"] == create_data["description"]
    assert response.json()["priority"] == create_data["priority"]


def test_create_todos_unauthorized(client, create_data):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.post(f"/api/todos/", json=create_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_update_todo(client, headers, update_data, test_todo_one):
    response = client.put(
        f"/api/todos/{test_todo_one.id}", json=update_data, headers=headers
    )
    assert response.status_code == status.HTTP_200_OK
    assert response.json()["title"] == update_data["title"]
    assert response.json()["description"] == update_data["description"]
    assert response.json()["priority"] == update_data["priority"]


def test_update_todo_not_found(client, headers, update_data, non_existing_user):
    response = client.put(
        f"/api/todos/{non_existing_user}", json=update_data, headers=headers
    )
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


def test_update_todos_unauthorized(client, update_data, test_todo_one):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.put(f"/api/todos/{test_todo_one.id}", json=update_data)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_delete_todo(client, headers, test_todo_one):
    response = client.delete(f"/api/todos/{test_todo_one.id}", headers=headers)
    assert response.status_code == status.HTTP_204_NO_CONTENT


def test_delete_todo_not_found(client, headers, non_existing_user):
    response = client.delete(f"/api/todos/{non_existing_user}", headers=headers)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    assert response.json() == {"detail": "Todo not found"}


def test_delete_todo_unauthorized(client, test_todo_one):
    app.dependency_overrides.pop(get_current_user, None)
    response = client.delete(f"/api/todos/{test_todo_one.id}")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED

```


## まとめ
FastAPIでテストする際は依存性の注入を比較的少ない記述量でできるのでテストを直感的に書けるのはいいですね

## 参考
https://fastapi.tiangolo.com/advanced/testing-dependencies/

https://fastapi.tiangolo.com/ja/tutorial/testing/
