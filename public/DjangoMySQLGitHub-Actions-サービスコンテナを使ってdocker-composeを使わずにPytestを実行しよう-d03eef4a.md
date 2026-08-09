---
title: '[Django+MySQL+GitHub Actions] サービスコンテナを使ってdocker-composeを使わずにPytestを実行しよう'
tags:
  - Django
  - MySQL
  - pytest
  - GitHubActions
  - Poetry
private: false
updated_at: '2026-08-10T07:59:47+09:00'
id: d03eef4acbb8d8980d1a
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- GitHub Actionsの基本的な用語についてある程度理解している
- フレームワークはDjangoを使用
- DBはMySQLを使用
- Pytestを使用
- Poetryを使用
- PR内にカバレッジを表示させる方法についても説明

## サービスコンテナとは
ワークフロー中でアプリケーションをテストもしくはビルドするのに必要なサービスを提供するためのDockerコンテナです
サービスコンテナを使うことでワークフロー内で例えばdocker-composeを使って自前でDBを作成せずにテストを実行することができます
runner内のリソースは限られているのでGitHub側で用意するサービスコンテナなどを使うケースが多いです
また、docker-composeを使わずにワークフローを実行するのでコンテナの起動時間分ワークフローの時間を短縮できます
今回はMySQLのサービスコンテナを使ってPytestを実行させます

## 必要なファイル一覧
以下のファイルを編集していきます
```
❯ tree 
.
├── .github
│   └── workflows
│       └── test.yml
└── application # Djangoのプロジェクトファイルおよびpyproject.tomlが入ったディレクトリ
    ├── project
    │   └── settings.py
    ├── manage.py
    ├── poetry.lock
    └── pyproject.toml
```

##  settings.py
settings.pyに以下のように設定します
```settings.py
import os

SECRET_KEY = os.environ.get("SECRET_KEY")

DEBUG = os.environ.get("DEBUG") == "True"

ALLOWED_HOSTS = os.environ.get("ALLOWED_HOSTS").split(" ")

# データベースの設定を行う
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.environ.get("MYSQL_DATABASE"),
        "USER": os.environ.get("MYSQL_USER"),
        "PASSWORD": os.environ.get("MYSQL_PASSWORD"),
        "HOST": os.environ.get("MYSQL_HOST", "db"),
        "PORT": os.environ.get("MYSQL_PORT", 3306),
    }
}
```

### ワークフローの作成
`.github/workflows/test.yml`にテストの自動実行までの処理を記載していきます

```yml:.github/workflows/test.yml
name: Run Pytest
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings
  ALLOWED_HOSTS: 127.0.0.1
  # "True"にしないとDEBUG内がFalseになってしまう
  DEBUG: "True"
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test-db
  MYSQL_HOST: 127.0.0.1
  MYSQL_PORT: 3306
  MYSQL_USER: test
  MYSQL_PASSWORD: test

jobs:
  Test:
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    name: Run Test Code
    runs-on: ubuntu-24.04
    # ルート直下にpyproject.tomlを置いている場合は不要
    # 今回はapplication/内にPoetryを含めたDjangoのソースコードが含まれているため、指定する
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    # MySQLのサービスコンテナを設定
    services:
      db:
        # MySQLのDocker imageを使用
        image: mysql:8.0
        ports:
          - 3306:3306
        env:
          MYSQL_ROOT_PASSWORD: ${{ env.MYSQL_ROOT_PASSWORD }}
          MYSQL_DATABASE: ${{ env.MYSQL_DATABASE }}
          MYSQL_USER: ${{ env.MYSQL_USER }}
          MYSQL_PASSWORD: ${{ env.MYSQL_PASSWORD }}
        # MySQLより先にDjangoが起動しないようヘルスチェックを使って起動順を制御
        options: >-
          --health-cmd "mysqladmin ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Chekcout code
        uses: actions/checkout@v6
      # MySQLのユーザに実行権限を付与
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
      # Poetryのインストール
      - name: Install poetry
        run: pipx install poetry
      # Pythonのセットアップを実行
      # 2回目以降のテスト実行時はrunner内にPoetryのCacheを生成してPoetryのセットアップを高速化
      - name: Use cache dependencies
        uses: actions/setup-python@v6
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      # Poetry内の必要なパッケージのインストールを実行
      - name: Install Packages
        run: poetry install
      - name: Run migration
        run: |
          poetry run python manage.py makemigrations
          poetry run python manage.py migrate
      # Pytestを実行
      - name: Run Pytest
        run: |
          set -o pipefail
          poetry runpytest --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail | tee pytest-coverage.txt
      # カバレッジをPRに表示
      - name: Pytest coverage comment
        uses: MishaKav/pytest-coverage-comment@main
        with:
          pytest-coverage-path: ${{ env.WORKING_DIRECTORY }}/pytest-coverage.txt
          junitxml-path: ${{ env.WORKING_DIRECTORY }}/pytest.xml
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
name: Run Pytest
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings
  ALLOWED_HOSTS: 127.0.0.1
  DEBUG: "True"
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test-db
  MYSQL_HOST: 127.0.0.1
  MYSQL_PORT: 3306
  MYSQL_USER: test
  MYSQL_PASSWORD: test
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
今回はapplication/内にPoetryを含めたDjangoのソースコードが含まれているため、以下のように記載します
```yml:.github/workflows/test.yml
    defaults:
      run:
        working-directory: {{ env.WORKING_DIRECTORY }}
```

### MySQL用のサービスコンテナの設定
MySQLのサービスコンテナを設定する際に
- Docker image
- ポート
- 環境変数
- ヘルスチェック

を記載します
Docker imageは以下の`MySQL8.0`のものを使用します

https://hub.docker.com/layers/library/mysql/8.0/images/sha256-56b3754c827c12d583689a3c619b49653d0b22cc19e341511544685ffcd6037d?context=explore

MySQLの環境変数で必要なものは
- MYSQL_ROOT_PASSWORD
- MYSQL_DATABASE
- MYSQL_USER
- MYSQL_PASSWORD

です
上記がないとDBに接続できずにテストが失敗してしまうので必ず設定しましょう

`options`でヘルスチェックを行い、Djangoより先にMySQLの起動が完了するよう制御します

ヘルスチェックについて知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/a66d6214cdab5629029d

```yml:.github/workflows/test.yml
    # MySQLのサービスコンテナを設定
    services:
      db:
        # MySQLのDocker imageを使用
        image: mysql:8.0
        ports:
          - 3306:3306
        env:
          MYSQL_ROOT_PASSWORD: ${{ env.MYSQL_ROOT_PASSWORD }}
          MYSQL_DATABASE: ${{ env.MYSQL_DATABASE }}
          MYSQL_USER: ${{ env.MYSQL_USER }}
          MYSQL_PASSWORD: ${{ env.MYSQL_PASSWORD }}
        # MySQLより先にDjangoが起動しないようヘルスチェックを使って起動順を制御
        options: >-
          --health-cmd "mysqladmin ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

### MySQLのユーザの実行権限の付与
ワークフロー内で使うMySQLのユーザにアクセス権限を付与していきます
`--protocol=tcp`がないと`127.0.0.1`にアクセスする際はソケットファイル（mysql.sock）を見にいってしまって接続できないため、追加します
今回はテストの際に使用する`MYSQL_USER`に権限を付与します
また、`$MYSQL_ROOT_PASSWORD`、`$MYSQL_USER`と指定するとワークフローで設定した環境変数を使用できます

```yml:.github/workflows/test.yml
      # MySQLのユーザに実行権限を付与
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
```

### どうして127.0.0.1を指定しているのか
docker-composeを使う際はsettings.pyの`MYSQL_HOST`にservice名を指定することで名前解決でMySQLのIPアドレスを取得して接続していましたが、今回はDockerを使わずにランナー上で直接テストを実行しています
公式ドキュメントでも記載しているようにホストを127.0.0.1に指定します

>ランナーマシン上でのジョブの実行
ランナーマシン上でジョブを直接実行する場合、localhost:port か 127.0.0.1:port を使ってサービスコンテナにアクセスできます。 GitHubは、サービスコンテナからDockerホストへの通信を可能にするよう、コンテナネットワークを設定します

### Poetryの設定
公式ドキュメントに記載の通りPoetryの設定を行います

https://github.com/actions/setup-python

Poetryをインストールしたあとpyproject.toml内のパッケージをインストールしていきます
```
cache: 'poetry'
```

と指定することで2回目以降の`poetry install`をCacheを使って高速化させます
![スクリーンショット 2023-12-27 10.39.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ebad2c77-3b1a-f229-3401-fa7797c8da75.png)

```yml:.github/workflows/test.yml
      # Poetryのインストール
      - name: Install poetry
        run: pipx install poetry
      # Pythonのセットアップを実行
      # 2回目以降のテスト実行時はrunner内にPoetryのCacheを生成
      # Poetryのセットアップを高速化
      - name: Use cache dependencies
        uses: actions/setup-python@v6
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      # Poetry内の必要なパッケージのインストールを実行
      - name: Install Packages
        run: poetry install
```

### マイグレーションの実行
DB内にテーブルを作成するためにマイグレーションを行います
```yml:.github/workflows/test.yml
      - name: Run migration
        run: |
          poetry run python manage.py makemigrations
          poetry run python manage.py migrate
```

### Pytestの実行
Pytestを実行します
後述するカバレッジをPRに表示させるActionを使用する際にPytestが失敗したのにワークフローが成功してしまう不具合がありました

```
set -o pipefail
```
を記載することでPytestが失敗したら以下のコマンドが実行されず、ワークフローが異常終了してくれます
```
tee pytest-coverage.txt
```

以下のissueに記載されていました

https://github.com/MishaKav/pytest-coverage-comment/issues/69

```yml:.github/workflows/test.yml
      # Pytestを実行
      - name: Run Pytest
        run: |
          set -o pipefail
          # pytest.xmlとpytest-coverage.txtはapplication/の配下に作成される
          poetry run pytest --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail | tee pytest-coverage.txt
```

オプションは以下の通りです

| オプション | 説明 |
| -------- | -------- |
| -x     | テストが一つでも失敗したらPytestを強制終了させる  |
| -n auto | マルチスレッドでPytestを実行。runnerは1コア2スレッドなのでauto=2 |
| --no-cov-on-fail | テストが失敗したらカバレッジを表示させない |

#### -n auto
pytest-xdistをインストールすると上記のオプションを使用することができます

https://pypi.org/project/pytest-xdist/

### カバレッジをPRに表示
```yml:.github/workflows/test.yml
      # カバレッジをPRに表示
      - name: Pytest coverage comment
        uses: MishaKav/pytest-coverage-comment@main
        with:
          # パスは今回はカレントディレクトリではなく、applicationを指定
          pytest-coverage-path: ${{ env.WORKING_DIRECTORY }}/pytest-coverage.txt
          junitxml-path: ${{ env.WORKING_DIRECTORY }}/pytest.xml
```

以下のActionを使用します

https://github.com/MishaKav/pytest-coverage-comment

## ワークフローを実行しよう
PRを作成したらワークフローが実行されます
下記のようにテストが実行できたら成功です
![スクリーンショット 2023-07-05 8.14.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/67ba8df0-3759-2f98-4139-d1ddc873024d.png)
![スクリーンショット 2023-07-05 8.15.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/63fe61fc-d5ad-44f5-6f9e-65ee820a5b24.png)

また、以下のようにPRにカバレッジが表示させることも確認できました

![スクリーンショット 2023-07-05 8.15.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d3f18071-4f9d-12c5-2047-eb359beaef68.png)
![スクリーンショット 2023-07-05 8.16.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/314d773c-ad88-509e-17e0-9222db52f2bc.png)

## 参考
https://www.miracleave.co.jp/contents/1538/github-actions-ci/

https://www.hacksoft.io/blog/github-actions-in-action-setting-up-django-and-postgres

https://github.com/actions/setup-python

https://www.codingforentrepreneurs.com/courses/django-kubernetes/lessons/github-actions-run-django-tests/

https://docs.github.com/ja/actions/learn-github-actions/variables

https://docs.github.com/ja/actions/using-containerized-services/about-service-containers
