---
title: Django Rest FrameworkでLoggerのMiddlewareを作成してログの出力を共通化させよう
tags:
  - Django
  - logger
  - django-rest-framework
private: false
updated_at: '2023-12-19T09:12:30+09:00'
id: 337f4bba682ac2a099a8
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
ログを出力する際に各Viewごとに一つずつ設定するのは手間なのでMiddlewareとして共通化させる方法について解説します

## 前提
- loggerの基本的な知識を有している
- システムユーザのModelを作成済み

UserのModelについてはDjangoのAbstractUserを継承して作成します
詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

## ディレクトリ構成
今回作成していくのは以下のファイルです
- application/pyproject.toml
- project/settings.py
- application/logs.py
- application/middleware.py

```
tree
・
└── application
    ├── application
    │   └── utils
    │       ├── logs.py
    │       └── middleware.py
    ├── manage.py
    ├── poetry.lock
    ├── pyproject.toml
    └── project
        └── settings.py
```

では一つずつ解説していきます

## ログの設定
toml parserを使ったログの設定方法について詳細に知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/5a02c126b18009152cee

### pyproject.toml
pyproject.tomlにログを設定していきます

```pyproject.toml
# logの設定
[logging]
version = 1
[logging.formatters.simple]
format = "[%(levelname)s] %(name)s - %(message)s "
[logging.handlers.applicationHandler]
class = "logging.StreamHandler"
level = "INFO"
formatter = "simple"
stream = "ext://sys.stdout"
[logging.handlers.errorHandler]
class = "logging.StreamHandler"
level = "ERROR"
formatter = "simple"
stream = "ext://sys.stdout"
[logging.loggers.application]
level = "DEBUG"
handlers = ["applicationHandler"]
propagate = "no"
[logging.loggers.emergency]
level = "DEBUG"
handlers = ["errorHandler"]
propagate = "no"
```

今回はpyproject.toml内にLoggerの設定を記載しています

### settings.py
dictConfigを使ってtoml内のLoggerの設定を取得していきます

```project/settings.py
from logging.config import dictConfig


# ログ設定
dictConfig(ConfFile.get()["logging"])
```

### application/utils/logs.py
Loggerの設定を行います
今回はエラーを含めた想定内のログは
- Application

想定外のエラーのログは
- Emergency

として定義しています

```logs.py
import tomllib
from enum import Enum
from typing import Any, Optional


class LoggerName(Enum):
    """ロガー名"""

    APPLICATION = "application"
    EMERGENCY = "emergency"


class ConfFile:
    """confファイル取得用クラス
    Attributes:
        _conf_file (Optional[dict[Any, Any]]): pyproject.tomlのデータを辞書形式に変換した内容<br>
            最初の1回だけ読み込まれる
    """

    _conf_file: Optional[dict[Any, Any]] = None

    @classmethod
    def get(cls) -> dict[Any, Any]:
        """pyproject.tomlのデータを辞書形式で返す
        2回目以降はファイルの読み込みは実施しない
        Returns:
            dict[Any, Any]: pyproject.tomlの設定データの辞書形式
        """
        if cls._conf_file is None:
            with open("pyproject.toml", mode="rb") as file:
                cls._conf_file = tomllib.load(file)
        return cls._conf_file
```

## middlewareの設定
ログを出力する用のMiddlewareを作成します

```application/utils/middleware.py
"""ミドルウェア用のモジュール"""
import datetime
from logging import getLogger

from rest_framework import status

from application.utils.logs import LoggerName

application_logger = getLogger(LoggerName.APPLICATION.value)



class LoggingMiddleware:
    """APIの開始と終了をロギングするミドルウェア"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # API呼び出し以外はログに出さない
        if request.path.endswith(".js") or request.path in (
            # Swaggerのパス
            "/api/docs/",
            "/api/schema/",
        ):
            return self.get_response(request)

        method = request.method
        ip = get_client_ip(request)
        path = request.path

        user = request.user
        user_info = "未ログイン"
        if user.is_authenticated:
            user_info = f"{user.employee_number} {user.username}"

        start_time = datetime.datetime.now()
        response = self.get_response(request)
        status_code = response.status_code
        end_time = datetime.datetime.now()
        duration_time = end_time - start_time
        message = f"{ip} {user_info} {method} {path} 実行時間: {duration_time} {status_code} "
        if status.is_success(response.status_code):
            application_logger.info(message)
        else:
            application_logger.warning(message)
        return response


def get_client_ip(request):
    """クライアントのIPアドレスを取得"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
```

### get_response
```application/utils/middleware.py
response = self.get_response(request)
```
からAPIを実行した際のresponseを変数に格納します

### ログのフォーマット
API実行時のログの
- IPアドレス
- ユーザ情報
- HTTPメソッド
- APIのパス
- 実行時間
- ステータスコード


を出力したいので以下のフォーマットにします

```application/utils/middleware.py
message = f"{ip} {user_info} {method} {path} 実行時間: {duration_time} {status_code} "
```

### settings.py
MIDDLEWAREにLoggingMiddlewareを追加することでログの出力を有効化します

```settings.py
MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    # 先ほど作成したLoggingMiddlewareを追加
    "application.utils.middleware.LoggingMiddleware",
]
```

## ログの出力
試しに私の方でいくつかAPIを作成
以下のようにログが出力されたら成功です

```
[INFO] application 2023-07-04 16:43:01,753 - 127.0.0.1 00000001 test01 POST /api/users/send_invite_user_mail/ 200 実行時間:0:00:00.070526
[INFO] application 2023-07-04 16:43:02,402 - 127.0.0.1 未ログイン POST /api/login/ 200 実行時間:0:00:00.213168 
```

## 参考
https://docs.djangoproject.com/en/4.2/topics/http/middleware/

https://docs.djangoproject.com/en/4.2/howto/logging/

https://zeroes.dev/p/django-middleware-to-log-requests/

https://www.django-rest-framework.org/api-guide/status-codes/
