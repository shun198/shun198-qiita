---
title: Golang+Echo+Postgresのコンテナ開発環境をDockerfileとdocker-compose.ymlを使って構築しよう！
tags:
  - Go
  - PostgreSQL
  - Docker
  - echo
  - docker-compose
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: 58a1c5ca4d43a12419ce
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GolangのWebフレームワークであるEchoとPostgresのコンテナ開発環境を構築する方法について解説します

## 前提
- Golangをインストール済み
- ホットリロードの際にAirを使用します

## ディレクトリ構成
```
├── .gitignore
├── application
│   ├── .air.toml
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
├── containers
│   ├── go
│   │   └── Dockerfile
│   └── postgres
│       └── Dockerfile
└── docker-compose.yml
```

## 初期設定
applicationフォルダへ移行し、`go mod init`コマンドで初期設定を行います
```
cd application
go mod init github.com/username/app_name
```

その後、echoをインストールします
```
go get github.com/labstack/echo/v4
```

今回はAirを使ってホットリロードを実現したいので設定します
airをインストールした後に初期化します
```
go get github.com/cosmtrek/air@latest
air init
```

以下のように.air.tomlが作成されたら成功です

```toml:application/.air.toml
root = "."
testdata_dir = "testdata"
tmp_dir = "tmp"

[build]
  args_bin = []
  bin = "./tmp/main"
  cmd = "go build -o ./tmp/main ."
  delay = 1000
  exclude_dir = ["assets", "tmp", "vendor", "testdata"]
  exclude_file = []
  exclude_regex = ["_test.go"]
  exclude_unchanged = false
  follow_symlink = false
  full_bin = ""
  include_dir = []
  include_ext = ["go", "tpl", "tmpl", "html"]
  include_file = []
  kill_delay = "0s"
  log = "build-errors.log"
  poll = false
  poll_interval = 0
  post_cmd = []
  pre_cmd = []
  rerun = false
  rerun_delay = 500
  send_interrupt = false
  stop_on_error = false

[color]
  app = ""
  build = "yellow"
  main = "magenta"
  runner = "green"
  watcher = "cyan"

[log]
  main_only = false
  # ログに時間出力したいため、trueに変更
  time = true

[misc]
  clean_on_exit = false

[screen]
  clear_on_rebuild = false
  keep_scroll = true

```

## GolangのDockerfileの作成
今回はGolangのv1.20を使用します

```Dockerfile:containers/go/Dockerfile
FROM --platform=linux/x86_64 golang:1.20

WORKDIR /usr/local/go/src/go_crm/

# airをインストールし、コンテナ起動時にホットリロードできるよう実行する
RUN go install github.com/cosmtrek/air@v1.42.0

COPY application/. /usr/local/go/src/go_crm/

RUN go mod download

```

## PostgresのDockerfileの作成
```Dockerfile:containers/postgres/Dockerfile
FROM postgres:16.2

```

## docker-compose.ymlの作成
GolangとPostgres両方のコンテナを起動できるようにします
```docker-compose.yml
services:
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/go/Dockerfile
    volumes:
      - ./application:/usr/local/go/src/go_crm
    ports:
      - "8000:8000"
    command: air -d
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
  db:
    container_name: db
    image: postgres:16.2
    volumes:
      - db_data:/var/lib/postgresql/data
    # ヘルスチェックを使ってPostgresのコンテナが必ずGolangのコンテナより先に起動するようにする
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_NAME=postgres
      - POSTGRES_USER=postgres
      - POSTGRES_PASSWORD=postgres
    ports:
      - '5432:5432' # デバッグ用
volumes:
  db_data:

```

## main.goの作成
コンテナ起動時にmain.goを実行させるので作成します
今回はヘルスチェックのAPIのみ作成します

```main.go
package main

import (
	"net/http"
)

func main() {
	e := echo.New()
	e.GET("/health", func(c echo.Context) error {
		return c.JSON(http.StatusOK, map[string]string{"msg": "pass"})
	})
	e.Logger.Fatal(e.Start(":8000"))
}

```

## 実際に起動してみよう！
```
docker compose up -d --build
```

コマンドを実行し、Dockerfileのbuildとコンテナの起動を行います
`127.0.0.1:8000/health`へアクセスし、以下のように表示されたら成功です

```
2024-05-05 15:22:00 
2024-05-05 15:22:00   __    _   ___  
2024-05-05 15:22:00  / /\  | | | |_) 
2024-05-05 15:22:00 /_/--\ |_| |_| \_ , built with Go 
2024-05-05 15:22:00 
2024-05-05 15:22:00 [debug] mode
2024-05-05 15:22:00 [06:22:00] CWD: /usr/local/go/src/go_crm
2024-05-05 15:22:00 [06:22:00] watching .
2024-05-05 15:22:00 [06:22:00] watching docs
2024-05-05 15:22:00 [06:22:00] !exclude tmp
2024-05-05 15:22:00 [06:22:00] building...
2024-05-05 15:22:31 [06:22:31] running...
2024-05-05 15:22:31 [06:22:31] running process pid 1322
2024-05-05 15:22:31 
2024-05-05 15:22:31    ____    __
2024-05-05 15:22:31   / __/___/ /  ___
2024-05-05 15:22:31  / _// __/ _ \/ _ \
2024-05-05 15:22:31 /___/\__/_//_/\___/ v4.12.0
2024-05-05 15:22:31 High performance, minimalist Go web framework
2024-05-05 15:22:31 https://echo.labstack.com
2024-05-05 15:22:31 ____________________________________O/_______
2024-05-05 15:22:31                                     O\
2024-05-05 15:22:31 ⇨ http server started on [::]:8000
```

![スクリーンショット 2024-05-05 15.22.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0b491791-f0eb-3061-1ac9-755706a04c5c.png)

## 参考
https://echo.labstack.com/docs/quick-start

https://qiita.com/frkawa/items/1dd12e19f10de034e0f5
