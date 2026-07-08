---
title: '[入門]BoltとPythonを使ってSlack Appをローカル上で実行しよう！'
tags:
  - Python
  - Docker
  - Slack
  - docker-compose
  - Bolt
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 27d4961d7440f8c30c19
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
BoltとPythonを使ってSlack Appをローカル上で実行する方法について解説します

## 前提
- Pythonを使用
- Docker、docker-compose.ymlを使用
- Poetryを使用
- Slackのワークスペースを作成済み

## ディレクトリ構成
```
tree
.
├── .env
├── .gitignore
├── Makefile
├── README.md
├── application
│   ├── app.py
│   ├── poetry.lock
│   └── pyproject.toml
├── containers
│   └── python
│       └── Dockerfile
└── docker-compose.yml
```

## Slack Appの作成
SlackのAppを以下のリンクから作成します

https://api.slack.com/apps/new

![スクリーンショット 2024-06-16 12.05.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9396925f-e574-2b90-f640-c478dd6aafc2.png)

以下が管理画面です
![スクリーンショット 2024-06-16 12.06.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/096302e8-5a0b-d728-b31b-2b1f54018a44.png)

左のOAuth&PermissionsからBot Token Scopesへ移動し、`Add an OAuth Scope`を押します
![スクリーンショット 2024-06-16 12.17.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ad0d1df5-5f9b-0c8d-8e1b-9a4f3e171a1d.png)

メッセージを送信したいのでchat:writeを選択します
![スクリーンショット 2024-06-16 12.17.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/15643ab0-5805-db53-1f1e-d19a10b63b54.png)

`Install to Workspace`を押します
![スクリーンショット 2024-06-16 12.19.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3885e3f5-aa6d-342b-7d1c-17e3d50f4861.png)

許可する、を選択します
![スクリーンショット 2024-06-16 12.19.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8e623adf-1f2f-b3a5-5d8a-0143d2ead2db.png)

Bot User OAuth Tokenが表示されます
後ほど使用します
![スクリーンショット 2024-06-16 12.20.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/90889238-48c3-c928-655a-696588e97375.png)

Basic Informationのページまで戻り、アプリトークンのセクションまで下にスクロールしGenerate Token and Scopesをクリックしてアプリレベルトークンを作成します
![スクリーンショット 2024-06-16 12.41.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/00480f55-99c9-9e90-f903-bcfa15a24aff.png)

Generateを押します
![スクリーンショット 2024-06-16 12.43.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2ba70509-4f4c-9946-9c83-ab4a43687a8d.png)

トークンが作成されたら成功です
![スクリーンショット 2024-06-16 12.43.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/65255f05-41a3-e626-e9ce-8105c7bc4e6a.png)

ソケットモードを有効にします
スライダーを右にスライドします

![スクリーンショット 2024-06-16 12.45.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc5ae04c-836b-a485-b1cb-bc5d02712140.png)

Event Subscriptionsを有効にします
![スクリーンショット 2024-06-16 12.47.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/58b73811-f89b-c800-e660-a089cde7b7f7.png)

Bot Eventを追加します
今回は

- message.channels
- message.groups
- message.im
- message.mpim

を選択します

![スクリーンショット 2024-06-16 12.51.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a083d0b4-9b80-d9ec-bda2-7276963f7233.png)

また、インタラクティブ機能を有効にすると、ボタン、選択メニュー、日付ピッカー、モーダル、ショートカットなどの機能が利用できるようになります
アプリ設定ページの「Interactivity & Shortcuts」にアクセスしてください

![スクリーンショット 2024-06-16 13.06.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c9a9fc7e-96c5-a05d-1d0b-4f968d02da9d.png)

Slack App側の設定は以上です

## 環境構築
Python用のDockerfileを作成します
```Dockerfile
FROM python:3.12.3

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY application/pyproject.toml /code/
# Initialize python project with Poetry
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
```

Dockerfileを簡単に起動できるようdocker-composeを作成します
```docker-compose.yml
services:
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/python/Dockerfile
    volumes:
      - ./application:/code
    ports:
      - "8000:8000"
    command: poetry run python app.py
    env_file:
      - .env
```

PoetryでPythonのパッケージを管理したいのでpyproject.tomlを作成します
Slack Appを使用する際はslack-boltが必須なので追加します

```application/pyproject.toml
[tool.poetry]
name = "slack-workflow-practice"
version = "0.1.0"
description = ""
authors = ["shun198"]
readme = "README.md"

[tool.poetry.dependencies]
python = "3.12.3"
slack-bolt = "^1.19.0"

[tool.poetry.group.dev.dependencies]
black = "^24.0.0"
isort = "^5.11.4"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.isort]
line_length = 79
profile = "black"

[tool.black]
line-length = 79
include = '\.py$'
exclude = '''
(
  /(
      \.eggs         # exclude a few common directories in the
    | \.git          # root of the project
    | \.hg
    | \.mypy_cache
    | \.tox
    | \.venv
    | _build
    | buck-out
    | build
    | dist
  )/
)
'''
```


今回はパブリックチャンネルに`hello`というメッセージを送ったらHey there　というメッセージがアプリから送られ、 `Click Me`というボタンが表示され、`Click Me`を押した後にメンションされた状態で`clicked the button`というメッセージをAppが送信するAppを作成します

```app.py
import os

from slack_bolt import App
from slack_bolt.adapter.socket_mode import SocketModeHandler

# ボットトークンと署名シークレットを使ってアプリを初期化します
app = App(token=os.environ.get("SLACK_BOT_TOKEN"))

# 'hello' を含むメッセージをリッスンします
@app.message("hello")
def message_hello(message, say):
    # イベントがトリガーされたチャンネルへ say() でメッセージを送信します
    say(
        blocks=[
            {
                "type": "section",
                "text": {"type": "mrkdwn", "text": f"Hey there <@{message['user']}>!"},
                "accessory": {
                    "type": "button",
                    "text": {"type": "plain_text", "text":"Click Me"},
                    "action_id": "button_click"
                }
            }
        ],
        text=f"Hey there <@{message['user']}>!"
    )

@app.action("button_click")
def action_button_click(body, ack, say):
    # アクションを確認したことを即時で応答します
    ack()
    # チャンネルにメッセージを投稿します
    say(f"<@{body['user']['id']}> clicked the button")

# アプリを起動します
if __name__ == "__main__":
    SocketModeHandler(app, os.environ["SLACK_APP_TOKEN"]).start()
```


## Appの検証
作成したチャンネルにAppsを追加します
![スクリーンショット 2024-06-16 12.58.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/01fd2651-2e80-b249-3c22-213c65c867ed.png)

![スクリーンショット 2024-06-16 12.58.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c7adffbd-2cd2-1acd-eeda-3079bc4dd01b.png)

以下のように`hello`とメッセージを送り、Hey there　というメッセージがアプリから送られ、`Click Me`というボタンが表示されます
`Click Me`を押した後にメンションされた状態で`clicked the button`というメッセージをAppが送信したら成功です

![スクリーンショット 2024-06-16 13.20.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/baec38a0-6dcc-30f9-c720-b626fde1586e.png)

## 参考
https://docs.slack.dev/tools/bolt-python/ja-jp/getting-started
