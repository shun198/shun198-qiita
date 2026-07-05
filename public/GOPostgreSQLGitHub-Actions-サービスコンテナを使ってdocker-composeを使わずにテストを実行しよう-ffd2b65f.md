---
title: '[GO+PostgreSQL+GitHub Actions] サービスコンテナを使ってdocker-composeを使わずにテストを実行しよう'
tags:
  - Go
  - PostgreSQL
  - GitHubActions
private: false
updated_at: '2024-04-30T15:06:28+09:00'
id: ffd2b65feacdff03cd05
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- GitHub Actionsの基本的な用語についてある程度理解している
- 言語はGOを使用
- DBはPostgresを使用

## サービスコンテナとは
ワークフロー中でアプリケーションをテストもしくはビルドするのに必要なサービスを提供するためのDockerコンテナです
サービスコンテナを使うことでワークフロー内で例えばdocker-composeを使って自前でDBを作成せずにテストを実行することができます
runner内のリソースは限られているのでGitHub側で用意するサービスコンテナなどを使うケースが多いです
また、docker-composeを使わずにワークフローを実行するのでコンテナの起動時間分ワークフローの時間を短縮できます
今回はPostgresのサービスコンテナを使ってテストコードを実行させます

## ファイル構成
ファイル構成は以下の通りです
```
❯ tree 
.
├── .github
│   └── workflows
│       └── test.yml
└── application # GOのプロジェクトファイルおよびgo.mod、go.sumが入ったディレクトリ
    ├── go.mod
    ├── go.sub
    └── main.go
```

### ワークフローの作成
`.github/workflows/test.yml`にテストの自動実行までの処理を記載していきます

```yml:.github/workflows/test.yml
name: Run Test
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  POSTGRES_NAME: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_HOST: 127.0.0.1
  POSTGRES_PORT: 5432

jobs:
  Test:
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    name: Run Test Code
    runs-on: ubuntu-22.04
    # ルート直下にgo.modを置いている場合は不要
    # 今回はapplication/内にgo.modを含めたGOのソースコードが含まれているため、指定する
    defaults:
      run:
        working-directory: {{ env.WORKING_DIRECTORY }}
    # Postgresのサービスコンテナを設定
    services:
      db:
        # PostgresのDocker imageを使用
        image: postgres:16.2
        ports:
          - 5432:5432
        env:
          POSTGRES_NAME: ${{ env.POSTGRES_NAME }}
          POSTGRES_USER: ${{ env.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
        # Postgresより先にGOが起動しないようヘルスチェックを使って起動順を制御
        options: >-
          --health-cmd "pg_isready"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Chekcout code
        uses: actions/checkout@v4
      # GOのセットアップを実行
      # 2回目以降のテスト実行時はrunner内にCacheを生成してGOのセットアップを高速化
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.20'
          cache: true
          cache-dependency-path: ${{ env.WORKING_DIRECTORY }}/go.sum
      - name: Install dependencies
        run: go get -u
      - name: Build Go
        run: go build -v
      - name: Run Test
        run: go test -p 1 -v ./...
```

それでは、一つずつ解説していきます
### ワークフローを実行する前の設定
以下のように冒頭で
- どの場面でワークフローを実行するか
- どの環境変数を使用するか

記載します
今回はがプルリクエスト
- opened(作成時)
- reopened(再作成時)
- synchronize(pushするたびに)
- ready_for_review(レビューできる状態になったら)

の時にワークフローを実行します
また、`env`を使うとワークフロー内で使用できる独自の環境変数を定義できます
今回はテストを実行するだけのワークフロー内に秘匿情報を使う必要がないです
そのため、下記のようにsecretsを使わずに環境変数を直書きしています

```yml:.github/workflows/test.yml
name: Run Test
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  POSTGRES_NAME: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_HOST: 127.0.0.1
  POSTGRES_PORT: 5432
```

### テストの実行を制限したいとき
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

### ワーキングディレクトリの指定
今回はapplication/内にgo.modを含めたGOのソースコードが含まれているため、以下のように記載します
```yml:.github/workflows/test.yml
    defaults:
      run:
        working-directory: {{ env.WORKING_DIRECTORY }}
```

### Postgres用のサービスコンテナの設定
Postgresのサービスコンテナを設定する際に
- Docker image
- ポート
- 環境変数
- ヘルスチェック

を記載します
Docker imageは`Postgres16.2`のものを使用します

Postgresの環境変数で必要なものは
- POSTGRES_NAME
- POSTGRES_USER
- POSTGRES_PASSWORD

です
上記がないとDBへ接続できずにテストが失敗してしまうので必ず設定しましょう

`options`でヘルスチェックを行い、GOより先にPostgresの起動が完了するよう制御します

ヘルスチェックについて知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/a66d6214cdab5629029d

```yml:.github/workflows/test.yml
    # Postgresのサービスコンテナを設定
    services:
      db:
        # PostgresのDocker imageを使用
        image: postgres:16.2
        ports:
          - 3306:3306
        env:
          POSTGRES_NAME: ${{ env.POSTGRES_NAME }}
          POSTGRES_USER: ${{ env.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
        # Postgresより先にGOが起動しないようヘルスチェックを使って起動順を制御
        options: >-
          --health-cmd "pg_isready"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

### どうして127.0.0.1を指定しているのか
docker-composeを使う際は`POSTGRES_HOST`にservice名を指定することにより名前解決でPostgresのIPアドレスを取得して接続していましたが、今回はDockerを使わずにランナー上で直接テストを実行しています
公式ドキュメントでも記載しているようにホストを127.0.0.1に指定します

>ランナーマシン上でのジョブの実行
ランナーマシン上でジョブを直接実行する場合、localhost:port か 127.0.0.1:port を使ってサービスコンテナにアクセスできます。 GitHubは、サービスコンテナからDockerホストへの通信を可能にするよう、コンテナネットワークを設定します

### GOのセットアップとパッケージのインストール
公式ドキュメントに記載の通りGOのセットアップとパッケージのインストールを行います

https://github.com/actions/setup-go

go.mod内のパッケージをインストールしていきます

```yml
cache: true
cache-dependency-path: ${{ env.WORKING_DIRECTORY }}/go.sum
```

と指定することで2回目以降の`poetry install`をCacheを使って高速化させます
![スクリーンショット 2024-04-30 15.01.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c65dd5eb-8b7d-ad43-4438-c62c7620dfb0.png)
![スクリーンショット 2024-04-30 15.05.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e7f93d0d-bc69-d793-480f-0be9cb7f185e.png)

```yml:.github/workflows/test.yml
      # GOのセットアップを実行
      # 2回目以降のテスト実行時はrunner内にCacheを生成してGOのセットアップを高速化
      - name: Setup Go
        uses: actions/setup-go@v5
        with:
          go-version: '1.20'
          cache: true
          cache-dependency-path: ${{ env.WORKING_DIRECTORY }}/go.sum
      - name: Install dependencies
        run: go get -u
```

### buildの実行
GOのbuildを実行します
```yml:.github/workflows/test.yml
      - name: Build Go
        run: go build -v
```

### テストの実行
テストコードを実行します
```yml:.github/workflows/test.yml
      - name: Run Test
        run: go test -p 1 -v ./...
```

## ワークフローを実行しよう
PRを作成したらワークフローが実行されます
下記のようにテストが実行できたら成功です

![スクリーンショット 2024-04-30 15.04.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f2700103-5eab-f117-ba1b-a88e2b7fe12b.png)

## 参考
https://github.com/actions/setup-go

https://docs.github.com/ja/actions/learn-github-actions/variables

https://docs.github.com/ja/actions/using-containerized-services/about-service-containers
