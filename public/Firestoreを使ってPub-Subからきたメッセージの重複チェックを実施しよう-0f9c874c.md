---
title: Firestoreを使ってPub/Subからきたメッセージの重複チェックを実施しよう！
tags:
  - Terraform
  - PubSub
  - Firestore
  - GoogleCloud
  - CloudRun
private: false
updated_at: '2025-05-09T07:24:40+09:00'
id: 0f9c874c11acb08f67ce
organization_url_name: null
slide: false
---
## 概要
Pub/Subへメッセージを送る際にSubscriberでat-least-onceのオプションを有効にしていると稀にメッセージを再配信する可能性があります
Subscriberでexactly-onceのオプションを有効にすることで、メッセージの配信を1回限りに設定はできるものの、Subscriberが複数のリージョンに分散されている場合は再配信される可能性があったり、pushとエクスポートのサブスクリプションではサポートされていなかったりとメッセージが絶対に再配信されない保証ができないです

> 通常、Pub/Sub は各メッセージを公開された順序で 1 回配信します。ただし、メッセージが順不同で配信される場合や複数回配信される場合があります。Pub/Sub は、メッセージの確認応答リクエストが正常に返された後でも、メッセージを再配信する場合があります。この再配信は、サーバーサイドの再起動やクライアントサイドの問題などの問題が原因で発生する可能性があります。したがって、まれにメッセージが再配信される可能性があります。

> StreamingPull API を使用するサブスクライバーを含め、pull サブスクリプション タイプのみが 1 回限りの配信をサポートします。push とエクスポートのサブスクリプションでは 1 回限りの配信はサポートされていません

> 1 回限りの配信の保証は、サブスクライバーが同じリージョンのサービスに接続する場合にのみ適用されます。サブスクライバー アプリケーションが複数のリージョンに分散されていると、1 回限りの配信が有効になっている場合でも、メッセージの重複配信が発生する可能性があります。パブリッシャーは任意のリージョンにメッセージを送信でき、1 回限りの保証は維持されます。

データの重複を許さないアプリケーションを実装している場合はアプリケーション側で一度使用したPub/Subのメッセージの値をFirestoreのCollection内でハッシュ化保存し、全く同じメッセージが来た時はCollection内のハッシュ値を比較し、一致した場合はアプリケーションの処理を終了させる実装がよく行われます
そうすることでメッセージの再配信が万が一行われたとしても重複されないことを担保できます
今回はFirestoreを使ってPub/Subからきたメッセージの重複チェックを行う方法について解説します

## 前提
- PythonとFastAPIを使ったアプリケーションを作成
- パッケージ管理はuvを使用

## 実装
### Docker環境の構築
```
tree
.
├── Dockerfile
├── Makefile
├── README.md
├── __init__.py
├── .dockerignore
├── main.py
├── pyproject.toml
├── service
│   ├── __init__.py
│   └── firestore.py
└── uv.lock
```

- .dockerignore
- Dockerfile
- pyproject.toml

を使ってDocker環境を構築します

```.dockerignore
Dockerfile
.dockerignore
__pycache__
.pytest_cache
.venv
Makefile
.ruff_cache

```

```pyproject.toml
[project]
name = "app"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.115.12",
    "google-cloud>=0.34.0",
    "google-cloud-firestore>=2.20.1",
    "uvicorn>=0.34.0",
]

[dependency-groups]
dev = [
    "ruff>=0.11.5",
]

```

```Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

# Install dependencies.
RUN uv sync --no-dev

COPY . ./

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]

```

### アプリケーションの作成
Pub/Subからのメッセージを受け取ったらCloudRunへPOSTするアプリケーションを作成します
request.json内にPub/SubからのメッセージがJSONで送られます
メッセージのバリデーションをしてからFirestoreへハッシュ値があるか確認します
ハッシュ値がある(同じメッセージをすでに送信済み)の場合は処理を終了させます
同じハッシュ値がないことを確認したら本来はPub/Subのメッセージを使った処理を記載しますが今回はFirestoreを使った重複チェックの実装方法に関する記事なのでなければそのままFirestoreのcollectionへdocumentをInsertします
documentをInsertできたら正常終了です

```main.py
import base64
import logging
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response
from google.cloud import firestore
from service.firestore import FirestoreService

app = FastAPI()

db = firestore.Client(project=os.environ.get("GCP_PROJECT"))

collection = db.collection(os.environ.get("FIRESTORE_COLLECTION_NAME"))

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

firestore_service = FirestoreService(logger, collection)


@app.post("/")
async def index(request: Request):
    """Receive and parse Pub/Sub messages."""
    envelope = await request.json()
    logger.info(f"envelope: {envelope}")
    if not envelope:
        msg = "no Pub/Sub message received"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    if not isinstance(envelope, dict) or "message" not in envelope:
        msg = "invalid Pub/Sub message format"
        logger.error(msg)
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    pubsub_message = envelope["message"]
    if isinstance(pubsub_message, dict) and "data" in pubsub_message:
        try:
            decoded_message = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            logger.info(f"decoded_message: {decoded_message}")
            if firestore_service.if_record_exists(decoded_message):
                logger.info("record already exists")
                return Response(status_code=status.HTTP_204_NO_CONTENT)
            firestore_service.enter_single_record(decoded_message)
            return Response(status_code=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"exception happened: {e}")
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)

```

Firestoreを使った重複チェックを実装します
if_record_existsメソッドでcollectionからハッシュ化された値をgetし、存在するかどうかをreturnします
また、enter_single_recordメソッドでsetを使ってcollectionにdocumentを作成します
expireAtにcollectionの有効期限を設定します
Firestore側でexpireAtを検知して有効期限内か確認する場合はFirestoreの機能で実現できるのでTerraform実装時に後ほど説明します

```firestore.py
import datetime
import hashlib
import json


class FirestoreService:
    def __init__(self, logger, collection):
        self.logger = logger
        self.collection = collection

    def if_record_exists(self, message: str) -> bool:
        """firestoreハッシュ値重複チェック

        Args:
            message (str): decoded Pub/Subメッセージ

        Returns:
            bool: 重複している場合がTrue、重複していない場合がFalse
        """
        hash_ptr = hashlib.md5(message.encode()).hexdigest()
        doc_ref = self.collection.document(hash_ptr)
        try:
            doc = doc_ref.get()
            if doc.exists:
                return True
            return False
        except Exception as e:
            self.logger.error("if record exists Error: ", e)
            return False

    def enter_single_record(self, message: str):
        """重複チェックのためにfirestoreにハッシュ値を登録する

        Args:
            message (str): decoded Pub/Subメッセージ
        """
        json_message = json.loads(message)
        try:
            hash_ptr = hashlib.md5(message.encode()).hexdigest()
            doc_ref = self.collection.document(hash_ptr)
            json_message["expireAt"] = datetime.datetime.now(
                datetime.timezone.utc
            ) + datetime.timedelta(minutes=30)
            doc_ref.set(json_message)
            self.logger.info("record inserted")
        except Exception as e:
            self.logger.error("enter single record Error: ", e)


```

### インフラ
- Artifact Registry
- CloudRun
- Pub/Sub
- Firestore

の必要なリソースを作成します

```artifact_registry.tf
resource "google_artifact_registry_repository" "app_artifact_repository" {
  cleanup_policy_dry_run = false
  description            = null
  format                 = "DOCKER"
  location               = var.region
  mode                   = "STANDARD_REPOSITORY"
  project                = var.project
  repository_id          = "app"
}
```

```cloudrun.tf
resource "google_cloud_run_v2_service" "cloud_run_service" {
  name     = "${var.project}-cloud-run-service"
  location = var.region

  deletion_protection = false

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.app_artifact_repository.repository_id}/fastapi-app:latest"
      env {
        name  = "GCP_PROJECT"
        value = var.project
      }
      env {
        name  = "FIRESTORE_COLLECTION_NAME"
        value = var.collection
      }
      ports {
        container_port = 8080
      }
    }
  }
  depends_on = [
    google_artifact_registry_repository.app_artifact_repository,
  ]
}

```

PubSubからメッセージが来たらCloudRunへメッセージを送りたいのでpush_configを設定します
CloudRunがSubscriberにあたるのでpush_endpointはCloudRunのuriを指定します

```pubsub.tf
resource "google_pubsub_topic" "pubsub" {
  name = "${var.project}-topic"
}

resource "google_pubsub_subscription" "cloud_run_subscription" {
  name  = "pubsub_subscription"
  topic = google_pubsub_topic.pubsub.name
  push_config {
    push_endpoint = google_cloud_run_v2_service.cloud_run_service.uri
    oidc_token {
      service_account_email = google_service_account.cloud_run_sa.email
    }
    attributes = {
      x-goog-version = "v1"
    }
  }
  depends_on = [google_cloud_run_v2_service.cloud_run_service]
}

```

FirestoreにexpireAtのfieldから有効期限を設定する処理を記載できます
fieldの設定は任意ですがdocumentの数が増えてくることを想定して追加することを推奨しています

```firestore.tf
resource "google_firestore_database" "database" {
  project     = var.project
  name        = "(default)"
  location_id = "nam5"
  type        = "FIRESTORE_NATIVE"
}

resource "google_firestore_field" "expireAtTTL" {
  project    = var.project
  collection = "collection"
  database   = google_firestore_database.database.name
  field      = "expireAt"

  ttl_config {}
}

```

## ローカル上で検証するには？
ローカル上で検証する際はPub/Subのメッセージをエンコードした上で実行する必要があります
```python
import base64
import json

js = {
    "data": "Hello World",
}
text = json.dumps(js, ensure_ascii=False)
print(base64.b64encode(text.encode("utf-8")).decode("utf-8"))
```

```
curl -XPOST -d '{"message": {"data": "eyJkYXRhIjogIkhlbGxvIFdvcmxkIn0="}}' http://localhost:8080
```

## 実際に実行してみよう！
以下のようにPub/SubへJSONメッセージを送信することができます
メッセージを送信し、Firestoreへドキュメントが追加されたことを確認できれば成功です

```
gcloud pubsub topics publish {topic_name} --message "{'message': {'data': 'Hello World'}}"
messageIds:
- '14595580847343152'
```

![スクリーンショット 2025-04-13 9.57.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/436c6fd2-362b-48d3-9f7b-89b4d245bceb.png)

もう一度Pub/Subへメッセージを送信し、Firestoreへドキュメントが追加されていないことを確認できれば成功です

![スクリーンショット 2025-04-13 10.19.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d114bedb-e636-499b-a34d-49a6894ac993.png)

![スクリーンショット 2025-04-13 9.57.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/436c6fd2-362b-48d3-9f7b-89b4d245bceb.png)

# 参考
https://firebase.google.com/docs/firestore/data-model?hl=ja


https://cloud.google.com/python/docs/reference/firestore/latest/google.cloud.firestore_v1.client.Client

https://dev.classmethod.jp/articles/use-firestore-to-avoid-cloud-functions-duplicate-execution/
