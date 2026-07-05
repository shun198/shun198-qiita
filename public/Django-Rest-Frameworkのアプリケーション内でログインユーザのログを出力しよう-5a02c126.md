---
title: Django Rest Frameworkのアプリケーション内でログインユーザのログを出力しよう！
tags:
  - Django
  - logger
  - django-rest-framework
  - Poetry
private: false
updated_at: '2023-06-14T16:56:12+09:00'
id: 5a02c126b18009152cee
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Djangoのアプリケーション内でログインユーザの
- ログインした時間
- ログインが成功したか、失敗したか
- ログインに成功したユーザのユーザ名と社員番号
- ログインに失敗したユーザの社員番号
- IPアドレス

をログに出力する方法について解説します

## 前提
- 通常はconf.yml内にlogの設定を記載しますが、今回はpyproject.toml内に記載します
- tomllibを使うため、python3.11を使用
- プロジェクトとアプリケーションを作成済み

本記事では
- 管理者ユーザを作成済み
- settings.pyをlocal.py(開発用)とdev.py(本番用)に分割済み
- ログイン機能を作成済み

のため、上記の実装に不安のある方は以下の記事を参照してくださると幸いです

https://qiita.com/shun198/items/1e97889942f5da3bec1e

https://qiita.com/shun198/items/d5402d75d739ff17f8c9

https://qiita.com/shun198/items/067e122bb291fed2c839


## ディレクトリ構成
構成は以下の通りです

```
tree
.
├── application
│   ├── __init__.py
│   ├── __pycache__
│   ├── admin.py
│   ├── apps.py
│   ├── fixtures
│   │   └── fixture.json
│   ├── migrations
│   ├── models
│   ├── permissions.py
│   ├── serializers.py
│   ├── urls.py
│   └── views
│       └── login.py
├── output # ログ生成時に作成される
│   ├── application.log
│   └── emergency.log
├── project
│   ├── __init__.py
│   ├── __pycache__
│   ├── asgi.py
│   ├── settings
│   │   ├── base.py
│   │   ├── local.py
│   │   └── dev.py
│   ├── urls
│   │   ├── base.py
│   │   └── local.py
│   └── wsgi.py
├── manage.py
├── poetry.lock
└── pyproject.toml
```

今回は
- pyproject.toml
- project/settings/local.py
- application/utils/logs.py
- application/utils/get_client_ip.py
- application/views/login.py

の順に作成していきます
かなり量が多いですが私も精一杯解説しますので一緒に頑張っていきましょう！

## pyproject.toml
pyproject.tomlには以下のように記載します

```pyproject.toml
# logの設定（開発環境）
[local.logging]
version = 1
[local.logging.formatters.simple]
format = "[%(levelname)s] %(name)s %(asctime)s - %(message)s "
[local.logging.handlers.consoleHandler]
class = "logging.StreamHandler"
level = "DEBUG"
formatter = "simple"
stream = "ext://sys.stdout"
[local.logging.handlers.applicationHandler]
class = "logging.handlers.TimedRotatingFileHandler"
when = "D"
level = "INFO"
formatter = "simple"
filename = "./output/application.log"
[local.logging.handlers.errorHandler]
class = "logging.handlers.TimedRotatingFileHandler"
when = "D"
level = "ERROR"
formatter = "simple"
filename = "./output/emergency.log"
[local.logging.loggers.console]
level = "DEBUG"
handlers = ["consoleHandler"]
propagate = "no"
[local.logging.loggers.application]
level = "DEBUG"
handlers = ["consoleHandler","applicationHandler"]
propagate = "no"
[local.logging.loggers.emergency]
level = "DEBUG"
handlers = ["consoleHandler","errorHandler"]
propagate = "no"
```

これだけ見ると何を設定しているのか分かりずらいので1つずつ解説します

### バージョン
バージョンの設定です
通常は1を指定します
```pyproject.toml
[local.logging]
version = 1
```

###  ログのフォーマット
ログのフォーマットを設定します
後述するhandlerにformatterを指定する際に利用します
今回はsimpleという名前にしています
フォーマットは公式ドキュメントに沿って設定しています


| フォーマット | 説明 |
| -------- | -------- | 
| %(levelname)s     | ログのレベル(Info, Warningなど)     |
| %(name)s | getLogger()メソッド内の引数 |
| %(asctime)s | ログを設定する処理が実行された日付と時刻 |
| %(message)s |logging.getLogger('simple_example').info("message")内の"message"  |

```pyproject.toml
[local.logging.formatters.simple]
format = "[%(levelname)s] %(name)s %(asctime)s - %(message)s "
```

### ログのハンドラ
ログの出力方法を指定するハンドラの設定を行います
後述するロガーで使用します
今回は以下のハンドラを作成します

| ハンドラ | 説明 | 
| -------- | -------- | 
| consoleHandler     | 標準出力用のハンドラ     | 
| applicationHandler | application.logファイルにログを出力するハンドラ |
| errorHandler | 異常終了した際にapplication.logファイルにログを出力するハンドラ |


また、以下のハンドラクラスを使用します

| ハンドラクラス | 説明 | 
| -------- | -------- | 
| StreamHandler     | ログをターミナル上に出力するハンドラ     | 
| TimedRotatingFileHandler | 一定期間ごとに新しいログファイルを作成(ローテーション)できるハンドラクラス |

また、指定できるオプションは以下の通りです

| オプション | ハンドラ | 説明 |
| -------- | -------- | -------- |
| class     | 共通     | 指定できるハンドラクラス     |
| level | 共通 | 追跡できるログのレベル<br>デフォルトがWarningのため、たとえばDEBUGを指定すると<br>DEBUGとINFOレベルのログも追跡できる |
| formatter | 共通 | ハンドラが使用するログのフォーマット<br>前述のsimpleを使用 |
| stream | StreamHandler | 今回は標準出力するよう設定<br>`ext://sys.stdout` |
| filename | TimedRotatingFileHandler | 指定したファイルへログを出力<br>`./output/application.log` |
| when | TimedRotatingFileHandler |ログファイルが作成(ローテーション)されるタイミング<br>例えば`D`と指定した場合はログファイルは1日ごとに自動的に上書きされます<br>他にも、`S`（秒）、`H`（時間）、`M`（分）など、さまざまな値を指定できます  |

```pyproject.toml
[local.logging.handlers.consoleHandler]
class = "logging.StreamHandler"
level = "DEBUG"
formatter = "simple"
stream = "ext://sys.stdout"
[local.logging.handlers.applicationHandler]
class = "logging.handlers.TimedRotatingFileHandler"
when = "D"
level = "INFO"
formatter = "simple"
filename = "./output/application.log"
[local.logging.handlers.errorHandler]
class = "logging.handlers.TimedRotatingFileHandler"
when = "D"
level = "ERROR"
formatter = "simple"
filename = "./output/emergency.log"
```

### ロガー
最後にロガーを作成し、どのハンドラを使用するか設定します
ロガーはgetLogger()メソッドを使って取得されます
たとえば
```python
getLogger("application")
```
と指定すると
```pyproject.toml
[local.logging.loggers.application]
```
のロガーが選択されます
全てのロガーが出すログを標準出力したいのでレベルは全てconsoleHandlerに合わせてDEBUGにしています
また、今回はpropagate(ロガーの伝搬の設定)を"no"にします

```pyproject.toml
[local.logging.loggers.console]
level = "DEBUG"
handlers = ["consoleHandler"]
propagate = "no"
[local.logging.loggers.application]
level = "DEBUG"
handlers = ["consoleHandler","applicationHandler"]
propagate = "no"
[local.logging.loggers.emergency]
level = "DEBUG"
handlers = ["consoleHandler","errorHandler"]
propagate = "no"
```

## local.py
```project/settings/local.py
from logging.config import dictConfig

from application.utils.logs import ConfFile


# ログの設定
output_path = Path("output")
if not output_path.exists():
    output_path.mkdir()
dictConfig(ConfFile.get()["local"]["logging"])
```

まず、ログを出力する用のoutputフォルダがあるかないか確認し、ない場合は作成します
dictConfigを使ってログの設定を辞書形式で取得します
- dictConfigを使う意図
- `ConfFile.get()["local"]["logging"]`で何を取得してるのか

は後述のlogs.pyで詳しく説明します

## logs.py
ログ関連の設定は以下のファイルに記載しています
```application/utils/logs.py
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

### tomllib
Python 3.11から新しく標準ライブラリに追加された、pyproject.tomlの内容をパースするライブラリです

https://docs.python.org/ja/dev/library/tomllib.html

### ConfFileクラス
ConfFileクラスを作成します
その際にクラスメソッドを作成し、ログイン用のviewにimportするだけでインスタンス化しなくても呼ばれるようになります
```application/utils/logs.py
class ConfFile:
    """confファイル取得用クラス
    Attributes:
        _conf_file (Optional[dict[Any, Any]]): pyproject.tomlのデータを辞書形式に変換した内容<br>
            最初の1回だけ読み込まれる
    """

    _conf_file: Optional[dict[Any, Any]] = None
    
    @classmethod
    def get(cls) -> dict[Any, Any]:
```

### pyproject.toml内のログの設定情報を取得
まだpyproject.toml内のログの設定情報を取得していない場合は
```python
with open("pyproject.toml", mode="rb") as file:
```
でpyproject.tomlを開き、
```python
cls._conf_file = tomllib.load(file)
```
でpyproject.tomlを読み取り、cls._conf_fileに代入します
代入後、cls._conf_fileをreturnします
```
return cls._conf_file
```

Conffile.get()で取得される情報は以下の通りです

```
print(Conffile.get())
{'tool': {'poetry': {...}, 'isort': {...}, 'black': {...}, 'pytest': {...}}, 'build-system': {'requires': [...], 'build-backend': 'poetry.core.masonry.api'}, 'local': {'logging': {...}}, 'dev': {'logging': {...}}}
special variables
function variables
'tool':
{'poetry': {'name': 'api', 'version': '0.1.0', 'description': 'api', 'authors': [...], 'readme': 'README.md', 'dependencies': {...}, 'group': {...}}, 'isort': {'profile': 'black'}, 'black': {'line-length': 79, 'include': '\\.py$', 'exclude': '(\n  /(\n      \\.eggs ...st\n  )/\n)\n'}, 'pytest': {'ini_options': {...}, 'DJANGO_SETTINGS_MODULE': 'project.settings.local'}}
'build-system':
{'requires': ['poetry-core'], 'build-backend': 'poetry.core.masonry.api'}
'local':
{'logging': {'version': 1, 'formatters': {...}, 'handlers': {...}, 'loggers': {...}}}
'dev':
{'logging': {'version': 1, 'formatters': {...}, 'handlers': {...}, 'loggers': {...}}}
```

### cls._conf_fileの中身は？
そこで、前述のlocal.pyで以下の内容を記載されたかと思います
```application/settings/local.py
# ログ設定
output_path = Path("output")
if not output_path.exists():
    output_path.mkdir()
dictConfig(ConfFile.get()["local"]["logging"])
```

今回はクラスメソッドが呼ばれる際にpyproject.toml内の`[local.logging]`が含まれる情報が取得されます

```
print(cls._conf_file["local"]["logging"])
'formatters':
{'simple': {'format': '[%(levelname)s] %(na...message)s '}}
'handlers':
{'consoleHandler': {'class': 'logging.StreamHandler', 'level': 'DEBUG', 'formatter': 'simple', 'stream': 'ext://sys.stdout'}, 'applicationHandler': {'class': 'logging.handlers.Tim...ileHandler', 'when': 'D', 'level': 'INFO', 'formatter': 'simple', 'filename': './output/application.log'}, 'errorHandler': {'class': 'logging.handlers.Tim...ileHandler', 'when': 'D', 'level': 'ERROR', 'formatter': 'simple', 'filename': './output/emergency.log'}}
'loggers':
{'console': {'level': 'DEBUG', 'handlers': [...], 'propagate': 'no'}, 'application': {'level': 'DEBUG', 'handlers': [...], 'propagate': 'no'}, 'emergency': {'level': 'DEBUG', 'handlers': [...], 'propagate': 'no'}}
```

## get_client_ip.py
以下のコードでクライアントのIPアドレスを取得します
```application/utils/get_client_ip.py
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0]
    else:
        ip = request.META.get("REMOTE_ADDR")
    return ip
```

ための関数です
リバースプロキシやロードバランサーを使用している場合は
```python
request.META.get("HTTP_X_FORWARDED_FOR")
```
でクライアントのIPアドレスします
今回は使用していないため、
```python
request.META.get("REMOTE_ADDR")
```
から127.0.0.1(ループバックアドレス)をクライアント(自分自身)のIPアドレスとして取得します

## login.py
今回は
- ログイン失敗時
- ログイン成功時
- ログアウト時

のログを出力します
```application/views/login.py
from logging import getLogger

from django.contrib.auth import authenticate, login, logout
from django.http import HttpResponse, JsonResponse
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.viewsets import ViewSet

from application.serializers import LoginSerializer
from application.utils.get_client_ip import get_client_ip
from application.utils.logs import LoggerName


class LoginViewSet(ViewSet):
    serializer_class = LoginSerializer
    permission_classes = [AllowAny]
    application_logger = getLogger(LoggerName.APPLICATION.value)


    @action(detail=False, methods=["POST"])
    def login(self, request):
        """ユーザのログイン"""
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return JsonResponse(
                serializer.errors, status=status.HTTP_400_BAD_REQUEST
            )

        employee_number = serializer.validated_data.get("employee_number")
        password = serializer.validated_data.get("password")
        user = authenticate(employee_number=employee_number, password=password)
        if not user:
            self.application_logger.warning(
                f"ログイン失敗:{serializer.data.get('employee_number')}, IP: {get_client_ip(request)}"
            )
            return JsonResponse(
                data={
                    "msg": "either employee number or password is incorrect"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        else:
            login(request, user)
            self.application_logger.info(
                f"ログイン成功: {user}, {serializer.data.get('employee_number')}, IP: {get_client_ip(request)}"
            )
            return JsonResponse(data={"role": user.Role(user.role).name})

    @action(methods=["POST"], detail=False)
    def logout(self, request):
        """ログアウト"""
        self.application_logger.info(
            f"ログアウト: {request.user}, IP: {get_client_ip(request)}"
        )
        logout(request)
        return HttpResponse()
```

## 出力されたログ
今回はapplication_loggerのログはoutput/application.logに出力するよう設定しています
出力されるログは以下の通りです
以下のように [local.logging.formatters.simple]で指定したフォーマットになっていれば成功です
```output/application.log
[WARNING] application 2023-03-18 19:33:49,455 - ログイン失敗:11000000, IP: 127.0.0.1
[INFO] application 2023-03-18 19:46:58,506 - ログイン成功: test01, 00000001, IP: 127.0.0.1 
[INFO] application 2023-03-18 21:07:25,233 - ログアウト: test01, IP: 127.0.0.1 
```

## まとめ
conf.ymlではなく、pyproject.tomlにログの設定を入れることで不要なファイルを作らずにかなり設定を楽に管理できるようになりました
おかげでログインユーザの操作ログを楽に実装できました
ログイン以外のログの取得も今のようなやり方で取りたいですね

## 参考
https://docs.python.org/ja/dev/library/tomllib.html

https://gihyo.jp/article/2022/11/monthly-python-2211

https://qiita.com/Snorlax/items/9365788f922eab8a98ae

https://resanaplaza.com/2021/07/23/%E3%80%90%E8%89%AF%E3%81%8F%E5%88%86%E3%81%8B%E3%82%8B%E3%80%91python-logger%E3%81%AE-%E4%BD%BF%E3%81%84%E6%96%B9%E3%81%A8%E6%B3%A8%E6%84%8F%E7%82%B9/#i-2

http://stackoverflow.com/questions/4581789/how-do-i-get-user-ip-address-in-django

https://gihyo.jp/article/2022/11/monthly-python-2211
