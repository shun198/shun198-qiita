---
title: Nest.js+Docker+VSCodeでNode.jsのコンテナへリモートデバッグしよう！
tags:
  - Docker
  - docker-compose
  - VSCode
  - NestJS
  - devcontainer
private: false
updated_at: '2025-07-21T12:09:28+09:00'
id: 68230d4b471c14907820
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
コンテナ内のNest.jsのアプリケーションをVSCodeの拡張機能であるRemote Containersを使用してリモートデバッグする方法について解説します
VSCodeのブレークポイントやウォッチが使えるとかなり開発効率が上がるのでぜひ設定してみてくださ

## 前提
- Nest.jsのプロジェクトを作成済み
- Dockerfileおよびdocker-compose.ymlを作成済み

## ディレクトリ構成
```
.
├── .devcontainer
│   └── devcontainer.json
├── .env
├── application
│   ├── .vscode
│   │   └── launch.json
│   ├── README.md
│   ├── nest-cli.json
│   ├── package-lock.json
│   ├── package.json
│   ├── src
├── containers
│   ├── node
│   │   ├── Dockerfile
│   │   └── entrypoint.sh
│   └── postgres
│       └── Dockerfile
└── docker-compose.yml
```

## 実装
- docker-compose.yml
- entrypoint.sh
- package.json
- devcontainer.json
- launch.json

の2種類のファイルを作成します

### docker-compose.yml
リモートデバッグする際にデバッグ用のポート(今回は9229)を開放します

```yaml:docker-compose.yml
version: '3.9'

services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
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
      - '5432:5432'

  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/node/Dockerfile
    volumes:
      - ./application:/code
    ports:
      - '5555:5555'
      - '8000:8000'
      # デバッグ用
      - '9229:9229'
    command: sh -c "/usr/local/bin/entrypoint.sh"
    stdin_open: true
    tty: true
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
volumes:
  db_data:


```

### entrypoint.sh
デバッグモードでローカルを起動させます
```entrypoint.sh
#!/bin/sh
set -eu

npx prisma migrate dev
npm run start:debug

```

### package.json
package.jsonにstart:debugコマンドを設定します

```package.json
  "scripts": {
    "start:debug": "nest start --debug 0.0.0.0:9229 --watch",
  }
```

### devcontainer.json
Remote Containersを使用するために作成します
今回はコンテナのサービス名をappにしています

```.devcontainer/devcontainer.json
{
	"name": "Existing Docker Compose (Extend)",
	"dockerComposeFile": [
		"../docker-compose.yml"
	],
	"service": "app",
	"workspaceFolder": "/workspaces/${localWorkspaceFolderBasename}"
}

```

続いてRemote Containerを使ってコンテナ内へアクセスした際にブレークポイントが使えるよう設定します
今回はDockerfileのアプリケーションのマウント先を/codeにしているのでremoteRootを/codeにします

```application/vscode/launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Attatch to Node",
            "type": "node",
            "request": "attach",
            "address": "localhost",
            "port": 9229,
            "sourceMaps": true,
            "restart": true,
            "localRoot": "${workspaceFolder}",
            "remoteRoot": "/code"
        }
    ]
}

```

## 実際に使用してみよう！
まだ拡張機能のRemote Containersをインストールしていない人はインストールしましょう
![スクリーンショット 2022-08-21 21.23.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/55b9de47-b8fa-1ac5-ccdd-7b3b8cfe3d17.png)

Remotes Containerのインストールができたら左下の緑色のマークをクリックします
![スクリーンショット 2022-08-21 21.24.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ccfa9e5a-637a-a1c4-8a45-41a76c0d9263.png)

`実行中のコンテナーにアタッチ`を選択します
![スクリーンショット 2024-03-07 15.38.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b11e17e3-18c2-6f1b-5653-9da983e3b735.png)


該当するコンテナ(app)を選択します
![スクリーンショット 2024-03-07 15.38.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/22065a22-3c66-e39b-b818-871bd7d2adab.png)

VSCodeの新しいWindowが開いたら上から4番目の三角のアイコンを選択し、緑の三角のアイコンを押します
![スクリーンショット 2024-03-07 15.39.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a659887d-2996-15a7-ed32-e47c18190de2.png)

緑のボタンを押すと以下のようにコールスタックにデバッガーがアタッチされていると表示されます
![スクリーンショット 2024-03-07 15.42.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6b75cd43-f7bd-c857-7d30-d396e740a1ef.png)

以下のようにブレークポイントが有効化されたら成功です

![スクリーンショット 2024-03-07 15.44.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9d513a68-a871-1da3-0977-c7d5c98ecd4e.png)

また、デバッグコンソールを使用すると現在の変数の中身の確認や変更もできます

![スクリーンショット 2024-03-07 15.45.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/be5419ec-8684-8745-b78b-051b09825b4d.png)

## 参考
https://blog.itaywol.com/dockerizing-nestjs-application-and-debugging

https://qiita.com/rema424/items/36475ea7379e0d9c5972
