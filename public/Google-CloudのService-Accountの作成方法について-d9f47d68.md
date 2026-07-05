---
title: Google CloudのService Accountの作成方法について
tags:
  - IAM
  - Terraform
  - ServiceAccount
  - GoogleCloud
private: false
updated_at: '2025-03-23T13:56:19+09:00'
id: d9f47d68a407cd3d1883
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- 今回はBigQueryのScheduled Queryのリソースを例に説明します

## ServiceAccountとは
> サービス アカウントは、ユーザーではなく、アプリケーションや Compute Engine インスタンスなどのコンピューティング ワークロードで通常使用される特別なアカウントです。サービス アカウントは、アカウント固有のメールアドレスで識別されます。

簡単にいうとリソースごとに実行するためのアカウントを使用する仕組みです
Google Cloudの各サービス用のAPIが提供されており、サービスごとのAPIを実行するには対象のAPIの呼び出しをユーザのアカウントではなく、サービスアカウント経由で使用することで
- API キーを使わずにIAMを通じて安全に権限管理できる
- 必要なリソースへの最小のアクセス権限のみ付与できるようになる

などのメリットがあります
AWSでいうIAM Roleに該当するかと思います

## ServiceAccountと必要なIAMメンバーの作成方法
Scheduled Queryを実行するためのサービスアカウントと必要な権限が付与されたIAMメンバーを作成します
今回は
- BigQuery Data Transfer Service エージェントのロールをもつIAMメンバー
    - BigQuery Data TransferのAPIを有効化するため
- BigQuery 管理者のロールをもつIAMメンバー
    - Scheduled Queryの実行、更新権限が付与されている

を作成します

```iam.tf
resource "google_service_account" resource "google_service_account" "scheduled_query_service_account" {
  account_id   = "scheduled-query-sa"
  display_name = "Scheduled Query Service Account"
}


resource "google_project_iam_member" "bq_admin" {
  project = var.project
  role    = "roles/bigquery.admin"
  member  = "serviceAccount:${google_service_account.scheduled_query_service_account.email}"
}

resource "google_project_iam_member" "bq_transfer" {
  project = var.project
  role    = "roles/bigquerydatatransfer.serviceAgent"
  member  = "serviceAccount:${google_service_account.scheduled_query_service_account.email}"
}
```

以下のように
- BigQuery Data Transfer Service エージェント
- BigQuery 管理者

のロールが付与された状態でService Accountが作成されていたら成功です

![スクリーンショット 2025-03-23 10.35.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/331ee3ab-894e-4f83-a12f-48065a270af2.png)


## サービスアカウントの付与
作成したサービスアカウントをScheduled Queryに設定します
serviec_account_nameへService Accountのメールを紐づけることで実現できます

```bigquery.tf
resource "google_bigquery_data_transfer_config" "insert_coupon_usage_query" {
  data_refresh_window_days  = 0
  data_source_id            = "scheduled_query"
  destination_dataset_id    = null
  disabled                  = true
  display_name              = "insert_coupon_usage"
  location                  = "us"
  notification_pubsub_topic = null
  params = {
    query = templatefile("${path.module}/query/insert_coupon_usage.sql", {
      dataset = var.dataset
    })
  }
  project              = var.project
  schedule             = "every 15 minutes synchronized"
  service_account_name = google_service_account.scheduled_query_service_account.email
}
```

以下のようにScheduled Queryを実行できれば成功です

![スクリーンショット 2025-03-23 10.46.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5e3ae608-4d73-442d-85a4-0c58ea654cc4.png)

## 必要なロールの確認方法
`サービス名 IAM`などと調べることで権限の一覧が記載されている公式ドキュメントを閲覧できます
今後自身でサービスに必要な権限を調べる際は公式ドキュメントを熟読することを推奨しm

https://cloud.google.com/bigquery/docs/access-control?hl=ja

## カスタムロールの作成方法
今回はroles/bigquery.adminのロールを使用したので実行に成功しましたがScheduled Query実行時に不要なBigQueryの権限も付与されているので権限が大きすぎます
そのため、Scheduled Queryの権限とBigQueryのテーブルへの参照、更新のみ付与されたカスタムロールを作成するのも手です
google_project_iam_custom_roleを作成し、permissions内に必要な権限を記載していきます

```iam.tf
resource "google_service_account" "scheduled_query_service_account" {
  account_id   = "scheduled-query-sa"
  display_name = "Scheduled Query Service Account"
}

resource "google_project_iam_member" "bq_transfer" {
  project = var.project
  role    = "roles/bigquerydatatransfer.serviceAgent"
  member  = "serviceAccount:${google_service_account.scheduled_query_service_account.email}"
}

resource "google_project_iam_member" "custom_bq_transfer" {
  project = var.project
  role    = google_project_iam_custom_role.custom_bigquery_transfer_role.name
  member  = "serviceAccount:${google_service_account.scheduled_query_service_account.email}"
}

resource "google_project_iam_custom_role" "custom_bigquery_transfer_role" {
  project     = var.project
  role_id     = "customBigQueryTransferRole"
  title       = "Custom BigQuery Transfer Role"
  description = "Custom role with BigQuery Transfer permissions"
  permissions = [
    "bigquery.tables.getData",
    "bigquery.tables.updateData",
    "bigquery.transfers.get",
    "bigquery.transfers.update",
  ]
}
```

以下のように
- BigQuery Data Transfer Service エージェント
- BigQuery カスタムロール

のロールが付与された状態でService Accountが作成されていたら成功です

![スクリーンショット 2025-03-23 10.51.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b0f48b8d-ce0d-4469-b92b-f74d882b103c.png)

![スクリーンショット 2025-03-23 11.07.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/aa06ca45-ca21-4c3a-8332-0b8c38027746.png)

以下のようにScheduled Queryを実行できれば成功です

![スクリーンショット 2025-03-23 11.07.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f4ddc829-fa3e-4939-b43b-48dd39d5d945.png)


## 参考
https://cloud.google.com/iam/docs/service-account-overview?hl=ja

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_service_account

https://dev.classmethod.jp/articles/20240510-tera-sc/

https://cloud.google.com/bigquery/docs/access-control?hl=ja

https://cloud.google.com/bigquery/docs/enable-transfer-service?hl=ja

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/google_project_iam_custom_role

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_data_transfer_config
