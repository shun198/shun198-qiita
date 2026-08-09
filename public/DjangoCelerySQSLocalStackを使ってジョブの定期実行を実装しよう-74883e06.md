---
title: Django+Celery+SQS+LocalStackを使ってジョブの定期実行を実装しよう！
tags:
  - Django
  - Celery
  - sqs
  - docker-compose
  - LocalStack
private: false
updated_at: '2026-08-10T07:49:18+09:00'
id: 74883e06d3a8d2bc98c3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Djangoで定期実行機能を実装する際はCeleryを使うのが一般的です
Celeryを使う際にブローカーを指定する必要がありますが
- Redis
- AWS SQS
- RabbitMQ

が一般的です
今回はCeleryとSQSを使ってジョブを定期実行していきます

## 前提
- Djangoのプロジェクトを作成済み
- Poetryを使用
- Dockerに関する基本的な知識を有している
- LocalStackを使用

## ファイル構成
今回実装する機能のファイル構成は以下の通りです
プロジェクト名はproject, アプリケーション名はapplicationとします

```ディレクトリ構成
・
├── application
│    ├── application
│    │   ├── __init__.py
│    │   ├── admin.py
│    │   ├── apps.py
│    │   ├── migrations
│    │   ├── models.py
│    │   ├── urls.py
│    │   ├── celery.py
│    │   └── tasks.py.py
│    ├── manage.py
│    ├── poetry.lock
│    ├── project
│    │   ├── __init__.py
│    │   ├── asgi.py
│    │   ├── settings.py
│    │   ├── urls.py
│    │   └── wsgi.py
│    └── pyproject.toml
├── containers
│    ├── django
│    │   └── Dockerfile
│    ├── mysql
│    │   └── Dockerfile
│    └── localstack
│        └── entrypoint.sh
└── docker-compose.yml                                 
```

## そもそもCeleryって何？
Celeryは非同期にタスクを実行する分散タスクキューを処理するフレームワークです
Celeryを使って非同期にタスクを実行することで
- 分散処理
- レスポンスの高速化

を実現することができるため、
- 定期実行したいバッチ処理
- 非同期で実行させたい画像処理などの重い処理
 
で使用されるのが一般的です

## Celeryを使用する際に知っておきたい用語
Celeryを使用する際に以下の用語について知る必要があります


| 用語 | 役割 | 今回の実装に相当するもの |
| -------- | -------- | -------- |
| Celery-Beat | 実行するタスクのスケジュールを管理し、Brokerに渡す | Celery-Beatのコンテナ |
| Broker | Celery-Clientから受け取ったタスクをQueueに入れる | LocalStack(AWS SQSはBrokerとQueue両方の役割を果たしてる) |
| Celery-Worker | Brokerから受け取ったタスクを実行する | Celeryのコンテナ |

## 必要なファイルの作成
今回は以下のファイルを作成していきます
- DjangoのDockerfile
- pyproject.toml
- entrypoint.sh
- docker-compose.yml
- settings.py
- .env
- tasks.py
- celery.py

### Dockerfile
DjangoのDockerfileを作成します
今回はPoetryを使用します

```Dockerfile:containers/django/Dockerfile
FROM python:3.14

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /code
COPY application/pyproject.toml /code/
# Initialize python project with Poetry
RUN pip install --upgrade pip && pip install poetry
RUN poetry install
```

### pyproject.toml
Celeryを使って定期実行処理をする際は
- celery
- pycurl
- kombu

をインストールする必要があります

```application/pyproject.toml
[tool.poetry.dependencies]
python = "^3.14"
Django = "^4.1.2"
mysqlclient = "^2.1.1"
celery = "^5.2.7"
pycurl = "^7.45.2"
kombu = "^5.2.4"
```

### entrypoint.sh
LocalStack起動時にSQSのQueueを自動生成するスクリプトを作成します
後述するLocalStack内の`/etc/localstack/init/ready.d`へマウントすることで実行されます
今回はQueueの名前を`my-queue`とします
```containers/localstack/entrypoint.sh
#!/bin/bash

set -eu

LOCALSTACK_HOST=localhost
# 後述する.envファイルから環境変数を取得
AWS_REGION=$AWS_DEFAULT_REGION_NAME
QUEUE_NAME_TO_CREATE=$SQS_QUEUE_NAME

awslocal --endpoint-url=http://${LOCALSTACK_HOST}:4566 sqs create-queue --queue-name ${QUEUE_NAME_TO_CREATE} --region ${AWS_REGION}
```

### docker-compose.yml
- 今回使うAWS SQSをエミュレートするLocalStack
- Celery
- Celery Beat

のコンテナをdocker-composeを使って立ち上げます
LocalStackの環境変数をDjangoと接続する際に使用するので設定します
ローカル上で検証する用で使うので実際の
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY
 
を指定する必要がありません
今回はどちらもlocalstackにします

また、Celery、Celery Beatのコンテナを作成する際はDjangoのDockerfileを使用します
Django、MySQLのコンテナの作成方法について詳細に知りたい方は以下の記事を参考にしてください


https://qiita.com/shun198/items/f6864ef381ed658b5aba

```docker-compose.yml
services:
  db:
    container_name: mysql
    build:
      context: .
      dockerfile: containers/mysql/Dockerfile
    platform: linux/x86_64
    volumes:
      - db_data:/var/lib/mysql
    env_file:
      - .env
    ports:
      - "3306:3306"
    healthcheck:
      test: mysqladmin ping -h 127.0.0.1 -u$$MYSQL_USER -p$$MYSQL_PASSWORD
      interval: 10s
      timeout: 10s
      retries: 3
      start_period: 30s

  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./application:/code
      - ./static:/static
    ports:
      - "8000:8000"
    command: poetry run python manage.py runserver 0.0.0.0:8000
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy

  localstack:
      container_name: localstack
      image: localstack/localstack:latest
      environment:
        - SERVICES=sqs
        - AWS_ACCESS_KEY_ID=localstack
        - AWS_SECRET_ACCESS_KEY=localstack
        - DEBUG=1
        # シェルスクリプト用の環境変数を.envから取得
        - AWS_DEFAULT_REGION_NAME
        - SQS_QUEUE_NAME
      volumes:
        - ./localstack:/var/lib/localstack
        - /var/run/docker.sock:/var/run/docker.sock
        # queueを自動生成するシェルスクリプトをマウントさせる
        - ./containers/localstack/entrypoint.sh:/etc/localstack/init/ready.d/entrypoint.sh
      ports:
        - "4566:4566" 

  celery:
    container_name: celery
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./application:/code
    env_file:
      - .env
    # -Aの後ろにアプリケーション名を指定
    # ログはinfoレベルのものを出力
    command: poetry run celery -A application worker -l info
    depends_on:
      - app
      - localstack

  celery-beat:
    container_name: celery-beat
    build:
      context: .
      dockerfile: containers/django/Dockerfile
    volumes:
      - ./application:/code
    env_file:
      - .env
    # -Aの後ろにアプリケーション名を指定
    # ログはinfoレベルのものを出力
    command: poetry run celery -A application beat -l info
    depends_on:
      - app
      - localstack

volumes:
  db_data:
  static:
```

### settings.py
CELERYの設定とAWS SQSと接続する設定を記載します
IAMロールを使用する際は`sqs://`のみで大丈夫ですがlocalstackを使用する際は後ろに
- AWS_ACCESS_KEY_ID
- AWS_SECRET_ACCESS_KEY

をkombuで暗号化した状態で`:`を挟んで記載し、@の後ろにlocalstackとポート番号を指定します
また、CELERYの設定は下記の通りです
|Celeryの設定|説明|
|---|---|
|CELERY_TIMEZONE|Celeryが使用するタイムゾーン<br>今回は日本のタイムゾーンを設定|
|CELERY_TASK_TRACK_STARTED|タスクを実行するときに、タスクの開始を追跡するかどうかを指定|
|CELERY_TASK_TIME_LIMIT|タスクを実行する最大時間|
|CELERY_TASK_SERIALIZER|タスクのデータをシリアライズする方法<br>今回はjsonを指定|
|CELERY_RESULT_SERIALIZER|タスクの結果をシリアライズする方法<br>今回はjsonを指定|
|CELERY_ACCEPT_CONTENT|受け入れ可能なコンテンツタイプを指定<br>今回はapplication/jsonを指定|
|CELERY_TASK_DEFAULT_QUEUE|タスクを格納するQueueを指定<br>このオプションを指定しないとAWS上で設定したQueueではなく、Celery側で自動生成したQueueが使われてしまう|
|CELERY_RESULT_BACKEND|タスクの結果を格納するバックエンドを指定<br>今回はNoneを指定|
|CELERY_BROKER_TRANSPORT_OPTIONS|Celeryが使用するブローカーの設定<br>predefined_queuesにQueueのURLを指定|

```settings.py
from kombu.utils.url import safequote


AWS_ACCESS_KEY_ID = safequote("localstack")
AWS_SECRET_ACCESS_KEY = safequote("localstack")

CELERY_BROKER_URL = (
    f"sqs://{AWS_ACCESS_KEY_ID}:{AWS_SECRET_ACCESS_KEY}@localstack:4566"
)

CELERY_TIMEZONE = "Japan"
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 60
CELERY_TASK_SERIALIZER = "json"
CELERY_RESULT_SERIALIZER = "json"
CELERY_ACCEPT_CONTENT = ['application/json']
CELERY_BROKER_CONNECTION_RETRY_ON_STARTUP = True
CELERY_TASK_DEFAULT_QUEUE = os.environ.get("SQS_QUEUE_NAME")
CELERY_RESULT_BACKEND = None
CELERY_BROKER_TRANSPORT_OPTIONS = {
    "predefined_queues": {
        CELERY_TASK_DEFAULT_QUEUE: {
            "url": os.environ.get("SQS_QUEUE_URL"),
        }
    },
    "region": os.environ.get("AWS_DEFAULT_REGION_NAME"),
    "visibility_timeout": 30,
    "polling_interval": 60,
}
```

### .env
Django側で必要な環境変数を指定します
使用する環境変数は以下の通りです

```.env
AWS_DEFAULT_REGION_NAME=ap-northeast-1
SQS_QUEUE_NAME=my-queue
SQS_QUEUE_URL=http://localstack:4566/000000000000/my-queue
```

### tasks.py
定期実行するジョブを作成します
今回は以下のように"タスクの実行"とprintするだけの簡単なタスクを作成します

```tasks.py
from celery import shared_task
from celery.utils.log import get_task_logger


@shared_task
def print_task():
    print("タスクの実行")
```

### celery.py
tasks.pyで記載したジョブをCeleryで実行できるよう設定します
タスクを設定する際はアプリケーション名から絶対パスで指定しましょう
また、今回は1分ごとにタスクを実行するためcrontabを使って指定します

```celery.py
import os

from celery import Celery
from celery.schedules import crontab

"""環境変数を設定"""
os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE", "project.settings"
)

"""Celeryをdjango.conf:settingsに設定"""
app = Celery("application")
app.config_from_object("django.conf:settings", namespace="CELERY")

"""登録された全てのDjangoアプリからタスクモジュールをロード"""
app.autodiscover_tasks()

"""tasks.pyから実行するメソッドをスケジューラに設定"""
app.conf.beat_schedule = {
    "print_task": {
        "task": "application.tasks.print_task",
        "schedule": crontab(minute="*/1"),
    },
}
```

## タスクを実行しよう！
```
docker compose up -d --build
```
でコンテナを立ち上げます

Celeryのコンテナを起動するときに下記のように表示されたら成功です
```
2023-04-28 18:03:32  -------------- celery@aa09391fcfb1 v5.2.7 (dawn-chorus)
2023-04-28 18:03:32 --- ***** ----- 
2023-04-28 18:03:32 -- ******* ---- Linux-5.15.49-linuxkit-x86_64-with-glibc2.31 2023-04-28 18:03:32
2023-04-28 18:03:32 - *** --- * --- 
2023-04-28 18:03:32 - ** ---------- [config]
2023-04-28 18:03:32 - ** ---------- .> app:         application:0x7f87d2687d50
2023-04-28 18:03:32 - ** ---------- .> transport:   sqs://localstack:**@localstack:4566//
2023-04-28 18:03:32 - ** ---------- .> results:     disabled://
2023-04-28 18:03:32 - *** --- * --- .> concurrency: 4 (prefork)
2023-04-28 18:03:32 -- ******* ---- .> task events: OFF (enable -E to monitor tasks in this worker)
2023-04-28 18:03:32 --- ***** ----- 
2023-04-28 18:03:32  -------------- [queues]
2023-04-28 18:03:32                 .> celery           exchange=celery(direct) key=celery
```

タスクが1分ごとに実行されたことを確認できました
```
2023-04-28 18:03:32 [tasks]
2023-04-28 18:03:32   . application.tasks.print_task
2023-04-28 18:03:33 [2023-04-28 18:03:33,554: INFO/MainProcess] Connected to sqs://localstack:**@localstack:4566//
2023-04-28 18:03:33 [2023-04-28 18:03:33,791: WARNING/MainProcess] /root/.cache/pypoetry/virtualenvs/api-MATOk_fk-py3.14/lib/python3.14/site-packages/celery/fixups/django.py:203: UserWarning: Using settings.DEBUG leads to a memory
2023-04-28 18:03:33             leak, never use this setting in production environments!
2023-04-28 18:03:33   warnings.warn('''Using settings.DEBUG leads to a memory
2023-04-28 18:03:33 
2023-04-28 18:03:33 [2023-04-28 18:03:33,791: INFO/MainProcess] celery@aa09391fcfb1 ready.
2023-04-28 18:03:33 [2023-04-28 18:03:33,903: INFO/MainProcess] Task application.tasks.print_task[96665ac5-ec17-4a94-9ba3-dc8edf52e4e9] received
2023-04-28 18:03:33 [2023-04-28 18:03:33,919: WARNING/ForkPoolWorker-2] タスクの実行
2023-04-28 18:03:33 [2023-04-28 18:03:33,920: INFO/ForkPoolWorker-2] Task application.tasks.print_task[96665ac5-ec17-4a94-9ba3-dc8edf52e4e9] succeeded in 0.0012625530362129211s: None
2023-04-28 18:04:00 [2023-04-28 18:04:00,059: INFO/MainProcess] Task application.tasks.print_task[1aba2e01-08cb-4666-bd44-4a87792de7d7] received
2023-04-28 18:04:00 [2023-04-28 18:04:00,085: WARNING/ForkPoolWorker-2] タスクの実行
2023-04-28 18:04:00 [2023-04-28 18:04:00,085: INFO/ForkPoolWorker-2] Task application.tasks.print_task[1aba2e01-08cb-4666-bd44-4a87792de7d7] succeeded in 0.0005537119577638805s: None
2023-04-28 18:05:00 [2023-04-28 18:05:00,052: INFO/MainProcess] Task application.tasks.print_task[b8bb5dd2-8942-403f-9874-9f416746e96b] received
2023-04-28 18:05:00 [2023-04-28 18:05:00,076: WARNING/ForkPoolWorker-2] タスクの実行
```

## 参考
https://docs.celeryq.dev/en/stable/getting-started/backends-and-brokers/sqs.html

https://testdriven.io/blog/django-celery-periodic-tasks/

https://stackoverflow.com/questions/60217193/dockerized-celery-worker-not-picking-up-tasks-from-localstack-sqs-queue

https://dot-blog.jp/news/django-async-celery-redis-mac/

https://docs.localstack.cloud/getting-started/installation/#docker-compose

https://stackoverflow.com/questions/68131349/automatically-create-sqs-queue-using-localstack-and-docker-compose

https://stackoverflow.com/questions/43062120/how-i-can-specify-sqs-queue-name-in-celery


