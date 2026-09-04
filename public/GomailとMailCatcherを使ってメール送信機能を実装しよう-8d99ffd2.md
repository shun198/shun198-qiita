---
title: GomailとMailCatcherを使ってメール送信機能を実装しよう！
tags:
  - Go
  - mailcatcher
  - gin
  - docker-compose
private: false
updated_at: '2026-09-05T08:55:28+09:00'
id: 8d99ffd27f1ec81c8210
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GomailとMailCatcherのコンテナを使ってローカル上でメール送信機能を使用する方法について解説していきたいと思います

## 前提
- フレームワークはGinを使用
- 本記事はローカル環境でメール送信機能を試す方法について記載していますので本番環境では別のツールを使用してください
- compose.yamlを使ってMailCatcherを構築します

## ディレクトリ構成
```
tree
.
├── .env
├── .gitignore
├── Makefile
├── README.md
├── application
│   ├── .air.toml
│   ├── controllers.go
│   ├── emails.go
│   ├── go.mod
│   ├── go.sum
│   ├── main.go
│   └── routes.go
├── containers
│   ├── go
│   │   └── Dockerfile
│   └── postgres
│       └── Dockerfile
└── compose.yaml
```

## MailCatcherとは
> MailCatcher runs a super simple SMTP server which catches any message sent to it to display in a web interface. 

公式ドキュメントに記載されている通り簡易的なSMTPサーバでMailCatcherに送信されたメールをWebインターフェイス(Webブラウザ)に表示させることができます
本番環境ではAWSのSESを使うのでローカルでメール送信テストを行いたいときはMailCatcherを使ってみましょう

> Run mailcatcher, set your favourite app to deliver to smtp://127.0.0.1:1025 instead of your default SMTP server, then check out http://127.0.0.1:1080 to see the mail that's arrived so far.

公式ドキュメントに記載されている通り
MailCatcherのイメージを指定して
- SMTP用の1025番ポート
- Webブラウザで閲覧する用の1080番ポート
 
の2種類のポートを解放します

```compose.yaml
  mail:
    container_name: mail
    image: schickling/mailcatcher
    ports:
      - '1080:1080'
      - '1025:1025'
```

## 環境変数の設定
今回は送信元を`example@co.jp`に設定します
MAIL_HOSTはMailCatcherのコンテナのホスト名、MAIL_PORTはSMTP用の1025番ポートを指定します
```.env
MAIL_ADMIN="example@co.jp"
MAIL_HOST=mail
MAIL_PORT=1025

```

## メール送信APIの作成
今回はメール本文にようこそ！と書かれたメールを送信するAPIを作成します

```routes.go
package routes

import (
	"github.com/gin-gonic/gin"
)

func GetUserRoutes(router *gin.Engine) *gin.Engine {
	userRoutes := router.Group("/api/admin/users")
	{
		userRoutes.POST("/send_invite_user_email", func(c *gin.Context) {
			controllers.SendInviteUserEmail(c)
		})
	}
	return router
}

```

```controllers.go
package controllers

import (
	"github.com/gin-gonic/gin"
	"github.com/shun198/gin-crm/emails"
)

func SendInviteUserEmail(c *gin.Context) {
	emails.SendEmail()
}

```

Gomailを使用するのでimportします
以下のようにメール送信に必要な環境変数を.envから取得するよう設定します

```emails.go
package emails

import (
	"os"
	"strconv"

	"gopkg.in/gomail.v2"
)

func SendEmail() {
	m := gomail.NewMessage()
	m.SetHeader("From", os.Getenv("MAIL_ADMIN"))
	m.SetHeader("To", "to@example.com")
	m.SetHeader("Subject", "ようこそ")
	m.SetBody("text/html", "ようこそ!")
	m.AddAlternative("text/plain", "ようこそ!")

	host := os.Getenv("MAIL_HOST")
	port, _ := strconv.Atoi(os.Getenv("MAIL_PORT"))
	username := os.Getenv("MAIL_USERNAME")
	password := os.Getenv("MAIL_PASSWORD")

	d := gomail.NewDialer(host, port, username, password)
	if err := d.DialAndSend(m); err != nil {
		panic(err)
	}
}

```

## 実際に実行してみよう！
MailCatcherのコンテナを起動後、APIを実行し、メールを送信することに成功したら成功です
![スクリーンショット 2024-05-26 13.02.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/373f6cf6-9b7c-7ae8-f5a3-4d7d975fb3b4.png)

127.0.0.1:1080にアクセスするとメールの中身を確認することができます
![スクリーンショット 2024-05-26 9.02.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2460054d-a5f6-4077-e741-e4032bb6c790.png)

## 参考
https://github.com/go-gomail/gomail
