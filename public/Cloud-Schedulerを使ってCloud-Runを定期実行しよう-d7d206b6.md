---
title: Cloud Schedulerを使ってCloud Runを定期実行しよう！
tags:
  - Terraform
  - cloudscheduler
  - GoogleCloud
  - CloudRun
private: false
updated_at: '2025-04-06T22:59:06+09:00'
id: d7d206b618aeee4436e6
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Cloud Schedulerを使ってCloud Runを定期実行する方法について解説します

## 実装
Cloud Scheduler用のService Accountを作成します
今回はCloud SchedulerのAdmin権限とCloud Runを実行するinvokerの権限を付与します

```iam.tf
resource "google_service_account" "cloud_scheduler_sa" {
  account_id   = "cloud-scheduler-jobs-invoker"
  display_name = "Cloud Scheduler Jobs Invoker"
}

resource "google_project_iam_member" "cloud_scheduler_jobs_admin" {
  project = var.project
  role    = "roles/cloudscheduler.admin"
  member  = "serviceAccount:${google_service_account.cloud_scheduler_sa.email}"
}

resource "google_project_iam_member" "cloud_scheduler_jobs_invoker" {
  project = var.project
  role    = "roles/run.invoker"
  member  = "serviceAccount:${google_service_account.cloud_scheduler_sa.email}"
}
```

Cloud Schedulerを作成します
今回は5分に1回実行するよう設定します
また、uriは以下のようにgoogleapis.comを使って指定しているので認証はoauth_tokenを使用します

```scheduler.tf
resource "google_cloud_scheduler_job" "job_scheduler" {
  name        = "trigger-sample-job"
  region      = var.region
  description = "Trigger Cloud Run Job every 5 minutes"
  schedule    = "*/5 * * * *"
  time_zone   = "Asia/Tokyo"

  http_target {
    http_method = "POST"
    uri         = "https://${google_cloud_run_v2_job.cloud_run_job.location}-run.googleapis.com/apis/run.googleapis.com/v1/namespaces/${var.project_number}/jobs/${google_cloud_run_v2_job.cloud_run_job.name}:run"

    oauth_token {
      service_account_email = google_service_account.cloud_scheduler_sa.email
    }
  }
}
```

## 実際に実行してみよう！
以下のように5分に一回Cloud Runが定期実行できれば成功です

![スクリーンショット 2025-04-06 22.55.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/60da297b-07f9-45e3-9c1b-d15063ab866a.png)

## 参考
https://cloud.google.com/run/docs/execute/jobs-on-schedule?hl=ja#terraform

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/cloud_scheduler_job

https://cloud.google.com/run/docs/troubleshooting?hl=ja#401

https://moito.com/blog/google-cloud-scheduler-call-to-cloud-functions-401-error/
