---
title: '[Django+MySQL+Pytest] Pytestを各カテゴリ別で並列に実行しよう'
tags:
  - Django
  - MySQL
  - pytest
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 593c36f7cb7d35c066de
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
テストコードが肥大化していくとテストの実行時間がどんどん長くなっていきます
そのため、テストの実行時間を短縮する手段の一つとして例えばDjangoのModelとViewのテストを同時並列で進めるのが有効になっていきます
今回はJobとMatrixがデフォルトで並行実行できることを応用してPytestをディレクトリごとに並列で実行させる方法について解説していきたいと思います
Matrixについて詳細に知りたい方は以下を参照してください

https://qiita.com/shun198/items/ea53b6614cea777b3130

## 前提
今回はあくまで並列実行の方法についての記事なので以下の内容については細かく説明しません

- MySQLのサービスコンテナを使用

サービスコンテナについて詳細に知りたい方は以下を参照してください

https://qiita.com/shun198/items/d03eef4acbb8d8980d1a

## ワークフローの作成
今回は
- test.yml

にPytestを並列実行するワークフローを記載します
ディレクトリ構成は以下のとおりです

```
❯ tree 
.
├── .github
│   └── workflows
│       └── test.yml
└── application # Djangoのプロジェクトファイルおよびpyproject.tomlが入ったディレクトリ
    ├── project
    │   └── settings.py
    ├── application
    │   └── tests # application内のtestsディレクトリにテストを格納
    ├── manage.py
    ├── poetry.lock
    └── pyproject.toml
```

```yml:.github/workflows/test.yml
name: Run Pytest Parallel
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

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
  test:
    name: Run Test Code
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    strategy:
      matrix:
        test-path: ['models', 'serializers', 'utils', 'views']
    runs-on: ubuntu-24.04
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
      - name: Checkout
        uses: actions/checkout@v6
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
      - name: Install poetry
        run: pipx install poetry
      - name: Use cache dependencies
        uses: actions/setup-python@v6
        with:
          python-version: '3.10'
          cache: 'poetry'
      - name: Install Packages
        run: poetry install
      - name: Execute Migration
        run: |
          poetry run python manage.py makemigrations
          poetry run python manage.py migrate
      - name: Run Pytest
        run: poetry run pytest application/tests/${{ matrix.test-path }}
```

### 分割するフォルダの設定
以下のようにtest-pathを定義し、配列の中に該当するファイルを記載します
今回は
- models
- serializers
- utils(パスワードのバリデータなどの自作モジュールのテスト)
- views

にテストを分割して実行します
```yml
    strategy:
      matrix:
        test-path: ['models', 'serializers', 'utils', 'views']
```

### テストを並列実行する設定
先ほど設定したtest-path内の配列の値が`${{ matrix.test-path }}`に入ります
```yml
      - name: Run Pytest
        run: poetry run pytest application/tests/${{ matrix.test-path }}
```

## テストを実行してみよう！
実際にテストを実行していくと以下のようにJob名の横にMatrix内に記載した配列の中身がカッコつきで表示されている上で並列で実行されていることが確認できました

<img width="715" alt="スクリーンショット 2023-02-17 11.31.55.png (178.4 kB)" src="https://img.esa.io/uploads/production/attachments/14274/2023/02/17/133248/ec18d20c-e3dc-4030-97ab-1d4797b0b7c5.png">

## まとめ
Matrixを使わずにJobを使うだけでも並列実行自体はできるのですがJobの数分だけサービスコンテナの設定を何回も書くのが冗長で嫌だったので今回はMatrixを使ってみました
Matrixを使うとサービスコンテナの設定を1回記載するだけで良くなる上に格段に可読性が向上するので個人的に試してみて良かったと感じております
