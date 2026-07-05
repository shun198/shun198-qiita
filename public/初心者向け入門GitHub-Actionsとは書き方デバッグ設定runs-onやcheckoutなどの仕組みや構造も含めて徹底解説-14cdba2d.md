---
title: 【初心者向け】【入門】GitHub Actionsとは？書き方、デバッグ設定、runs-onやcheckoutなどの仕組みや構造も含めて徹底解説
tags:
  - Linux
  - GitHub
  - GitHubActions
private: false
updated_at: '2025-08-15T19:42:09+09:00'
id: 14cdba2d8e58ab96cf95
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsの
- 仕組みや構造
- 基本的な書き方(ワークフロー、ジョブ、イベントなど)
- よく出てくるruns-on、actions/checkoutで何してるのか
- 環境変数とsecrets
- サービスコンテナ
- 環境のsetup
- 権限
- GitHub Pages
- Matrix
- メタデータ構文
- OpenID Connect

について解説していきたいと思います

## そもそもGitHub Actionsとは
公式に
> GitHub Actions is a continuous integration and continuous delivery (CI/CD) platform that allows you to automate your build, test, and deployment pipeline.

と書かれているようにビルド、テスト、デプロイなどを自動化するCI/CDプラットフォームのことです
今まではCircleCIやTravisCIなどの外部サービスと連携する必要がありましたがGitHub Actionsと使うことでCI/CDをGitHub内で完結させることができるようになりました

## GitHub Actionsの仕組み
`.github/workflows`ディレクトリ内にymlファイルを設置し、Workflow(ワークフロー)をファイル内に書きます。指定したEvent(push、pull_requestなど。後述)が発生すると実行されます

:::note warn
.github/workflowsのディレクトリ名を間違えると実行されないので注意してください
:::

Workflow(ワークフロー)はJob(ジョブ)単位で分けられています
JobはRunner(ランナー)という仮想マシンのインスタンス上で実行されます
JobはさらにStep単位で分けられており、Step内にコマンドなどの処理が実行されます。
![github_actions.jpg](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/10ccc7c8-ea17-fa75-c4a2-2136364ac725.jpeg)

## 書き方を学んでいこう！
簡単なワークフローを例に書き方について解説します
かなり量が多いですが一つずつ一緒に頑張っていきましょう

### jobs
処理の最上位単位です
jobsの中に1つ以上のジョブIDと共に処理が設定され、並列で実行されます
```yml:.github/workflows/tutorial.yml
jobs:
  # "my_first_job"というジョブIDでジョブを定義
  my_first_job:
    name: My first job
  # "my_second_job"というジョブIDでジョブを定義
  my_second_job:
    name: My second job
```
左のJobsにジョブ名が記載されます

![スクリーンショット 2023-06-15 10.26.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cdd97f0c-ae83-ccdf-1452-e00259f8bcff.png)

### on
どのイベントが発生したら処理を実行するか指定します

```yml:.github/workflows/on.yml
# リモートリポジトリへpush時にjobsを実行
on: [push]
```

よく使われるのは以下の表のとおりです

|イベント|説明|
|--|--|
|push|リモートリポジトリへpush時|
|pull_request|プルリクエスト作成時|
|deployment|デプロイ時|
|release|リリース時|
|issues|GitHub Issues関連の処理発生時|
|schedule|cronによる定期実行|


上記以外で使用できるイベントはかなり多いため、詳細はドキュメントを参照してください

https://docs.github.com/ja/actions/using-workflows/events-that-trigger-workflows#available-events

### runs-on
ジョブを実行するOS(ランナー)を指定します

```yml:.github/workflows/os.yml
# ubutnuの最新版を指定
runs-on: ubuntu-latest
```

指定したランナーの詳細は実行する際にSet up jobsという項目が表示されるのでそこから確認できます
![スクリーンショット 2022-10-10 9.40.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/50f31af0-b7b1-554f-dafd-0307b3ef7ae0.png)

一般的なWeb開発ではUbuntuを選択するケースが多いかと思います(ローカル上で動かすコンテナのイメージがUbuntuかAlphineのため)
使用できるランナーの一覧は以下の通りです

|  使用できるランナー(OS)  |  記述方法  |  メモ  |
|-----|-----|-----|
|  Windows Server 2025  |  windows-latest/windows-2025  |  windows-latestと記述してもWindows Server 2025を指定できる  |
|  Windows Server 2022  |  windows-2022  |  -  |
|  Ubuntu 24.04  |  ubuntu-latest/ubuntu-24.04  |  ubuntu-latestと記述してもUbuntu 24.04を指定できる  |
|  Ubuntu 22.04  |  ubuntu-22.04  |  -  |
|  Ubuntu 26.04 |  ubuntu-26.04  |  Preview版  |
|  macOS 15  |  macos-latest/macos-15  |  macos-latestと記述してもmacOS 15を指定できる  |
|  macOS 14 |  macos-14  |   -  |

### uses

第三者もしくはGitHubが作成したActionsをyml内に記載することで実行することもできます
よく使われているのがGitHubが用意している`actions/checkout@v6`です

https://github.com/actions/checkout

```yml:.github/workflows/checkout.yml
  - name: Checkout
    uses: actions/checkout@v6
```

usesに見たことない文字列が表示されていることが多いのでそういう時は下記のmarketplaceから検索してみましょう

https://github.com/marketplace?type=actions

#### actions/checkout@v5って何してるの？
興味のある方だけ見ていただければ幸いです
簡単なActionを作ってみたので挙動を確認してみましょう
今までのおさらいで
- jobs
- on
- runs-on

を使用しています。後述のsteps、name、runについては後ほど説明します
現時点ではこれ書いてたらコマンド実行できるんだなあと思っていただけたらと大丈夫です
リモートリポジトリへpushすると

- (チェックアウト前の)ファイル構成とパスを確認するコマンドを実行
- usesを使ってactions/checkout@v5を実行
- (チェックアウト後の)ファイル構成とパスを確認するコマンドを実行

するという流れになっています

```yml:.github/workflows/linux-command.yml
name: command
on: [push]
jobs:
  command:
    name: Use Linux commands
    runs-on: ubuntu-24.04
    steps:
      - name: Show ubuntu details
        run: lsb_release -a
      - name: Inspect files before checkout
        run: ls -la
      - name: show current directory before checkout
        run: pwd
      - name: Checkout
        uses: actions/checkout@v6
      - name: Inspect files after checkout
        run: ls -la
      - name: show current directory after checkout
        run: pwd
      - name: show all branches after checkout
        run: git branch -a
```

まずはUbuntuのバージョンやコードネームを確認します
runs-onで指定したUbuntuが選択されていることが確認できます
```yml:.github/workflows/linux-command.yml
  - name: Show ubuntu details
    run: lsb_release -a
```
```terminal:logs
Run lsb_release -a
No LSB modules are available.
Distributor ID:	Ubuntu
Description:	Ubuntu 20.04.5 LTS
Release:	20.04
Codename:	focal
```

次に`actions/checkout@v6`を実行する前のファイル構成とパスを確認します
```yml:.github/workflows/linux-command.yml
  - name: Inspect files before checkout
    run: ls -la
  - name: show current directory before checkout
    run: pwd
```

`/home/runner/work/<リポジトリ名>/<リポジトリ名>`のパス内に何も入っていないことが確認できます
```terminal:logs
Run ls -la
total 8
drwxr-xr-x 2 runner docker 4096 Oct  9 22:02 .
drwxr-xr-x 3 runner docker 4096 Oct  9 22:02 ..
Run pwd
/home/runner/work/<リポジトリ名>/<リポジトリ名>
```

`/home/runner/work/<リポジトリ名>/<リポジトリ名>`ってどこから来ているのか解説すると、自身で作成されたワークフローを実行するパスのことで$GITHUB_WORKSPACEという環境変数を読み込んで実行しています
環境変数の中身を確認すると以下のようになっているかと思います

```
GITHUB_WORKSPACE=/home/runner/work/<リポジトリ名>/<リポジトリ名>
```

`/home/runner/work/`までは一緒ですがその後はWorkflowを実行するリポジトリ名がディレクトリ名として指定されます

`actions/checkout@v6`を実行します
```yml:.github/workflows/linux-command.yml
  - name: Checkout
    uses: actions/checkout@v6
```

```terminal:logs
Run actions/checkout@v6
Syncing repository: shun198/***-<リポジトリ名>
Getting Git version info
Temporarily overriding HOME='/home/runner/work/_temp/da727d01-5e2c-459c-b8db-380fb0265762' before making global git config changes
Adding repository directory to the temporary git global config as a safe directory
/usr/bin/git config --global --add safe.directory /home/runner/work/<リポジトリ>/<リポジトリ>
Deleting the contents of '/home/runner/work/*/<リポジトリ名>/<リポジトリ名>'
Initializing the repository
Disabling automatic garbage collection
Setting up auth
Fetching the repository
Determining the checkout info
Checking out the ref
/usr/bin/git log -1 --format='%H'
```

ログがかなり多いので手順を簡単に説明すると

1. ランナー内のリポジトリのGitの処理設定
1. Gitの認証設定
1. リモートリポジトリから処理を実行するブランチのリポジトリのソースコードをfetch
1. fetchしたソースコードと同じブランチをチェックアウト

しています。要するにランナー内にリモートリポジトリにあるソースコードをクローンに限りなく近い形(厳密には違う)で複製していることになります。
クローンだとデフォルトのブランチ(main、develop)のソースコードしか抽出できず、作業する際に使うfeatureブランチのソースコードだけテストできないからfetchとcheckoutをしているのだと筆者は考えています
これについて詳しい方がいましたらぜひご教授いただけると幸いです
`actions/checkout@v6`の詳細を知りたい方は実際にログを確認してみてください

実行した後のファイル構成、パス、ブランチ一覧を確認します
```yml:.github/workflows/linux-command.yml
  - name: Inspect files after checkout
    run: ls -la
  - name: show current directory after checkout
    run: pwd
  - name: show all branches after checkout
    run: git branch -a
```

`/home/runner/work/<リポジトリ名>/<リポジトリ名>`のパス内に自身が作業したブランチのファイル構成が確認できました
また、`git branch -a`を実行してもmainやdevelopブランチはなく、作業していたfeatureブランチのみ表示されたことが確認できました(git cloneだとデフォルトで設定したmainブランチのソースコードがクローンされるはずです)
```terminal:logs
Run ls -la
  ls -la
  shell: /usr/bin/bash -e {0}
total 88
drwxr-xr-x 11 runner docker 4096 Oct  9 22:02 .
drwxr-xr-x  3 runner docker 4096 Oct  9 22:02 ..
drwxr-xr-x  2 runner docker 4096 Oct  9 22:02 .devcontainer
drwxr-xr-x  8 runner docker 4096 Oct  9 22:02 .git
drwxr-xr-x  3 runner docker 4096 Oct  9 22:02 .github
-rw-r--r--  1 runner docker 3088 Oct  9 22:02 .gitignore
drwxr-xr-x  2 runner docker 4096 Oct  9 22:02 .vscode
-rw-r--r--  1 runner docker 4664 Oct  9 22:02 README.md
drwxr-xr-x  5 runner docker 4096 Oct  9 22:02 containers
-rw-r--r--  1 runner docker 1836 Oct  9 22:02 docker-compose.yml
-rwxr-xr-x  1 runner docker  126 Oct  9 22:02 entrypoint.sh
-rwxr-xr-x  1 runner docker  661 Oct  9 22:02 manage.py
drwxr-xr-x  3 runner docker 4096 Oct  9 22:02 application
-rw-r--r--  1 runner docker  207 Oct  9 22:02 requirements.txt
drwxr-xr-x  5 runner docker 4096 Oct  9 22:02 static
Run pwd
  pwd
  shell: /usr/bin/bash -e {0}
/home/runner/work/<ディレクトリ名>/<ディレクトリ名>
Run git branch -a
  git branch -a
  shell: /usr/bin/bash -e {0}
* feature/01
```

#### オプション
checkoutにはコミット履歴を取得する機能も存在します
以下のように`fetch-depth: 0`と指定すれば全てのタグとブランチのコミット履歴を取得できます

```yaml
jobs:
  command:
    name: Use Linux commands
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v6
        with:
          fetch-depth: 0
```

`actions/checkout@v6`の説明は以上です

### steps
図でも説明した通り一つのjobsは1つ以上のstepsで構成されており、stepsの中にrunコマンドが1つ以上構成されています

```yaml
jobs:
  command:
    name: Use Linux commands
    runs-on: ubuntu-24.04
    steps:
      - name: Checkout
        uses: actions/checkout@v6
```

### run
runに実行するコマンドを以下のように記載していきます
nameにrunの処理について書くことができ、GitHub上で確認できます
```yml:.github/workflows/linux-command.yml
  - name: Inspect files before checkout
    run: ls -la
  - name: show current directory before checkout
    run: pwd
```

![スクリーンショット 2022-10-10 12.07.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f0b5d1ab-310b-9d53-ea6b-9741ba686e68.png)


また、複数以上のコマンドを実行したい時は `run　| `と記載します
```yml:.github/workflows/linux-command.yml
  - name: Inspect and show current directory files before checkout
    run: |
        ls -la
        pwd
```

### env
ワークフロー内に環境変数を設定できます
環境変数を使用する際はenvの下に以下のように
```
SECRET_KEY: test
```
という風に環境変数の名前と対応する値を記載します

```yml:.github/workflows/env.yml
env:
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings.local
  ALLOWED_HOSTS: 127.0.0.1
  MYSQL_ROOT_PASSWORD: root
  MYSQL_DATABASE: test-db
  MYSQL_HOST: 127.0.0.1
  MYSQL_PORT: 3306
  MYSQL_USER: test
  MYSQL_PASSWORD: test
```

### secrets
こちらも環境変数を格納することができます
envと違って
- AWSのシークレットキー
- AWSのアクセスキー

など見られたくない情報を格納するときに使うのが一般的です
secretsを使うことで秘匿情報を暗号化した状態で使用できます

リポジトリのSettingsを開きます
![スクリーンショット 2022-09-30 21.18.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/433b26ef-828b-8dfc-e5dd-cbcf5bbd80c8.png)

Security>Secrets>Actionsを開きます
![スクリーンショット 2022-09-30 21.18.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/74db794a-2b50-369b-45c5-b4a1845df488.png)

New repository secretを押します
![スクリーンショット 2024-07-26 11.34.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5458108c-a691-def2-0107-5c8868ccda76.png)

以下にsecret名と値を入れます
一度Add secretを押すと二度と中身が見れないので注意してください
![スクリーンショット 2023-07-14 21.39.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d72a93f8-390c-f17c-e07a-04d1c75b81af.png)

以下のようにsecretsが作成されたら成功です

![スクリーンショット 2024-07-26 11.35.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7b3a47bb-11ea-f0ee-f448-0af1b28b7676.png)

#### secretsの使用方法
secretsを使用するときは
```
${{ secrets.AWS_ACCESS_KEY }}
```
という風に記載することで暗号化した状態の環境変数を使用できます
以下が公式のAWSの認証用のActionを使った例です

https://github.com/aws-actions/configure-aws-credentials

```yaml:.github/workflows/secrets.yml
    - name: Configure AWS Credentials
      uses: aws-actions/configure-aws-credentials@v6
      with:
        aws-access-key-id: ${{ secrets.AWS_ACCESS_KEY }}
        aws-secret-access-key: ${{ secrets.AWS_SECRET_KEY }}
        aws-region: ap-northeast-1
```

#### デバッグの設定
Settingsタブのsecretsに

- ACTIONS_RUNNER_DEBUG
- ACTIONS_STEP_DEBUG

をTrueで保存すると

- Runnerの実行ログ
- Step毎の実行ログ

を確認することができ、デバッグ効率がよくなリます

![スクリーンショット 2023-06-15 10.27.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a8c0c133-8ae2-a824-3d22-731ebe9c31c1.png)

![スクリーンショット 2023-06-15 10.27.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6443d9ec-0e28-eb63-bc8b-c5779c5c11bf.png)

- 設定前
![スクリーンショット 2023-06-15 10.28.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/de667398-1c3f-d2d2-1b36-af8c69cc1a5d.png)

- 設定後
![スクリーンショット 2023-06-15 10.28.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a7daa208-3174-184d-9958-2055eadf62a3.png)

### サービスコンテナ
ワークフローを実行する際に必要になるサービスを使用するためのDockerコンテナです
バックエンドの単体テストを自動実行する際にDBのサービスコンテナを使うのが一般的です
サービスコンテナを使うことでGitHub内のランナー上でDBなどのサービスを利用する必要がないのでワークフローを単純化できる上にランナー内の限られたリソースを無駄に使わなくて済むので実行速度も短縮できます

#### サービスコンテナの設定方法
```yaml:.github/workflows/service-container.yml
    services:
      db:
        image: mysql:8.0
        ports:
          - 3306:3306
        env:
          MYSQL_ROOT_PASSWORD: root
          MYSQL_DATABASE: test-db
          MYSQL_USER: test
          MYSQL_PASSWORD: test
        options: >-
          --health-cmd "mysqladmin ping"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
```

サービスコンテナを作成するときはservicesを定義し、
imageはDocker hubにある各サービスの公式のDocker imageのバージョンを指定します
今回はMySQLのコンテナを作成します
DBをフレームワークと接続する際は環境変数も設定するのが一般的なので先ほど紹介したenvを使用します
今回の例ではテストを実行するだけなのでsecrets内に環境変数を定義せずにテスト用の環境変数を使用しています

#### options
options内に実行したい任意のコマンドを記載します
DBやRedisなどのインメモリキャッシュとの接続の際はヘルスチェックコマンドを記載するのが一般的です
ヘルスチェックって何？コマンドの意味がわからないという方は以下の記事を参考にしてください

https://qiita.com/shun198/items/a66d6214cdab5629029d

サービスコンテナの詳細は以下のとおりです

https://docs.github.com/ja/actions/using-containerized-services/about-service-containers

### 環境のsetup
GitHub Actionsの公式もしくは各言語の公式が出しているactionを使うとワークフロー内でパッケージのインストールコマンドを書かずに設定できます
例えばGitHub Actionsが出しているsetup-pythonというactionを使うだけでランナー内にpipを入れたり、Pythonを入れるコマンドを書かずにPythonを実行できる環境を用意できます

今回は
- Python
- Node.js

を例にsetup系のactionの使い方を記載します

#### Python
公式が出しているPythonのsetup用のactionです

```yaml:.github/workflows/setup-python.yml
steps:
    - uses: actions/checkout@v6

    - uses: actions/setup-python@v6
      with:
        python-version: '3.14' 
    - run: python my_script.py
```

オプションとしてPoetryを使ってインストールしたパッケージをCacheできます
Cacheを使うことで2回目以降ワークフローを実行する際にpoetry installを実行するとインストールしたパッケージをCacheを参照して使うのでインストール時間が短縮されます

```yaml:.github/workflows/setup-python.yml
steps:
    - uses: actions/checkout@v6
    - name: Install poetry
      run: pipx install poetry
    - uses: actions/setup-python@v6
      with:
        python-version: '3.14'
        cache: 'poetry'
    - run: poetry install
```

また、python-version-fileのオプションを使うことでpyproject.toml内に記載されたPythonのversionを自動的に適用させることもできます
```yml
    - uses: actions/setup-python@v6
      with:
        python-version-file: "pyproject.toml"
        cache: 'poetry'
    - run: poetry install
```

以下がsetup-pythonの詳細です

https://github.com/actions/setup-python

#### Node.js
公式が出しているNode.jsのsetup用のactionです
Nodeのversionについては16,18,20をサポートしています
以下がnpmを使ってCacheを使うときのワークフロー例です

```yaml:.github/workflows/setup-node.yml
steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version: 16
        cache: 'npm'
        cache-dependency-path: '**/package-lock.json'
    - run: npm ci
```

npm以外にyarnを使ったCacheのワークフローも実装できます
```yaml:.github/workflows/setup-node.yml
steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version: 16
        cache: 'yarn'
        cache-dependency-path: '**/package-lock.json'
    - run: npm ci
```

また、node-version-fileのオプションを使うことでpackage.json内に記載されたNodeのversionを自動的に適用させることもできます

> The node-version-file input accepts a path to a file containing the version of Node.js to be used by a project, for example .nvmrc, .node-version, .tool-versions, or package.json. If both the node-version and the node-version-file inputs are provided then the node-version input is used. See supported version syntax.

```yaml:.github/workflows/setup-node.yml
steps:
    - uses: actions/checkout@v6
    - uses: actions/setup-node@v6
      with:
        node-version-file: 'package.json'
    - run: npm ci
    - run: npm test
```

Voltaを使ってNodeのバージョンを指定した際はVoltaに記載したNodeのバージョンを適用します
もし、Voltaの記述がない場合はenginesがあればengines内のNodeのバージョンを適用します

> When using the package.json input, the action will look for volta.node first. If volta.node isn't defined, then it will look for engines.node.

```package.json
{
  "engines": {
    "node": ">=16.0.0"
  },
  "volta": {
    "node": "16.0.0"
  }
}
```

https://github.com/actions/setup-node

### 権限
GitHub Actionsではデフォルトのバージョンをワークフロー内で自身で決めることもできます
各権限のことをスコープといい、デフォルトは全てread権限です
スコープには
- read
- write
- none

の3つの権限を付与できます
ワークフロー内でスコープとその権限を一つ以上定義した場合、定義していない他のスコープの権限は全てnoneになります
各スコープの詳細は以下の通りです

```
permissions:
  actions: read|write|none
  checks: read|write|none
  contents: read|write|none
  deployments: read|write|none
  id-token: read|write|none
  issues: read|write|none
  discussions: read|write|none
  packages: read|write|none
  # GitHub Pages
  pages: read|write|none
  pull-requests: read|write|none
  repository-projects: read|write|none
  security-events: read|write|none
  statuses: read|write|none
```

https://docs.github.com/en/actions/using-jobs/assigning-permissions-to-jobs

#### permissionを自身で定義するワークフロー例
GitHubが公式に出しているconfigure-aws-credentialsを例に説明します
詳細はOpenID Connectの章で説明しますが、本ワークフローではAWSと認証するためにトークンが必要で、そのトークンを使うためにpermissionを変更しているんだ、くらいの理解で大丈夫です

```yml
jobs:
  deploy:
    name: Upload to Amazon S3
    runs-on: ubuntu-latest
    # These permissions are needed to interact with GitHub's OIDC Token endpoint.
    permissions:
      id-token: write
      contents: read
    steps:
    - name: Checkout
      uses: actions/checkout@v6
    - name: Configure AWS credentials from Test account
      uses: aws-actions/configure-aws-credentials@v6
      with:
        role-to-assume: arn:aws:iam::111111111111:role/my-github-actions-role-test
        aws-region: us-east-1
    - name: Copy files to the test website with the AWS CLI
      run: |
        aws s3 sync . s3://my-s3-test-website-bucket
    - name: Configure AWS credentials from Production account
      uses: aws-actions/configure-aws-credentials@v6
      with:
        role-to-assume: arn:aws:iam::222222222222:role/my-github-actions-role-prod
        aws-region: us-west-2
    - name: Copy files to the production website with the AWS CLI
      run: |
        aws s3 sync . s3://my-s3-prod-website-bucket
```

yml内で以下のようにpermissionを使っています
```yml
    permissions:
      id-token: write
      contents: read
```

id-tokenはGitHub Actions内でOIDCを使う際に使用します

> 	Fetch an OpenID Connect (OIDC) token. This requires id-token: write. For more information, see "About security hardening with OpenID Connect"

先ほど説明した通り全てのスコープのデフォルトの権限はreadです
OIDCを取得するにはwrite権限を付与する必要があるので明記します
ここで一つ注意してほしいのが、先ほど
> ワークフロー内でスコープとその権限を一つ以上定義した場合、定義していない他のスコープの権限は全てnoneになります

と記載しました
ワークフロー内で`checkout`を使ってリポジトリ内のコードをfetchしています
id-tokenのpermissionをwriteにしてしまうとcheckoutを実行するのに必要なcontentsスコープがnoneになってしまい、fetchできなくなってしまうのでcontentsのpermissionをreadと明記する必要があります
permissionを書き換えるときは注意しましょう

### GitHub Pages
HTML、CSS、JSなどの静的ファイルを直接取得した後、任意でビルドプロセスを通じてファイルを実行し、ウェブサイトを公開できる静的なサイトホスティングサービスです
使用例として挙げられるのは

- Swagger
- StoryBook

のホスティングです

:::note warn
プライベートリポジトリでの使用はGitHub Pro、GitHub Team、GitHub Enterprise Cloud、GitHub Enterprise Serverで利用できます
:::

https://docs.github.com/ja/pages/getting-started-with-github-pages/about-github-pages

今回はSwaggerをGitHub Pagesへ公開するワークフローを作成します
まず、`Legion2/swagger-ui-action@v1`を使ってswagger-uiフォルダに静的ファイルとしてexportします
次に公式の`upload-pages-artifact`を使ってGitHub PagesへアップロードできるようArtifactを作成します
似たようなactionに`upload-artifact`もありますが
- Artifact名をgithub-pagesにする必要がある
- 単一のtarファイルを含む単一のgzipアーカイブにする必要がある

など手間がかかるので公式ではGitHub Pages用のArtifactを生成するのであれば`upload-pages-artifact`を使うよう推奨しています

> While choosing to use this action as part of your approach to deploying to GitHub Pages is technically optional, we highly recommend it since it takes care of producing (mostly) valid artifacts.
However, if you do not choose to use this action but still want to deploy to Pages using an Actions workflow, then you must upload an Actions　artifact that meets the following criteria:
・Be named github-pages
・Be a single gzip archive containing a single tar file

https://github.com/actions/upload-pages-artifact

最後に公式の`deploy-pages`を使って作成したArtifactをデプロイします

https://github.com/actions/deploy-pages

```yml
name: Deploy Swagger UI to GitHub Pages

on:
  push:
    branches:
      - develop

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout code
        uses: actions/checkout@v6
      - name: Install swagger-cli
        run: npm install -g swagger-cli
      - name: Generate Swagger UI
        uses: Legion2/swagger-ui-action@v1
        with:
          output: swagger-ui
          spec-file: doc/openapi.yml
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v3
        with:
          path: swagger-ui

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
        uses: actions/deploy-pages@v4

```

GitHub Pagesの設定は
Settings>Pages
で行うことができ、GitHub Actionsを選択します

:::note warn
2024年6月30日から全てのGitHub PagesではGitHub Actionsが使用されるので今後も使用する場合はGitHub Actionsを有効にする必要があります
:::

![スクリーンショット 2024-05-29 7.36.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/67cd9da1-eb2e-b38a-f054-906bd210636e.png)

ワークフローを実行すると以下のようにdeployの箇所にURLのリンクがあります
![スクリーンショット 2024-05-29 7.36.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/feb72f4d-ba3a-5cf3-fbeb-4823386f4bc3.png)

URLにアクセスすると以下のようにSwaggerが表示されます
ただし、静的ファイルをアップロードしてるだけなので実行することはできません

![スクリーンショット 2024-05-29 7.35.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79bfcbc7-f8e2-fd70-ab91-a6de81e43374.png)

リポジトリ内のDeploymentsからでも参照できます
![スクリーンショット 2024-05-29 7.42.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/171da3b3-22f4-25b5-a2ce-51dd63f9ae7c.png)

### Matrix
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


#### Matrixの設定方法
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

Matrixで定義したバージョンを適用させたい処理には以下のように記載します
例えばOSのバージョンを適用させたいときは以下のように記載します
```
${{ matrix.os }}
```

以下がワークフロー例です
```yaml:.github/workflows/test.yml
name: Run Pytest Using Matrix

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
      - name: Checkout code
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

各Jobが並列で実行され、成功すると以下のようになります
![スクリーンショット 2023-02-12 11.59.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3ddf1867-d07e-3fef-faed-51fb2ad32adc.png)

#### 特定のバージョンのみ追加したいとき
例えば
- Python 3.10.8
- Ubuntu 18.04

だけ追加で検証したいときは`include`を使用します
2つとも配列に入れてしまうと
- Python 3.10.8
- Ubuntu 20.04 と latest

など、実行しなくてもいいバージョンのJobまで実行されてしまいます
そのため、今回みたいなケースでは`include`を使用します

```yaml:.github/workflows/test.yml
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

のJobのみ追加されていることが確認できます

![スクリーンショット 2023-02-12 12.14.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b907a60e-d8b0-b54f-caf8-c372cd254076.png)

#### 特定のバージョンのみ除外したいとき
特定のバージョンのみ除外するときはincludeとは逆にexcludeを使用します
今回は
- Python 3.10.5
- Ubuntu 20.04

のJobのみ実行しないようにします

```yaml:.github/workflows/test.yml
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

が実行されていないことが確認できます

![スクリーンショット 2023-02-12 12.17.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/031b2b15-cd47-9b2a-8535-35971fbe9cc9.png)

### メタデータ構文
メタデータ構文を使うことで
- パッケージのインストール
- Cacheの設定

など、複数のワークフローで共通利用できるものを1つのファイルにまとめることができます
今回は一般的によく利用されている`composite　action`について解説します
`composite action`を使用するために共通化したい

- パッケージのインストール
- Cacheの設定

などの処理をaction.ymlに記載します

作成するファイルの構成は以下の通りです

```
tree
└──.github
     ├── actions
     │   └── set-up-node
     |       └── action.yml
     └── workflows
       ├── build.yml
       └── jest.yml
```

今回は今後別の処理を共通化したい時を想定してaction.ymlを`.github/actions/set-up-node/`内に格納します

```yml:.github/actions/set-up-node/action.yml
name: 'Setup Node.js'

description: 'Setup Node.js by using cache and npm'

inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: true

runs:
  # compositeが必須
  using: 'composite'
  steps:
      - name: Setup NodeJS
        uses: actions/setup-node@v6
        with:
          node-version-file: ${{ inputs.working-directory }}/package.json
      - name: Install dependencies
        run: npm ci
        shell: bash
        working-directory: ${{ inputs.working-directory }}
```

メタデータファイルを作成する場合は以下の構文が必須です

| 構文 | 説明 | 
| -------- | -------- | 
| name     | アクションの名前   | 
| description | アクションの簡単な説明 |
| runs | 共通化したい処理を記載 |
| using |  compositeに設定する必要があります |

#### action.yml内でrun句を使うとき
runを使用するときは使用するshellを必ず定義する必要があります

```yml
shell: bash
```

以下に使用できるshellが記載されていますが基本的にはbashで問題ないかと思います

https://docs.github.com/ja/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsshell

また、action.yml内で処理を行う際は参照先で
```yml
    defaults:
      run:
        working-directory: application
```

と定義したとしてもルートディレクトリで実行されてしまいます
そのため、action.yml内の処理にworking-directoryを使ってディレクトリを指定する必要があります

#### inputs
そこでinputsを使って参照先のyml側で実行するディレクトリを指定するようにすれば
action.yml内でハードコーディングしなくてもよくなります
今回は必須入力にしています

```yml:.github/actions/set-up-node/action.yml
inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: true
```

また、任意入力にする場合はrequiredの値をfalseにし、defaultを定義することでデフォルト値を設定することもできます
```yml
inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: false
    default: 'application'
```

#### 作成したaction.ymlの処理をワークフローで使おう！
- build.yml
- jest.yml

にaction.ymlの処理を参照するよう設定します
まずは、usesにaction.ymlのパスを指定します
パスを指定する際はaction.ymlまで記載しなくても大丈夫です
また、inputsを使用する際はwith内に値を指定します
working-directoryにapplicationを指定します

```yml
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
```

以上を踏まえると以下のようになります
```yml:.github/workflows/build.yml
# アクション名
name: Jest

# タイミングを指定
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application

jobs:
  test:
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
        uses: actions/checkout@v6
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Show coverage
        run: npm test -- --bail --maxWorkers=100% --watchAll=false --coverage
```

```yml:.github/workflows/build.yml
name: Build

on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application

jobs:
  build:
    name: Build
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Check out
        uses: actions/checkout@v6
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Run npm run build
        run: npm run build
```

### OpenID Connect
OpenID Connectを使用することでAWSの
- シークレットキー
- アクセスキー

を使わずにIAMロールを使ってよりセキュアにGitHub Actionsを実行できますので設定していきます

#### OpenID Connectとは
簡単にいうと認証を行うための仕組みです
OpenID Connectを使用することでAWSの
- シークレットキー
- アクセスキー

を使わずにIAMロールを使ってよりセキュアにGitHub Actionsを実行できます
GitHub Actions内でOpenID Connectを使うメリットは以下の通りです

- GitHub Secretsでアクセスキーとシークレットキーを管理する必要がないため、AWS関連の秘匿情報を管理するコストがなくなる
- IAMロールを使った運用になるため、ロールに応じた細かい権限別のワークフローを実行できる
- OpenID Connectを使う際に生成されるJWTトークンが1つのジョブに対してのみ有効であり、自動的に失効する有効期間が短いトークンを使用できるためセキュリティリスクが低い

#### OpenID Connectの仕組み
仕組みをざっと説明すると
- AWSなどのクラウドプロバイダにOpenID Connect(OIDC Trust)を設定
- GitHub Actionsのワークフロー内のjobを実行するたびにGitHubがJWTトークンを生成し、クラウドプロバイダへ渡す
- クラウドプロバイダが受け取ったJWTトークンを使って認証が成功したらGitHubのOpenID Connectのプロバイダがクラウドプロバイダからアクセストークンを受け取る
- 受け取ったアクセストークンを使用してaws cliコマンドをIAMロールを使って実行する

という流れになっています

詳細は以下の公式ドキュメントを参照してください

https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

#### Next.jsのアプリケーションをS3へデプロイするには
今回はNext.jsのアプリケーションをS3へデプロイするワークフローを作成するので

- 静的ファイルをデプロイするS3バケット
- デプロイを実行するIAMロール

の作成が完了した状態でワークフローを作成します
OpenID Connectを使用する際はAWSが出している公式のActionを使用します

https://github.com/aws-actions/configure-aws-credentials

```yaml:.github/workflows/deploy-frontend.yml
name: Deploy Frontend Project to S3

on:
  push:
    branches:
      - main

env:
  REGION_NAME: ap-northeast-1
  WORKING_DIRECTORY: frontend

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Checkout
        uses: actions/checkout@v6
      - name: configure aws credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ secrets.S3_DEPLOY_ROLE }}
          role-session-name: deploy_role_session
          aws-region: ${{ env.REGION_NAME }}
      - name: Setup Node.js
        uses: actions/setup-node@v6
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
      - name: Build and Export
        run: npm run build
      - name: Deploy To S3 Bucket
        run: aws s3 sync --region ${{ env.REGION_NAME }} ./out s3://${{ secrets.BUCKET_NAME }} --delete

```

S3バケット、IAMロール、OpenID Connectの作成および設定方法は以下の記事を参照してください

https://qiita.com/shun198/items/a7ae37e0da3eba2c4387

## まとめ
初めてGitHub Actionsを触った時はどれが何をしているかさっぱりわからなかったのですが仕組みや書き方をある程度理解していればそこまで難しくなく、むしろやっていて楽しいなと個人的に思いました

## 参考
https://docs.github.com/ja/actions/using-workflows/workflow-syntax-for-github-actions

https://docs.github.com/en/actions/using-github-hosted-runners/about-github-hosted-runners

https://docs.github.com/en/actions

https://blog1.mammb.com/entry/2021/12/11/090000

https://dev.classmethod.jp/articles/latest-current-using-actions/

https://docs.github.com/ja/actions/using-github-hosted-runners/about-github-hosted-runners

https://qiita.com/suzuki0430/items/951ed9753c04743537cc

https://github.com/actions/checkout

https://dev.classmethod.jp/articles/how-to-checkout-remote-branch/

https://dev.classmethod.jp/articles/set-secrets-before-actions-test/
