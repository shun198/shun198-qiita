---
title: GitHub ActionsとTerraformとWorkload Identityを使ってGoogle Cloudのリソースを自動デプロイしよう！
tags:
  - Terraform
  - GitHubActions
  - GoogleCloud
  - WorkloadIdentity
private: false
updated_at: '2025-09-15T17:13:03+09:00'
id: 978a978d6f4715dc9451
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub ActionsとTerraformとWorkload Identityを使ってコードベースでインフラ周りのデプロイを自動化できるので実装方法について解説します

## 前提
- 必要なAPIを有効化済み

## Workload Identityとは？
> Google Cloud の外部で実行されているアプリケーションは、サービス アカウント キーを使用して Google Cloud リソースにアクセスできます。ただし、サービス アカウント キーは強力な認証情報であり、正しく管理しなければセキュリティ上のリスクとなります。Workload Identity 連携により、サービス アカウント キーに関連するメンテナンスとセキュリティの負担が軽減されます。
Workload Identity 連携を使用すると、Identity and Access Management（IAM）を使用して、外部 ID に IAM ロールを付与し、Google Cloud リソースへの直接アクセスを許可できます。サービス アカウントの権限借用によってアクセス権を付与することもできます。

公式ドキュメントに記載の通り、サービスアカウントキーではなく、IAMロールを使ったGoogle Cloudリソースへのアクセス権を付与する仕組みです
IAMロールを使ったアクセスになるため、サービスアカウントキーのメンテナンスやセキュリティに関する負担が軽減されます

## GitHub ActionsからGoogle Cloudリソースを操作するためのサービスアカウントとIAMの作成
- サービスアカウント
- IAM

を以下のように作成します
今回は検証用のため、ロールはOwner権限にしています

## Workload Identity Federationの作成
IDプールを作成します
今回は名前をIDを以下の通りにします

![Screenshot 2025-09-15 at 13.48.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/884c7b66-b55c-451b-89ed-6bff50eccddf.png)

下記の公式ドキュメントに従ってプロバイダの設定を行います

https://cloud.google.com/iam/docs/workload-identity-federation-with-deployment-pipelines

![Screenshot 2025-09-15 at 13.49.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4b3f848f-4128-49dc-ba95-cd698eaf4983.png)

オーディエンスはデフォルトのものを使用します
![Screenshot 2025-09-15 at 13.50.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5044e3a2-65eb-4a00-9e78-9a808c0d6313.png)

今回は属性マッピングではassertion.repositoryを記載します
属性条件は以下の通りにします
組織名とリポジトリ名はご自身が使用するものに置き換えて設定しましょう

```
assertion.repository == "GitHub組織名/リポジトリ名"
```

![Screenshot 2025-09-15 at 13.51.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9ff882ab-1681-4d6b-aea4-12f3e878c430.png)

以下のように作成できれば成功です
その後、`アクセスを許可`を押します
![Screenshot 2025-09-15 at 13.58.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/70efcd2f-d88c-4955-83bb-87c1fabba818.png)

サービスアカウントの権限借用を使用して権限アクセス権を付与します
subjectには"GitHub組織名/リポジトリ名"を入力します
![Screenshot 2025-09-15 at 14.03.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fb65f76d-a09c-4d88-adfe-796212cce2a7.png)

## 実装
以下のようにmainブランチへのpushをトリガーにTerraformを使って自動デプロイを行うワークフローを作成します
Google Cloud認証時は作成した
- workload_identity_provider
    - projects/{プロジェクト番号}/locations/global/workloadIdentityPools/github-actions-cicd/providers/github
- service_account

を指定します

```yaml:.github/workflows/deploy.yml
name: Deploy

on:
  push:
    branches:
      - main

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v5
      - name: Authenticate to Google Cloud with Workload Identity
        uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIER }}
          service_account: ${{ secrets.SERVICE_ACCOUNT }}
          create_credentials_file: true
      - name: Setup Terraform
        uses: hashicorp/setup-terraform@v3
        with:
          terraform_version: ">1.11.0"
      - name: Terraform Init
        run: terraform init
      - name: Terraform Validate
        run: terraform validate -no-color
      - name: Terraform Plan
        run: terraform plan -no-color
      - name: Terraform Apply
        run: terraform apply -no-color -auto-approve
```

## 参考
https://github.com/hashicorp/setup-terraform

https://zenn.dev/cloud_ace/articles/fcb1f0abf8d67c

https://github.com/google-github-actions/auth

https://cloud.google.com/blog/ja/products/identity-security/secure-your-use-of-third-party-tools-with-identity-federation

https://zenn.dev/hi_ka_ru/articles/github-actions-with-workload-identity-20240706

https://cloud.google.com/iam/docs/workload-identity-federation?hl=ja

https://cloud.google.com/iam/docs/best-practices-for-using-workload-identity-federation?hl=ja&_gl=1*19dy39d*_ga*NDYxNTU0NjE1LjE3NDA4MzE3NTg.*_ga_WH2QY8WWF5*MTc0MzIzMzEyMy4xNS4xLjE3NDMyMzMxMzUuNDguMC4w

https://cloud.google.com/iam/docs/manage-workload-identity-pools-providers?hl=ja

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iam_workload_identity_pool

https://registry.terraform.io/providers/hashicorp/google/latest/docs/resources/iam_workload_identity_pool_provider

https://stackoverflow.com/questions/79082721/why-is-this-workload-identity-pool-not-being-created
