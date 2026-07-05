---
title: Docker+Django+Nginx+MySQL+Gunicornで環境構築~M1Mac対応
tags:
  - Django
  - nginx
  - Docker
  - gunicorn
  - MySQL8.0
private: false
updated_at: '2024-03-23T14:17:24+09:00'
id: f6864ef381ed658b5aba
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- フレームワークはDjango
- DBはMySQL
- アプリケーションサーバはGunicorn
- WebサーバはNginx
- DB側のコンテナ名はmysql、django側のコンテナ名はapp、nginx側はwebにします
- 開発用はdocker-compose.yml(Django+MySQL)として作成します
- 本番用はdocker-compose.prod.yml(Django+MySQL+Nginx)として作成します
- 作成するプロジェクト名はdjangopjにしていますが別のプロジェクト名で作成する際はdjangopjと置き換えて作成してください

## 概要
タイトルに記載の通り、
- Django
- MySQL
- Nginx
    - Gunicorn

を使ったコンテナ開発環境の作成方法について解説していきます
その際にパッケージ管理にrequirements.txtを使用します

また、記事の後半に応用編として
- Poetryを使った開発環境の構築方法
- Pydanticを使った環境変数の管理方法

について解説していきます
はじめてDockerを使う方はまずはrequirements.txtを使った基本的な構築方法を理解してから挑戦していただければと思います

## ディレクトリ構成
初回作成時のディレクトリ構成は以下の通りです
containersフォルダを作成し、その中にDjango、MySQL、Nginxのフォルダを作成してください
また、Nginxのフォルダの中にconf.dフォルダも作成します

```terminal
tree
.
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   └── nginx
│       ├── Dockerfile
│       └── conf.d
│           └── default.conf
├── .gitignore
├── .env
├── .env.prod
├── entrypoint.sh
├── docker-compose.prod.yml
├── docker-compose.yml
└── requirements.txt
```

## 作成するファイル
- DjangoのDockerfile
- MySQLのDockerfile
- NginxのDockerfile
- my.cnf(MySQL用の設定ファイル)
- init.sql(MySQLのユーザに権限を付与)
- default.conf(Nginx用の設定ファイル)
- docker-compose.yml(開発用)
- docker-compose.prod.yml(本番用)
- requirements.txt(ざっくり言うとRailsでいうGemfileにあたる)
- .env(開発用の環境変数の設定ファイル)
- .env.prod(本番用の環境変数の設定ファイル)
- entrypoint.sh(Djangoのコマンドを実行する用のシェルスクリプト)
- .gitignore

の作成方法について順に説明します

## そもそもなんで開発用と本番用に分けるの？
Django+MySQL+Nignxの構成で開発する場合、Nginxは静的ファイルを表示させる機能しかないため、ViewやModelの変更を反映させるには都度コンテナを再起動させる必要があります(要するにホットリロードができないため、開発効率が悪い)
そのため、開発はDjango+MySQLのコンテナで行い、本番環境ではNginxのポートから画面を確認する運用になるかと思います
実際は本番環境ではAWSのECSやFargateなどを使用しますが本記事ではローカル上で使用する開発用、本番用のDockerfileとdocker-compose.ymlの書き方もあわせて解説します

## 各ファイルに必要なコードを記入しよう
### Dockerfile(Django)

```Dockerfile:containers/django/Dockerfile
# Pythonのイメージを指定
FROM python:3
# PYTHONDONTWRITEBYTECODEとPYTHONUNBUFFEREDはオプション
# pycファイル(および__pycache__)の生成を行わないようにする
ENV PYTHONDONTWRITEBYTECODE=1
# 標準出力・標準エラーのストリームのバッファリングを行わない
ENV PYTHONUNBUFFERED=1
# コンテナのワークディレクトリを/codeに指定
WORKDIR /code
# ローカルのrequirements.txtをコンテナの/codeフォルダ直下に置く
COPY requirements.txt /code/
# コンテナ内でpipをアップグレード
RUN pip install --upgrade pip
# pip install -r requirements.txtを実行
RUN pip install -r requirements.txt
# ソースコードをコンテナにコピー
COPY . /code/
# entrypoint.shに実行権限を付与
RUN chmod 755 entrypoint.sh
```

### MySQL
```Dockerfile:containers/MySQL/Dockerfile
# MySQL8系のイメージを指定
FROM mysql:8.0

# MySQLのローカルの設定ファイルをコンテナにコピー
COPY containers/mysql/my.cnf /etc/mysql/conf.d/my.cnf
# init.sqlをコンテナの/docker-entrypoint-init.db.dと共有
COPY containers/mysql/init.sql /docker-entrypoint-initdb.d
```

### Nginx
```Dockerfile:Dockerfile
FROM nginx:1.21-alpine

# ローカルのdefault.confをコンテナにコピー
COPY containers/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
```

### my.cnf(MySQL用の設定ファイル)
```containers/MySQL/my.cnf
# MySQLサーバーへの設定
[mysqld]
# 文字コード/照合順序の設定
character_set_server=utf8mb4
collation_server=utf8mb4_bin
# タイムゾーンの設定
default_time_zone=SYSTEM
log_timestamps=SYSTEM
# MySQL8.0以上用のデフォルト認証プラグインの設定
default_authentication_plugin=caching_sha2_password
# mysqlオプションの設定
[mysql]
# 文字コードの設定
default_character_set=utf8mb4
# mysqlクライアントツールの設定
[client]
# 文字コードの設定
default_character_set=utf8mb4
```

### init.sql
```sql
-- MYSQL_USERに権限を付与
-- 今回はdjangoというユーザを指定
GRANT ALL PRIVILEGES ON *.* TO 'django'@'%';
FLUSH PRIVILEGES;
```

### default.conf(Nginx用の設定ファイル)
```nginx:default.conf
# Django(Gunicorn)の8000番ポートとつなぐ
upstream django {
    # サーバにDjangoのコンテナ名を指定。今回はapp
    # ポートはDjangoのコンテナの8000番ポート
    server app:8000;
}

server {
    # HTTPの80番ポートを指定
    listen 80;
    server_name 0.0.0.0;

    # プロキシ設定
    # 実際はNginxのコンテナにアクセスしてるのをDjangoにアクセスしてるかのようにみせる
    location / {
        proxy_pass http://django;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }
    
    # djangoの静的ファイル(HTML、CSS、Javascriptなど)を管理
    location /static/ {
		alias /static/;
	}
}
```

### docker-compose.yml(開発用)
```docker-compose.yml
# db(MySQL),app(Django)のコンテナを作成
services:
  db:
    # コンテナ名をmysqlに設定
    container_name: mysql
    # MySQLのDockerfileをビルドする
    build:
      # ビルドコンテキストはカレントディレクトリ
      context: .
      dockerfile: containers/mysql/Dockerfile
    # M1チップでも動くように
    # Intel Macの場合あってもなくても動く
    platform: linux/x86_64
    # DBのボリュームを指定
    # ローカルの/data/dbをコンテナの/var/lib/mysqlにマウントする
    volumes:
      - db_data:/var/lib/mysql
    # 環境変数を.envを使って設定
    env_file:
      - .env
    # DBのコンテナのヘルスチェックを行う
    # mysqladmin(MySQLサーバーの管理を行うクライアントを使ってDBコンテナ自身(127.0.0.1)にpingを送ってヘルスチェックを行う
    healthcheck:
      test: mysqladmin ping -h 127.0.0.1 -u$$MYSQL_USER -p$$MYSQL_PASSWORD
      # ヘルスチェックのインターバルは10秒
      interval: 10s
      # タイムアウト時間は10秒
      timeout: 10s
      # リトライ回数は3回
      retries: 3
      # ヘルスチェックが失敗しても無視する時間は30秒
      start_period: 30s
  app:
    # コンテナ名をappに設定
    container_name: app
    # DjangoのDockerfileをビルドする
    build:
      # ビルドコンテキストはカレントディレクトリ
      context: .
      dockerfile: containers/django/Dockerfile
    # ボリュームを指定
    # ローカルのカレントディレクトリをコンテナの/codeにマウントする
    # ローカルの/staticをコンテナの/staticにマウントする
    volumes:
      - .:/code
      - ./static:/static
    # ローカルの8000番ポートとコンテナの8000番ポートをつなぐ
    ports:
      - "8000:8000"
    # シェルスクリプトを実行
    command: sh -c "/code/entrypoint.sh"
    # 環境変数を.envを使って設定
    env_file:
      - .env
    # 先にdbを起動してからappを起動する
    depends_on:
      db:
        # dbのヘルスチェックが終わってからappを起動させる
        condition: service_healthy
volumes:
  db_data:
  static:
```

### docker-compose.prod.yml(本番用)
```docker-compose.prod.yml
# db(MySQL),app(Django),web(Nginx)のコンテナを作成
services:
  db:
    container_name: mysql
    build:
      context: .
      dockerfile: containers/mysql/Dockerfile
    platform: linux/x86_64
    volumes:
      - db_data:/var/lib/mysql
    # コンテナ内の環境変数を.env.prodを使って設定
    env_file:
      - .env.prod
    healthcheck:
      test: mysqladmin ping -h 127.0.0.1 -u$$MYSQL_USER -p$$MYSQL_PASSWORD
      interval: 10s
      timeout: 10s
      retries: 3
      start_period: 30s
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - .:/code
      - ./static:/static
    # 8000番ポートをNginx側が接続できるよう開く
    expose:
      - "8000"
    command: sh -c "/code/entrypoint.sh"
    # コンテナ内の環境変数を.env.prodを使って設定
    env_file:
      - .env.prod
    depends_on:
      db:
        # dbのヘルスチェックが終わってからappを起動させる
        condition: service_healthy
  web:
    # コンテナ名をwebに指定
    container_name: web
    # NginxのDockerfileをビルドする
    build:
      # ビルドコンテキストはカレントディレクトリ
      context: .
      dockerfile: containers/nginx/Dockerfile
    # ボリュームを指定
    # ローカルの/staticをコンテナの/staticにマウントする
    volumes:
      - ./static:/static
    # ローカルの80番ボートをコンテナの80番ポートとつなぐ
    ports:
      - "80:80"
    # 先にappを起動してからwebを起動する
    depends_on:
      - app
volumes:
  db_data:
  static:
```

### requirements.txt
- Django
- mysqlclient
- Gunicorn

をDjangoのコンテナにインストールするので記載します
```requirements.txt
Django>=3.0,<4.0
mysqlclient>=1.3.6,<2.0
gunicorn>=19.9.0,<20.0
```

### .env(開発用)
MySQLのrootユーザのパスワードなどをdocker-compose.ymlやDjangoのsettings.pyに書くのは危険なので.envファイルを使います
今回は開発用のためDEBUG=Trueにする必要があります
.gitignore(後述)があることで.envファイルはGitHubに上がることはありません
今回は以下のような内容にします
```.env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=django-db
MYSQL_USER=django
MYSQL_PASSWORD=django
# SECRET_KEYに任意の値を入力
SECRET_KEY=django
ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
# 開発環境のためTrue
DEBUG=True
```

### .env.prod(本番用)
続いて本番環境用の環境変数を設定します
実際に本番環境の環境変数はAWSのパラメータストアなどに保存しますが今回は.env.prodを使います
本番用のためDEBUG=Falseにする必要があります

```.env.prod
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=django-db
MYSQL_USER=django
MYSQL_PASSWORD=django-prod
# SECRET_KEYについては本番環境では推測されない値に変更しておきましょう
SECRET_KEY=xdmjx=9l@x)-jitznpb^%yjn6h=7g)$%e8_+1s)o+8o79csa4d
ALLOWED_HOSTS=localhost 127.0.0.1 [::1]
# 本番環境のためFalse
DEBUG=False
```

### entrypoint.sh
Djangoのマイグレーションや管理者画面、Django Rest Frameworkの静的ファイルを集めるコマンドを定義します
また、開発環境、本番環境では使うコマンドが違うので1つのシェルスクリプトに記載すると同じような記述をdocker-compose.ymlに書かなくてもいい上に可読性が上がります
```
#!/bin/sh
```
はshebangと言ってシェルスクリプトを実行するためのおまじないみたいなものなので忘れずに記載しましょう
```entrypoint.sh
#!/bin/sh
python manage.py makemigrations --noinput
python manage.py migrate --noinput
python manage.py collectstatic --noinput
# 環境変数のDEBUGの値がTrueの時はrunserverを、Falseの時はgunicornを実行します
if [ $DEBUG = "True" ]
then
    python manage.py runserver 0.0.0.0:8000
else
    # gunicornを起動させる時はプロジェクト名を指定します
    # 今回はdjangopjにします
    gunicorn djangopj.wsgi:application --bind 0.0.0.0:8000
fi
```

### .gitignore
GitHubの公式サイトからPythonの.gitignoreを作成します
.env.prodは.gitignoreにないため追記します
また、migrationとstaticは実際の開発ではGitの管理下に置く必要がないため、こちらも.gitignoreに追記します
```
# Environments
.env
# .env.prodを.gitignoreする
.env.prod
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

・・・

# ignore static files
static/
# ignore migration files
migrations/
```

https://github.com/github/gitignore

## imageのビルド、Djangoの画面表示まで行おう
今回はNginxのポートにアクセスしてDjangoの画面を表示させたいのでdocker-compose.prod.yml(本番用)を使います
開発する場合はコマンドで指定しているファイルをdocker-compose.ymlに置き換えて、8000番ポートにアクセスしてください

### docker-composeでDocker imageを作成しよう(初回)
プロジェクトを新規作成する際はプロジェクト名と作成するディレクトリを指定して以下のコマンドを実行します
今回はdjangopjのプロジェクトをカレントディレクトリに作成します
```terminal:terminal
docker compose -f docker-compose.prod.yml run app django-admin startproject djangopj .
```

実行するとローカルのディレクトリ構成は以下のようになります
data/db内はファイルが非常に多いので省略します
```terminal
tree
.
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   └── nginx
│       ├── Dockerfile
│       └── conf.d
│           └── default.conf
├── djangopj
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .env.prod
├── .gitignore
├── docker-compose.prod.yml
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
├── requirements.txt
└── static
```

### すでにプロジェクトがある場合
GitHubにあるソースコードをcloneする場合など、プロジェクトが作成済みの時は以下のコマンドを実行します
```
docker compose -f docker-compose.prod.yml build
```

### settings.pyのDATABASESを変更
DjangoのデフォルトのDBはSQliteのため、MySQLに変更する必要がある
```settings.py
from pathlib import Path
# osのモジュールをインポート
import os

# [・・・]

# SECRET_KEYを.envから取得
SECRET_KEY = os.environ.get("SECRET_KEY")

# DEBUGを.envから取得
# envファイルにTrue、Falseと書くとDjangoがString型と認識してしまいます
# os.environ.get("DEBUG") == "True"を満たすとboolean型のTrueになり、
# env内のDEBUGがTrue以外ならFalseになります
DEBUG = os.environ.get("DEBUG") == "True"

# ALLOWED_HOSTSを.envから取得
ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(" ")

# [・・・]

# MySQLのパラメータを.envから取得
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        # コンテナ内の環境変数をDATABASESのパラメータに反映
        "NAME": os.environ.get("MYSQL_DATABASE"),
        "USER": os.environ.get("MYSQL_USER"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": "db",
        "PORT": 3306,
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}


# [・・・]

# 言語を日本語に設定
LANGUAGE_CODE = "ja"
# タイムゾーンをAsia/Tokyoに設定
TIME_ZONE = "Asia/Tokyo"

# [・・・]

# STATIC_ROOTを設定
# Djangoの管理者画面にHTML、CSS、Javascriptが適用されます
STATIC_ROOT = "/static/"
STATIC_URL = "/static/"
```

### コンテナを起動
コンテナをデタッチモードで起動する
デタッチモード起動することでコンテナの中に入らずにバックグラウンドで起動させることができます
```terminal:terminal
docker compose -f docker-compose.prod.yml up -d
```

### 127.0.0.1:80にアクセスしてみよう
ホストからNginxのポートに接続します
ブラウザにアクセスし、NginxのポートからDjangoのポートへアクセスできます
以下のページが表示されます

このようにNot Foundと表示される場合はルーティングの設定をしてないからでコンテナ自体はうまく起動しています
![スクリーンショット 2022-10-16 21.03.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9c45c85e-c291-7157-d7d4-1c5e8c1a8655.png)

127.0.0.1:80/adminにアクセスし、以下の画面が出たら成功です

:::note
![スクリーンショット 2022-10-16 21.06.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0befd4ff-54f8-27ed-8c05-233f132cae34.png)
:::

DEBUG=Trueに設定した場合は下記の画像が表示されます

:::note
![スクリーンショット 2022-08-17 21.10.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ba5f46c3-2f7d-5fd9-3a21-9294b85be146.png)
:::

:::note alert
画面が表示されない時は？
:::

上記のような画面が表示されない場合は初回起動時にMySQL側のコンテナがうまく立ち上がってない可能性があるので
```terminal
docker compose -f docker-compose.prod.yml down
```
でコンテナを停止させた後に
```terminal
docker compose -f docker-compose.prod.yml up -d
```
でコンテナをもう一度立ち上げてみてください

### もう一度`docker compose -f docker-compose.prod.yml up -d`しても接続できない時
#### failed (111: Connection refused) while connecting to upstream
Nginxのdefault.confを見直す必要があります
```containers/nginx/conf.d/default.conf
upstream django {
    server app:8000;
}
```
serverの後はDjangoではなく、Nginxのコンテナ名を間違えて指定してしまうことはよくあるので`docker ps`コマンドでDjangoのコンテナ名を指定しているか確認してください

#### django.db.utils.OperationalError: FATAL: database does not exist
.envファイル内のMYSQL_DATABASEの名前が命名規則に即してない場合は上記のようなエラーが出る場合があります
下記のサイトからご自身が設定したデータベース名がMySQLの命名規則に沿っているか確認してください

https://dev.mysql.com/doc/refman/8.0/ja/identifiers.html

## Poetryを使ったコンテナ環境の構築
PoetryとはPythonのパッケージ管理ツールのことです
Poetryを使用することで
- コマンド一つでパッケージをインストールできる
- パッケージ間の依存関係を自動で解消してくれる
- Blackなどの設定を共通のファイルにまとめることができる

などとても便利です
実際の開発現場でよく使われているので可能なのであれば習得しましょう
詳細は以下の記事を参考にしてください

https://qiita.com/shun198/items/97483a227f288ad58112

### ディレクトリ構成
ディレクトリ構成に関してはrequirements.txtがpyproject.tomlに置き換わります

```terminal
tree
.
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   └── nginx
│       ├── Dockerfile
│       └── conf.d
│           └── default.conf
├── .gitignore
├── .env
├── .env.prod
├── entrypoint.sh
├── docker-compose.prod.yml
├── docker-compose.yml
└── pyproject.toml
```

### pyproject.toml
requirements.txt同様
```
[tool.poetry.dependencies]
```
内に以下のパッケージをインストールします

```pyproject.toml
[tool.poetry]
name = "api"
version = "0.1.0"
description = "api"
authors = ["shun198"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.14"
Django = "^4.2.3"
djangorestframework = "^3.14.0"
mysqlclient = "^2.1.1"
gunicorn = "^20.1.0"
```

### Dockerfile(Django)
```Dockerfile:containers/django/Dockerfile
FROM python:3.14

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY pyproject.toml /code/
# Initialize python project with Poetry
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
# entrypoint.shに実行権限を付与
RUN chmod 755 entrypoint.sh
```

### 新規プロジェクトの作成
新規プロジェクトを作成する際は以下のコマンドを入力します
```
docker compose -f docker-compose.prod.yml run app poetry run django-admin startproject djangopj .
```

以下のようになれば成功です
```terminal
tree
.
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   └── nginx
│       ├── Dockerfile
│       └── conf.d
│           └── default.conf
├── djangopj
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .env.prod
├── .gitignore
├── docker-compose.prod.yml
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
├── poetry.lock
├── pyproject.toml
└── static
```



## Pydanticを使った環境変数の管理
PydanticはPythonの型アノテーションを使って型ヒントを提供したり、バリデーションエラーを簡単にしてくれるライブラリです
環境変数の設定に使うことで
- 使用している環境変数の型が直感的にわかる
- 環境変数関連でエラーが発生するとPydanticのエラーが出るのでデバッグが容易になる

などのメリットがあります

### pyproject.toml
Pydanticをインストールします

```pyproject.toml
[tool.poetry]
name = "djangopj"
version = "0.1.0"
description = "api"
authors = ["shun198"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.14"
Django = "^4.2.3"
djangorestframework = "^3.14.0"
mysqlclient = "^2.1.1"
gunicorn = "^20.1.0"
pydantic = "^1.10.6"
```

### 環境変数の設定
今回はdjangopjの中にenvironment.pyを作成します

```terminal
tree
.
├── containers
│   ├── django
│   │   └── Dockerfile
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   └── nginx
│       ├── Dockerfile
│       └── conf.d
│           └── default.conf
├── djangopj
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── environment.py
│   ├── urls.py
│   └── wsgi.py
├── .env
├── .env.prod
├── .gitignore
├── docker-compose.prod.yml
├── docker-compose.yml
├── entrypoint.sh
├── manage.py
├── poetry.lock
├── pyproject.toml
└── static
```

### environment.py
下記のように環境変数を設定します

```environment.py
"""環境変数定義用のモジュール"""

from pydantic import BaseSettings


class DjangoSettings(BaseSettings):
    """Django関連の環境変数を設定するクラス"""

    SECRET_KEY: str = "secretkey"
    ALLOWED_HOSTS: str = "localhost 127.0.0.1 [::1] back web"
    MYSQL_DATABASE: str = "django"
    MYSQL_USER: str = "django"
    MYSQL_PASSWORD: str = "django"
    MYSQL_HOST: str = "db"
    MYSQL_PORT: int = 3306


django_settings = DjangoSettings()
```

以下のようにdjango_settingsをimportすると環境変数を設定できます
エディタの補完機能を使えば該当する環境変数をタイポなしで設定できるので開発が捗ります
また、上記のようにデフォルト値を設定できますが、
docker-compose.ymlでMySQLのコンテナを起動させるときにMySQLの環境変数が必要です
```.env
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=django-db
MYSQL_USER=django
MYSQL_PASSWORD=django
```

```settings.py
from .environment import django_settings

# SECRET_KEYを.envから取得
SECRET_KEY = django_settings.SECRET_KEY

# ALLOWED_HOSTSを.envから取得
ALLOWED_HOSTS = django_settings.ALLOWED_HOSTS.split()

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        # コンテナ内の環境変数をDATABASESのパラメータに反映
        "NAME": django_settings.MYSQL_DATABASE,
        "USER": django_settings.MYSQL_USER,
        "PASSWORD": django_settings.MYSQL_PASSWORD,
        "HOST": django_settings.MYSQL_HOST,
        "PORT": django_settings.MYSQL_PORT,
        "OPTIONS": {
            "init_command": "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

以上です

## 記事の紹介
以下の記事も書いたので良かったら読んでいただけると幸いです

https://qiita.com/shun198/items/23c6baa450ba37a5fd66

https://qiita.com/shun198/items/ee93c50eac2f7c77e443

https://qiita.com/shun198/items/ab6eca4bbe4d065abb8f


## 参考文献
https://docs.docker.com/samples/django/

https://testdriven.io/blog/dockerizing-django-with-postgres-gunicorn-and-nginx/

https://docs.docker.jp/engine/reference/builder.html

https://tech.actindi.net/2022/02/21/083000
