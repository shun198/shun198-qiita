---
title: Pub/Subで設定したDead Letter QueueのメッセージをBigQueryで管理するには？
tags:
  - BigQuery
  - Terraform
  - PubSub
  - GoogleCloud
private: false
updated_at: '2025-04-19T09:13:28+09:00'
id: 2ed2affa5e7b197d17ce
organization_url_name: null
slide: false
---
## 概要
Pub/Subに入ったメッセージをSubscriberへ何かしらの理由で送信できなかったことを想定してDLQ(Dead Letter Queue)を作成するケースがあるかと思います
BigQuery SubscriptionとDLQを組み合わせて使用すれば実現できます
今回はDLQの作成方法およびDLQ内のメッセージを履歴としてBigQueryのテーブルで管理する方法について解説します

## 前提
下記記事をもとに実装しています
CloudRun、Pub/Subの設定等について詳細に知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/0f9c874c11acb08f67ce

## 実装
- BigQueryとPub/SubのService Account
- BigQueryのDatasetとTable
- DLQ用のPub/SubのTopicとSubscriber

の順に作成します

### BigQueryとPub/SubのService Account
今回はBigQuery テーブルへの書き込み権限とPub/Subのeditor権限が必要なので以下のように記載します

```iam.tf
resource "google_service_account" "dlq_to_bq_sa" {
  account_id   = "dlq-to-bq-sa"
  display_name = "Service Account for DLQ to BigQuery push"
}
resource "google_project_iam_member" "bq_data_editor" {
  project = var.project
  role    = "roles/bigquery.dataEditor"
  member  = "serviceAccount:${google_service_account.dlq_to_bq_sa.email}"
}

resource "google_project_iam_member" "pubsub_subscriber" {
  project = var.project
  role    = "roles/pubsub.editor"
  member  = "serviceAccount:${google_service_account.dlq_to_bq_sa.email}"
}
```

### BigQueryのDatasetとTable
DLQにメッセージが入った時に履歴として入れるDatasetとTableを作成します
今回はPub/SubトピックのschemaをBigQueryのTableに適用します
必要なカラムは以下のとおりです

|パラメータ|型|詳細|
|--|--|--|
|subscription_name|STRING|サブスクリプション名|
|message_id|STRING|メッセージID|
|publish_time|TIMESTAMP|メッセージがパブリッシュされた時刻|
|data|BYTES、STRING、または JSON|メッセージの本文|
|attributes|STRING または JSON|すべてのメッセージ属性を含む JSON オブジェクト|

https://cloud.google.com/pubsub/docs/subscription-properties?hl=ja#use-topic-schema

```bigquery.tf
resource "google_bigquery_dataset" "pubsub_history" {
  dataset_id                  = "pubsub_history"
  location                    = "EU"
  default_table_expiration_ms = null
}

resource "google_bigquery_table" "dlq_errors" {
  clustering          = null
  dataset_id          = google_bigquery_dataset.pubsub_history.dataset_id
  deletion_protection = false
  description         = "Error logs for messages sent to the dead letter queue"
  expiration_time     = 0
  project             = var.project
  schema = jsonencode([{
    mode = "NULLABLE"
    name = "data"
    type = "STRING"
  }])
  table_id = "dlq_errors"
}
```

### DLQ用のPub/SubのTopicとSubscriber
DLQ用のPub/SubのTopicとSubscriberを作成します
Subscriberのbigquery_configの箇所でBigQueryの設定の詳細を記載します
対象のテーブル、テーブルのスキーマ定義に合わせてデータを入れるか、などの設定をします
今回はPub/Subのスキーマを使用するのでuse_topic_schemaとwrite_metadataをTrueに設定します

```pubsub.tf
resource "google_pubsub_topic" "pubsub" {
  name = "${var.project}-topic"
}
resource "google_pubsub_subscription" "cloud_run_subscription" {
  name  = "${var.project}-subscription"
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
  dead_letter_policy {
    dead_letter_topic     = google_pubsub_topic.pubsub_dlq.id
    max_delivery_attempts = 5
  }
  depends_on = [google_cloud_run_v2_service.cloud_run_service]
}

resource "google_pubsub_topic" "pubsub_dlq" {
  name = "${var.project}-dlq-topic"
}

resource "google_pubsub_subscription" "pubsub_dlq_subscription" {
  ack_deadline_seconds         = 600
  enable_exactly_once_delivery = false
  enable_message_ordering      = false
  filter                       = null
  labels                       = {}
  message_retention_duration   = "604800s"
  name                         = "${google_pubsub_topic.pubsub_dlq.name}-sub"
  project                      = var.project
  retain_acked_messages        = false
  topic                        = google_pubsub_topic.pubsub_dlq.id

  bigquery_config {
    drop_unknown_fields   = false
    table                 = "${var.project}.${google_bigquery_dataset.pubsub_history.dataset_id}.${google_bigquery_table.dlq_errors.table_id}"
    use_table_schema      = false
    use_topic_schema      = true
    write_metadata        = true
    service_account_email = google_service_account.dlq_to_bq_sa.email
  }

  expiration_policy {
    ttl = ""
  }
  retry_policy {
    maximum_backoff = "30s"
    minimum_backoff = "5s"
  }
  depends_on = [
    google_pubsub_topic.pubsub_dlq,
    google_bigquery_table.dlq_errors
  ]
}
```

## Subscriberとして設定したCloudRunのソースコード
Pub/Subからメッセージを送ったことをトリガーに下記のコードを実行します

```python
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

## 実際に実行してみよう！
今回は検証のためDLQの設定をしたPub/Subそのままメッセージを送信します
CloudRun側ではJSONのメッセージが送られる前提で処理をするのでstringを送って400を返すようにします

```
gcloud pubsub topics publish {topic_name} --message='hello'
```

以下のようにCloudRun側で400を返し、作成したDLQ用のテーブルにメッセージの詳細がカラムとしてInsertされていたら成功です

![スクリーンショット 2025-04-19 9.08.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1fcc9837-2337-458b-b6d6-2a9215788900.png)

![スクリーンショット 2025-04-19 9.09.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cf443745-3c76-4b09-b989-3cf32cfb2077.png)


## 参考
https://cloud.google.com/pubsub/docs/handling-failures?hl=ja#dead_letter_topic

https://cloud.google.com/pubsub/docs/create-bigquery-subscription?hl=ja#roles-permissions-for-subscriptions

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/pubsub_subscription

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_dataset
