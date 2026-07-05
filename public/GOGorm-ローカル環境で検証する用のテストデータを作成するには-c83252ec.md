---
title: '[GO+Gorm] ローカル環境で検証する用のテストデータを作成するには？'
tags:
  - Go
  - seed
  - GORM
private: false
updated_at: '2025-07-20T10:52:29+09:00'
id: c83252ec41b457257764
organization_url_name: null
slide: false
---
## 概要
GO+Gormを使ったローカル上で検証する時のテストデータを自動で作成する方法について解説します

## 前提
- DBはPostgresを使用

## modelの定義
今回は
- User
- Todo

の2つのmodelを定義します

```models/user.go
package models

import (
	"time"
)

const (
	AdminRole   = "admin"
	GeneralRole = "general"
)

type User struct {
	ID        int       `gorm:"primaryKey" json:"id"`
	Email     string    `gorm:"unique;not null" json:"email" validate:"required,email"`
	Username  string    `gorm:"not null" json:"username" validate:"required"`
	Password  string    `gorm:"not null" json:"password" validate:"required"`
	Role      string    `gorm:"not null" json:"role" validate:"required,oneof=admin general"`
	CreatedBy int       `gorm:"not null" json:"created_by" validate:"required"`
	UpdatedBy int       `gorm:"not null" json:"updated_by" validate:"required"`
	IsActive  bool      `gorm:"default:true;not null" json:"is_active"`
	CreatedAt time.Time `gorm:"autoCreateTime;not null" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

```

```models/todo.go
package models

type Todo struct {
	ID          int    `gorm:"primaryKey" json:"id"`
	Title       string `gorm:"not null" json:"title" validate:"required"`
	Description string `gorm:"not null" json:"description" validate:"required"`
	IsStarred   bool   `gorm:"default:false;not null" json:"is_starred"`
	IsCompleted bool   `gorm:"default:false;not null" json:"is_completed"`
}

```

## Gormの設定
GormとDB(Postgres)と接続する設定を記載します
gormのDBのstructureはAPIの作成や今回のテストデータ作成時に使用するのでポインタ型として定義してます

```database.go
package database

import (
	"fmt"
	"log"
	"os"

	"gorm.io/driver/postgres"
	"gorm.io/gorm"
)

var DB *gorm.DB

type DBConfig struct {
	User     string
	Password string
	Host     string
	Port     string
	DBName   string
	SSLMode  string
}

func getDBConfig() *DBConfig {
	return &DBConfig{
		User:     os.Getenv("POSTGRES_USER"),
		Password: os.Getenv("POSTGRES_PASSWORD"),
		Host:     os.Getenv("POSTGRES_HOST"),
		Port:     os.Getenv("POSTGRES_PORT"),
		DBName:   os.Getenv("POSTGRES_NAME"),
		SSLMode:  os.Getenv("POSTGRES_SSLMODE"),
	}
}

func (c *DBConfig) buildDSN() string {
	// ローカルと本番とでsslmodeの設定を変える
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=%s",
		c.User, c.Password, c.Host, c.Port, c.DBName, c.SSLMode,
	)
}

func InitDB() {
	config := getDBConfig()
	dsn := config.buildDSN()

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		TranslateError: true, // エラー翻訳機能を有効化
	})
	if err != nil {
		log.Fatalf("データベース接続失敗: %v", err)
	}

	DB = db
	log.Println("データベース接続に成功しました")
}
```

## テストデータの用意
- User
- Todo

のテストデータを用意します
modelのスライスをreturnします

```seeds/user.go
package seed

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
)

func CreateUserLocalData() []models.User {

	return []models.User{
		// システム管理者
		{
			ID:        1,
			Email:     "system1@example.com",
			Username:  "システム管理者1",
			Password:  "test",
			Role:      models.AdminRole,
			CreatedBy: 1,
			UpdatedBy: 1,
			IsActive:  true,
		},
		{
			ID:        2,
			Email:     "system2@example.com",
			Username:  "システム管理者2",
			Password:  "test",
			Role:      models.AdminRole,
			CreatedBy: 1,
			UpdatedBy: 1,
			IsActive:  true,
		},
	}
}

```

```seeds/todo.go
package seed

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
)

func CreateTodoLocalData() []models.Todo {

	return []models.Todo{
		{
			ID:          1,
			Title:       "タスク1",
			Description: "タスク詳細1",
			IsStarred:   false,
			IsCompleted: false,
		},
		{
			ID:          2,
			Title:       "タスク2",
			Description: "タスク詳細2",
			IsStarred:   true,
			IsCompleted: false,
		},
		{
			ID:          3,
			Title:       "タスク3",
			Description: "タスク詳細3",
			IsStarred:   true,
			IsCompleted: true,
		},
	}
}

```

## テストデータの作成処理
テストデータの作成処理を作成します
まず、database.goで作成したDBとの接続処理を記載します
その後、for loopでGormを使ってテストデータを作成していきます

```seed.go
package main

import (
	"log"

	seed "github.com/shun198/golang-clean-architecture/internal/domains/seeds"
	database "github.com/shun198/golang-clean-architecture/internal/infrastructures/databases"
	"golang.org/x/crypto/bcrypt"
)

func hashPassword(password string) string {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(password), bcrypt.DefaultCost)
	if err != nil {
		log.Fatalf("パスワードのハッシュ化に失敗しました: %v", err)
	}
	return string(hashedPassword)
}

func main() {
	database.InitDB()

	users := seed.CreateUserLocalData()
	usersSuccessCount := 0

	for i := range users {
		users[i].Password = hashPassword(users[i].Password)
		if err := database.DB.Create(&users[i]).Error; err != nil {
			log.Printf("システムユーザの作成に失敗しました: %v", err)
			continue
		}
		usersSuccessCount++
	}

	if usersSuccessCount > 0 {
		log.Printf("システムユーザのテストデータを %d 件作成しました", usersSuccessCount)
	}

	todos := seed.CreateTodoLocalData()
	todosSuccessCount := 0

	for i := range todos {
		if err := database.DB.Create(&todos[i]).Error; err != nil {
			log.Printf("Todoの作成に失敗しました: %v", err)
			continue
		}
		todosSuccessCount++
	}

	if todosSuccessCount > 0 {
		log.Printf("Todoのテストデータを %d 件作成しました", todosSuccessCount)
	}
}

```

## 実際に作成してみよう！
以下のようにコマンドを実行し、テストデータが作成されたら成功です

```
go run ./cmd/seed/seed.go
2025/07/20 01:50:43 データベース接続に成功しました
2025/07/20 01:50:43 システムユーザのテストデータを 2 件作成しました
2025/07/20 01:50:43 Todoのテストデータを 3 件作成しました
```

```
postgres=# SELECT * FROM users;
 id |        email        |    username     |                           password                           | role  | created_by | updated_by | is_active |          created_at           |          updated_at           
----+---------------------+-----------------+--------------------------------------------------------------+-------+------------+------------+-----------+-------------------------------+-------------------------------
  1 | system1@example.com | システム管理者1 | $2a$10$Z.9LRVsW.BV/xgszyCz8reIxbzsUQv3hmWLp/BcioiW5hzUZHrfMW | admin |          1 |          1 | t         | 2025-07-20 01:50:43.211705+00 | 2025-07-20 01:50:43.211705+00
  2 | system2@example.com | システム管理者2 | $2a$10$6XEWXZ7NTaiRNTo14z6gpO9yAQt23FAvULtfJOOrW8M1YAyQS50Li | admin |          1 |          1 | t         | 2025-07-20 01:50:43.326529+00 | 2025-07-20 01:50:43.326529+00
(2 rows)

postgres=# SELECT * FROM todos;
 id |  title  | description | is_starred | is_completed 
----+---------+-------------+------------+--------------
  1 | タスク1 | タスク詳細1 | f          | f
  2 | タスク2 | タスク詳細2 | t          | f
  3 | タスク3 | タスク詳細3 | t          | t
(3 rows)
```
