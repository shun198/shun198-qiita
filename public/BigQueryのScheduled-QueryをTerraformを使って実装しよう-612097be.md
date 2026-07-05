---
title: BigQueryのScheduled QueryをTerraformを使って実装しよう！
tags:
  - BigQuery
  - Terraform
  - GoogleCloud
private: false
updated_at: '2025-03-15T09:21:10+09:00'
id: 612097beaffe3f163eae
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
BigQueryのScheduled QueryをTerraformで管理できたら非常に便利なので実装方法について解説します

## 前提
- BigQuery Data Transfer Service を有効にする
    - https://cloud.google.com/bigquery/docs/enable-transfer-service?hl=ja

## 実装
Scheduled QueryをTerraform化する際はgoogle_bigquery_data_transfer_configを使用します
今回はPub/Sub topicやservice_accountの設定を行っていないのでnullにしています
paramsにSQLを記載しますが、そのまま書くとdatasetを動的に変えることができない上にsqlfluffなどのリンターを使用できないのでtemplatefile関数を使って別ファイルに切り出してます

```bigquery.tf
resource "google_bigquery_data_transfer_config" "insert_coupon_usage" {
  data_refresh_window_days  = 0
  data_source_id            = "scheduled_query"
  destination_dataset_id    = null
  disabled                  = false
  display_name              = "insert_coupon_usage"
  location                  = "us"
  notification_pubsub_topic = null
  params = {
    query = templatefile("${path.module}/query/insert_coupon_usage.sql", {
      dataset = var.dataset
    })
  }
  project              = var.project
  schedule             = "every 15 minutes"
  service_account_name = null
}

```

templatefile関数を使うことで変数のdatasetを動的に変えることができます
例えば複数環境で同じSQLファイルを参照させたいときに重宝します

```sql
MERGE INTO ${dataset}.used_coupons AS target
USING (
    SELECT user_id, coupon_code, used_at
    FROM ${dataset}.coupon_usage
    WHERE is_used = TRUE
)
AS source ON target.user_id = source.user_id
AND target.coupon_code = source.coupon_code
WHEN NOT MATCHED THEN
    INSERT (user_id, coupon_code, used_at, migrated_at)
    VALUES (source.user_id, source.coupon_code, source.used_at, CURRENT_TIMESTAMP());
```

## 実行結果
terraform applyした後に以下のようにScheduled Queryが作成および実行されたら成功です

![スクリーンショット 2025-03-08 15.14.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bd6dc61a-ed54-43da-8924-ce5938be3ebc.png)

![スクリーンショット 2025-03-08 15.14.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/326b24bc-f1d6-4ee9-a852-d5433e7fcf08.png)

## import blockを使用したい時
import blockを使って既存のScheduled QueryをTerraform化する方法について記載します
以下のようにリソースidとリソース名を指定します

```import.tf
import {
  id = "projects/111111111111/locations/us/transferConfigs/11111111-1111-1111-1111-111111111111"
  to = google_bigquery_data_transfer_config.insert_coupon_usage
}
```

idはコンソール上の以下のリソース名から取得できます

![スクリーンショット 2025-03-08 15.15.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1b96da5b-526b-44c5-a059-59c13efc0e4b.png)

以下のコマンドを実行し、bigquery.tfにScheduled Queryの設定が出力されたら成功です

```
terraform plan -generate-config-out=bigquery.tf
```

```bigquery.tf
# __generated__ by Terraform
# Please review these resources and move them into your main configuration files.

# __generated__ by Terraform from "projects/111111111111/locations/us/transferConfigs/11111111-1111-1111-1111-111111111111"
resource "google_bigquery_data_transfer_config" "insert_coupon_usage" {
  data_refresh_window_days  = 0
  data_source_id            = "scheduled_query"
  destination_dataset_id    = null
  disabled                  = false
  display_name              = "insert_coupon_usage"
  location                  = "us"
  notification_pubsub_topic = null
  params = {
    query = "MERGE INTO practice_dataset.used_coupons AS target\nUSING (\n    SELECT user_id, coupon_code, used_at\n    FROM practice_dataset.coupon_usage\n    WHERE is_used = TRUE\n) AS source\nON target.user_id = source.user_id AND target.coupon_code = source.coupon_code\nWHEN NOT MATCHED THEN\n    INSERT (user_id, coupon_code, used_at, migrated_at)\n    VALUES (source.user_id, source.coupon_code, source.used_at, CURRENT_TIMESTAMP());\n\n"
  }
  project              = "practice01-dev"
  schedule             = "every 15 minutes"
  service_account_name = null
}

```

## 0:00ぴったりに定期実行するには？
現状の記述だとデプロイされた時間を起点に定期実行されます
例えば0:00から15分おきに実行したい、というニーズがある場合は下記のように`synchronized`を記載する必要があります

```bigquery.tf
resource "google_bigquery_data_transfer_config" "insert_coupon_usage" {
  data_refresh_window_days  = 0
  data_source_id            = "scheduled_query"
  destination_dataset_id    = null
  disabled                  = false
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
  service_account_name = null
}
```

詳細は下記公式ドキュメントの`開始時刻の間隔`のタグを参照してください

https://cloud.google.com/appengine/docs/flexible/scheduling-jobs-with-cron-yaml?hl=ja#%E9%96%8B%E5%A7%8B%E6%99%82%E5%88%BB%E3%81%AE%E9%96%93%E9%9A%94

## 参考
https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/bigquery_data_transfer_config

https://developer.hashicorp.com/terraform/language/import

https://dev.classmethod.jp/articles/terraform-import-command-and-import-block/

https://developer.hashicorp.com/terraform/language/functions/templatefile

https://zenn.dev/t_horikoshi/articles/25f3f2216a7108

https://cloud.google.com/appengine/docs/flexible/scheduling-jobs-with-cron-yaml?hl=ja#%E9%96%8B%E5%A7%8B%E6%99%82%E5%88%BB%E3%81%AE%E9%96%93%E9%9A%94

https://qiita.com/shiozaki/items/ae85f3f9403129e5a359
