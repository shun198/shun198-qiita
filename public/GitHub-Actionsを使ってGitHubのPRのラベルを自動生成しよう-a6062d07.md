---
title: GitHub Actionsを使ってGitHubのPRのラベルを自動生成しよう！
tags:
  - GitHub
  - pullrequest
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: a6062d07a05cacb8a277
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
プロジェクトによって使用しているラベルの色や名称がバラバラだと困るかと思います
そのため、ラベルの運用を統一すべきだと私は考えています
今回は手動で作成せずにラベルを自動生成及び定期的に更新できるようGitHub Actionsを使って自動化したいと思います

## 使用するAction
今回はlabel-syncerを使用します

https://github.com/micnncim/action-label-syncer

## workflowを書いてみよう
今回作成するファイルは
- .github/worklfows/label-syncer.yml
- .github/labels.yml

の2種類です
```
tree
.
└── .github
        ├──workflows
        │     └──label-syncer.yml
        └──labels.yml
```

label-syncer.ymlにラベルを自動生成するワークフローを作成します
また、チェックアウトについて詳しく知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/14cdba2d8e58ab96cf95

```.github/worklfows/label-syncer.yml
name: Sync labels

on: pull_request
jobs:
  build:
    name: Sync labels
    runs-on: ubuntu-latest
    steps:
      # リポジトリのチェックアウト
      - uses: actions/checkout@v7
      # label-syncerを使用
      - uses: micnncim/action-label-syncer@v1.3.0
        env:
          # GITHUB_TOKENはデフォルトで使用できるため、secretsへの追記は不要
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          # .github/labels.ymlに自動生成するラベルの設定を記載
          manifest: .github/labels.yml
```

ラベルの設定を行います
ymlファイルに
- 色
- 説明
- ラベル名

を指定します
```.github/labels.yml
- color: d73a4a
  description: Something isn't working
  name: bug
- color: 0075ca
  description: Improvements or additions to documentation
  name: documentation
- color: a2eeef
  description: New feature or request
  name: enhancement
- color: b60205
  description: An urgent pull request to look
  name: emergency
- color: f9d0c4
  description: Refactor Code
  name: refactor
- color: 1d76db
  description: Test Code
  name: test
```

## ラベルを確認してみよう！
ラベルの初期設定は以下の通りです
![スクリーンショット 2023-01-01 6.26.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2560e3f8-9d3a-dc00-e0d8-7cf2eb077036.png)

先ほど設定したラベルに変更されていることが確認できました！
![スクリーンショット 2023-01-01 6.28.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0cd22b2b-d355-27b0-bcd1-62fb285e1bde.png)

## ラベルの更新を決まった時間に定期的に行うには？
ラベルの作成及び更新は初回に作成する以外頻繁に変えるものではないので
下記のようにcronを使って例えば毎週月曜日朝9時に更新する運用をしてもいいかと思います

```.github/worklfows/label-syncer.yml
name: Sync labels
on:
  schedule:
    - cron: "0 9 * * 1"
jobs:
  build:
    name: Sync labels
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v7
      - uses: micnncim/action-label-syncer@v1.3.0
        env:
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
        with:
          manifest: .github/labels.yml
```

schedule及びcronの使い方は以下の公式ドキュメントを参照してください

https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#scheduled-events

## 参考
https://github.com/micnncim/action-label-syncer

https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#scheduled-events

https://pubs.opengroup.org/onlinepubs/9699919799/utilities/crontab.html#tag_20_25_07
