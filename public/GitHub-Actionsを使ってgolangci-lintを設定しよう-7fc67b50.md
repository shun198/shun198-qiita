---
title: GitHub Actionsを使ってgolangci-lintを設定しよう！
tags:
  - Go
  - GitHubActions
  - golangci-lint
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 7fc67b50b409d70a576c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actions内でLinterを使用することでGOのソースコードを解析して、バグの検出や、言語のルールに沿ってコードが書かれているかをチェックすることができます
今回はgolangci-lintを使ったワークフローを作成する方法について解説します

## 前提
- GOのプロジェクトを作成済み

## golang-ci-lintとは
GOで使用できるLinterの一つで実行時に公式のgovetをはじめとする様々なLinterを一緒に使用できるのが特徴です

## ディレクトリ構成
```
├── .env
├── .github
│   └── workflows
│       └── lint.yml
└── backend
    ├── go.mod
    ├── go.sum
    └── main.go
```

## 実装
以下がワークフローです
詳細はこのあと解説します

```lint.yml
name: Lint Code

on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]
    branches-ignore:
      - 'release/**'
      - 'doc/**'

env:
  WORKING_DIRECTORY: backend

jobs:
  lint:
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    name: Lint
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7
      - name: Setup Golang
        uses: actions/setup-go@v7
        with:
          go-version-file: ${{ env.WORKING_DIRECTORY }}/go.mod
          cache: true
          cache-dependency-path: |
            **/go.sum
            **/go.mod
      - name: Install Dependencies
        run: go mod download
      - name: Lint Code
        uses: golangci/golangci-lint-action@v9
        with:
          version: v2.12
          working-directory: ${{ env.WORKING_DIRECTORY }}
```

### setup-go
公式が出しているsetup-goを使用することでGOの環境設定を行うことができます
go-version-fileを指定することでgo.modファイル内のGOのバージョンを自動で検出します
また、`cache: true`にすることでキャッシュを使ってインストールを高速化します
cache-dependency-pathに下記のようにgo.sumとgo.modファイルを指定します

https://github.com/actions/setup-go

```yml
      - name: Setup Golang
        uses: actions/setup-go@v7
        with:
          go-version-file: ${{ env.WORKING_DIRECTORY }}/go.mod
          cache: true
          cache-dependency-path: |
            **/go.sum
            **/go.mod
```

### golangci-lint用のActions
golangci-lintが公式で出しているActionsを使用します
公式ドキュメントによると公式のActionsを使用するとgolangci-lintをバイナリインストールするより早くインストールできるので推奨しているとのことです

https://golangci-lint.run/welcome/install/#github-actions

```yml
      - name: Lint Code
        uses: golangci/golangci-lint-action@v9
        with:
          version: v2.12
          working-directory: ${{ env.WORKING_DIRECTORY }}
```

## 実際に実行してみよう！
以下のようにワークフロー実行時にLinterが適用され、エラーを検知した場合はPR上にエラー箇所を表示できれば成功です

![スクリーンショット 2024-12-02 9.51.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4f393f57-224e-95b1-9bf9-e8e11cdb78e5.png)


## 参考
https://github.com/actions/setup-go

https://golangci-lint.run/
