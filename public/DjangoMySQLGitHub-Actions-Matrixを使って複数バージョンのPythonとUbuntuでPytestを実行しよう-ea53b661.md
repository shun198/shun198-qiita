---
title: '[Django+MySQL+GitHub Actions] Matrixを使って複数バージョンのPythonとUbuntuでPytestを実行しよう'
tags:
  - Django
  - MySQL
  - pytest
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:12+09:00'
id: ea53b6614cea777b3130
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
今回はMatrixを使用する例としてDjangoとMySQLとPytestを使用します
DjangoとMySQLのサービスコンテナを使ってPytestを実行する方法について
本記事では解説しないので詳細に知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/d03eef4acbb8d8980d1a

## Matrixとは
同じワークフローを複数の

- 実行環境(Node.jsなど)
- runnerOS (Ubuntuなど)
- 言語(Pythonなど)

のバージョンで実行できる仕組みです
Matrixを使うと例えばバージョンをアップデートする際の検証やトラブルシューティングに役立つかと思います
デフォルトでは全てのバージョンを以下のように並列で実行できます

![スクリーンショット 2023-02-12 11.54.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/91c72afe-3675-9a29-5d13-57b39c7dff50.png)

また、Matrixを使用する際は一つのJobsが失敗すると他のJobsが実行されないのも特徴です
(ただし、continue-on-errorを追加した場合は除く)

![スクリーンショット 2023-02-12 11.55.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/53c85d17-be05-7c43-b4cf-6c298f1b0cd7.png)


## Matrixの設定方法
Matrixを設定する際は以下の例のように`strategy`を定義し、その下に`matrix`を定義します
matrixの下に任意の変数を定義し、テストしたいバージョンの一覧を配列に入れます

```.github/workflows/test.yml
jobs:
  Setup:
    name: Run Test Code
    # 実行したいバッケージ等のバージョンを配列内にstrategyとmatrixに指定
    strategy:
      matrix:
        python-version: [3.10.5, 3.10.6, 3.10.7]
        os: [ubuntu-latest, ubuntu-20.04]
```

Job内でMatrixで定義したバージョンを適用させたい処理には以下のように記載します
例えばOSのバージョンを適用させたいときは以下のように記載します
```
${{ matrix.os }}
```

## 実際に実行してみよう！
以上を踏まえてMatrixを適用させると以下の例のようになります

### ディレクトリ構成
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

### ワークフロー
```.github/workflows/test.yml
name: Run Pytest Using Matrix

# ワークフローのイベントは任意です
# 今回は検証用なので手動でワークフローを実行するようにします
on: workflow_dispatch

env:
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

jobs:
  Setup:
    name: Run Test Code
    # 実行したいバッケージ等のバージョンを配列内にstrategyとmatrixに指定
    strategy:
      matrix:
        python-version: [3.10.5, 3.10.6, 3.10.7]
        os: [ubuntu-latest, ubuntu-20.04]
    runs-on: ${{ matrix.os }}
    defaults:
      run:
        working-directory: application
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
      - name: Chekcout code
        uses: actions/checkout@v6
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
      - name: Install poetry
        run: pipx install poetry
      - name: Use cache dependencies
        uses: actions/setup-python@v6
        with:
          python-version: ${{ matrix.python-version }}
          cache: 'poetry'
      - name: Install Packages
        run: poetry install
      - name: Run migration
        run: |
          poetry run python manage.py makemigrations
          poetry run python manage.py migrate
      - name: Run Pytest
        run: poetry run pytest -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code
```

### Django側の設定
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

前述の通り、各Jobが並列で実行され、成功すると以下のようになります
![スクリーンショット 2023-02-12 11.59.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3ddf1867-d07e-3fef-faed-51fb2ad32adc.png)

## 特定のバージョンのみ追加したいとき
例えば
- Python 3.10.8
- Ubuntu 18.04

だけ追加で検証したいときは`include`を使用します
2つとも配列に入れてしまうと
- Python 3.10.8
- Ubuntu 20.04 と latest

など、実行しなくてもいいバージョンのJobまで実行されてしまいます
そのため、今回みたいなケースでは`include`を使用します

```.github/workflows/test.yml
    strategy:
      matrix:
        python-version: [3.10.5, 3.10.6, 3.10.7]
        os: [ubuntu-latest, ubuntu-20.04]
        # includeを使って python-version: 3.10.8 と ubuntu-18.04 のみ追加
        include:
          - python-version: 3.10.8
            os: ubuntu-18.04
```

以下のように
- Python 3.10.8
- Ubuntu 18.04

のJobのみ追加されていることが確認できました

![スクリーンショット 2023-02-12 12.14.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b907a60e-d8b0-b54f-caf8-c372cd254076.png)

## 特定のバージョンのみ除外したいとき
特定のバージョンのみ除外するときはincludeとは逆にexcludeを使用します
今回は
- Python 3.10.5
- Ubuntu 20.04

のJobのみ実行しないようにします

```.github/workflows/test.yml
    strategy:
      matrix:
        python-version: [3.10.5, 3.10.6, 3.10.7]
        os: [ubuntu-latest, ubuntu-20.04]
        # includeを使って python-version: 3.10.5 と ubuntu-20.04 のみ除外
        exclude:
          - python-version: 3.10.5
            os: ubuntu-20.04
```

以下のように
- Python 3.10.5
- Ubuntu 20.04

が実行されていないことが確認できました
![スクリーンショット 2023-02-12 12.17.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/031b2b15-cd47-9b2a-8535-35971fbe9cc9.png)


## 参考
https://docs.github.com/en/actions/using-jobs/using-a-matrix-for-your-jobs
