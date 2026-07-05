---
title: Django Debug Toolbarを使ってアプリケーションを効率よくデバッグしよう！
tags:
  - Django
  - nginx
  - swagger
  - docker-compose
  - debug-tool-bar
private: false
updated_at: '2023-12-08T16:46:07+09:00'
id: 59c388f3b7f731d28985
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Django Debug Toolbarを使うと実行されたSQL、シグナル、APIの実行履歴などがわかりやすく表示されて便利です
今回はDjango Debug Toolbarの設定方法について解説します

## 前提
- Djangoのプロジェクトを作成済み
- 検証時にSwaggerを使用します
- 静的ファイル共有時にdocker-composeを使用

## 設定
### バッケージのインストール
まず、Debug Toolbarをインストールします
```
pip install django-debug-toolbar
```

### docker-compose.ymlの作成
Debug Toolbarの静的ファイルを共有できるようdocker-compose.ymlのNginxに設定を行います
その際はstaticのvolumeを作成します

```docker-compose.yml
version: '3.9'

services:
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

  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./backend:/code
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
    depends_on:
      db:
        condition: service_healthy

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

volumes:
  db_data:
  static:
```

### settings.py
settings.pyにDebug Toolbarの設定を記載します
```settings.py
INSTALLED_APPS = [
    # ...
    "django.contrib.staticfiles",
    "debug_toolbar",
    # ...
]

MIDDLEWARE = [
    # ...
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    # ...
]

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        # ...
    }
]

STATIC_ROOT = "/static/"
STATIC_URL = "/static/"

INTERNAL_IPS = [
    # ...
    "127.0.0.1",
    # ...
]

# debug tool barのconfig
DEBUG_TOOLBAR_CONFIG = {
    # ツールバーを表示させる
    "SHOW_TOOLBAR_CALLBACK" : lambda request: True,
}
```

### urls.py
urls.pyにDebug Toolbarの設定を記載します
```urls.py
from django.urls import include, path

urlpatterns = [
    # ...
    path("__debug__/", include("debug_toolbar.urls")),
]
```

## 実際に検証してみよう！
Django Rest Frameworkの画面上に右のようなメニューがでたら成功です
![スクリーンショット 2023-12-08 13.35.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1e532905-44a8-2bf8-a481-185fec2091ed.png)

Swaggerでも同様の画面が表示されます
![スクリーンショット 2023-12-08 13.33.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c94365cc-6714-2252-dc67-b118d2f82480.png)

SQLを実行すると以下のようにクエリの実行回数などが表示されます
![スクリーンショット 2023-12-08 13.35.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fe9bd45a-3684-cffa-dd59-05ccb5b6971f.png)

SQL以外にリクエストの中身、SQLの実行履歴、シグナルなども表示されます
![スクリーンショット 2023-12-08 13.37.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d96e479e-d487-bccf-b79c-084b8b3186e3.png)

![スクリーンショット 2023-12-08 13.37.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/97c2bfd6-433f-d059-ac77-5610c099b71e.png)

![スクリーンショット 2023-12-08 13.38.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/094f3339-be75-28ff-44e6-fedf668aa95e.png)

以上です

## 参考
https://django-debug-toolbar.readthedocs.io/en/latest/
