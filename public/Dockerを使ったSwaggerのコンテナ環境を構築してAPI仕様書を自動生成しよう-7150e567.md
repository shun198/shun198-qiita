---
title: Dockerを使ったSwaggerのコンテナ環境を構築してAPI仕様書を自動生成しよう！
tags:
  - Django
  - swagger
  - docker-compose
private: false
updated_at: '2023-08-19T19:51:49+09:00'
id: 7150e567c87d6a85a8b5
organization_url_name: null
slide: false
---
## 概要
APIの検証、ドキュメント化およびドキュメント化にSwaggerを使っているプロダクトが多いかと思います
今回はDockerを使ってSwagger用の環境を構築する方法について解説していきます

## 前提
- 今回はバックエンドのフレームワークにDjangoを使用します
    - 後述するCORSの設定に関してましてはDjangoの設定ファイル内の記載方法を解説していますがSwaggerのドキュメントの記載方法は使用しているフレームワークが違っていても参考になるかと思います
- Dockerとdocker-composeに関する基礎的な知識を有していること

## ファイル構成
```
tree
・
├── application # アプリケーションを格納する専用フォルダ
│   └── project
    │   └── settings.py # Djangoの設定ファイル
├── doc
│   └── openapi.yml
└── docker-compose.yml
```

### Swagger用のコンテナの設定
今回はdocker-compose.ymlを使ってSwaggerのコンテナを作成します

```docker-compose.yml
  # swaggerの設定
  doc:
    image: swaggerapi/swagger-ui
    container_name: doc
    # 後述するdocフォルダ内のAPI仕様書(openapi.yml)を/usr/share/nginx/html/openapi.ymlへマウントする
    volumes:
      - ./doc/openapi.yml:/usr/share/nginx/html/openapi.yml
    # openapi.ymlを指定
    environment:
      API_URL: openapi.yml
    ports:
      - 9000:8080
```

### API仕様書(openapi.yml)の作成
openapi.ymlを作成します

```doc/openapi.yml
# https://swagger.io/specification/
# openapiのバージョン。今回は
openapi: 3.1.0
# APIに関するメタデータ
info:
　　　　# プロジェクト名を記載
  title: project
  description: |-
    # プロジェクトの詳細

  version: 1.0.0
# Djangoは8000ポートを使用しているので今回は以下のように指定
servers:
  - url: http://localhost:8000/
```

### Corsの設定
アプリケーション側とSwagger側のオリジンが違うためSwaggerのコンテナからAPIへリクエストを送るとCORSエラーが発生してしまいます
![スクリーンショット 2023-08-19 9.51.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8140ebea-7fc2-0409-e7f9-5a9092a49f94.png)

そのため、Swagger側のオリジンを許可するようCORSの設定を行います

```project/settings.py
INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "rest_framework",
    "application.apps.ApplicationConfig",
    # corsheadersをINSTALLED_APPSに追加
    "corsheaders",
]

# 自身以外のオリジンのHTTPリクエスト内にクッキーを含めることを許可する
CORS_ALLOW_CREDENTIALS = True
# アクセスを許可したいURL（アクセス元）を追加
CORS_ALLOWED_ORIGINS = "localhost:9000"
# プリフライト(事前リクエスト)の設定
# 30分だけ許可
CORS_PREFLIGHT_MAX_AGE = 60 * 30
```

以下のような画面が表示されたら成功です

![スクリーンショット 2023-08-19 9.38.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c8d5a639-75a3-cb41-7b3d-1825f0f207f6.png)

## 実際にAPI仕様書を作成してみよう！
ここから以下のAPIのドキュメントを作成していきます
- ログイン
- ユーザ
    - 一覧表示
    - 詳細

### ログイン
```doc/openapi.yml
# タグ
tags:
  - name: login
    description: ログインAPI
    externalDocs:
      description: ログインについて
      url: https://qiita.com/shun198/items/067e122bb291fed2c839

  # APIのパス
  /api/login/:
    post:
      tags:
        - login
      summary: ログインAPI
      description: アプリケーションにログインする
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_number:
                  type: string
                  description: 社員番号
                  example: "00000001"
                password:
                  type: string
                  description: パスワード
                  example: "test"
              required:
                - "employee_number"
                - "password"
      responses:
        # 成功した時と失敗した時など複数以上のResponse例を記載できる
        "200":
          description: ログインに成功
          content:
            application/json:
              schema:
                type: object
              example:
                role: "MANAGEMENT"
        "400":
          description: ログインに失敗
          content:
            application/json:
              schema:
                type: object
              example:
                msg: "社員番号またはパスワードが間違っています"
```

`/api/login/`に以下に表示させたい項目を記載していきます
RequestとResponseのschemaの下に必要な項目の詳細や入力する値のデフォルト値などを設定できます

![スクリーンショット 2023-08-19 19.25.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dabde25e-da5d-7c45-1376-10efd444507f.png)

こちらはSchemaを選択すると表示されます
![スクリーンショット 2023-08-19 19.26.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5712203d-6b9a-6082-1a83-4ff30662cd6d.png)

また、タグをつけることでSwagger内にAPIの仕様の詳細のリンクを貼ったりできます
![スクリーンショット 2023-08-19 19.26.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a5536b9-919f-3ec7-5c69-d2fa88f3968c.png)

以下のように作成されたら成功です
![スクリーンショット 2023-08-19 19.19.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/59435306-f4f1-6cf2-b441-a31f4c15131f.png)
![スクリーンショット 2023-08-19 19.20.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1485f506-171c-c4de-3f53-13a80a0b99d8.png)

### 認証の設定
ログイン機能を実装した際は認証の設定をSwagger側でする必要があります
今回はBasic認証の設定方法を記載します

```doc/openapi.yml
openapi: 3.1.0
info:
  title: project
  description: |-
  version: 1.0.0
servers:
  - url: http://localhost:8000/

# basic認証の設定
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

security:
  - basicAuth: [] 
```

securityに認証方法を記載することで一度認証に成功すれば、認証が必要なAPI全てにアクセスできるようになります

以下のような認証画面が表示されたら成功です
![スクリーンショット 2023-08-19 19.32.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4b7eb790-182f-7460-96d8-31a810d9df65.png)

![スクリーンショット 2023-08-19 19.33.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/493ed7e5-b65a-6049-4727-33cf88c69404.png)

### ユーザのAPI
ここからユーザAPIの
- 一覧表示
- 詳細

の設定方法について解説していきます

#### 一覧表示
```doc/openapi.yml
  /api/users/:
    get:
      tags:
        - users
      summary: システムユーザのAPI
      description: システムユーザを一覧表示する
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              properties:
                id:
                  type: string
                  description: UUID
                employee_number:
                  type: string
                  description: 社員番号
                username:
                  type: string
                  description: ユーザ名
                email:
                  type: string
                  description: メールアドレス
                role:
                  type: int
                  description: ロール
              examples:
                user_example:
                  value:
                    - id: "00000000-0000-0000-0000-000000000001"
                      employee_number: "00000001"
                      username: "test01"
                      email: "test01@example.com"
                      role: 0
                    - id: "00000000-0000-0000-0000-000000000002"
                      employee_number: "00000002"
                      username: "test02"
                      email: "test02@example.com"
                      role: 1
                    - id: "00000000-0000-0000-0000-000000000003"
                      employee_number: "00000003"
                      username: "test03"
                      email: "test03@example.com"
                      role: 2
                    - id: "00000000-0000-0000-0000-000000000004"
                      employee_number: "00000004"
                      username: "test04"
                      email: "test04@example.com"
                      role: 0
```

一覧表示など複数以上のJSONデータを表示させるときは以下のようにexamplesの下に値を記載していきます
以下のように表示されたら成功です

![スクリーンショット 2023-08-19 19.37.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9633de82-a6ba-0bc0-ae6f-78aab8453aac.png)
![スクリーンショット 2023-08-19 19.38.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/20c59c4a-888b-330c-049b-f9d0a186c61e.png)

#### 詳細
今回は/api/users/{id}/を例に記載します
IDをなどのパラメータを指定するときはparametersに記載することでデフォルト値をあらかじめ入れることができます

```doc/openapi.yml
  # APIのパス内にIDがあるときは以下のように{id}と記載
  /api/users/{id}/:
    get:
      tags:
        - users
      summary: システムユーザのAPI
      description: 該当するUUIDのシステムユーザを取得する
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              example:
                id: "00000000-0000-0000-0000-000000000001"
                employee_number: "00000001"
                username: "test01"
                email: "test01@example.com"
                role: 0
      parameters:
        - name: id
          in: path
          required: true
          description: 取得したいシステムユーザのUUID
          schema:
            type: string
          example: "00000000-0000-0000-0000-000000000001"
```

以下のように表示されたら成功です
![スクリーンショット 2023-08-19 19.43.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/585f57da-e721-cced-9a46-f181a288d90d.png)

## 完成
ユーザのAPIのCRUD操作もまとめると以下のようになります
```doc/openapi.yml
# https://swagger.io/specification/
openapi: 3.1.0
info:
  title: project
  description: |-
  version: 1.0.0
servers:
  - url: http://localhost:8000/

# basic認証の設定
components:
  securitySchemes:
    basicAuth:
      type: http
      scheme: basic

security:
  - basicAuth: [] 

tags:
  - name: login
    description: ログインAPI
    externalDocs:
      description: ログインについて
      url: https://qiita.com/shun198/items/067e122bb291fed2c839
  - name: users
    description: システムユーザ関連のAPI

paths:
  /api/login/:
    post:
      tags:
        - login
      summary: ログインAPI
      description: アプリケーションにログインする
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_number:
                  type: string
                  description: 社員番号
                  example: "00000001"
                password:
                  type: string
                  description: パスワード
                  example: "test"
              required:
                - "employee_number"
                - "password"
      responses:
        "200":
          description: ログインに成功
          content:
            application/json:
              schema:
                type: object
              example:
                role: "MANAGEMENT"
        "400":
          description: ログインに失敗
          content:
            application/json:
              schema:
                type: object
              example:
                msg: "社員番号またはパスワードが間違っています"
          
  /api/users/:
    get:
      tags:
        - users
      summary: システムユーザのAPI
      description: システムユーザを一覧表示する
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              properties:
                id:
                  type: string
                  description: UUID
                employee_number:
                  type: string
                  description: 社員番号
                username:
                  type: string
                  description: ユーザ名
                email:
                  type: string
                  description: メールアドレス
                role:
                  type: int
                  description: ロール
              examples:
                user_example:
                  value:
                    - id: "00000000-0000-0000-0000-000000000001"
                      employee_number: "00000001"
                      username: "test01"
                      email: "test01@example.com"
                      role: 0
                    - id: "00000000-0000-0000-0000-000000000002"
                      employee_number: "00000002"
                      username: "test02"
                      email: "test02@example.com"
                      role: 1
                    - id: "00000000-0000-0000-0000-000000000003"
                      employee_number: "00000003"
                      username: "test03"
                      email: "test03@example.com"
                      role: 2
                    - id: "00000000-0000-0000-0000-000000000004"
                      employee_number: "00000004"
                      username: "test04"
                      email: "test04@example.com"
                      role: 0
    post:
      tags:
        - users
      summary: システムユーザのAPI
      description: システムユーザを登録する
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_number:
                  type: string
                  description: 社員番号
                  example: "00000005"
                username:
                  type: string
                  description: ユーザ名
                  example: "test05"
                email:
                  type: string
                  description: メールアドレス
                  example: "test05@example.com"
                role:
                  type: int
                  description: ユーザ名
                  example: 0
              required:
                - "employee_number"
                - "username"
                - "email"
                - "role"
      responses:
        '201':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              example:
                id: "Random UUID"
                employee_number: "00000005"
                username: "test05"
                email: "test05@example.com"
                role: 0

  /api/users/{id}/:
    get:
      tags:
        - users
      summary: システムユーザのAPI
      description: 該当するUUIDのシステムユーザを取得する
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              example:
                id: "00000000-0000-0000-0000-000000000001"
                employee_number: "00000001"
                username: "test01"
                email: "test01@example.com"
                role: 0
      parameters:
        - name: id
          in: path
          required: true
          description: 取得したいシステムユーザのUUID
          schema:
            type: string
          example: "00000000-0000-0000-0000-000000000001"

    put:
      tags:
        - users
      summary: システムユーザのAPI
      description: 該当するUUIDのシステムユーザを更新する
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_number:
                  type: string
                  description: 社員番号
                  example: "00000005"
                username:
                  type: string
                  description: ユーザ名
                  example: "test05"
                email:
                  type: string
                  description: メールアドレス
                  example: "test05@example.com"
                role:
                  type: int
                  description: ユーザ名
                  example: 0
              required:
                - "employee_number"
                - "username"
                - "email"
                - "role"
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              example:
                id: "00000000-0000-0000-0000-000000000004"
                employee_number: "00000004"
                username: "test04"
                email: "test04@example.com"
                role: 0
      parameters:
        - name: id
          in: path
          required: true
          description: 更新したいシステムユーザのUUID
          schema:
            type: string
          example: "00000000-0000-0000-0000-000000000004"

    patch:
      tags:
        - users
      summary: システムユーザのAPI
      description: 該当するUUIDのシステムユーザを一部更新する
      requestBody:
        content:
          application/json:
            schema:
              type: object
              properties:
                employee_number:
                  type: string
                  description: 社員番号
                  example: "00000005"
                username:
                  type: string
                  description: ユーザ名
                  example: "test05"
                email:
                  type: string
                  description: メールアドレス
                  example: "test05@example.com"
                role:
                  type: int
                  description: ユーザ名
                  example: 0
              required:
                - "employee_number"
                - "password"
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
              example:
                id: "00000000-0000-0000-0000-000000000004"
                employee_number: "00000004"
                username: "test04"
                email: "test04@example.com"
                role: 0
      parameters:
        - name: id
          in: path
          required: true
          description: 一部更新したいシステムユーザのUUID
          schema:
            type: string
          example: "00000000-0000-0000-0000-000000000004"

    delete:
      tags:
        - users
      summary: システムユーザのAPI
      description: 該当するUUIDのシステムユーザを削除する
      responses:
        '204':
          description: 成功
          content:
            application/json:
              schema:
                type: object
      parameters:
        - name: id
          in: path
          required: true
          description: 削除したいシステムユーザのUUID
          schema:
            type: string
          example: "00000000-0000-0000-0000-000000000004"
```

## まとめ
ドキュメント作成に必要な項目を一通り記載してみました
- Dockerでローカルを汚さない
- GitHubでAPI仕様書をバージョン管理できる
- SwaggerでAPIの検証ができる
 
ことに大きな魅力を感じますね
今後は
- ファイルのアップロード
- クエリパラメータ

などの設定方法も追記していきたいと思います

## 参考
https://swagger.io/specification/

https://qiita.com/A-Kira/items/3d17396c7cc98873e29d

https://hodalog.com/build-the-environment-of-swagger-on-docker-and-publish-it-on-github-pages/

https://github.com/hodanov/docker-template-swagger/tree/master

https://zenn.dev/yumemi_inc/articles/dfd7eeb8ad4691
