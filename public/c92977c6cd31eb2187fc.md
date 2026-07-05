---
title: '[初心者向け] Nginxの設定ファイルの書き方について'
tags:
  - nginx
  - dockerfile
  - docker-compose
private: false
updated_at: '2023-10-08T19:16:54+09:00'
id: c92977c6cd31eb2187fc
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Webアプリケーション開発でNginxをWebサーバとして使用しているプロジェクトが多いので今回は

- ローカル環境
- 本番環境

別で
- NginxのDockerfileおよびnginx.confファイルの作成方法
- フロントエンドとバックエンドの連携方法
 
等について解説していきたいと思います

## 前提
- 今回は例としてフレームワークはDjango、WSGIサーバはGunicornを使用します
- インフラはAWSを使用する前提でお話しします

## プロキシサーバとリバースプロキシサーバの違い
プロキシサーバはインターネット(クライアント)と通信する際にクライアントが直接Webサーバに接続せずに別のサーバーに経由する役割を担うサーバーのことです
プロキシを経由することで直接アクセスできないWebサーバにアクセスすることができるなどの利点があります
一方で、リバースプロキシサーバはクライアントからのリクエストをバックエンドサーバーに中継する役割を担うサーバーです
まとめるとプロキシサーバは代理(Proxy)するのはインターネット(クライアント)に対してリバースプロキシはその逆でパックエンドサーバの代理になります
今回説明するNginxはクライアントからの通信をプロキシし、バックエンドのAPIサーバに送信するプロキシサーバの役割を担います

## ローカル環境
ローカル環境ではDockerfileと一緒にdocker-compose.ymlも使用するので
- docker-compose.yml
- Dockerfile
- nginx.conf

の順に解説していきます

### docker-compose.yml
以下が
- Django
- MySQL
- Nginx
- Node.js

用のdocker-compose.ymlです
ローカル環境ではNginxを使ってフロントエンドとバックエンドを連携させる際にDockerのnetworkを使います
今回はtestnetというネットワークを作成します

```docker-compose.yml
version: '3.9'

services:
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./application:/code
      - ./static:/static
    ports:
      - '8000:8000'
      # デバッグ用ポート
      - '8080:8080'
    command: sh -c "/usr/local/bin/entrypoint.sh"
    stdin_open: true
    tty: true
    env_file:
      - .env

  nginx:
    container_name: web
    build:
      context: .
      dockerfile: containers/nginx/Dockerfile
    volumes:
      - ./static:/static
    ports:
      - 80:80
    depends_on:
      - app

  front:
    container_name: front
    build:
      context: .
      dockerfile: containers/front/Dockerfile
    volumes:
      - ./frontend:/code
      - node_modules_volume:/frontend/node_modules
    command: sh -c "npm run dev"
    ports:
      - '3000:3000'
    environment:
      - CHOKIDAR_USEPOLLING=true
      - RESTAPI_URL=http://localhost/back

volumes:
  static:

networks:
  default:
    name: testnet
```

### Dockerfile
後述するnginx.confをコピーするよう設定します

```Dockerfile:Dockerfile
FROM nginx:1.21

RUN rm -f /etc/nginx/conf.d/*
COPY ./containers/nginx/nginx.conf /etc/nginx/conf.d/
```

### nginx.conf
ローカル環境で使うNginxの設定ファイルです
```nginx.conf
upstream front {
    server host.docker.internal:3000;
}

upstream back {
    server host.docker.internal:8000;
}
 
server {
    listen       80;
    server_name  localhost;

    client_max_body_size 20M;
    
    location / {
        proxy_pass http://front/;
    }
 
    location /back/ {
        # X-Forwarded-Hostヘッダにバックエンドのホスト名とポートを指定
        proxy_set_header X-Forwarded-Host $host:$server_port;
        # X-Forwarded-Serverヘッダにバックエンドのホスト名を指定
        proxy_set_header X-Forwarded-Server $host;
        # X-Forwarded-Forヘッダにリクエストを送ったクライアントまたはプロキシのIPアドレスの履歴(リスト)を設定
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # 上記の情報のヘッダが今回だとMacの8000番ポートに最終的に転送される
        proxy_pass http://back/;
    }

    location /_next/webpack-hmr {
        proxy_pass http://front/_next/webpack-hmr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }

}
```

一つずつ解説します

#### upstream
upstreamディレクティブを使用して
- バックエンドサーバ
- フロントエンドサーバ
 
を定義しています
その際はserverの後にserver名を記載します
今回はDockerコンテナとDockerホスト(Mac)間で通信させます
```
host.docker.internal
```
はDockerの機能の1つでこれを使用するとIPアドレスを指定せずにコンテナからホスト(Mac)に簡単にアクセスできます
docker-compose.ymlのポートでフロントエンドは3000、バックエンドは8000にしてるのでこちらも同様にポート番号をそろえます

```nginx.conf
upstream front {
    server host.docker.internal:3000;
}

upstream back {
    server host.docker.internal:8000;
}
```

#### server
80番ポートを経由してプロキシする設定です
サーバ名はローカル環境を使っているのでlocalhostです

```nginx.conf
server {
    listen       80;
    server_name  localhost;
```

Nginxからフロントエンドにプロキシする設定を記載します
upstreamでfrontと記載しているので名前を合わせます

```nginx.conf
    location / {
        proxy_pass http://front/;
    }
```

Nginxからバックエンドにプロキシする設定を記載します
upstreamでbackと記載しているので名前を合わせます

```nginx.conf
    location /back/ {
        # X-Forwarded-Hostヘッダにバックエンドのホスト名とポートを指定
        proxy_set_header X-Forwarded-Host $host:$server_port;
        # X-Forwarded-Serverヘッダにバックエンドのホスト名を指定
        proxy_set_header X-Forwarded-Server $host;
        # X-Forwarded-Forヘッダにリクエストを送ったクライアントまたはプロキシのIPアドレスの履歴(リスト)を設定
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # 上記の情報のヘッダが今回だとMacの8000番ポートに最終的に転送される
        proxy_pass http://back/;
    }
```

### Webpackerの設定
NginxからNext.jsのWebpackerへリバースプロキシする設定です
公式ドキュメントに記載の通り、Nginxのversion1.3.13以降ではホットモジュールリローディング（HMR）を有効化するには以下のヘッダーを明示的に渡す必要があります

```nginx.conf
    location /_next/webpack-hmr {
        proxy_pass http://front/_next/webpack-hmr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
```

> To turn a connection between a client and server from HTTP/1.1 into WebSocket, the protocol switch mechanism available in HTTP/1.1 is used.
There is one subtlety however: since the “Upgrade” is a hop-by-hop header, it is not passed from a client to proxied server. With forward proxying, clients may use the CONNECT method to circumvent this issue. This does not work with reverse proxying however, since clients are not aware of any proxy servers, and special processing on a proxy server is required.
Since version 1.3.13, nginx implements special mode of operation that allows setting up a tunnel between a client and proxied server if the proxied server returned a response with the code 101 (Switching Protocols), and the client asked for a protocol switch via the “Upgrade” header in a request.
As noted above, hop-by-hop headers including “Upgrade” and “Connection” are not passed from a client to proxied server, therefore in order for the proxied server to know about the client’s intention to switch a protocol to WebSocket, these headers have to be passed explicitly

## 本番環境
本番環境ではdocker-compose.ymlを使わずにECS Fargateを使用するので
- NginxのDockerfile
- nginx.conf

の順に解説していきます

### Dockerfile
```Dockerfile:Dockerfile
FROM --platform=linux/x86_64 nginx:stable-alpine

RUN rm -f /etc/nginx/conf.d/*
COPY ./containers/nginx/nginx.conf /etc/nginx/conf.d/

CMD /usr/sbin/nginx -g 'daemon off;' -c /etc/nginx/nginx.conf
```

Apple Silicon Macを使用する際はNginxのDockerfileをAWS上で使用する際に
```Dockerfile
--platform=linux/x86_64
```
を指定する必要があります
M1Macがarmのアーキテクチャになっているのに対し、ECS上ではlinux/x86_64になっており、
ECSをbuildする際にplatform errorが発生するからです
そこで上記のコマンドを追記してDockerfile内のplatformをECSと同じになるよう設定します
また、Nginxはデフォルトでバックグラウンド(デーモンがオンの状態)で実行されてしまいます
Cloud Watch上でログが見れるようフォアグラウンドで実行できるようデーモンをオフにします

```Dockerfile
CMD /usr/sbin/nginx -g 'daemon off;' -c /etc/nginx/nginx.conf
```

### nginx.conf
Nginxの本番環境の設定ファイルです
```nginx.conf
upstream gunicorn {
    # gunicornとdjangoがunixソケットを通じて通信する
    server unix:///code/tmp/gunicorn_socket;
}

server {
    listen 80;
    server_name example.com api.example.com;
    # Nginxのバージョン情報を非表示にする
    # サーバ情報を隠すことでセキュリティ上のリスクを軽減させる
    server_tokens off;

    # ファイルサイズの変更、デフォルト値は1M
    client_max_body_size 5M;

    # HTTP レスポンスヘッダの Content_Type に付与する文字コード
    charset utf-8;

    # ログ設定
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # API 通信
    # プロキシ先のGunicornに対して、元のクライアントIPアドレスやヘッダ情報を転送
    location /api {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_read_timeout 3600;
        proxy_pass http://gunicorn;
    }

    # ヘルスチェック用のレスポンスを転送
    location /api/health {
        empty_gif;
        access_log off;
        break;
    }

    # HTTP 通信をタイムアウトせずに待つ秒数
    keepalive_timeout 60;
}
```

1つずつ解説します

### upstream
```nginx
upstream gunicorn {
    # gunicornとdjangoがunixソケットを通じて通信する
    server unix:///code/tmp/gunicorn_socket;
}
```
GunicornとDjangoをソケット通信させる設定を行います
ソケット通信することでインターネットを経由せずに直接データ間のやり取りができるのでセキュリティもパフォーマンスも向上します

### APIとの通信の設定
ローカルの時とほぼ同じ設定になります
proxy_passだけupstreamで定義したgunicornを設定します
```nginx
    # API 通信
    # プロキシ先のGunicornに対して、元のクライアントIPアドレスやヘッダ情報を転送
    location /api {
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header Host $http_host;
        proxy_read_timeout 3600;
        proxy_pass http://gunicorn;
    }
```

### ヘルスチェック
ヘルスチェックの設定を記載します
ヘルスチェックに関してはaccess_logの設定をoffにします
```nginx
    # ヘルスチェック用のレスポンスを転送
    location /api/health {
        empty_gif;
        access_log off;
        break;
    }
```

## まとめ
Nginxの設定ファイルやDockerfileをなんとなくでしか書いていなかったんでまとめてみました
ローカル上でもAWS上でも使うのに必須の知識なので覚えておいて損はないかと思います

## 参考
http://nginx.org/en/docs/http/ngx_http_core_module.html

http://nginx.org/en/docs/http/ngx_http_proxy_module.html

https://www.nginx.com/resources/wiki/start/topics/examples/forwarded/

https://docs.docker.com/desktop/networking/#i-want-to-connect-from-a-container-to-a-service-on-the-host

https://developer.mozilla.org/ja/docs/Web/HTTP/Headers/X-Forwarded-For

https://qiita.com/skobaken/items/03a8b9d0e443745862ac

https://qiita.com/Mayumi_Pythonista/items/11b412e59e045a2c5eb3

https://ja.wikipedia.org/wiki/X-Forwarded-For

https://qiita.com/zawawahoge/items/a931de1464ccaa228551

http://nginx.org/en/docs/http/websocket.html

https://github.com/vercel/next.js/issues/30491

https://qiita.com/takatakaryoryo/items/ba4ab40b79b24ca4548d

https://stackoverflow.com/questions/67361936/exec-user-process-caused-exec-format-error-in-aws-fargate-service

https://eset-info.canon-its.jp/malware_info/special/detail/201021.html

https://wa3.i-3-i.info/word1755.html
