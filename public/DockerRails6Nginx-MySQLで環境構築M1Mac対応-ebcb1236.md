---
title: Docker+Rails6+Nginx +MySQLで環境構築~M1Mac対応
tags:
  - Rails
  - MySQL
  - nginx
  - Docker
  - docker-compose
private: false
updated_at: '2026-09-05T08:55:28+09:00'
id: ebcb1236b061acd14405
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- フレームワークはRails
- Rubyのバージョンは2.7.3
- Railsのバージョンは6.1.3
- DBはMySQL
- アプリケーションサーバはPuma
- WebサーバはNginx
- DB側のコンテナ名はmysql、Rails側のコンテナ名はapp、Nginx側はwebにします
- 開発用はcompose.yaml(Rails+MySQL)として作成します
- 本番用はcompose.prod.yaml(Rails+MySQL+Nginx)として作成します

## はじめに
プロジェクトを作成するディレクトリを作成します
初回作成時のディレクトリ構成は以下の通りです
containersフォルダを作成し、その中にRails、MySQL、Nginxのフォルダを作成してください
また、Nginxのフォルダの中にconf.dフォルダも作成します
```
❯ tree
.
├── Gemfile
├── Gemfile.lock
├── .env
├── containers
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── conf.d
│   │       └── default.conf
│   └── rails
│       └── Dockerfile
├── compose.prod.yaml
└── compose.yaml
```

## 作成するファイル
- RailsのDockerfile
- MySQLのDockerfile
- NginxのDockerfile
- my.cnf(MySQL用の設定ファイル)
- init.sql(MySQLのユーザに権限を付与)
- default.conf(Nginx用の設定ファイル)
- compose.yaml(開発用)
- compose.prod.yaml(本番用)
- Gemfile
- Gemfile.lock
- .env(環境変数の設定ファイル)

の作成方法について順に説明します

## そもそもなんで開発用と本番用に分けるの？
Rails+MySQL+Nignxの構成で開発する場合、Nginxは静的ファイルを表示させる機能しかないため、ControllerやModelの変更を反映させるには都度コンテナを再起動させる必要があります(要するにホットリロードができないため、開発効率が悪い)
そのため、開発はRails+MySQLのコンテナで行い、本番環境ではNginxのポートから画面を確認する運用になるかと思います
本記事では開発用、本番用のcompose.yamlの書き方もあわせて解説します

## 各ファイルに必要なコードを記入しよう
### Dockerfile
#### Rails
```Dockerfile:containers/rails/Dockerfile
# ruby2.7.3のイメージを指定
FROM ruby:2.7.3
# yarnとnodeをインストール
# 特にyarnをインストールしないとwebpacker.ymlが作成されず、railsのコンテナが起動しない
# また、`RUN yarn`ステートメントだとインストールされるyarnが古すぎてwebpacker.ymlがインストールされない現象が発生するので下記のように記載
RUN apt-get update -qq && \
    apt-get install -y curl gnupg2 && \
    curl -sS https://dl.yarnpkg.com/debian/pubkey.gpg | apt-key add - && \
    echo "deb https://dl.yarnpkg.com/debian/ stable main" | tee /etc/apt/sources.list.d/yarn.list && \
    apt-get update -qq && apt-get install -y nodejs yarn
RUN mkdir /code
WORKDIR /code
# GemfileとGemfile.lockが変更されるたびに/codeへコピー
COPY Gemfile /code/
COPY Gemfile.lock /code/
# bundle installを実行後/codeにソースコードをコピーする
RUN bundle install
COPY . /code/
```

#### MySQL
```Dockerfile
# MySQL8系のイメージを指定
FROM mysql:8.0

# MySQLのローカルの設定ファイルをコンテナにコピー
COPY containers/mysql/my.cnf /etc/mysql/conf.d/my.cnf
# init.sqlをコンテナの/docker-entrypoint-init.db.dと共有
COPY containers/mysql/init.sql /docker-entrypoint-initdb.d
```

#### Nginx
```Dockerfile:containers/nginx/Dockerfile
FROM nginx:1.21-alpine

# ローカルのdefault.confをコンテナにコピー
COPY containers/nginx/conf.d/default.conf /etc/nginx/conf.d/default.conf
```

### my.cnf(MySQL用の設定ファイル)
```
# MySQLサーバーへの設定
[mysqld]
# 文字コード/照合順序の設定
character_set_server=utf8mb4
collation_server=utf8mb4_bin
# タイムゾーンの設定
default_time_zone=SYSTEM
log_timestamps=SYSTEM
# MySQL8.0以上用のデフォルト認証プラグインの設定
default_authentication_plugin=mysql_native_password
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
今回はユーザをrailsとして権限を付与します
.env(後述)でもMySQLのユーザをrailsにしています
```
-- MYSQL_USERに権限を付与
GRANT ALL PRIVILEGES ON *.* TO 'rails'@'%';
FLUSH PRIVILEGES;
```

### default.conf(Nginx用の設定ファイル)
```nginx:containers/nginx/conf.d/default.conf
# Railsの3000番ポートとつなぐ
upstream rails {
    # サーバにRailsのコンテナ名を指定。今回はapp
    # ポートはRailsのコンテナの3000番ポート
    server app:3000;
}

server {
    # HTTPの80番ポートを指定
    listen 80;
    server_name 0.0.0.0;

    # プロキシ設定
    # 実際はNginxのコンテナにアクセスしてるのをRailsにアクセスしてるかのようにみせる
    location / {
        proxy_pass http://rails;
        proxy_set_header Host $host;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_redirect off;
    }
}
```

### compose.yaml(開発用)
```compose.yaml
# db(MySQL),app(Rails)のコンテナを作成
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
    platform: linux/x86_64
    # DBのボリュームを指定
    # ローカルの/data/dbをコンテナの/var/lib/mysqlにマウンティング
    volumes:
      - db_data:/var/lib/mysql
    # コンテナ内の環境変数を.envを使って設定
    env_file:
      - .env
    # DBのコンテナのヘルスチェックを行う
    # mysqladmin(MySQLサーバーの管理を行うクライアントを使ってDBコンテナ自身(127.0.0.1)にpingを送ってヘルスチェックを行う
    healthcheck:
      test: mysqladmin ping -h 127.0.0.1 -u$$MYSQL_USER -p$$MYSQL_PASSWORD
  app:
    # コンテナ名をappに設定
    container_name: app
    # RailsのDockerfileをビルドする
    build:
      # ビルドコンテキストはカレントディレクトリ
      context: .
      dockerfile: containers/rails/Dockerfile
    # ボリュームを指定
    volumes:
      # ローカルのカレントディレクトリをコンテナの/codeにマウントする
      - .:/code
      # bundle用の永続volumeを作成することでGemfileを更新するたびにbuildし直すのを防ぐ
      - bundle:/usr/local/bundle
    # ローカルの3000番ポートとコンテナの3000番ポートをつなぐ
    ports:
      - "3000:3000"
    # server.pidを削除し、3000番ポートを指定してrails sを実行
    # 削除しないと正常にコンテナをdownできなかった際にもう一度起動できなくなってしまう
    command: bash -c "rm -f tmp/pids/server.pid && bundle exec rails s -p 3000 -b '0.0.0.0'"
    # コンテナ内の環境変数を.envを使って設定
    env_file:
      - ./.env
    # 先にdbを起動してからappを起動する
    depends_on:
      db:
        # dbのヘルスチェックが終わってからappを起動させる
        condition: service_healthy
volumes:
  db_data:
  bundle:
```

### compose.yaml(本番用)
```compose.prod.yaml
services:
  db:
    container_name: mysql
    build:
      context: .
      dockerfile: containers/mysql/Dockerfile
    # M1チップでも動くように
    platform: linux/x86_64
    # ローカルの/data/dbをコンテナの/var/lib/mysqlにマウンティング
    volumes:
      - db_data:/var/lib/mysql
    # 環境変数
    env_file:
      - .env
    healthcheck:
      test: mysqladmin ping -h 127.0.0.1 -u$$MYSQL_USER -p$$MYSQL_PASSWORD
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/rails/Dockerfile
    volumes:
      - .:/code
      - bundle:/usr/local/bundle
    expose:
      - "3000"
    command: bash -c "rm -f tmp/pids/server.pid && bundle exec rails s -p 3000 -b '0.0.0.0'"
    env_file:
      - ./.env
    depends_on:
      db:
        condition: service_healthy
  web:
    # コンテナ名をwebに指定
    container_name: web
    # NginxのDockerfileをビルドする
    build:
      # ビルドコンテキストはカレントディレクトリ
      context: .
      dockerfile: containers/nginx/Dockerfile
    # ローカルの80番ボートをコンテナの80番ポートとつなぐ
    ports:
      - "80:80"
    # 先にappを起動してからwebを起動する
    depends_on:
      - app
volumes:
  db_data:
  bundle:
```

### Gemfile
```ruby:Gemfile
source 'https://rubygems.org'
gem 'rails', '6.1.3'
```

### Gemfile.lock
空のGemfile.lockを作成します
```ruby:Gemfile.lock
# 何も記入しなくていい
```

### .env
MySQLのrootユーザのパスワードなどをcompose.yamlやRailsのdatabase.ymlに書くのは危険なので.envファイルを使います
.gitignore(後述)があることで.envファイルはGitHubに上がることはありません
今回は以下のような内容にします
```.env
# MYSQLのルートパスワードがないとコンテナが起動しない
# MYSQL_ROOT_PASSWORD="任意のルートパスワード"
# MYSQL_DATABASE="任意のデータベース名"
# MYSQL_USER="任意のユーザ名"
# MYSQL_PASSWORD="任意のパスワード"
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=rails-db
MYSQL_USER=rails
MYSQL_PASSWORD=rails
```

## imageのビルド、Railsの画面表示まで行おう
今回はNginxのポートにアクセスしてRailsの画面を表示させたいのでcompose.prod.yaml(本番用)を使います
開発する場合はコマンドで指定しているファイルをcompose.yamlに置き換えて、3000番ポートにアクセスしてください

## docker-composeでDocker imageを作成しよう(初回)
プロジェクトを新規作成する際は以下のコマンドを実行します
今回はデータベースをMySQLにするので`--force --database=mysql`も指定します
初回はyarnのインストールも含めると時間がかかるので気長に待ちます
```terminal:terminal
docker compose run app rails new . --force --database=mysql
```

実行するとローカルのディレクトリ構成は以下のようになります
全てのファイルを表示すると膨大な量になるので主要なディレクトリ、ファイルのみ表示します
```
❯ tree -d
.
├── Gemfile
├── Gemfile.lock
├── .gitignore
├── .env
├── app
├── bin
├── config
├── containers
│   ├── mysql
│   │   ├── Dockerfile
│   │   ├── init.sql
│   │   └── my.cnf
│   ├── nginx
│   │   ├── Dockerfile
│   │   └── conf.d
│   │       └── default.conf
│   └── rails
│       └── Dockerfile
├── db
├── lib
├── log
├── public
├── static
├── storage
├── test
├── tmp
├── vendor
├── compose.prod.yaml
└── compose.yaml
```

### database.yml
database.ymlにMySQLの設定を反映させます
```yaml:config/database.yml
default: &default
  adapter: mysql2
  encoding: utf8mb4
  pool: <%= ENV.fetch("RAILS_MAX_THREADS") { 5 } %>
  # .envのMYSQL_USERとMYSQL_PASSWORDを指定します
  username: <%= ENV['MYSQL_USER'] %>
  password: <%= ENV['MYSQL_PASSWORD'] %>
  # MySQLコンテナの名前を指定します
  host: db

development:
  <<: *default
  # envのMYSQL_DATABASEを指定します
  database: <%= ENV['MYSQL_DATABASE'] %>
```

### 環境変数の設定
.envの中身を読み取る'dotenv-rails'というgemを追記します
```ruby:Gemfile
gem 'dotenv-rails'
```

### .gitignoreに.envを追加
rails newで.gitignoreが自動生成されましたが、.envが記載されていません
このままだとgit pushした際に.envの内容がGitHub上に上がってしまって非常に危険なので
.gitignoreに.envを追加します
```.gitignore
.env
```

### コンテナを起動
コンテナをデタッチモードで起動する
デタッチモード起動することでコンテナの中に入らずにバックグラウンドで起動させることができます
```terminal:terminal
docker compose -f compose.prod.yaml up -d
```

### 127.0.0.1/80にアクセスしてみよう
ホストからNginxのポートに接続します
ブラウザにアクセスし、NginxのポートからRailsのポートへアクセスできます
以下のページが表示されたら成功です

![スクリーンショット 2022-09-18 22.54.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/57c7c9b1-3ba5-3ae1-67c4-0aa049c509f3.png)

### `docker compose -f compose.prod.yaml up -d`しても接続できない時
#### failed (111: Connection refused) while connecting to upstream
Nginxのdefault.confを見直す必要があります
```containers/nginx/conf.d/default.conf
upstream rails {
    server app:3000;
}
```
serverの後はRailsではなく、Nginxのコンテナ名を間違えて指定してしまうことはよくあるので`docker ps`コマンドでRailsのコンテナ名を指定しているか確認してください

## 記事の紹介
以下の記事も書いたので良かったら読んでいただけると幸いです

https://qiita.com/shun198/items/ab6eca4bbe4d065abb8f

https://qiita.com/shun198/items/f6864ef381ed658b5aba


## 参考
https://docs.docker.jp/compose/rails.html

https://qiita.com/fuku_tech/items/a380ebb1fd156c14c25b

https://zenn.dev/shibata/articles/2e6c7345b57b3e

https://qiita.com/neko-neko/items/abe912eba9c113fd527e

https://teratail.com/questions/157380

https://qiita.com/neko-neko/items/abe912eba9c113fd527e
