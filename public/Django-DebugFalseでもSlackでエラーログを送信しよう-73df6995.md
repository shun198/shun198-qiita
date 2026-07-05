---
title: '[Django] Debug=FalseでもSlackでエラーログを送信しよう！'
tags:
  - Django
  - Slack
  - logging
  - Webhook
private: false
updated_at: '2024-09-14T16:04:53+09:00'
id: 73df699569be24387b1b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
本番環境でDebug=Falseにすると500エラーの際のログが表示されなくなるのはいいものの、エラーの特定が難しくなります
そこで、500エラーの時はSlackにエラーメッセージを送信する実装について解説します

## 前提
- loggerについてある程度知っている

## ディレクトリ構成
```
tree
.
├── project
│   ├── __init__.py
│   ├── __pycache__
│   ├── asgi.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
└── application
    ├── __init__.py
    ├── admin.py
    ├── apps.py
    ├── utils
    │   └── logs.py   
    └── views
```

## ログの設定
ログの設定を行いますので1つずつ説明します
Djangoは`dicConfig format`といってdictを使ってログの設定を行います

### filters
今回はDebug=Falseの時もエラーログを送信したいのでfiltersに
```
require_debug_false
```
を指定します

### handlers
今回はAdminEmailHandlerを継承したSlackHandlerという独自のハンドラークラスを使います
AdminEmailHandlerを継承することでERROR以上のメッセージを全てSlackHandlerで処理します

### loggers
`django.request`と`"level": "ERROR",`を指定することでERROR以上(500系)のログを指定したハンドラー(SlackHandler)に渡すことができます

```settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "slack": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "application.utils.logs.SlackHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["slack"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# DEBUG=Falseの時に環境変数としてincomming webhookのurlを取得
if not DEBUG:
    SLACK_ENDPOINT_URL = os.environ.get("SLACK_ENDPOINT_URL")
```

設定の詳細は公式ドキュメントに記載されています

https://docs.djangoproject.com/en/4.2/topics/logging/

## Slack通知の設定
Slack通知の設定を行います
今回はSlackのAPIを使ってメッセージをPOSTしたいのでrequestsをインストールします
```
pip install requests
```


```application.utils.logs.py
import json

import requests
from django.utils.log import AdminEmailHandler

from project import settings


class SlackHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        webhook_url = settings.SLACK_ENDPOINT_URL
        if "Request" in message:
            alarm_emoji = ":rotating_light:"
            text = alarm_emoji + message.split("COOKIES")[0]
            data = json.dumps(
                {
                    "attachments": [{"color": "#e01d5a", "text": text}],
                }
            )
            headers = {"Content-Type": "application/json"}
            requests.post(url=webhook_url, data=data, headers=headers)
```

順番に説明します
今回はsend_mailメソッド内にslackへメッセージをPOSTする処理を記載します
このメソッドが呼ばれるタイミングは
- 500エラーをハンドリングする時
- 500エラーを出した際のhtmlを出力する時

の2回なので500エラーをハンドリングする時(Requestがエラーメッセージ内に入っている時)のみ実行させます
Requestsが入ってる時のエラーメッセージは以下のとおりです

![スクリーンショット 2023-09-08 19.40.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ac1ac49c-9fae-5040-47ff-b4d3eb373bc8.png)
![スクリーンショット 2023-09-08 19.41.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/04547187-c2c2-9f67-1a41-7b973c0010f4.png)

また、Djangoのエラーメッセージ内に環境変数が入ってしまっているのでCOOKIESでsplit()して不要な情報を取り除きます

```
data = json.dumps(
    {
        "attachments": [{"color": "#e01d5a", "text": text}],
    }
)
```
を記載することで後述するSlackのメッセージの横に赤い線が入る上に長いメッセージを折り畳めるようになるので見やすくなります
詳細はこちらの公式ドキュメントを参照してください

https://api.slack.com/reference/messaging/attachments


## Incomming Webhookの作成
作成方法についてはかなりわかりやすい記事があるので紹介します

https://documents.trocco.io/docs/how-to-generate-slack-webhook-url

Webhookを作成後、.envファイルに環境変数を記載します
```.env
SLACK_ENDPOINT_URL=https://hooks.slack.com/services/XXXXXXXXXXXXXXXXXX
```

## 実際に送信してみよう！
500エラーになった後、以下のようにSlackの通知が送られてきたら成功です
![スクリーンショット 2023-09-08 19.47.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b252f131-d5b4-c7d8-9edb-b340d0e1a230.png)

詳細を表示させると以下のようになります
![スクリーンショット 2023-09-08 19.48.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/df439c44-aab4-f980-c809-c8c063ee2a12.png)
![スクリーンショット 2023-09-08 19.49.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c147f2e8-a13d-505f-c79e-d47e70a3d9b8.png)

## Debug=Trueの状態で検証するには？
以下のようにRequireDebugTrueを使用すればDebug=Trueでもエラーログを送信できます

```settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_true": {
            "()": "django.utils.log.RequireDebugTrue",
        },
    },
    "handlers": {
        "slack": {
            "level": "ERROR",
            "filters": ["require_debug_true"],
            "class": "application.utils.logs.SlackHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["slack"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}
```

## グループにメンションしたい時
### SlackのグループIDの取得方法
その他>自分のオーガナイゼーション>メンバーディレクトリ
を選択します

<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/163ce3fb-59e2-cb37-18de-3d5b18ab921c.png" width="300">
<img src="https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/01125ad2-7ba7-6f81-bfe7-a49c4709eb06.png" width="300">

ユーザグループのグループIDを取得できます

![スクリーンショット 2024-04-28 19.13.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2e3ba13b-c0d4-a2b6-21b4-04d879b463de.png)


### 実装
グループにメンションした状態でSlackにエラーログを送信したい時は以下のように

```
`<!subteam^ID>`
```

を使うと実装できます

```settings.py
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "require_debug_false": {
            "()": "django.utils.log.RequireDebugFalse",
        },
    },
    "handlers": {
        "slack": {
            "level": "ERROR",
            "filters": ["require_debug_false"],
            "class": "application.utils.logs.SlackHandler",
        }
    },
    "loggers": {
        "django.request": {
            "handlers": ["slack"],
            "level": "ERROR",
            "propagate": True,
        },
    },
}

# DEBUG=Falseの時に環境変数としてincomming webhookのurlとSlackのTeamIDを取得
if not DEBUG:
    SLACK_ENDPOINT_URL = os.environ.get("SLACK_ENDPOINT_URL")
    SLACK_TEAM_ID = os.environ.get("SLACK_TEAM_ID")
```

```application.utils.logs.py
import json

import requests
from django.utils.log import AdminEmailHandler

from project import settings


class SlackHandler(AdminEmailHandler):
    def send_mail(self, subject, message, *args, **kwargs):
        webhook_url = settings.SLACK_ENDPOINT_URL
        team_id = settings.SLACK_TEAM_ID
        if "Request" in message:
            alarm_emoji = ":rotating_light:"
            error_msg = message.split("COOKIES")[0]
            mention = ""
            if team_id:
                mention = "<!subteam^" + team_id + ">\n"
            text = mention + alarm_emoji + error_msg
            data = json.dumps(
                {
                    "attachments": [{"color": "#e01d5a", "text": text}],
                }
            )
            headers = {"Content-Type": "application/json"}
            requests.post(url=webhook_url, data=data, headers=headers)
```

詳細は公式ドキュメントに記載されています

https://api.slack.com/reference/surfaces/formatting#mentioning-groups

以下のようにメンションされた状態で送信できたら成功です

![スクリーンショット 2024-02-02 11.41.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b2f8a795-fb6d-6502-9f7d-05831fd283cc.png)

## 参考
https://docs.djangoproject.com/en/4.2/topics/logging/

https://stackoverflow.com/questions/29914390/send-production-errors-to-slack-instead-of-email

https://stackoverflow.com/questions/54284389/mention-users-group-via-slack-api

https://qiita.com/kenkanayama/items/1c3238a6c21b6b87bdec

https://api.slack.com/messaging/sending

