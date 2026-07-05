---
title: Pub/SubとBigQueryを連携してBigquery Subscriptionを実装するには？
tags:
  - Python
  - BigQuery
  - Terraform
  - PubSub
  - GoogleCloud
private: false
updated_at: '2026-02-28T09:36:03+09:00'
id: 9c5e96b415d43c670fc4
organization_url_name: null
slide: false
---
## 概要
Pub/SubとBigQueryを連携することでBigQuery Subscriptionという機能を使用することができます
BigQuery SubscriptionとPub/Subが受け取ったイベントをBigQueryへ書き込無仕組みで使用するメリットは以下の通りになります

- Pub/Sub -> BigQuery間の中間処理を実装する必要がなくなる
- 中間処理実装時はBigQueryのClientを使用することになるので、Client使用時のrate limitを気にしなくてよくなる
- Pub/SubのschemaとBigQueryのtable schemaを紐づける事ができるので、型安全が担保される

今回はPub/Sub -> Cloud Runのバッチ内でPython/FastAPI/Terraformを使ってBigQuery Subscriptionを実装してみます
BigQuery Subscription使用時はPub/Subから受け取ったメッセージをBigQueryに履歴として保存します

## 実装
### インフラ
インフラを実装するので以下のコンポーネントが必要です
- Pub/Sub
- BigQuery
- IAM
- Cloud Run
- Artifact Registry

順番に説明していきます

#### Pub/Sub
PubSub -> Cloud Run用とBigQuery Subcription用のTopicとSubscriptionを実装します
Subscriptionのbigquery_configにBigQuery Subscriptionの設定を記載します
今回は下記のドキュメントに記載のメタデータを書き込むオプションをTrueにして以下のfieldをBigQueryへ書き込みます

- subscription_name
- message_id
- publish_time
- data
- attributes

https://docs.cloud.google.com/pubsub/docs/create-bigquery-subscription?hl=ja#write-metadata

```pubsub/main.tf
resource "google_pubsub_topic" "pubsub" {
  name = "${var.project}-topic"
}

resource "google_pubsub_subscription" "cloud_run_subscription" {
  name  = "${var.project}-subscription"
  topic = google_pubsub_topic.pubsub.name
  push_config {
    push_endpoint = var.cloud_run_service_uri
    oidc_token {
      service_account_email = var.cloud_run_service_account_email
    }
    attributes = {
      x-goog-version = "v1"
    }
  }
  filter = null
}

resource "google_pubsub_topic" "pubsub_bq_topic" {
  name = "${var.project}-bq-topic"
}

resource "google_pubsub_subscription" "bq_subscription" {
  name  = "shun198-bq-subscription"
  topic = google_pubsub_topic.pubsub_bq_topic.id

  bigquery_config {
    table                 = "${var.project}.${var.pubsub_history_dataset_id}.${var.bq_subscription_history_table_id}"
    use_table_schema      = false
    use_topic_schema      = false
    write_metadata        = true
    drop_unknown_fields   = true
    service_account_email = var.bq_subscription_service_account_email
  }
}

```

#### BigQuery
```bigquery/main.tf
resource "google_bigquery_dataset" "pubsub_history" {
  dataset_id                  = "pubsub_history"
  location                    = "US"
  project                     = var.project
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "bq_subscription_history" {
  clustering          = null
  dataset_id          = google_bigquery_dataset.pubsub_history.dataset_id
  deletion_protection = false
  description         = "History of messages sent to the subscription"
  expiration_time     = 0
  project             = var.project
  schema = jsonencode([{
    mode = "NULLABLE"
    name = "subscription_name"
    type = "STRING"
    }, {
    mode = "NULLABLE"
    name = "message_id"
    type = "STRING"
    }, {
    mode = "NULLABLE"
    name = "publish_time"
    type = "TIMESTAMP"
    }, {
    mode = "NULLABLE"
    name = "data"
    type = "STRING"
    }, {
    mode = "NULLABLE"
    name = "attributes"
    type = "STRING"
  }])
  table_id = "bq_subscription_history"
}
```

#### iam
Cloud Run Serviceに対して必要な権限をservice accountに付与します
- roles/run.invoker

がないとPub/Subからのイベント受け取り時に認証エラーが出るので忘れず付与しましょう

```
Important: To accept authenticated invocations to your Cloud Run service, you must associate your trigger with a service account that has the roles/run.invoker role. When creating or updating your trigger, select that service account.
```

https://docs.cloud.google.com/eventarc/standard/docs/run/route-trigger-cloud-pubsub?hl=ja

また、今回はカスタムサービスアカウントを使用するので、カスタムサービスアカウントに
- roles/bigquery.dataEditor

ロールを付与するのに加えて、
BigQuery Subscriptionを実施する際にPub/Subのservice agent(service-project-number@gcp-sa-pubsub.iam.gserviceaccount.com)に対して

- iam.serviceAccounts.getAccessToken 

を付与することでPub/Subのservice agentがカスタムサービスアカウントのaccess tokenを取得して認証できるようにします

```iam/main.tf
esource "google_service_account" "cloud_run_sa" {
  account_id   = "cloud-run-service-invoker"
  display_name = "Cloud Run Service Invoker"
}

resource "google_project_iam_member" "cloud_run_service_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_service_bigquery_admin" {
  project = var.project
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_project_iam_member" "cloud_run_service_pubsub_admin" {
  project = var.project
  role    = "roles/pubsub.admin"
  member  = "serviceAccount:${google_service_account.cloud_run_sa.email}"
}

resource "google_service_account" "bq_subscription" {
  account_id   = "bq-subscription-sa"
  display_name = "Service Account for BigQuery Subscription"
}

resource "google_project_iam_member" "bq_data_editor" {
  project = var.project
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.bq_subscription.email}"
}

https://docs.cloud.google.com/pubsub/docs/create-bigquery-subscription?hl=ja#assign_bigquery_custom_service_account
resource "google_service_account_iam_member" "allow_pubsub_sa_to_get_token" {
  service_account_id = google_service_account.bq_subscription.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${var.project_number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_service_account_iam_member" "allow_pubsub_sa_to_get_token" {
  service_account_id = google_service_account.bq_subscription.name
  role               = "roles/iam.serviceAccountTokenCreator"
  member             = "serviceAccount:service-${var.project_number}@gcp-sa-pubsub.iam.gserviceaccount.com"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.bq_subscription.email}"
}
```

#### Cloud Run

```cloud_run/main.tf
resource "google_cloud_run_v2_service" "cloud_run_service" {
  name     = "${var.project}-cloud-run-service"
  location = var.region

  deletion_protection = false

  template {
    containers {
      image = "${var.region}-docker.pkg.dev/${var.project}/${var.app_artifact_repository_id}/cloud-run-service-app:latest"
      env {
        name  = "GCP_PROJECT"
        value = var.project
      }
      env {
        name  = "BQ_PUBSUB_TOPIC_NAME"
        value = var.google_pubsub_bq_subscription_topic_name
      }
      ports {
        container_port = 8080
      }
    }
    service_account = var.cloud_run_service_account_email
  }
}
```

```artifact_registry/main.tf
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

### アプリケーション
Python/FastAPIで実行しているCloud Run Service内でcallするためのpostのAPIを作成します
今回は最低限のバリデーションしかしてませんので必要に応じて自身でバリデーションを追加してください
Pub/Subからイベントを受け取ったあとはバリデーションし、メッセージに問題がなければdecodeし、bq_subscription_serviceを呼び出し、後続のBigQuery Subscriptioinの処理を実施します

```main.py
import base64
import logging
import os

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import Response
from google.cloud import pubsub_v1
from service.bq_subscription import SendHistoryToBigQueryService

app = FastAPI()

project = os.environ.get("GCP_PROJECT")

bq_topic = os.environ.get('BQ_PUBSUB_TOPIC_NAME')

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

publisher = pubsub_v1.PublisherClient()

topic_path = publisher.topic_path(
    project,
    bq_topic
)

bq_subscription_service = SendHistoryToBigQueryService(logger, publisher, topic_path)


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
            decoded_str = base64.b64decode(pubsub_message["data"]).decode("utf-8").strip()
            logger.info(f"decoded_message: {decoded_str}")
            bq_subscription_service.regist(decoded_str)
            logger.info("request succeeded")
            return Response(status_code=status.HTTP_200_OK)
        except Exception as e:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"exception happened: {e}")
    else:
        return Response(status_code=status.HTTP_204_NO_CONTENT)
```

Pub/Sub Clientのpublisher.publishメソットを実行して該当するプロジェクトのBigQuery Subscriptionのtopicに対して非同期でメッセージを送ります
topicが受け取ったメッセージはBigQueryへ書き込まれます

https://docs.cloud.google.com/pubsub/docs/publish-receive-messages-client-library#publish_messages

```service/bq_subscription.py
import json


class SendHistoryToBigQueryService:
    def __init__(self, logger, publisher, topic_path):
        self.logger = logger
        self.publisher = publisher
        self.topic_path = topic_path

    def regist(
        self,
        message: str,
    ) -> None:
        try:
            json_message = json.loads(message)
            encoded_message = json.dumps(json_message).encode("utf-8")
            # 送信履歴テーブル更新用Pub/Subメッセージ送信
            future = self.publisher.publish(self.topic_path, encoded_message)
            future.result()
            self.logger.info("message history written inside BigQuery")
        except Exception as e:
            self.logger.error(f"Error updating history table: {e}")

```

## 実際に検証してみよう！
リソース作成後、手動でPub/Subイベントを送ってみましょう

```
gcloud pubsub topics publish ${var.project}-topic --message='{"data":"Hello World!"}' 
```

以下のようにメッセージを受け取り、BigQueryへ受け取ったメッセージの書き込みが行われていたら成功です

![Screenshot 2026-02-28 at 9.24.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f11fdf09-f77d-4833-ac23-614eccde8ff6.png)

![Screenshot 2026-02-28 at 9.24.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/59a3f70c-b0a4-454f-8f59-c492d3d631e8.png)


## 参考
https://cloud.google.com/pubsub/docs/samples/pubsub-create-bigquery-subscription?hl=ja

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription#example-usage---pubsub-subscription-push-bq

https://dev.classmethod.jp/articles/release-bq-pubsub/
