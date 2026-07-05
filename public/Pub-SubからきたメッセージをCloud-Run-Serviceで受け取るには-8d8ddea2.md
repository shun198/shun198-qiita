---
title: Pub/SubからきたメッセージをCloud Run Serviceで受け取るには
tags:
  - Terraform
  - PubSub
  - GoogleCloud
  - FastAPI
  - CloudRun
private: false
updated_at: '2025-04-06T19:25:16+09:00'
id: 8d8ddea271faccf11d24
organization_url_name: null
slide: false
---
## 概要
Pub/Subからきたメッセージを受け取るCloud Run Serviceのアプリケーションの作成方法について解説します

## 前提
- 言語はPythonを使用
- フレームワークはFastAPIを使用
- パッケージマネージャーはuvを使用

## 実装
### アプリケーションの作成
```
❯ tree
.
├── .dockerignore
├── .python-version
├── Dockerfile
├── README.md
├── main.py
├── pyproject.toml
└── uv.lock
```

```.dockerignore
Dockerfile
.dockerignore
__pycache__
.pytest_cache
.venv
```

uvを使ってパッケージを管理するので以下のようにuvの公式イメージを指定し、
uv syncコマンドでパッケージをインストールしてます
uvicornを使ってアプリケーションを8080番ポートで起動します

```Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

# Install dependencies.
RUN uv sync

COPY . ./

CMD ["uv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```.python-version
3.12
```

main.pyにPub/Subからきたメッセージを受け取る処理を記載します
Pub/Subトピックに送られてきたのをトリガーにmain.py実行されます
今回はメッセージを受け取った後にデコードし、loggerで出力する簡単なアプリケーションを実装しています

```main.py
import base64
import logging

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response

app = FastAPI()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@app.post("/")
async def index(request: Request):
    """Receive and parse Pub/Sub messages."""
    envelope = await request.json()
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
            name = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
        except Exception as e:
            msg = f"failed to decode message data: {e}"
            logger.error(msg)
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=msg)

    logger.info(f"Pub/Sub message: {name}!")
    return Response(status_code=status.HTTP_204_NO_CONTENT)

```

### インフラの作成
- サービスアカウント
- Artifact Registry
- Pub/Sub
- Cloud Run Service

を作成していきます

まずはCloud Run ServiceのService Accountを作成します
Cloud Runの実行権限を付与します

```iam.tf
resource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-service-invoker"
  display_name = "Cloud Run Invoker"
}

resource "google_project_iam_member" "cloud_run_service_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}
```

Dockerfileを格納するArtifact Registryを作成します

```registry.tf
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

PubSubのトピックとサブスクリプションを作成します
push_endpointにPub/Subのメッセージを受け取るCloud Run Serviceを作成していきます

```pubsub.tf
# https://cloud.google.com/functions/docs/tutorials/terraform-pubsub?hl=ja
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

Pub/Subのメッセージを受け取るCloud Run Serviceを作成します
ポート番号はDockerfileで指定した8080にします

```cloudrun.tf
resource "google_cloud_run_v2_service" "cloud_run_service" {
  name     = "${var.project}-cloud-run-service"
  location = var.region

  deletion_protection = false

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.app_artifact_repository.repository_id}/fastapi-app:latest"
      ports {
        container_port = 8080
      }
    }
  }
}
```

## 実際に実行してみよう！
gcloudコマンドでPub/Subへメッセージを送ります

```
gcloud pubsub topics publish ${トピック名} --message "{'msg':'hello'}"
```

以下のように送信したメッセージをアプリケーションで受け取ることができれば成功です

![スクリーンショット 2025-04-06 19.18.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8dc10070-5284-4194-b29b-0d5674e2ea65.png)

## 参考
https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_topic.html

https://cloud.google.com/pubsub/docs/how-to?hl=ja

https://cloud.google.com/pubsub/docs/pubsub-basics?hl=ja

https://cloud.google.com/run/docs/tutorials/pubsub?hl=ja
