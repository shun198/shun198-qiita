---
title: GCSへファイルをアップロードしたのをトリガーにPub/Subへイベントを送信してみよう！
tags:
  - GoogleCloudStorage
  - Terraform
  - PubSub
  - GoogleCloud
private: false
updated_at: '2025-10-01T13:53:17+09:00'
id: 98687818d7ea08b1b06e
organization_url_name: null
slide: false
---
## 概要
Google CloudではCloud StorageサブスクリプションというGoogle Cloud Storageにファイルなどのオブジェクトを新規でアップロードしたり更新したりしたことをトリガーにイベントをPub/Subに連携する仕組みがあります
今回はTerraformを使って実装する方法について解説します

## 前提
- Terraformの初期設定が完了済み

## ディレクトリ構成
```
└── terraform
    ├── env
    │   ├── dev
    │   │   ├── backend.tf
    │   │   ├── main.tf
    │   │   └── variables.tf
    │   └── prod
    │       ├── backend.tf
    │       ├── main.tf
    │       └── variables.tf
    └── modules
        ├── gcs
        │   ├── main.tf
        │   ├── output.tf
        │   └── variables.tf
        └── pubsub
            ├── main.tf
            └── variables.tf
```

## 実装
### env/dev内の設定
- GCS
- Pub/Sub

のmoduleを作成します
```terraform/env/dev/main.tf
# https://developer.hashicorp.com/terraform/tutorials/gcp-get-started/google-cloud-platform-build
terraform {
  required_version = ">= 1.11.0"

  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "6.8.0"
    }
  }
}

provider "google" {
  project = var.project
  region  = var.region
}

module "pubsub" {
  source = "../../modules/pubsub"

  project                         = var.project
  pubsub_notification_bucket_name = module.gcs.pubsub_notification_bucket_name
}

module "gcs" {
  source  = "../../modules/gcs"
  project = var.project
}
```

dev配下で共通利用する変数を定義します
プロジェクト名は自身が使用するものに置き換えてください

```variables.tf
variable "project" {
  type = "dev-project"
}

variable "region" {
  type    = string
  default = "us-central1"
}

```

### GCSの設定
GCSを作成します
バケット名は一意になるよう設定します

```terraform/modules/gcs/main.tf
resource "google_storage_bucket" "pubsub_notification_bucket" {
  name     = "${var.project}-pubsub-notification-bucket"
  location = "US"

  uniform_bucket_level_access = true

  lifecycle {
    prevent_destroy = false
  }

}
```

```terraform/modules/gcs/variables.tf
variable "project" {
  type = string
}
```

Pub/Subのmoduleでバケット名を使用するのでバケット名を定義します

```output.tf
output "pubsub_notification_bucket_name" {
  value       = google_storage_bucket.pubsub_notification_bucket.name
  description = "The name of the Pub/Sub notification bucket"
}
```

### Pub/Sub
Pub/Subの
- Topic
- Subscription
- Cloud Storage Subscription

の設定を行います
`google_storage_notification`のリソースブロック内に対象のbucket, topicを紐づけます
オブジェクトのイベントは
- OBJECT_FINALIZE
- OBJECT_METADATA_UPDATE
- OBJECT_DELETE
- OBJECT_ARCHIVE

の4種類を指定できます
今回はオブジェクトの新規作成、更新時をトリガーにイベントを送りたいので以下のように設定してます
object_name_prefixで特定のパス配下でイベントが発生したら送るよう設定してます
`google_pubsub_topic_iam_binding`のリソースブロックではGCSのサービスアカウントにPub/Subへイベントを送れるようpublishのロールを付与するよう設定してます
Pub/Subのsubscriberについてはデフォルトのpull subscriptionで作成します

```terraform/modules/pubsub/main.tf
resource "google_storage_notification" "pubsub_notification" {
  bucket             = var.pubsub_notification_bucket_name
  payload_format     = "JSON_API_V1"
  topic              = google_pubsub_topic.gcs_notification_topic.id
  event_types        = ["OBJECT_FINALIZE", "OBJECT_METADATA_UPDATE"]
  object_name_prefix = "tmp/"
  depends_on         = [google_pubsub_topic_iam_binding.pubsub_topic_binding]
}

data "google_storage_project_service_account" "gcs_account" {
}

resource "google_pubsub_topic_iam_binding" "pubsub_topic_binding" {
  topic      = google_pubsub_topic.gcs_notification_topic.name
  role       = "roles/pubsub.publisher"
  members    = ["serviceAccount:${data.google_storage_project_service_account.gcs_account.email_address}"]
  depends_on = [google_pubsub_topic.gcs_notification_topic]
}

resource "google_pubsub_topic" "gcs_notification_topic" {
  name = "${var.project}-gcs-notification-topic"
}

resource "google_pubsub_subscription" "gcs_notification_subscription" {
  name  = "${var.project}-gcs-notification-subscription"
  topic = google_pubsub_topic.gcs_notification_topic.name
}
```

```terraform/modules/pubsub/variables.tf
variable "project" {
  type = string
}

variable "pubsub_notification_bucket_name" {
  description = "Name of the GCS bucket for PubSub notifications"
  type        = string
}
```

## 実際に実行してみよう！
terraform apply後、GCSとPub/Subが作成できれば成功です

![Screenshot 2025-10-01 at 10.20.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7e7ec682-6d48-4092-8027-6c033d01b40f.png)

![Screenshot 2025-10-01 at 10.23.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a1aac939-b694-4256-af4c-fec814ead8d1.png)

![Screenshot 2025-10-01 at 10.24.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/37e72f59-678b-419d-9b3d-51525fd4ba2b.png)


試しにGCSのtmp/内にファイルをアップロードしてみます

![Screenshot 2025-10-01 at 10.25.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62757f8b-8c95-4b89-b967-a4fd37b7078d.png)

GCSにファイルが新規でアップロードされた際のOBJECT_FINALIZEイベントをトリガーにsubscriberへイベントが送信されました
今回作成したsubscriberはpull型なので、作成したsubscriberを選択してpullボタンを押します

![Screenshot 2025-10-01 at 10.26.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2d497e01-3242-4c09-a7fc-920755cff8ca.png)

以下のようにイベントを取得できれば成功です
![Screenshot 2025-10-01 at 10.28.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6808f1a3-8fcb-454a-bd03-360477f2aeba.png)

## 参考
https://cloud.google.com/storage/docs/pubsub-notifications?hl=ja

https://cloud.google.com/storage/docs/reporting-changes?hl=ja#terraform

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/storage_notification
