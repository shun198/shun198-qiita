---
title: GitHub Actionsを使ってStorybookをGitHub Pagesにデプロイしよう！
tags:
  - Node.js
  - GithubPages
  - storybook
  - GitHubActions
private: false
updated_at: '2026-08-10T07:59:47+09:00'
id: 18f852caea2b4068ebaf
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
StorybookをGitHub Actionsを使ってGitHub Pagesにデプロイする方法について解説します

## 前提
- GitHub Actionsに関する基礎知識を有している
- コンポーネントとStoryを作成済

## ディレクトリ構成
ファイル構成は以下のとおりです
```
❯ tree
.
├── .github
│   └── workflows
│       └── deploy-storybook.yml
└── application
    ├── storybook-static
    └── package.json
```

## 実装するファイル一覧
- deploy-storybook.yml
- package.json

## Storybookの設定
package.jsonにstorybook buildコマンドを実行できるよう修正します
コマンドを実行することでstorybook-staticディレクトリが作成され、Storybookを表示するための静的ファイルが生成されます

```package.json

  "scripts": {
    "build-storybook": "storybook build",
  },
```

## ワークフローの作成
StorybookをGitHub Pagesにデプロイするワークフローを作成します
まず、Node.jsのセットアップを行います
```yaml
      - name: Setup Node.js
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
```

```
npm ci
```
コマンドで必要なパッケージをインストールした後に
```
npm run build-storybook
```
を実行してStorybookを表示させるために静的ファイルを作成します
その後、storybook-static内の静的ファイルをGitHub Actions公式のArtifactのactionを使ってArtifact内に格納します
Artifact内の静的ファイルをGitHub Actions公式のdeploy-pagesを使ってGitHub Pages上にデプロイします

```deploy-storybook.yml
name: Deploy Storybook to GitHub Pages

on:
  push:
    branches:
      - develop
      - main

env:
  WORKING_DIRECTORY: application

jobs:
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Chekcout code
        uses: actions/checkout@v7
      - name: Setup Node.js
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
      - name: Install Node Dependencies
        run: npm ci
      - name: Build storybook
        run: npm run build-storybook
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v5
        with:
          # 絶対パスを指定
          path: ${{ env.WORKING_DIRECTORY }}/storybook-static

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
        uses: actions/deploy-pages@v5

```

## GitHub Pagesの設定
Build and deploymentの箇所をGitHub Actionsに設定します

![スクリーンショット 2024-02-15 16.00.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e9765fec-d066-e261-86f6-2449321c80cf.png)

## 実際にデプロイしてみよう！
以下のようにワークフローが成功し、Storybookの画面をGitHub Pages上で表示できたら成功です

![スクリーンショット 2024-02-15 16.25.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eaf17b7c-9d6b-d7b6-db5c-ecab4967ac6b.png)

![スクリーンショット 2024-02-15 16.42.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c309b8cc-7976-52f7-9eaa-93e047966f30.png)

![スクリーンショット 2024-02-15 16.19.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7026386f-8531-5dc9-5644-95348b558be3.png)

## 参考
https://storybook.js.org/tutorials/intro-to-storybook/react/en/simple-component/

https://docs.github.com/ja/pages/getting-started-with-github-pages/configuring-a-publishing-source-for-your-github-pages-site

https://github.com/actions/upload-artifact
