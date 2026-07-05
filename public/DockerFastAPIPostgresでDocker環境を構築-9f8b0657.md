---
title: Docker+FastAPI+PostgresでDocker環境を構築
tags:
  - PostgreSQL
  - Docker
  - docker-compose
  - FastAPI
  - uvicorn
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 9f8b0657cf5eed1af4f3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
- Docker
- FastAPI
- Postgres

を使ってコンテナ環境を構築する方法について解説します
また、コンテナを起動させる際にヘルスチェックを行います

## 前提
- Docker、FastAPI、Postgres、Poetryに関する基礎知識を有している
- FastAPIのプロジェクトを作成済み
- コンテナ環境を構築する方法について説明するのでDBとの接続方法については本記事では解説しません

## ディレクトリ構成
```
tree
.
├── application
│   ├── main.py
│   ├── poetry.lock
│   ├── pyproject.toml
│   └── routers
│       ├── __init__.py
│       └── common.py
├── containers
│   ├── fastapi
│   │   └── Dockerfile
│   └── postgres
│       └── Dockerfile
├── .gitignore
├── .env
└── docker-compose.yml

```

## 実装
- pyproject.toml
- FastAPIのDockerfile
- PostgresのDockerfile
- .env
- docker-compose.yml

の順に作成していきます

### pyproject.toml
Poetryを使ったPythonのパッケージの管理をする際にpyproject.tomlファイルが必要になります
今回は
- python
- fastapi
- psycopg2
- uvicorn

が必要なので以下のように記載します

```application/pyproject.toml
[tool.poetry]
name = "fastapi-playground"
version = "0.1.0"
description = ""
authors = ["shun198"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11.8"
fastapi = "^0.78.0"
psycopg2 = "^2.9.9"
uvicorn= "^0.17.6"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

```

### FastAPIのDockerfile

```Dockerfile:containers/fastapi/Dockerfile
# FastAPIで使用するPythonのイメージを指定
FROM tiangolo/uvicorn-gunicorn:python3.11
# PYTHONDONTWRITEBYTECODEとPYTHONUNBUFFEREDはオプション
# pycファイル(および__pycache__)の生成を行わないようにする
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
# コンテナのワークディレクトリを/codeに指定
WORKDIR /code
# ローカルのapplication/pyproject.tomlをコンテナの/codeフォルダ直下に置く
COPY application/pyproject.toml /code/
# コンテナ内でpipのアップグレードとPoetryのインストールを行う
RUN pip install --upgrade pip && pip install poetry
# コンテナ内でPoetry内のパッケージをインストール
RUN poetry install
# ソースコードをマウント先にコピー
COPY application/ /code/
```

### PostgresのDockerfile

```Dockerfile:containers/postgres/Dockerfile
FROM postgres:16.2
```

### .env
```.env
POSTGRES_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_HOST=db
POSTGRES_PORT=5432
```

### docker-compose.yml

```docker-compose.yml
services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    # ヘルスチェックを使ってPostgresのコンテナより先にFastAPIが起動しないようにする
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
      - "8000:8000"
    command: poetry run uvicorn main:app --reload --host 0.0.0.0 --port 8000
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
volumes:
  db_data:
```

### main.py
main.pyを使ってFastAPIのアプリケーションを起動します
今回は後述するヘルスチェック用のルーティングを作成します

```main.py
from fastapi import FastAPI

from routers import common

app = FastAPI(
    title="FastAPI Playground",
    version="0.0.1",
)
app.include_router(common.router, prefix="/api", tags=["common"])
```

### ヘルスチェックAPIの作成
今回はAPIが正常に実行できることを確認するためにヘルスチェック用のAPIを作成します

```routers/common.py
from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check():
    """ヘルスチェック用のAPI"""
    return {"status": "pass"}

```

以下のようにSwaggerが表示され、ヘルスチェックが正常に実行できたら成功です

![スクリーンショット 2024-03-29 15.12.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/73b6f2c3-f556-a9ed-2746-c8f01292660a.png)

![スクリーンショット 2024-03-29 15.24.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0862d163-27f2-e4b2-2f4b-cd2687c2209f.png)

## 参考
https://qiita.com/kurodenwa/items/653c7b74f2f8ba5b7c0d

https://sqripts.com/2022/06/16/20408/
