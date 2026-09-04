---
title: DockerとGormを使ってデータベース(Postgres)への接続とMigrationを実行しよう！
tags:
  - Go
  - PostgreSQL
  - Docker
  - GORM
  - docker-compose
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 24938ea52a71e39b00f3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Docker環境でGormを使ってデータベースへの接続とマイグレーションを行う方法について解説します

## 前提
- WebフレームワークはGin、DBはPostgresを使用
- GormとPostgresのドライバーをインストール済み
- Docker環境を構築している前提で解説するので今回はDockerfileとcompose.yamlの書き方については解説しませんのでご了承ください


## ディレクトリ構成
```
❯ tree
.
├── .env
├── .gitignore
├── Makefile
├── README.md
├── application
│   ├── .air.toml
│   ├── config
│   │   └── database.go
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   ├── models.go
├── containers
│   ├── go
│   │   └── Dockerfile
│   └── postgres
│       └── Dockerfile
└── compose.yaml
```

## Docker環境の構築
GolangとPostgresのコンテナを用意します

```compose.yaml
services:
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/go/Dockerfile
    volumes:
      - ./application:/usr/local/go/src/go-practice
    ports:
      - '8000:8000'
    command: air -c .air.toml
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
    networks:
      - proxynet
  db:
    container_name: db
    image: postgres:16.2
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
    networks:
      - proxynet
networks:
  proxynet:
    name: testnet
    external: false
volumes:
  db_data:

```

環境変数は.envに記載します
```.env
POSTGRES_NAME=postgres
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_PORT=5432
POSTGRES_HOST=db
```

## main.go
main.goにDBへ接続する設定を記載します
```go
db, err := config.StartDatabase()
```
からDBのインスタンスかエラーを取得し、
エラーが出力されたら処理を終了させます

```application/main.go
package main

import (
	"net/http"

	"github.com/gin-gonic/gin"
	"github.com/shun198/go-practice/config"
)

func main() {
	r := gin.Default()
	r.Use(gin.Logger())
	r.Use(gin.Recovery())
	db, err := config.StartDatabase()

	if err != nil {
		panic(err)
	}
	r.GET("/api/health", func(c *gin.Context) {
		c.JSON(http.StatusOK, gin.H{
			"msg": "pass",
		})
	})
	routes.GetUserRoutes(r, db)
	routes.GetEventRoutes(r, db)
	r.Run(":8000")
}

```

## データベースへの接続とMigrationの実行
Postgresのコンテナへ接続するよう設定します
以下のようにdsnにDBへ接続するための情報を代入します
コンテナを使用するときのホストはcompose.yamlで設定したdbを使用しています

```go
dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s",
		host, user, password, dbName, port)
```
　
その後、DBをopenにした後、Migrationを実行します

```application/config/database.go
package config

import (
	"fmt"
	"os"

	"github.com/shun198/go-practice/models"
	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

func StartDatabase() (*gorm.DB, error) {
	host := os.Getenv("POSTGRES_HOST")
	user := os.Getenv("POSTGRES_USER")
	password := os.Getenv("POSTGRES_PASSWORD")
	dbName := os.Getenv("POSTGRES_NAME")
	port := os.Getenv("POSTGRES_PORT")

	dsn := fmt.Sprintf("host=%s user=%s password=%s dbname=%s port=%s",
		host, user, password, dbName, port)
	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{})
	if err != nil {
		return nil, err
	}
	if err := migrateDatabase(db); err != nil {
		return nil, err
	}
	return db, err
}

func migrateDatabase(db *gorm.DB) error {
	return db.AutoMigrate(
		models.User{},
	)
}

```

## Modelの作成
今回はUser用のModelを作成します

```applicatin/models.go
package models

import (
	"time"
)

type User struct {
	ID             uint      `gorm:"primaryKey" json:"id"`
	EmployeeNumber string    `gorm:"uniqueIndex;not null;size:8" json:"employeeNumber"`
	Email          string    `gorm:"uniqueIndex;not null;size:255" json:"email"`
	Name           string    `gorm:"not null;size:255" json:"name"`
	Password       string    `gorm:"not null;size:255" json:"-"`
	Verified       bool      `gorm:"not null" json:"verified"`
	Role           uint8     `gorm:"not null" json:"role"`
	Disabled       bool      `gorm:"not null;default:false"`
	CreatedAt      time.Time `gorm:"- autoCreateTime" json:"-"`
	UpdatedAt      time.Time `gorm:"- autoUpdateTime" json:"-"`
	CreatedByID    *uint     `gorm:"" json:"-"`
	CreatedBy      *User     `gorm:"not null" json:"-"`
	UpdatedByID    *uint     `gorm:"" json:"-"`
	UpdatedBy      *User     `gorm:"not null" json:"-"`
}

```

## 実際にMigrationを実行してみよう！
GOのコンテナを起動すると自動的にmigrationが実行されます
以下のようにUserテーブルが作成されていたら成功です

```
postgres=# \d users
                                         Table "public.users"
     Column      |           Type           | Collation | Nullable |              Default              
-----------------+--------------------------+-----------+----------+-----------------------------------
 id              | bigint                   |           | not null | nextval('users_id_seq'::regclass)
 employee_number | character varying(8)     |           | not null | 
 email           | character varying(255)   |           | not null | 
 name            | character varying(255)   |           | not null | 
 password        | character varying(255)   |           | not null | 
 verified        | boolean                  |           | not null | 
 role            | smallint                 |           | not null | 
 disabled        | boolean                  |           | not null | false
 created_at      | timestamp with time zone |           |          | 
 updated_at      | timestamp with time zone |           |          | 
 created_by_id   | bigint                   |           |          | 
 updated_by_id   | bigint                   |           |          | 
Indexes:
    "users_pkey" PRIMARY KEY, btree (id)
    "idx_users_email" UNIQUE, btree (email)
    "idx_users_employee_number" UNIQUE, btree (employee_number)
Foreign-key constraints:
```

## 参考
https://gorm.io/docs/connecting_to_the_database.html

https://gorm.io/docs/models.html
