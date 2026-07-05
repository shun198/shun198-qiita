---
title: prisma-client-goを使ったDocker環境の構築から初期設定、テストデータ投入、接続、使用法まで徹底解説！
tags:
  - Go
  - PostgreSQL
  - Docker
  - docker-compose
  - prisma
private: false
updated_at: '2024-05-29T11:53:33+09:00'
id: 1231a16dc8e523fb530b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GOのDocker環境を使ったPrismaの
- 初期設定
- テストデータ作成と投入
- Prisma Clientとの接続
- Prismaの使用(今回は一覧表示APIを作成しながら解説します)

方法について解説します

## 前提
- フレームワークはGinを使用します
- DBはPostgresを使用します

## ディレクトリ構成
```
tree
.
├── .env
├── .gitignore
├── README.md
├── application
│   ├── config
│   │   ├── database.go
│   │   └── passwordManagement.go
│   ├── controllers.go
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   ├── prisma
│   │   ├── schema.prisma
│   │   └── seed.go
│   ├── routes.go
│   ├── services.go
├── containers
│   ├── go
│   │   └── Dockerfile
│   └── postgres
│       └── Dockerfile
└── docker-compose.yml
```

## Dockerfileの作成
GoのDockerfileを作成します
今回はairを使ってホットリロードがしたいのでDockerfile内でインストールするコマンドを記載します

```Dockerfile:containers/go/Dockerfile
FROM golang:1.21

WORKDIR /usr/local/go/src/gin-crm/

RUN go install github.com/cosmtrek/air@v1.42.0

COPY application/go.mod application/go.sum ./
RUN go mod download
# prisma-clientのダウンローががキャッシュされるよう実行する
RUN go run github.com/steebchen/prisma-client-go prefetch

COPY application/. /usr/local/go/src/gin-crm/
# Prisma Clientを生成
RUN go run github.com/steebchen/prisma-client-go generate

```

https://goprisma.org/docs/reference/deploy/docker

続いてPostgresのDockerfileを作成します
```Dockerfile:containers/postgres/Dockerfile
FROM postgres:16.2

```

## docker-compose.ymlの作成
GoとPostgresをdocker-composeを使って起動させます
```docker-compose.yml
services:
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/go/Dockerfile
    volumes:
      - ./application:/usr/local/go/src/gin-crm
    ports:
      - '8000:8000'
    command: air -c .air.toml
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
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
      - '5432:5432' # デバッグ用
volumes:
  db_data:

```

### .envファイルの作成
POSTGRESとPrisma用の環境変数を.envファイルに記載します
```.env
POSTGRES_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=db
DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres?schema=public
```

```
docker compose up -d --build
```
を実行後、以下のようにコンテナが起動できれば成功です
```
❯ docker ps -a
CONTAINER ID   IMAGE                    COMMAND                   CREATED       STATUS                 PORTS                                            NAMES
a80d2d9c46b1   gin-crm-app              "air -c .air.toml"        3 hours ago   Up 3 hours             0.0.0.0:8000->8000/tcp, 0.0.0.0:8080->8080/tcp   app
eb4f6f3e1a5f   gin-crm-db               "docker-entrypoint.s…"   3 hours ago   Up 3 hours (healthy)   0.0.0.0:5432->5432/tcp                           db
```

## Prismaの初期設定
### schemaの設定
今回はUser用のModelを作成します
```typescript:schema.prisma
datasource db {
    provider = "postgresql"
    url      = env("DATABASE_URL")
}

generator db {
    provider = "go run github.com/steebchen/prisma-client-go"
}

model User {
    id              Int             @id @default(autoincrement())
    name            String          @db.VarChar(255)
    employee_number String          @unique @db.VarChar(8)
    email           String          @unique
    password        String          @db.VarChar(255)
    role            Role            @default(ADMIN)
    is_active       Boolean         @default(true)
    is_verified     Boolean         @default(false)
    is_superuser    Boolean         @default(false)
    createdAt       DateTime        @default(now())
    updatedAt       DateTime        @updatedAt
}

enum Role {
    ADMIN
    GENERAL
}

```

### migrationの実行
schemaの設定後、以下のコマンドでmigrationを行います

```
docker compose exec app go run github.com/steebchen/prisma-client-go db push
Prisma schema loaded from prisma/schema.prisma
Datasource "db": PostgreSQL database "postgres", schema "public" at "db:5432"

Your database is now in sync with your schema.

✔ Generated Prisma Client Go to ./prisma/db in 1.18s
```

以下のようにUserのテーブルが作成されたら成功です
```
postgres=# \d
                  List of relations
 Schema |         Name         |   Type   |  Owner   
--------+----------------------+----------+----------
 public | User                 | table    | postgres
 public | User_id_seq          | sequence | postgres
(6 rows)
```

## テストデータの作成
seed.goにテストデータを作成するスクリプトを記載します
```go
client := db.NewClient()
```
でPrisma Clientを初期化した後にPrisma Clientを使ってDBと接続します
今回はPrismaのUpsertを使って該当するメールアドレスのUserがあれば更新、なければ新規作成します

https://goprisma.org/docs/walkthrough/upsert

```seed.go
package main

import (
	"context"
	"log"

	"github.com/shun198/gin-crm/config"
	"github.com/shun198/gin-crm/prisma/db"
)

func main() {
	// Prismaクライアントの初期化
	client := db.NewClient()

	// データベースに接続
	err := client.Prisma.Connect()
	if err != nil {
		log.Fatalf("データベースとの接続に失敗しました: %v", err)
	}
	defer func() {
		if err := client.Prisma.Disconnect(); err != nil {
			log.Fatalf("データベースの接続の切断に失敗しました: %v", err)
		}
	}()

	password, err := config.HashPassword("test")
	if err != nil {
		log.Fatalf("パスワードのハッシュ化に失敗しました: %v", err)
	}

	// ユーザーを作成または更新
	_, err = client.User.UpsertOne(
		db.User.Email.Equals("test01@example.com"),
	).
		Create(
			db.User.Name.Set("テストユーザゼロイチ"),
			db.User.EmployeeNumber.Set("00000001"),
			db.User.Email.Set("test01@example.com"),
			db.User.Password.Set(password),
			db.User.Role.Set("ADMIN"),
			db.User.IsActive.Set(true),
			db.User.IsVerified.Set(false),
			db.User.IsSuperuser.Set(false),
		).
		Update(
			db.User.Name.Set("テストユーザゼロイチ"),
			db.User.Password.Set(password),
			db.User.Role.Set("ADMIN"),
			db.User.IsActive.Set(true),
			db.User.IsVerified.Set(false),
			db.User.IsSuperuser.Set(false),
		).
		Exec(context.TODO())
	_, err = client.User.UpsertOne(
		db.User.Email.Equals("test02@example.com"),
	).
		Create(
			db.User.Name.Set("テストユーザゼロニ"),
			db.User.EmployeeNumber.Set("00000002"),
			db.User.Email.Set("test02@example.com"),
			db.User.Password.Set(password),
			db.User.Role.Set("GENERAL"),
			db.User.IsActive.Set(true),
			db.User.IsVerified.Set(false),
			db.User.IsSuperuser.Set(false),
		).
		Update(
			db.User.Name.Set("テストユーザゼロニ"),
			db.User.Password.Set(password),
			db.User.Role.Set("GENERAL"),
			db.User.IsActive.Set(true),
			db.User.IsVerified.Set(false),
			db.User.IsSuperuser.Set(false),
		).
		Exec(context.TODO())
	if err != nil {
		log.Fatalf("ユーザーの作成に失敗しました: %v", err)
	}

	log.Println("テストデータの作成が完了しました")
}

```

パスワードのハッシュ化はbcryptを使って行います
```config/passwordManagement.go
package config

import "golang.org/x/crypto/bcrypt"

func HashPassword(password string) (string, error) {
	result, err := bcrypt.GenerateFromPassword([]byte(password), 15)
	return string(result), err
}
```

以下のようにseed.goが正常に実行され、テストデータが作成されたら成功です

```
docker compose exec app go run prisma/seed.go
2024/05/29 02:42:01 テストデータの作成が完了しました
```

```
SELECT * FROM "User";
 id |         name         | employee_number |       email        |                           password                           |  role   | is_active | is_verified | is_superuser |        createdAt        |        updatedAt        
----+----------------------+-----------------+--------------------+--------------------------------------------------------------+---------+-----------+-------------+--------------+-------------------------+-------------------------
  1 | テストユーザゼロイチ | 00000001        | test01@example.com | $2a$15$cQ46un1.FcUGgIvj.QCtV.4P9GYHe3nAlVr9lnp7Bsbz6IH7J4F/G | ADMIN   | t         | f           | f            | 2024-05-29 00:17:00.312 | 2024-05-29 02:42:01.476
  2 | テストユーザゼロニ   | 00000002        | test02@example.com | $2a$15$cQ46un1.FcUGgIvj.QCtV.4P9GYHe3nAlVr9lnp7Bsbz6IH7J4F/G | GENERAL | t         | f           | f            | 2024-05-29 00:17:00.337 | 2024-05-29 02:42:01.496
(2 rows)
```

## Prisma Clientと接続
main.goにPrisma ClientとDBを接続する設定を記載します
```main.go
package main

import (
	"log"

	"github.com/gin-gonic/gin"
	database "github.com/shun198/gin-crm/config"
	"github.com/shun198/gin-crm/routes"
)

func main() {
	r := gin.Default()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())
	client, err := database.StartDatabase()
	if err != nil {
		log.Fatal("データベースとの接続に失敗しました:%v", err)
	}
	defer func() {
		if err := client.Prisma.Disconnect(); err != nil {
			log.Fatal("データベースの接続の切断に失敗しました:%v", err)
		}
	}()
	routes.GetUserRoutes(r, client)
	r.Run(":8000")
}

```

```config/database.go
package config

import (
	"github.com/shun198/gin-crm/prisma/db"
)

func StartDatabase() (*db.PrismaClient, error) {
	client := db.NewClient()
	if err := client.Prisma.Connect(); err != nil {
		return nil, err
	}
	return client, nil
}

```

## Prismaを使った一覧表示APIの作成
今回は`127.0.0.1:8000/api/admin/users`へGETリクエストを送るとユーザの一覧が表示されるAPIを作成します

まずはroutes.goにルーティングの設定を行います
```routes.go
package routes

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/shun198/gin-crm/controllers"
	"github.com/shun198/gin-crm/prisma/db"
)

func GetUserRoutes(router *gin.Engine, client *db.PrismaClient) *gin.Engine {
	userRoutes := router.Group("/api/admin/users")
	{
		userRoutes.GET("", func(c *gin.Context) {
			controllers.GetAllUsers(c, client)
		})
	}
	return router
}
```

次にcontrollerを作成してステータスコードとUserの一覧を返すよう設定します
```controllers.go
package controllers

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/shun198/gin-crm/prisma/db"
	"github.com/shun198/gin-crm/services"
)

func GetAllUsers(c *gin.Context, client *db.PrismaClient) {
	users, err := services.GetAllUsers(client)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": err.Error()})
		return
	}
	c.JSON(http.StatusOK, users)
}

```

最後はservicesにPrisma Clientを使ってUserテーブルから一覧を取得するロジックを作成します
PrismaのFindManyメソッドを使ってUserの配列を取得します
また、今回は
- スーパーユーザ
- パスワード

のfieldを非表示にしたいのでOmitを使用します

https://goprisma.org/docs/walkthrough/find#find-many-records

https://goprisma.org/docs/walkthrough/fields#omit

```services.go
package services

import (
	"context"
	"strconv"

	"github.com/shun198/gin-crm/prisma/db"
)

func GetAllUsers(client *db.PrismaClient) ([]db.UserModel, error) {
	users, err := client.User.FindMany().Omit(
		db.User.Password.Field(),
		db.User.IsSuperuser.Field(),
	).Exec(context.Background())
	return users, err
}

```

## 実際に実行してみよう！
以下のようにAPIへリクエストを送るとユーザの一覧が表示されたら成功です

![スクリーンショット 2024-05-29 9.17.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/aa140a7c-a396-6656-9235-0c3e3ad5e862.png)

## 参考
https://goprisma.org/docs/getting-started/quickstart

https://goprisma.org/docs/reference/client/options

https://www.prisma.io/docs/orm/overview/databases/postgresql

https://goprisma.org/docs/reference/deploy/docker

https://github.com/steebchen/prisma-client-go/issues/1274
