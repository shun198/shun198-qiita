---
title: GitHub ActionsでJestを自動実行しよう！Cacheを使ったパッケージのインストールの高速化も解説
tags:
  - Node.js
  - npm
  - Jest
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 86668be6a90634f9480c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- GitHub Actionsの基本的な用語についてある程度理解している
- Node.jsを使用
- パッケージマネージャーはnpmを使用
- Jestを使用

## 必要なファイル一覧
以下のファイルを編集していきます
```
❯ tree 
.
└── .github
    └── workflows
        └── test.yml
```

## ワークフローの作成
.github/workflows/test.ymlにテストの自動実行までの処理を記載していきます
```yml:.github/workflows/test.yml
# アクション名
name: Jest

# タイミングを指定
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application

jobs:
  Test:
    name: Run test codes
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7
      - name: Install and cache nodejs
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
      - name: Install packages
        run: npm ci
      - name: Show coverage
        run: npm test -- --bail --maxWorkers=100% --watchAll=false --coverage
```

それでは、一つずつ解説していきます

## ワークフローを実行する前の設定
以下のように冒頭で

- どの場面でワークフローを実行するか

記載します
今回はプルリクエストが

- opened(作成時)
- reopened(再作成時)
- synchronize(pushするたびに)
- ready_for_review(レビューできる状態になったら)

の時にワークフローを実行します

## テストの実行を制限したいとき
テストに関しては

- draft
- releaseブランチ
- docブランチ(ドキュメント作成用)

の時は実行したくないので

```yml:.github/workflows/test.yml
if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
```
を追記します

## ワーキングディレクトリの指定
今回はapplication/内にpackage.jsonを含めたReactおよびTypescriptのソースコードが含まれているため、以下のように記載します

```yml:.github/workflows/test.yml
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
```

## Node.jsの設定
公式ドキュメントに記載の通りNode.jsの設定を行います

https://github.com/actions/setup-node

Node.jsのインストールと次回以降にワークフローを実行する際にCacheを使う設定をします
今回はパッケージマネージャーとしてnpmを使用しているので以下のように記載します
```yml:.github/workflows/test.yml
      - name: Install and cache nodejs
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
```

## npmのインストール
先ほどNode.jsの設定を行ったのでpackage.json内のパッケージをインストールしていきます
```yml:.github/workflows/test.yml
      - name: Install packages
        run: npm ci
```

## Jestの実行
Jestを実行します
```yml:.github/workflows/test.yml
      - name: Show coverage
        run: npm test -- --bail --maxWorkers=100% --watchAll=false --coverage
```

オプションは以下の通りです

| オプション | 説明 |
| -------- | -------- |
| --bail  | テストが一つでも失敗したらJestを強制終了させる  |
| --maxWorkers=100% | マルチスレッドでJestを実行。runnerはでふ1コア2スレッドなので--maxWorkers=100%を指定(デフォルトは50%) |
| --watchAll=false | ファイルの監視モードを無効化 |

## ワークフローを実行しよう
PRを作成したらワークフローが実行されます
下記のようにテストが実行できたら成功です

![スクリーンショット 2023-08-10 16.41.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/37139b20-60ee-843a-584f-9af5998e54bc.png)


## 参考
https://jestjs.io/ja/docs/cli

https://docs.github.com/en/actions/using-jobs/setting-default-values-for-jobs
