---
title: Docker+Flask+PostgresでDocker環境を構築
tags:
  - Flask
  - PostgreSQL
  - Docker
  - docker-compose
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 8c76a92a75c2adc16ca5
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
- Docker
- Flask
- Postgres

を使ってコンテナ環境を構築する方法について解説します
また、コンテナを起動させる際にヘルスチェックを行います

## 前提
- Docker、Flask、Postgres、Poetryに関する基礎知識を有している
- Flaskのプロジェクトを作成済み
- コンテナ環境を構築する方法について説明するのでDBとの接続方法については本記事では解説しません

## ディレクトリ構成
```
tree
.
├── application
│   ├── main.py
│   ├── poetry.lock
│   └── pyproject.toml
├── containers
│   ├── flask
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── postgres
│       └── Dockerfile
├── .gitignore
├── .env
└── compose.yaml

```

## 実装
- pyproject.toml
- FlaskのDockerfile
- PostgresのDockerfile
- .env
- compose.yaml
- entrypoint.sh

の順に作成していきます

### pyproject.toml
Poetryを使ったPythonのパッケージの管理をする際にpyproject.tomlファイルが必要になります
今回は
- python
- flask
- psycopg2

が必要なので以下のように記載します

```application/pyproject.toml
[tool.poetry]
name = "flask-practice"
version = "0.1.0"
description = ""
authors = ["shun198 <shunhiroseluvmri@gmail.com>"]
readme = "README.md"
packages = [{include = "flask_practice"}]

[tool.poetry.dependencies]
python = "3.12.8"
flask = "^3.1.0"
psycopg2 = "^2.9.10"


[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

### FlaskのDockerfile

```Dockerfile:containers/flask/Dockerfile
FROM python:3.12.8
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
WORKDIR /code
COPY application/pyproject.toml /code/
RUN pip install --upgrade pip && \
    pip install poetry
RUN poetry install
COPY ./containers/flask/entrypoint.sh /usr/local/bin/entrypoint.sh
RUN chmod +x /usr/local/bin/entrypoint.sh
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
```

### compose.yaml

```compose.yaml
services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    # ヘルスチェックを使ってPostgresのコンテナより先にFlaskが起動しないようにする
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
      dockerfile: containers/flask/Dockerfile
    volumes:
      - ./application:/code
    ports:
      - "8000:8000"
    command: sh -c "/usr/local/bin/entrypoint.sh"
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
volumes:
  db_data:
```

entrypoint.shを使ってFlaskのアプリケーションを起動させます
コンテナ内のFlaskを起動させるため、`-h 0.0.0.0`、今回は8000番ポートで起動させたいので`-p 8000`を指定します

```entrypoint.sh
#!/bin/sh
set -eu

poetry run flask --app main run --debug -h 0.0.0.0 -p 8000
```

### main.py
main.pyを使ってFlaskのアプリケーションを起動します
今回はヘルスチェック用のAPIを作成します

```main.py
from flask import Flask

app = Flask(__name__)

@app.route("/api/health")
def health():
    return {"msg": "pass"}
```

コンテナの設定およびAPIの作成が完了したら以下のコマンドでDockerfileのbuildとコンテナの起動を実現します

```
docker compose up -d --build
```

`127.0.0.1:8000/api/health`へアクセスし、以下のようにヘルスチェックが正常に実行できたら成功です

![スクリーンショット 2024-12-13 18.55.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/59428e5a-1ea3-0acb-f892-6a3572492e96.png)

## 参考
https://flask.palletsprojects.com/en/stable/quickstart/
