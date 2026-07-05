---
title: GO+Gorm+Ginを使ってPaginationを実装するには？
tags:
  - Go
  - GORM
  - gin
private: false
updated_at: '2025-07-21T10:31:30+09:00'
id: d85327614713cd383f67
organization_url_name: null
slide: false
---
## 概要
一覧表示APIを作成する際にGO+Gorm+Ginを使ってPaginationを実装する方法について解説します

## 前提
- CleanArchitectureの構成で作成しています
- Paginationのデフォルトの件数を20で実装します

## ディレクトリ構成
```
.
└── backend
    ├── cmd
    │   └── app
    │       └── main.go
    ├── go.mod
    ├── go.sum
    └── internal
        ├── domains
        │   ├── models
        │   │   └── user.go
        │   └── seeds
        │       └── user.go
        ├── infrastructures
        │   ├── databases
        │   │   └── database.go
        │   └── migrations
        │       └── migration.go
        ├── presentation
        │   │   └── user_handler.go
        │   ├── requests
        │   │   └── user_request.go
        │   └── responses
        │       └── user_response.go
        ├── repositories
        │   └── user_repository.go
        ├── routes
        │   └── routes.go
        └── usecases
            └── user_usecase.go

```

## 実装
### modelの作成
以下のようにmodelを作成します

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
	IsActive  bool      `gorm:"default:true;not null" json:"is_active"`
	CreatedAt time.Time `gorm:"autoCreateTime;not null" json:"created_at"`
	UpdatedAt time.Time `gorm:"autoUpdateTime" json:"updated_at"`
}

type ListUsersResult struct {
	Users []User
	Total int64
}
```

### クエリパラメータの設定
以下のようにクエリパラメータ用のstructureを作成します
Limitが表示件数、Offsetが取得を開始するデータの位置を指定する数値です

```user_request.go
package requests

type ListUsersQuery struct {
	Limit    int    `form:"limit" binding:"gte=0,max=100"`
	Offset   int    `form:"offset" binding:"gte=0"`
}
```

### レスポンスの設定
一覧表示用のレスポンスのstructureを作成します
ユーザごとにUsersResponseの形で返し、
- Count(DB内のUserの総件数)
- Length(実際に返ってくるユーザ数。今回だとPaginationがデフォルトで20なので最大20)
- Usersの配列

を一覧表示時にまとめてレスポンスとして返します

```user_response.go
package responses

import "time"

type UsersResponse struct {
	ID        int       `json:"id"`
	Email     string    `json:"email"`
	Username  string    `json:"username"`
	Role      string    `json:"role"`
	IsActive  bool      `json:"is_active"`
	CreatedAt time.Time `json:"created_at"`
	UpdatedAt time.Time `json:"updated_at"`
}

type ListUsersResponse struct {
	Count  int64           `json:"count"`
	Length int             `json:"length"`
	Users  []UsersResponse `json:"users"`
}
```

### handlerの作成
一覧表示用のhandlerを作成します
まず、GinのShouldBindQueryメソッドでクエリ文字列をcontextにバインドします
該当しないクエリパラメータである場合は400を返します
query.limitが0(クエリパラメータを使用しない)の場合はデフォルトでlimit=20になります
userUsecaseからUserを指定したクエリパラメータで取得した後はmakeを使ってUserの数分だけあらかじめsliceを作成しておきます
その後、for文を使って作成しておいたsliceにUser情報を入れてUsersResponseの形でレスポンスを返します

```user_handler.go
package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/shun198/golang-clean-architecture/internal/presentation/requests"
	"github.com/shun198/golang-clean-architecture/internal/presentation/responses"
	usecase "github.com/shun198/golang-clean-architecture/internal/usecases"
)

type UserHandler struct {
	userUsecase usecase.IUserUsecase
}

func NewUserHandler(userUsecase usecase.IUserUsecase) *UserHandler {
	return &UserHandler{
		userUsecase: userUsecase,
	}
}

func (h *UserHandler) GetUsers(c *gin.Context) {
	var query requests.ListUsersQuery
	if err := c.ShouldBindQuery(&query); err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"error": err.Error(),
		})
		return
	}

	if query.Limit == 0 {
		query.Limit = 20
	}

	results, err := h.userUsecase.GetAllUsers(query)
	if err != nil {
		c.JSON(http.StatusBadGateway, gin.H{
			"error": err.Error(),
		})
		return
	}
	users := make([]responses.UsersResponse, len(results.Users))
	for i, user := range results.Users {
		users[i] = responses.UsersResponse{
			ID:        user.ID,
			Email:     user.Email,
			Username:  user.Username,
			Role:      user.Role,
			IsActive:  user.IsActive,
			CreatedAt: user.CreatedAt,
			UpdatedAt: user.UpdatedAt,
			CreatedBy: user.CreatedBy,
			UpdatedBy: user.UpdatedBy,
		}
	}

	c.JSON(http.StatusOK, responses.ListUsersResponse{
		Count:  results.Total,
		Length: len(results.Users),
		Users:  users,
	})
}
```

### usecaseの作成
usecaseを使ってUserUsecaseのレシーバからuserRepositoryのGetAllメソッドを実行します

```user_usecase.go
package usecase

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
	"github.com/shun198/golang-clean-architecture/internal/presentation/requests"
	repository "github.com/shun198/golang-clean-architecture/internal/repositories"
)

type IUserUsecase interface {
    GetAllUsers(params requests.ListUsersQuery) (*models.ListUsersResult, error)
}

type UserUsecase struct {
	userRepository repository.IUserRepository
}

func NewUserUsecase(userRepository repository.IUserRepository) *UserUsecase {
	return &UserUsecase{
		userRepository: userRepository,
	}
}

func (u *UserUsecase) GetAllUsers(params requests.ListUsersQuery) (*models.ListUsersResult, error) {
	return u.userRepository.GetAll(params)
}
```

### repositoryの作成
クエリパラメータのOffsetとLimitを使ってusersのスライスを取得し、UsersとTotalを返します

```user_repository.go
package repository

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
	"github.com/shun198/golang-clean-architecture/internal/presentation/requests"
	"gorm.io/gorm"
)

type IUserRepository interface {
	GetAll(params requests.ListUsersQuery) (*models.ListUsersResult, error)
}

type UserRepository struct {
	db *gorm.DB
}

func NewUserRepository(db *gorm.DB) IUserRepository {
	return &UserRepository{
		db: db,
	}
}

func (r *UserRepository) GetAll(params requests.ListUsersQuery) (*models.ListUsersResult, error) {
	var users []models.User
	var total int64
	query := r.db.Model(&models.User{})
    query = query.Order("id ASC")
	if err := query.Count(&total).Error; err != nil {
		return nil, err
	}
	if err := query.Offset(params.Offset).Limit(params.Limit).Find(&users).Error; err != nil {
		return nil, err
	}
	return &models.ListUsersResult{
		Users: users,
		Total: total,
	}, nil
}

```

## 実際に実行してみよう！
あらかじめユーザを25人作成した後、クエリパラメータに何も設定しないでAPIを実行します
デフォルトでPaginationが20件になるので以下のようにcountが25件、lengthが20件になれば成功です

![スクリーンショット 2025-07-21 10.15.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/66e216a6-965a-4098-b8e1-109e4e940759.png)

limit=10のクエリパラメータを追加した状態でAPIを実行し、countが25件、lengthが10件になれば成功です
![スクリーンショット 2025-07-21 10.16.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/929c0e73-c4f2-4a24-b631-2cc9fcaa5784.png)

limit=10、offsetのクエリパラメータを追加した状態でAPIを実行し、countが25件、lengthが10件、11番目のユーザから表示されたら成功です
![スクリーンショット 2025-07-21 10.28.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fd70bd25-f021-4d6a-b7cb-f0e7101b17ea.png)

## 参考
https://gin-gonic.com/ja/docs/examples/only-bind-query-string/

https://gorm.io/ja_JP/docs/query.html#Limit-Offset
