---
title: Swaggerで作成したAPI仕様書をGitHub Pagesにデプロイしよう！
tags:
  - swagger
  - GithubPages
  - GitHubActions
private: false
updated_at: '2024-02-15T16:30:14+09:00'
id: 520806a86a14a4bd64a8
organization_url_name: null
slide: false
---
## 概要
Swaggerで作成したAPI仕様書をGitHub Actionsを使ってGitHub Pagesにデプロイする方法について解説します

## 前提
- GitHub Actionsに関する基礎知識を有している
- openapi.ymlを作成済
- Swaggerでドキュメントを自動生成する用のAPIを作成済み

## ディレクトリ構成
ファイル構成は以下のとおりです
```
❯ tree
.
├── .github
│   └── workflows
│       └── deploy-swagger.yml
└── doc
    └── openapi.yml
```

## 実装するファイル一覧
- deploy-swagger.yml

## ワークフローの作成
SwaggerをGitHub Pagesにデプロイするワークフローを作成します
まず、swagger-cliをインストールし、doc/openapi.yml内に書いたドキュメントを静的ファイルとして出力し、swagger-uiというフォルダに格納します
その後、swagger-ui内の静的ファイルをGitHub Actions公式のartifactのactionを使ってartifact内に格納します
最後にartifact内の静的ファイルをGitHub Actions公式のdeploy-pagesを使ってGitHub Pages上にデプロイします

```.github/workflows/deploy-swagger.yml
name: Deploy Swagger UI to GitHub Pages

on:
  push:
    branches:
      - develop
      - main
jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Chekcout code
        uses: actions/checkout@v4
      - name: Install swagger-cli
        run: npm install -g swagger-cli
      - name: Generate Swagger UI
        uses: Legion2/swagger-ui-action@v1
        with:
          output: swagger-ui
          spec-file: doc/openapi.yml
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v3
        with:
          # 絶対パスを指定
          path: swagger-ui

  # Deploy the artifact to GitHub pages.
  # This is a separate job so that only actions/deploy-pages has the necessary permissions.
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## GitHub Pagesの設定
Build and deploymentの箇所をGitHub Actionsに設定します

![スクリーンショット 2023-12-25 14.30.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d9bb532b-3fd5-db8f-760b-134848034b8b.png)

## 実際にデプロイしてみよう！
以下のようにワークフローが成功し、Swaggerの画面をGitHub Pages上で表示できたら成功です

![スクリーンショット 2023-12-25 9.17.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0cf911a3-c1d7-471f-bfbe-ef0e0d6161e5.png)

![スクリーンショット 2023-12-25 9.17.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f174536e-f3a3-6c9f-3ca2-8d21120a9609.png)

![スクリーンショット 2023-12-24 15.58.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/19de6572-2ea2-02a4-4a44-7e17c22d452c.png)

## 以下のエラーメッセージが出た時
![スクリーンショット 2023-12-24 15.57.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f954fb9c-5f09-5b66-c623-d46eb549b061.png)

Swagger3.1以上だとうまくGitHub Actions上でデプロイできないのでv3.0でデプロイしてみましょう

## 参考
https://github.com/Legion2/swagger-ui-action

https://docs.github.com/ja/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

https://github.com/actions/upload-artifact

