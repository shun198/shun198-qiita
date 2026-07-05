---
title: Cloud Run Jobsを使ってPub/Subへメッセージを送ろう！
tags:
  - Terraform
  - PubSub
  - GoogleCloud
  - CloudRun
  - ArtifactRegistry
private: false
updated_at: '2025-04-06T19:34:47+09:00'
id: 49e8dab0ff553f6f4c56
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Cloud Run Jobsを使ってPub/Subへメッセージを送る方法について解説します

## 前提
- 言語はPythonを使用
- パッケージマネージャーはuvを使用
- 今回は手動でCloud Run Jobsを実行します

## 実装
### アプリケーションの作成
Pub/Subへメッセージを送るアプリケーションを作成します
以下がディレクトリ構成です

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

```Dockerfile
FROM ghcr.io/astral-sh/uv:python3.12-alpine

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

COPY pyproject.toml uv.lock ./

# Install dependencies.
RUN uv sync

COPY . ./

CMD ["uv", "run", "python", "main.py"]
```


```.python-version
3.12
```

main.pyに必要な処理を記載します
Pub/Subのクライアントを使って対象のトピックへ向けてpublishメソッドを使ってutf-8でエンコードしたメッセージを送信します
送信後、PubSubのメッセージをprintします

```main.py
import json
import os

from google.cloud import pubsub_v1

PROJECT_ID = os.getenv("GCP_PROJECT")
TOPIC_ID = os.getenv("PUBSUB_TOPIC")

def main():
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(PROJECT_ID, TOPIC_ID)

    message = {"data": "Hello from Cloud Run Job!"}
    future = publisher.publish(topic_path, json.dumps(message).encode("utf-8"))
    print(f"Published message ID: {future.result()}")

if __name__ == "__main__":
    main()
```

今回必要になるパッケージはgoogle-cloud-pubsubです
```pyproject.toml
[project]
name = "cloud-run-job"
version = "0.1.0"
description = "cloud-run-job"
readme = "README.md"
requires-python = ">=3.12"
dependencies = [
    "google-cloud-pubsub>=2.29.0",
]
```

### Terraformファイルの作成
- サービスアカウント
- Artifact Registry
- Pub/Sub
- Cloud Run Jobs


を作成していきます

まずはCloud Run JobsのService Accountを作成します
Cloud Runの実行とPubSubへPublishする権限を付与します

```iam.tf
resource "google_service_account" "cloud_run_jobs_sa" {
  account_id   = "cloud-run-jobs-invoker"
  display_name = "Cloud Run Jobs Invoker"
}

resource "google_project_iam_member" "cloud_run_jobs_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_jobs_sa.email}"
}

resource "google_project_iam_member" "cloud_run_jobs_publisher" {
  project = var.project
  role    = "roles/pubsub.publisher"
  member  = "serviceAccount:${google_service_account.cloud_run_jobs_sa.email}"
}
```

Dockerfileを格納するArtifact Registryを作成します
```registry.tf
resource "google_artifact_registry_repository" "job_artifact_repository" {
  cleanup_policy_dry_run = false
  description            = null
  format                 = "DOCKER"
  location               = var.region
  mode                   = "STANDARD_REPOSITORY"
  project                = var.project
  repository_id          = "job"
}
```

PubSubのトピックとサブスクリプションを作成します
今回はpush_endpointにPub/Subのメッセージを受け取るCloud Run Serviceを作成しています
詳細は下記の記事の通りです

https://qiita.com/shun198/items/8d8ddea271faccf11d24

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

アプリケーションを実行するCloud Run Jobsを作成します

```cloudrun.tf
resource "google_cloud_run_v2_job" "cloud_run_job" {
  name     = "${var.project}-cloud-run-job"
  location = var.region

  template {
    template {
      containers {
        image = "${var.region}-docker.pkg.dev/${var.project}/${google_artifact_registry_repository.job_artifact_repository.repository_id}/fastapi-job:latest"
        env {
          name  = "GCP_PROJECT"
          value = var.project
        }
        env {
          name  = "PUBSUB_TOPIC"
          value = google_pubsub_topic.pubsub.name
        }
      }
      service_account = google_service_account.cloud_run_jobs_sa.email
    }
  }
}
```

### Artifact Registryの作成
まず、Artifact Registryを先に作成します
```
terraform apply -target=google_artifact_registry_repository.job_artifact_repository
```

### イメージのbuildとpush
先ほど作成したDockerfileのbuildとbuildしたDockerfileを作成したArtifact Registryへpushします

```
docker build -t us-central1-docker.pkg.dev/${プロジェクト名}/job/fastapi-job:latest .
```

```
docker push us-central1-docker.pkg.dev/${プロジェクト名}/job/fastapi-job
```

### 残りのインフラの作成
以下のコマンドで作成します

```
terraform apply
```

## 実際に実行してみよう！
Cloud Run Jobを手動で実行します
以下のようにPubSubへメッセージが送られてきたら成功です

![スクリーンショット 2025-04-06 18.33.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/25103030-5578-406c-b674-8f171de417ea.png)

![スクリーンショット 2025-04-06 18.33.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a978dbfa-ec6e-46cb-9a56-818914a62a68.png)

## まとめ
今回はCloud Run Jobを手動で実行して検証しました
次はSchedulerを使って定期実行する記事を書きたいと思います

## 参考
https://cloud.google.com/functions/docs/tutorials/terraform-pubsub?hl=ja

https://cloud.google.com/run/docs/execute/jobs-on-schedule?hl=ja

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_run_v2_job

https://cloud.google.com/pubsub/docs/publisher?hl=ja

https://cloud.google.com/python/docs/reference/pubsub/latest
