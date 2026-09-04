---
title: GitHub Actionsとgit diffを使って差分に応じて処理を変えるワークフローを作成するには
tags:
  - Django
  - Git
  - MySQL
  - checkout
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 16631c6720ec7c2b1a26
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsを使って例えばModelを追加したときのみModelのテストも行いたいなど、gitを使って差分に応じてテストする項目を変更したい場合(実行時間を短縮したい)場面があるかと思うので今回はその方法について解説したいと思います

## 前提
- 言語/FWはPython/Djangoを使用
- DBはMySQLを使用

## ディレクトリ構成
```
tree
・
├── .github
│   └── workflows
│       └── test-without-model.yml
└── application
    ├── application
    │   ├── __init__.py
    │   │   ├── models
    │   │   │   ├── __init__.py
    │   │   │   ├── customer.py
    │   │   │   └── user.py   
    │   ├── admin.py
    │   └── apps.py
    ├── manage.py
    ├── poetry.lock
    ├── project
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls.py
    │   └── wsgi.py
    └── pyproject.toml
```

## ワークフローの作成
以下のようにModelの変更を検知し、変更されたら全てのテストを実行し、変更されなかったらModel以外のテストを実行するワークフローを実行します
本ワークフローではサービスコンテナやカバレッジの表示方法などを記載していますが、詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/d03eef4acbb8d8980d1a

```test-without-model.yml
name: Run Pytest without Model
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test-db
  MYSQL_HOST: 127.0.0.1
  MYSQL_PORT: 3306
  MYSQL_USER: test
  MYSQL_PASSWORD: test
  DJANGO_SETTINGS_MODULE: project.settings.local

jobs:
  Setup:
    name: Run Test Code
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
          --health-interval 10
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - name: Check for model changes
        run: |
          MODEL_CHANGED=false
          if git diff --name-only origin/${{ github.base_ref }} | grep -c ${{ env.WORKING_DIRECTORY }}/application/models/ > 0; then
            MODEL_CHANGED=true
          fi
          echo "MODEL_CHANGED=$MODEL_CHANGED" >> $GITHUB_ENV
      - name: Grant privileges to user
        run: mysql --protocol=tcp -h 127.0.0.1 -P 3306 -u root -p$MYSQL_ROOT_PASSWORD -e "GRANT ALL PRIVILEGES ON *.* TO '$MYSQL_USER'@'%'; FLUSH PRIVILEGES;"
      # Poetryのインストール
      - name: Install poetry
        run: pipx install poetry
      # Pythonのセットアップを実行
      # 2回目以降のテスト実行時はrunner内にPoetryのCacheを生成してPoetryのセットアップを高速化
      - name: Use cache dependencies
        uses: actions/setup-python@v7
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      # Poetry内の必要なパッケージのインストールを実行
      - name: Install Packages
        run: poetry install
      - name: Run migration
        run: poetry run python manage.py migrate
      - name: Run Pytest Without Model
        if: env.MODEL_CHANGED == 'false'
        run: |
          set -o pipefail
          poetry run pytest ${{ env.WORKING_DIRECTORY }}/tests/serializers ${{ env.WORKING_DIRECTORY }}/tests/views --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code | tee pytest-coverage.txt
      - name: Run Pytest
        if: env.MODEL_CHANGED == 'true'
        run: |
          set -o pipefail
          poetry run pytest --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code | tee pytest-coverage.txt
      - name: Pytest coverage comment
        uses: MishaKav/pytest-coverage-comment@v1.12.2
        with:
          pytest-coverage-path: ${{ env.WORKING_DIRECTORY }}/pytest-coverage.txt
          junitxml-path: ${{ env.WORKING_DIRECTORY }}/pytest.xml

```

### gitの変更履歴を含めてcheckoutする
公式のcheckoutのactionを使用します
`fetch-depth: 0`がないとgit diffを使って差分を検知できず、
```
fatal: ambiguous argument 'origin': unknown revision or path 
       not in the working tree.
Use '--' to separate paths from revisions, like this:
'git <command> [<revision>...] -- [<file>...]'
```
というエラーを出すので注意が必要です
(checkout@v2以降はデフォルトで1コミットまでしかfetchできないため)

```yaml
      - name: Checkout code
        uses: actions/checkout@v7
        with:
          fetch-depth: 0
```

詳細は以下の記事とissueを参考にしてください

https://github.com/actions/checkout?tab=readme-ov-file#fetch-all-history-for-all-tags-and-branches

https://github.com/actions/checkout/issues/438#issuecomment-773284400

### 差分の検知
git diffを使って差分を検知します
git diffの--name-onlyをオプションを使って差分のあるファイル名の一覧を取得できます

```
git diff
application/application/migrations/0001_initial.py
application/application/migrations/0002_alter_address_table_comment_and_more.py
application/application/migrations/0003_alter_address_house_no_alter_address_id_and_more.py
application/application/migrations/0004_alter_customer_table_comment.py
application/application/models/user.py
```

`${{ github.base_ref }}`はGitHubのコンテキスト情報でこのコンテキストを使用するとリポジトリの基底ブランチ(デフォルトで設定しているブランチ)になります
今回はdevelopブランチに設定しており、
ただし、本コンテキストはpull_requestまたはpull_request_targetイベントでのみ使用できます

> The base_ref or target branch of the pull request in a workflow run. This property is only available when the event that triggers a workflow run is either pull_request or pull_request_target

https://docs.github.com/en/actions/learn-github-actions/contexts#github-context

grep -c を使って指定したModelのパスと一致するファイルの数を集計し、1以上であればMODEL_CHANGED=True、0であればMODEL_CHANGED=Falseにし、GITHUB_ENVに格納します
GITHUB_ENVを使って環境変数を定義または更新し、書き込むことで、後続の分岐のステップで環境変数が利用できるようになります

```yaml
      - name: Check for model changes
        run: |
          MODEL_CHANGED=false
          if git diff --name-only origin/${{ github.base_ref }} | grep -c ${{ env.WORKING_DIRECTORY }}/application/models/ > 0; then
            MODEL_CHANGED=true
          fi
          echo "MODEL_CHANGED=$MODEL_CHANGED" >> $GITHUB_ENV
```

### ワークフローシンタックスを使った分岐処理
GitHub Actions内でif文を使って処理を分岐します
GITHUB_ENV内のMODEL_CHANGEDがfalseの場合はModel以外のテストを実行し、trueの場合は全てのテストを実行します

```yaml
      - name: Run Pytest Without Model
        if: env.MODEL_CHANGED == 'false'
        run: |
          set -o pipefail
          poetry run pytest ${{ env.WORKING_DIRECTORY }}/tests/serializers ${{ env.WORKING_DIRECTORY }}/tests/views --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code | tee pytest-coverage.txt
      - name: Run Pytest
        if: env.MODEL_CHANGED == 'true'
        run: |
          set -o pipefail
          poetry run pytest --junitxml=pytest.xml -x -n auto --cov --no-cov-on-fail --suppress-no-test-exit-code | tee pytest-coverage.txt
```

https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idif

## 実際にワークフローを実行してみよう！
Modelを変更した状態で`if: env.MODEL_CHANGED == 'true'`へ分岐された状態でテストが実行されたら成功です

![スクリーンショット 2024-06-10 13.37.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a9969c13-ef5d-545e-3ae2-c3e22cc8f00f.png)

Modelが変更されていない状態で`if: env.MODEL_CHANGED == 'false'`へ分岐された状態でModel以外のテストが実行されたら成功です

![スクリーンショット 2024-06-10 13.37.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b1fbfea8-d63c-3657-d3e4-17c6afaedd23.png)

## 参考
https://docs.github.com/en/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idif

https://www.ibm.com/docs/ja/aix/7.1?topic=g-grep-command#grep__row-d3e144113

https://github.com/actions/checkout#fetch-all-history-for-all-tags-and-branches
