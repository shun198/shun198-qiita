---
title: GitHub Actionsのワークフロー間で環境変数を共有するには
tags:
  - GitHubActions
private: false
updated_at: '2023-07-11T17:38:15+09:00'
id: 47b54cf6a48d33b239b4
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
複数以上のワークフローで同じ環境変数を使用することがあるかと思います
新しいワークフローを作成するたびに同じ環境変数をハードコーディングするのは手間なので
今回はワークフロー間で環境変数を共有する方法について解説します

## 前提
- 今回はDjangoとPytestを使ったテストの自動実行とpdocでのドキュメントを自動生成するワークフローを例に作成します
- メタデータ構文を使用します
- テストの自動実行、pdocを使ったドキュメント生成のワークフローを作成する方法については解説しません

## ディレクトリ構成

```
tree
・
├── .github
|   ├── action
|   |   ├── set-up-env
|   |   |   └── action.yml
|   |   └── set-up-poetry
|   |       └── action.yml
|   └── workflows
|       ├── docs.yml
|       └── test.yml
└── .env.test
```

## 必要なファイルの作成
今回必要になるファイルは以下の通りです
- .github/action/set-up-env/action.yml
- .env.test

## 環境変数を共有するワークフローの作成
今回はメタデータ構文を使って環境変数を共有するワークフローを作成します
以下のワークフローを実行する際にsedコマンドを使って
.env.test内の環境変数の中身を`GITHUB_ENV`という
GitHub Actions内で使用できる環境変数に(SECRET_KEY=test)の状態で追加します

メタデータ構文について詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/e7b7a3d9d3b86aec4813

```.github/action/set-up-env/action.yml
name: 'Setup Environment Variables'

description: 'Setup Environment Variables for Django Project'

inputs:
  env-directory:
    description: 'working-directory of env file'
    required: false
    default: .env.test

runs:
  # compositeが必須
  using: 'composite'
  steps:
    - name: Add Environment Variables
      run: sed "" ${{ inputs.env-directory }} >> $GITHUB_ENV
      shell: bash
```

GITHUB_ENV内に追加した環境変数は以下のようにenvとして追加されます
```
  echo $GITHUB_ENV
  shell: /usr/bin/bash -e {0}
  env:
    MYSQL_ROOT_PASSWORD: root
    MYSQL_DATABASE: test-db
    MYSQL_HOST: 127.0.0.1
    MYSQL_PORT: 3306
    MYSQL_USER: test
    MYSQL_PASSWORD: test
    SECRET_KEY: test
    DJANGO_SETTINGS_MODULE: project.settings
    ALLOWED_HOSTS: 127.0.0.1
    DEBUG: 'True'
```

.env.testにはDjangoの起動に必要な環境変数を記載します

```.env.test
SECRET_KEY=test
DJANGO_SETTINGS_MODULE=project.settings
ALLOWED_HOSTS=127.0.0.1
DEBUG=True
MYSQL_ROOT_PASSWORD=root
MYSQL_DATABASE=test-db
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=test
MYSQL_PASSWORD=test
```

## 作成したワークフローを別のワークフローで使ってみよう
以下のワークフローに作成したaction.ymlを適用させます
- docs.yml
- test.yml

### docs.yml
```yml
      - name: Set Environment Variables
        uses: ./.github/actions/set-up-env
```
を記載することで作成したaction.ymlが実行され、環境変数がワークフロー内に追加されます

```.github/workflows/docs.yml
name: Pdoc
on:
  push:
    branches:
      - develop

# security: restrict permissions for CI jobs.
permissions:
  contents: read

env:
  WORKING_DIRECTORY: application
  CI_MAKING_DOCS: 1

jobs:
  # Build the documentation and upload the static HTML files as an artifact.
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Set Environment Variables
        uses: ./.github/actions/set-up-env
      - name: Setup Poetry
        uses: ./.github/actions/set-up-poetry
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Create documentation
        run: poetry run pdoc -o docs crm
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v1
        with:
          # 絶対パスを指定
          path: application/docs/

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
        uses: actions/deploy-pages@v2

```

pdocを使ってドキュメントを作成する方法については以下の記事を参考にしてください

https://qiita.com/shun198/items/85c6c203f4b40abba344

### test.yml
テスト用のワークフローも同様です

```.github/workflows/test.yml
name: Tests
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test-db
  MYSQL_USER: test
  MYSQL_PASSWORD: test

jobs:
  test:
    name: Run Test Code
    # プルリクエストがdraft,release,docの時は実行しない
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    runs-on: ubuntu-20.04
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    services:
      db:
        image: mysql:8.0
        ports:
          - 3306:3306
        env:
          MYSQL_ROOT_PASSWORD: ${{ env.MYSQL_ROOT_PASSWORD }}
          MYSQL_DATABASE: ${{ env.MYSQL_DATABASE }}
          MYSQL_USER: ${{ env.MYSQL_USER }}
          MYSQL_PASSWORD: ${{ env.MYSQL_PASSWORD }}
        options: >-
          --health-cmd "mysqladmin ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: Set Environment Variables
        uses: ./.github/actions/set-up-env
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
      - name: Setup Poetry
        uses: ./.github/actions/set-up-poetry
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Run migration
        run: |
            poetry run python manage.py makemigrations
            poetry run python manage.py migrate
      - name: Run Pytest
        run: |
          set -o pipefail
          poetry run pytest --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code | tee pytest-coverage.txt
      - name: Pytest coverage comment
        uses: MishaKav/pytest-coverage-comment@main
        with:
          pytest-coverage-path: ${{ env.WORKING_DIRECTORY }}/pytest-coverage.txt
          junitxml-path: ${{ env.WORKING_DIRECTORY }}/pytest.xml

```

サービスコンテナ内の環境変数が.env.testと一致するようにだけ注意してください
サービスコンテナについて詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/d03eef4acbb8d8980d1a

## ワークフローの実行
以下のようにワークフローの実行が成功したらOKです

![スクリーンショット 2023-07-11 17.30.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ff482ad7-4188-78c0-4a62-3b8c2c81d6ba.png)

![スクリーンショット 2023-07-11 17.31.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/694ebe15-57e1-afb1-b1e3-a6a17f5887af.png)

## まとめ
ワークフロー間での環境変数を共有する記事が思っていたより少なかったので記事を書いてみました
GitHub Actionsでも共通化できるところは共通化しておくと可読性が上がって読みやすいなと痛感しました

## 参考
https://arinco.com.au/blog/github-actions-share-environment-variables-across-workflows/

https://docs.github.com/ja/actions/using-workflows/workflow-commands-for-github-actions
