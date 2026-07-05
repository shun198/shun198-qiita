---
title: FlaskでSwaggerを設定する方法について
tags:
  - Flask
  - swagger
  - OpenAPI
private: false
updated_at: '2025-01-04T09:15:02+09:00'
id: 87837662d36dc660171d
organization_url_name: null
slide: false
---
## はじめに
FlaskでSwaggerを使えるように設定する方法について説明したいと思います

## 前提
- Flaskのプロジェクトを作成済み

## flask-swagger-uiのインストール
flask-swagger-uiをインストールすることで使用できるようになります
```terminal
pip install flask-swagger-ui
```

## ディレクトリ構成
今回はmain.py、swagger.ymlを作成します

```
.
└── application
    ├── main.py
    ├── poetry.lock
    ├── pyproject.toml
    └── static
        └── swagger.yml
```

## main.py
SWAGGER_URLにswaggerへアクセスする際のパス、API_URLにswagger.ymlのパスを記載します
get_swaggerui_blueprintを使ってSwagger用のBlueprintを取得し、SWAGGER_URLとAPI_URLを上書きした後にSwagger用のBlueprintをアプリケーションに登録します

```main.py
from flask_swagger_ui import get_swaggerui_blueprint

app = Flask(__name__)

SWAGGER_URL = "/api/docs"
API_URL = "/static/swagger.yml"

# Call factory function to create our blueprint
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL,
    API_URL,
)

app.register_blueprint(swaggerui_blueprint)


@app.route("/api/health")
def health():
    return {"msg": "pass"}
```

## APIのドキュメントが記載されたymlファイル
swagger.ymlにAPIのドキュメントを記載します
今回はヘルスチェック用のAPIについて記載してます

```static/swagger.yml
# https://swagger.io/specification/
openapi: "3.0.0"
# APIに関するメタデータ
info:
  title: project
  description: |-
    # プロジェクトの詳細
  version: 1.0.0

tags:
  - name: health
    description: ヘルスチェックAPI

paths:
  /api/health:
    get:
      tags:
        - health
      summary: ヘルスチェックAPI
      description: APIサーバー単独でのヘルスチェック
      responses:
        '200':
          description: 成功
          content:
            application/json:
              schema:
                type: object
                properties:
                  msg:
                    type: string
                    description: ステータス
                    example: pass
```

今回は8000ポートを使用します
http://127.0.0.1:8000/api/docs へアクセスした際にSwaggerが出たら成功です

![スクリーンショット 2025-01-04 9.03.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/13864415-1c24-ccb5-f44c-fc39f048b015.png)

また、ymlファイルを下記のようにGitHub Pagesにアップロードできます

https://qiita.com/shun198/items/520806a86a14a4bd64a8

## 参考文献
https://github.com/sveint/flask-swagger-ui
