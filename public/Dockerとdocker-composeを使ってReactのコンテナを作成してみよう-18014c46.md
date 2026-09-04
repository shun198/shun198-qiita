---
title: Dockerとdocker-composeを使ってReactのコンテナを作成してみよう！
tags:
  - Node.js
  - npm
  - Docker
  - React
  - docker-compose
private: false
updated_at: '2026-09-05T08:55:27+09:00'
id: 18014c46901f256af9ee
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## はじめに
- Dockerfile
- compose.yaml
- .gitignore

を作成します
ディレクトリ構成は以下の通りです
```
tree
.
├── .gitignore
├── Dockerfile
└── compose.yaml
```

## 必要なファイルの作成
### Dockerfile
今回はNodeJSの16.17.0のDocker imageから作成します
今回はワークディレクトリを`/code`にします
```Dockerfile:Dockerfile
FROM node:16.17.0-bullseye
WORKDIR /code
# 先にpackage.jsonとpackage-lock.jsonをマウントさせる
COPY ./app/package*.json /code
RUN npm install
```

### compose.yaml
```yml:compose.yaml
services:
  # サービス名はfront
  front:
    # コンテナ名はフロント
    container_name: front
    # ビルドコンテキストはカレントディレクトリ
    build:
      context: .
      dockerfile: Dockerfile
    # カレントディレクトリ内の`/app`のファイル・フォルダをコンテナにマウントします
    volumes:
      - ./app:/code
      # mode_modules用の永続化Volumeを作成して2回目以降のnode_modulesの呼び出しを高速化
      - node_modules_volume:/app/node_modules
    # npmを使って起動する
    command: sh -c "npm start"
    ports:
      # デフォルトの3000ポートを使う
      - "3000:3000"
    # ホットリロードを有効化
    environment:
      - CHOKIDAR_USEPOLLING=true
volumes:
  node_modules_volume:
```

## .gitignore
以下からNodeJSの.gitignoreをコピペしてきます

https://github.com/github/gitignore/blob/main/Node.gitignore

## 実際に作成してみよう！
今回はappという新しいアプリケーションを作成します
その際はサービス名(front)を指定する必要があります
npx create-react-appコマンドを使うと作成できます
後ろに作成するアプリケーション名(今回はapp)を指定します
```terminal
docker compose run --rm front sh -c "npx create-react-app app"
```

少なくとも3,4分は作成に時間がかかるので気長に待ちましょう
```terminal
npx: installed 67 in 7.283s
# コンテナの/code/app内にReactのアプリケーションが作成されます
Creating a new React app in /code/app.

Installing packages. This might take a couple of minutes.
Installing react, react-dom, and react-scripts with cra-template...
```

アプリケーションの作成に成功すると以下のようなファイル構成になるかと思います
```
tree
.
├── .gitignore
├── Dockerfile
├── README.md
├── app
│   ├── .gitignore
│   ├── README.md
│   ├── node_modules
│   ├── package-lock.json
│   ├── package.json
│   ├── public
│   └── src
└── compose.yaml
```

このようなログが出ますが、compose.yamlのcommandにすでに記載されているので`docker compose up -d`を実行すれば下記のコマンドは実行されます
```terminal
We suggest that you begin by typing:

  cd react-sample
  npm start

Happy hacking!
```

## 起動させよう！
```terminal
docker compose up -d
```
を実行してreactのコンテナを起動させます
```terminal
front | 
front | > app@0.1.0 start /code/app
front | > react-scripts start
front | 
front | (node:25) [DEP_WEBPACK_DEV_SERVER_ON_AFTER_SETUP_MIDDLEWARE] DeprecationWarning: 'onAfterSetupMiddleware' option is deprecated. Please use the 'setupMiddlewares' option.
front | (Use `node --trace-deprecation ...` to show where the warning was created)
front | (node:25) [DEP_WEBPACK_DEV_SERVER_ON_BEFORE_SETUP_MIDDLEWARE] DeprecationWarning: 'onBeforeSetupMiddleware' option is deprecated. Please use the 'setupMiddlewares' option.
front | Starting the development server...
front | 
front | Compiled successfully!
front | 
front | You can now view app in the browser.
front | 
front |   Local:            http://localhost:3000
front |   On Your Network:  http://192.168.16.2:3000
front | 
front | Note that the development build is not optimized.
front | To create a production build, use npm run build.
front | 
front | webpack compiled successfully
```

その後、http://localhost:3000/
にアクセスし、以下の画面が表示されたら成功です！
![スクリーンショット 2022-11-20 20.01.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dc67fe3b-46a3-b1a0-c626-1de0175e9c48.png)

## 参考
https://amateur-engineer.com/react-docker-compose/

https://zenn.dev/rihito/articles/96dfad8d4990f9

https://nekorokkekun.hatenablog.com/entry/2019/08/30/175407

https://ja.reactjs.org/docs/create-a-new-react-app.html

https://docs.docker.com/engine/storage/bind-mounts/
