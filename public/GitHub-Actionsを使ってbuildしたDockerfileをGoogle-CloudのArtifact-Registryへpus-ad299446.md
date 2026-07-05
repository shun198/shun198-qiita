---
title: GitHub Actionsを使ってbuildしたDockerfileをGoogle CloudのArtifact Registryへpushしよう！
tags:
  - Docker
  - GitHubActions
  - GoogleCloud
  - ArtifactRegistry
private: false
updated_at: '2025-09-15T17:11:44+09:00'
id: ad299446f3fda0b23ce3
organization_url_name: null
slide: false
---
## 概要
開発環境検証時に最新のソースコードをCloud RunやGKEに反映させる際、commitなどをトリガーにArtifact Registryへpushできたら便利なので今回はGitHub Actionsを使ってbuildとArtifact Registryへのpushまで自動化させる方法について解説します
GitHub Actions内でArtifact Registryへpushする際はWorkload Indentityを使用します

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

## Artifact Registryの作成
以下のようにArtifact Registryを作成することもできます
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

## ワークフローの作成
以下のようにワークフローを作成します
Google Cloud認証時は作成した
- workload_identity_provider
    - projects/{プロジェクト番号}/locations/global/workloadIdentityPools/github-actions-cicd/providers/github
- service_account

を指定します
その後、Artifact RegistryへpushできるようGoogle Cloud SDKに認証とArtifact Registryへの認証を行います
その後、docker buildとpushを行います

```yaml:build.yaml
name: Build

on:
  push:
    branches:
      - main

jobs:
  build:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v5
      # https://github.com/google-github-actions/auth
      - name: Authenticate to Google Cloud with Workload Identity
        uses: google-github-actions/auth@v3
        with:
          workload_identity_provider: ${{ secrets.WORKLOAD_IDENTITY_PROVIDER }}
          service_account: ${{ secrets.GITHUB_ACTIONS_SA }}
          create_credentials_file: true
      # https://github.com/google-github-actions/setup-gcloud
      - name: Set up Google Cloud SDK
        uses: google-github-actions/setup-gcloud@v2
      - name: Configure Docker for Artifact Registry
        run: gcloud auth configure-docker us-central1-docker.pkg.dev
      - name: Docker Build
        run: |
          docker build -t us-central1-docker.pkg.dev/${{ secrets.GOOGLE_CLOUD_PROJECT }}/app/cloud-run-service-app:latest .
      - name: Push to Google Container Registry
        run: |
          docker push us-central1-docker.pkg.dev/${{ secrets.GOOGLE_CLOUD_PROJECT }}/app/cloud-run-service-app:latest
```

Artifact Registryの認証からpushまでの一連の流れは公式ドキュメント通りです

https://cloud.google.com/artifact-registry/docs/docker/pushing-and-pulling?hl=ja

## 実際に実行してみよう！
以下のようにDockerfileがpushされたら成功です

![Screenshot 2025-09-15 at 14.56.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5ae2e580-1868-4bbb-a330-18b60198c1c9.png)

![Screenshot 2025-09-15 at 14.56.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c21250aa-fe5d-4f62-bfa1-7a24ad8a2b0d.png)

## 参考
https://cloud.google.com/iam/docs/workload-identity-federation?hl=ja

https://roger-that-dev.medium.com/push-code-with-github-actions-to-google-clouds-artifact-registry-60d256f8072f

https://zenn.dev/hi_ka_ru/articles/github-actions-with-workload-identity-20240706

https://zenn.dev/cloud_ace/articles/7fe428ac4f25c8
