---
title: GO+Gin+Gormを使ったアプリケーションをClean Architectureで実装してみた
tags:
  - Go
  - GORM
  - gin
  - CleanArchitecture
private: false
updated_at: '2025-07-21T09:39:26+09:00'
id: 918e3416caefd7d43e9e
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GO/Gin/GormでTODOアプリを作る際にClean Architectureを意識して実装してみたので解説します

## 前提
- DBはPostgresを使用

## Clean Architectureとは？
下記図のように「関心の分離」に基づいてレイヤー構造に分ける設計パターンの一つです
中心にビジネスロジックを据え、外側に技術的な要素を配置するのが特徴です

![スクリーンショット 2025-04-29 10.31.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bc5db4f7-d08c-4855-97d9-d898908e46f5.png)

### 各レイヤーの役割
- Entities（エンティティ）
    - ビジネスロジックを中心に記載
- Use Cases（ユースケース）
    - エンティティと組み合わせて、アプリの振る舞いを記載
- Interface Adapters（インターフェース層）
    - 外部の仕組み（フレームワーク、DBなど）とユースケースの橋渡し方法を記載
- Frameworks & Drivers（フレームワーク・ドライバ）
    - 実際のWebフレームワーク（FastAPIなど）、ORM（SQLAlchemyなど）、DB、外部サービス(メールサーバ、ファイルストレージ)との接続などを記載
    - 最も外側に位置し、アプリのコアには影響を与えないように設計する

Clean Architectureでアプリケーションを設計することで依存関係を円の内側へ向かいように設計することでビジネスロジックを技術的な変更から隔離でき、柔軟性やテスト性が向上し、保守性が上がると言われています

## ディレクトリ構成
今回は以下のようにアプリケーションを作成します
GOではinternalというディレクトリ内にprivateのパッケージを入れることが一般的なのでinternal内にアプリケーションのソースコードを配置します
また、コマンドやエントリーポイント(main.go)はcmdディレクトリ内に配置します

https://go.dev/doc/go1.4#internalpackages

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
        │   │   └── todo.go
        │   └── seeds
        │       └── todo.go
        ├── infrastructures
        │   ├── databases
        │   │   └── database.go
        │   └── migrations
        │       └── migration.go
        ├── presentation
        │   │   └── todo_handler.go
        │   ├── requests
        │   │   └── todo_request.go
        │   └── responses
        │       └── todo_response.go
        ├── repositories
        │   └── todo_repository.go
        ├── routes
        │   └── routes.go
        └── usecases
            └── todo_usecase.go
```

各レイヤーに対応するフォルダ名は以下のとおりです

|レイヤー|対応するフォルダ名|説明|
|---|---|---|
|Entities|models, repositories|models はドメインモデル（Entity）、repositories はそれに対する操作を定義するため、実質的にEntityに関係する|
|Use Cases|usecases|アプリケーションの振る舞いの中心。依存注入でRepositoryを呼ぶ|
|Interface Adapters|handlers, routes|handlers はDTO、routers はAPIのエンドポイント定義（Controllerに相当する）|
|Frameworks & Drivers|infrastructure, config|DB接続やSlack連携などの外部技術依存を実装。config もインフラ寄り|

## 実装例
### Entity(Model)の作成
以下のようにTodoのModelを作成します

```internal/domains/models/todo.go
package models

type Todo struct {
	ID          int    `gorm:"primaryKey" json:"id"`
	Title       string `gorm:"not null" json:"title" validate:"required"`
	Description string `gorm:"not null" json:"description" validate:"required"`
	IsStarred   bool   `gorm:"default:false;not null" json:"is_starred"`
	IsCompleted bool   `gorm:"default:false;not null" json:"is_completed"`
}
```

### Request/Responseのschemaの設定
Request/Response時のバリデーションの設定を行います
```internal/presentation/requests/todo_request.go
package requests

type CreateTodoRequest struct {
	Title       string `json:"title" binding:"required"`
	Description string `json:"description" binding:"required"`
}

type UpdateTodoRequest struct {
	Title       string `json:"title" binding:"required"`
	Description string `json:"description" binding:"required"`
	IsStarred   bool   `json:"is_starred" binding:"required"`
	IsCompleted bool   `json:"is_completed" binding:"required"`
}
```

```internal/presentation/requests/todo_response.go
package responses

type TodoResponse struct {
	ID          int    `json:"id"`
	Title       string `json:"title"`
	Description string `json:"description"`
	IsStarred   bool   `json:"is_starred"`
	IsCompleted bool   `json:"is_completed"`
}
```

### config/infrastructureファイル群
ORMとDBの接続設定を記載します

```internal/infrastructures/databases/database.go
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
	return fmt.Sprintf(
		"postgres://%s:%s@%s:%s/%s?sslmode=%s",
		c.User, c.Password, c.Host, c.Port, c.DBName, c.SSLMode,
	)
}

func InitDB() {
	config := getDBConfig()
	dsn := config.buildDSN()

	db, err := gorm.Open(postgres.Open(dsn), &gorm.Config{
		TranslateError: true,
	})
	if err != nil {
		log.Fatalf("データベースへの接続に失敗しました: %v", err)
	}

	DB = db
	log.Println("データベースへの接続に成功しました")
}
```

### handler
どのusecaseを使用するか、どういったリクエストを受け付け、レスポンスを返すか、ルーティングをどうするか、などを定義します

routes.goでは後述する各レイヤー(NewTodoRepository、NewTodoUsecase、NewTodoHandler)のインスタンスを作成し、DIを実現します
handler内に各ルートを定義しています

```internal/routes/routes.go
package routes

import (
	"github.com/gin-gonic/gin"
	database "github.com/shun198/golang-clean-architecture/internal/infrastructures/databases"
	"github.com/shun198/golang-clean-architecture/internal/presentation/handlers"
	repository "github.com/shun198/golang-clean-architecture/internal/repositories"
	usecase "github.com/shun198/golang-clean-architecture/internal/usecases"
)

func SetupRoutes(r *gin.Engine) {
	const apiBase = "/api"
	publicRoutes := r.Group(apiBase)
	setupPublicRoutes(publicRoutes)
}

func setupPublicRoutes(publicRoutes *gin.RouterGroup) {
	setupTodoPublicRoutes(publicRoutes)
}

func setupTodoPublicRoutes(publicRoutes *gin.RouterGroup) {
	todos := publicRoutes.Group("/todos")
	todoRepository := repository.NewTodoRepository(database.DB)
	todoUsecase := usecase.NewTodoUsecase(todoRepository)
	todoHandler := handlers.NewTodoHandler(todoUsecase)
	todos.GET("", todoHandler.GetTodos)
	todos.POST("", todoHandler.CreateTodo)
	todos.GET("/:id", todoHandler.GetTodo)
	todos.PUT("/:id", todoHandler.UpdateTodo)
	todos.DELETE("/:id", todoHandler.DeleteTodo)
}
```

TodoHandlerにはtodoUsecaseのfieldを定義します
NewTodoHandlerはITodoUseCase(TodoUseCaseのInterface)を受け取り、TodoHandlerのポインタを返します
各APIはTodoHandlerのポインタレシーバとして定義されており、UseCaseにアクセスします

```internal/presentation/handlers/todo_handler.go
package handlers

import (
	"net/http"
	"strconv"

	"github.com/gin-gonic/gin"
	"github.com/shun198/golang-clean-architecture/internal/presentation/requests"
	"github.com/shun198/golang-clean-architecture/internal/presentation/responses"
	usecase "github.com/shun198/golang-clean-architecture/internal/usecases"
)

type TodoHandler struct {
	todoUsecase usecase.ITodoUsecase
}

func NewTodoHandler(todoUsecase usecase.ITodoUsecase) *TodoHandler {
	return &TodoHandler{
		todoUsecase: todoUsecase,
	}
}

func (h *TodoHandler) GetTodos(c *gin.Context) {
	results, err := h.todoUsecase.GetAllTodos()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}
	var todos []responses.TodoResponse
	for _, todo := range results {
		todos = append(todos, responses.TodoResponse{
			ID:          todo.ID,
			Title:       todo.Title,
			Description: todo.Description,
			IsStarred:   todo.IsStarred,
			IsCompleted: todo.IsCompleted,
		})
	}

	c.JSON(http.StatusOK, todos)
}

func (h *TodoHandler) CreateTodo(c *gin.Context) {
	var req requests.CreateTodoRequest
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}
	todo, err := h.todoUsecase.CreateTodo(req)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}

	c.JSON(http.StatusCreated, responses.TodoResponse{
		ID:          todo.ID,
		Title:       todo.Title,
		Description: todo.Description,
		IsStarred:   todo.IsStarred,
		IsCompleted: todo.IsCompleted,
	})
}

func (h *TodoHandler) GetTodo(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id is not a valid integer",
		})
		return
	}
	todo, err := h.todoUsecase.GetTodo(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "todo not found",
		})
		return
	}
	c.JSON(http.StatusOK, responses.TodoResponse{
		ID:          todo.ID,
		Title:       todo.Title,
		Description: todo.Description,
		IsStarred:   todo.IsStarred,
		IsCompleted: todo.IsCompleted,
	})
}

func (h *TodoHandler) UpdateTodo(c *gin.Context) {
	var req requests.UpdateTodoRequest
	if err := c.ShouldBind(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id is not a valid integer",
		})
		return
	}
	todo, err := h.todoUsecase.GetTodo(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "todo not found",
		})
		return
	}
	updated_todo, err := h.todoUsecase.UpdateTodo(req, todo)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}
	c.JSON(http.StatusOK, responses.TodoResponse{
		ID:          updated_todo.ID,
		Title:       updated_todo.Title,
		Description: updated_todo.Description,
		IsStarred:   updated_todo.IsStarred,
		IsCompleted: updated_todo.IsCompleted,
	})
}

func (h *TodoHandler) DeleteTodo(c *gin.Context) {
	id, err := strconv.Atoi(c.Param("id"))
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": "id is not a valid integer",
		})
		return
	}
	_, err = h.todoUsecase.GetTodo(id)
	if err != nil {
		c.JSON(http.StatusNotFound, gin.H{
			"error": "todo not found",
		})
		return
	}
	_, err = h.todoUsecase.DeleteTodo(id)
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{
			"error": err.Error(),
		})
		return
	}
	c.Status(http.StatusNoContent)
}

```

### usecase
usecaseにビジネスロジックを集約します
TodoUsecase、todoRepositoryのfieldを定義します
NewTodoUsecaseはITodoRepository(TodoRepositoryのInterface)を受け取り、TodoUsecaseのポインタを返します
各UsecaseはTodoUsecaseのポインタレシーバとして定義されており、Repositoryにアクセスします

```internal/usecases/todo_usecase.go
package usecase

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
	"github.com/shun198/golang-clean-architecture/internal/presentation/requests"
	repository "github.com/shun198/golang-clean-architecture/internal/repositories"
	"golang.org/x/crypto/bcrypt"
)

type IUserUsecase interface {
	CreateUser(req requests.CreateUserRequest, auth_user_id int) (*models.User, error)
	GetUser(id int) (*models.User, error)
	GetAllUsers(params requests.ListUsersQuery) (*models.ListUsersResult, error)
	UpdateUser(req requests.UpdateUserRequest, user *models.User, auth_user_id int) (*models.User, error)
	DeleteUser(id int) (*models.User, error)
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

func (u *UserUsecase) CreateUser(req requests.CreateUserRequest, auth_user_id int) (*models.User, error) {
	hashedPassword, err := bcrypt.GenerateFromPassword([]byte(req.Password), bcrypt.DefaultCost)
	if err != nil {
		return nil, err
	}

	user := &models.User{
		Email:     req.Email,
		Username:  req.Username,
		Password:  string(hashedPassword),
		Role:      req.Role,
		CreatedBy: auth_user_id,
		UpdatedBy: auth_user_id,
	}
	return u.userRepository.Create(user)
}

func (u *UserUsecase) GetUser(id int) (*models.User, error) {
	return u.userRepository.GetOne(id)
}

func (u *UserUsecase) UpdateUser(req requests.UpdateUserRequest, user *models.User, auth_user_id int) (*models.User, error) {
	user.Email = req.Email
	user.Username = req.Username
	user.Role = req.Role
	user.UpdatedBy = auth_user_id
	return u.userRepository.Update(user)
}

func (u *UserUsecase) DeleteUser(id int) (*models.User, error) {
	return u.userRepository.DeleteOne(id)
}

```

### repository
最後に、repository内にDBから必要なデータを取得する方法を記載していきます
TodoRepositoryを定義し、db(Gorm)のfieldを定義します
NewTodoRepositoryはdb(Gorm)のポインタアドレスを受け取り、TodoRepositoryのポインタを返します
各メソッド内のTodoRepositoryはポインタレシーバとして定義されており、Gormを使ったDBへのアクセス処理を行っています

```internal/repositories/todo_repository.go
package repository

import (
	"github.com/shun198/golang-clean-architecture/internal/domains/models"
	"gorm.io/gorm"
)

type ITodoRepository interface {
	Create(*models.Todo) (*models.Todo, error)
	GetOne(id int) (*models.Todo, error)
	GetAll() ([]models.Todo, error)
	Update(*models.Todo) (*models.Todo, error)
	DeleteOne(id int) (*models.Todo, error)
}

type TodoRepository struct {
	db *gorm.DB
}

func NewTodoRepository(db *gorm.DB) ITodoRepository {
	return &TodoRepository{
		db: db,
	}
}

func (r *TodoRepository) GetAll() ([]models.Todo, error) {
	var todos []models.Todo
	if err := r.db.Find(&todos).Error; err != nil {
		return nil, err
	}
	return todos, nil
}

func (r *TodoRepository) Create(todo *models.Todo) (*models.Todo, error) {
	if err := r.db.Create(todo).Error; err != nil {
		return nil, err
	}
	return todo, nil
}

func (r *TodoRepository) GetOne(id int) (*models.Todo, error) {
	var todo models.Todo
	if err := r.db.First(&todo, id).Error; err != nil {
		return nil, err
	}
	return &todo, nil
}

func (r *TodoRepository) Update(todo *models.Todo) (*models.Todo, error) {
	if err := r.db.Save(&todo).Error; err != nil {
		return nil, err
	}
	return todo, nil
}

func (r *TodoRepository) DeleteOne(id int) (*models.Todo, error) {
	var todo models.Todo
	if err := r.db.Delete(&todo, id).Error; err != nil {
		return nil, err
	}
	return &todo, nil
}

```

## まとめ
Clean Architectureを使って実装してみましたが上記のように必ずしもやる必要がありません
プロジェクトの大きさや依存関係をどこまで切り出すかによって変わってくるのでこういう実装方法もあるんだな、って思っていただけたら幸いです

## 参考
https://postd.cc/golang-clean-archithecture/

https://github.com/bxcodec/go-clean-arch

https://medium.com/@rudrakshnanavaty/implementing-clean-architecture-in-go-5f06dd8c1596

https://qiita.com/ryoh07/items/8ebac006c5294b9b3f58

https://rightcode.co.jp/blogs/33486
