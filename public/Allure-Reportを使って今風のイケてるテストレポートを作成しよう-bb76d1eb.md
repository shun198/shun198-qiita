---
title: Allure Reportを使って今風のイケてるテストレポートを作成しよう!
tags:
  - Makefile
  - Docker
  - docker-compose
  - GitHubActions
  - Allure
private: false
updated_at: '2024-05-29T13:48:57+09:00'
id: bb76d1eb98bb7290a6a8
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Allure Reportをローカル上で使用する方法について解説します
また、記事の後半では自動生成したレポートをGitHub Pagesへデプロイする方法についても記載しています

## 前提
- 本記事ではDockerとdocker-composeを使用します
- WebフレームワークはDjango、テスト用フレームワークはPytestを使用

## Allureとは？
公式ドキュメントにも記載している通りテストレポートを自動生成するツールです

> Allure Framework is a flexible lightweight multi-language test report tool

- PythonのPytest
- RailsのRSpec
- JavaのjUnit
- PHPのPHPUnit
- KotlinのKotest
- JavaScriptのJasmine

にも対応しています
今あげたテストフレームワーク以外にも対応しているので詳細は公式ドキュメントを参照してください

https://docs.qameta.io/allure/


今回私はPytestでいくつかテストコードを作成してますが
- テスト数
- カバレージ
- 所要時間

などさまざまな情報を表示できます

![スクリーンショット 2023-01-14 22.23.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6eee7ffd-7323-8a51-d625-1ab7f60532df.png)

しかも日本語にも対応しているのでありがたいです
記事の後半でレポートの内容を詳細に説明をしたいと思います

## allure-docker-serviceとallure-docker-service-ui
ローカルで実行している記事が多いですが私はローカル環境を汚したくないので今回はDockerを使います
- allure-docker-service
- allure-docker-service-ui

の2つのDocker Imageを使用します

https://github.com/fescobar/allure-docker-service

https://github.com/fescobar/allure-docker-service-ui

docker-compose.ymlに以下を記載します

```docker-compose.yml
services:
  allure:
    container_name: allure
    image: "frankescobar/allure-docker-service"
    environment:
      # 毎秒テスト結果を確認するかどうかの設定です
      # マシンへの負担が大きいとのことなので今回はNONEにします
      CHECK_RESULTS_EVERY_SECONDS: NONE
      # テストの履歴を保存したいのでKEEP_HISTORYを有効化(TRUE)にします
      KEEP_HISTORY: 1
      # 直近25回分までを保存します
      KEEP_HISTORY_LATEST: 25
    ports:
      - "5050:5050"
    volumes:
      - ${PWD}/allure-results:/app/allure-results
      - ${PWD}/allure-reports:/app/default-reports

  allure-ui:
    container_name: allure-ui
    image: "frankescobar/allure-docker-service-ui"
    environment:
      ALLURE_DOCKER_PUBLIC_API_URL: "http://localhost:5050"
      ALLURE_DOCKER_PUBLIC_API_URL_PREFIX: ""
    ports:
      - "5252:5252"
```

公式ドキュメントに記載されている通りvolumesのディレクトリを変更してしまうとコンテナ側でテスト結果の保存や反映ができなくなってしまいます
今回は`container_name`だけ変更してポートも含めて公式に書いてある通りの構成にします

>The /app/allure-results directory is inside of the container. You MUST NOT change this directory, otherwise, the container won't detect the new changes.
The /app/default-reports directory is inside of the container. You MUST NOT change this directory, otherwise, the history reports won't be stored.

docker-compose.ymlを作成後、
```
docker compose up -d
```
を実行します
すると、プロジェクトのルートディレクトリに以下のフォルダが作成されます

```
❯ tree
.
├── allure-reports
└── allure-results
```

- allure
- allure-ui

のコンテナが起動できていることも確認できました
```
docker ps -a
3b88c08ffc9e   frankescobar/allure-docker-service      "/bin/sh -c '$ROOT/r…"   2 minutes ago   Up 2 minutes (healthy)   4040/tcp, 0.0.0.0:5050->5050/tcp                 allure
becb4e3f0b5d   frankescobar/allure-docker-service-ui   "docker-entrypoint.s…"   2 minutes ago   Up 2 minutes (healthy)   0.0.0.0:5252->5252/tcp                           allure-ui
```

## テストレポートを作成しよう！
テストレポートを作成する際は以下の順で行います
- プロジェクトの作成
- テストを実行し、テスト結果をJSONで出力
- JSONファイルをallureコンテナへアップロード
- レポートの作成

手順は多いですが順番にやっていきましょう

### プロジェクトの作成
http://127.0.0.1:5050　 にアクセスすると以下の画面が表示されます

![スクリーンショット 2023-01-14 21.38.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/702433c1-39d5-ba4e-f28d-6661c440c3c5.png)

Allure Reportを使用する際はプロジェクトごとにproject-idを設定します
`/projects`に任意のidを入力し、POSTリクエストを送ります
今回は`test-proj`というidで作成し、Executeを押します

![スクリーンショット 2023-01-14 21.41.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5eb40d4a-4f3c-3359-74f9-8790bda753ab.png)

以下の画面が表示されたら成功です

![スクリーンショット 2023-01-14 21.42.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d831ef12-1bce-c65f-2015-c8b9a12aaabd.png)

### テストを実行し、テスト結果をJSONで出力
任意のテストフレームワークを使ってテストを実行し、実行したテストの結果をJSONに出力する必要があります
その際は

各テストフレームワークでのやり方は以下の公式ドキュメントを参照してください

https://docs.qameta.io/allure/

今回私はPytestを使用するのでallure-pytestをインストールします

https://pypi.org/project/allure-pytest/

```
pip install allure-pytest
```

その後、以下のコマンドを使用します
```
pytest --alluredir=allure-results 
```

テストが実行されると`allure-results`フォルダ内にJSONファイルが作成されます

### JSONファイルをallureコンテナへアップロード
先ほどJSONファイルをもとにテストレポートを作成しました
しかし、現状ではローカル上にはあるもののallureコンテナ(サーバ)内にありません
そのため、ローカル上のJSONファイルをallureコンテナへアップロードする必要があります
公式ではアップロード用のシェルスクリプトを用意しています
allure-reportsやallure-resultsと同じプロジェクトのルートディレクトリにシェルスクリプトを作成し、実行します

```
❯ tree
.
├── allure-reports
├── allure-results
└── send_results.sh
```

PROJECT_IDの箇所に自身が作成されたプロジェクトidを入れます
今回私は`test-proj`を入れます
```send_results.sh
#!/bin/bash

# This directory is where you have all your results locally, generally named as `allure-results`
ALLURE_RESULTS_DIRECTORY='allure-results'
# This url is where the Allure container is deployed. We are using localhost as example
ALLURE_SERVER='http://localhost:5050'
# Project ID according to existent projects in your Allure container - Check endpoint for project creation >> `[POST]/projects`
PROJECT_ID='test-proj'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FILES_TO_SEND=$(ls -dp $DIR/$ALLURE_RESULTS_DIRECTORY/* | grep -v /$)
if [ -z "$FILES_TO_SEND" ]; then
  exit 1
fi

FILES=''
for FILE in $FILES_TO_SEND; do
  FILES+="-F files[]=@$FILE "
done

set -o xtrace
echo "------------------SEND-RESULTS------------------"
curl -X POST "$ALLURE_SERVER/allure-docker-service/send-results?project_id=$PROJECT_ID" -H 'Content-Type: multipart/form-data' $FILES -ik


#If you want to generate reports on demand use the endpoint `GET /generate-report` and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
#echo "------------------GENERATE-REPORT------------------"
#EXECUTION_NAME='execution_from_my_bash_script'
#EXECUTION_FROM='http://google.com'
#EXECUTION_TYPE='bamboo'

#You can try with a simple curl
#RESPONSE=$(curl -X GET "$ALLURE_SERVER/allure-docker-service/generate-report?project_id=$PROJECT_ID&execution_name=$EXECUTION_NAME&execution_from=$EXECUTION_FROM&execution_type=$EXECUTION_TYPE" $FILES)
#ALLURE_REPORT=$(grep -o '"report_url":"[^"]*' <<< "$RESPONSE" | grep -o '[^"]*$')

#OR You can use JQ to extract json values -> https://stedolan.github.io/jq/download/
#ALLURE_REPORT=$(echo $RESPONSE | jq '.data.report_url')
```

シェルスクリプトを作成したら実行します
```
sh send_results.sh
```

JSONのレスポンスが帰ってくるので以下のようなメッセージが含まれていたら成功です
```
"meta_data":{"message":"Results successfully sent for project_id 'test-proj'"}
```

### レポートの作成
ここでいよいよテストレポートを作成します

![スクリーンショット 2023-01-14 21.56.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a7ef96b5-8c31-a475-8666-372d16e58a56.png)

少し時間がかかるので待ちます

以下のようなレスポンスが帰ってきたら成功です
![スクリーンショット 2023-01-14 21.57.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8e8b6b38-769e-f1a7-a2c4-d2fedf6f0ed4.png)

## テストレポートを見てみよう!
/projects/{id}
へGETリクエストを送ります
idにプロジェクトidを指定し、Executeを押します

![スクリーンショット 2023-01-14 22.01.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3f6cbb22-8ac1-ec49-870c-2dc8d9fba491.png)

レスポンス内にindex.htmlのパスがあります
今回は最新のものが見たいので
http://127.0.0.1:5050/allure-docker-service/projects/test-proj/reports/latest/index.html
を選択します
![スクリーンショット 2023-01-14 22.01.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d2751427-a8af-25a4-f320-d81d4a0d5231.png)

以下の画面が表示されたら成功です
![スクリーンショット 2023-01-14 22.23.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0a86d1bf-d9c6-fe9d-8e6b-08ddbac62fc5.png)

### スイート
テストをステータス別で分類できます
分類の種類は以下の通りです
|色|分類|
|---|---|
|赤|失敗|
|黄色|故障|
|緑|成功|
|グレー|スキップ|
|紫|不明|

![スクリーンショット 2023-01-14 22.24.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/04ac759c-ffea-02d2-16b1-fd143f0eeb00.png)

また、ステータスの真上に結果をCSVファイルに出力するボタンがあります

![スクリーンショット 2023-01-14 22.26.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/57898e94-6ae0-cb37-58fe-6d462b907ce9.png)

### グラフ
テストの分類や速度をグラフで表示することができます

![スクリーンショット 2023-01-14 22.17.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0b93282b-7226-85df-cb27-04f7011d73d6.png)

### タイムライン
どの順番で、どのテストが、どれくらい時間がかかったかを表示することができます

![スクリーンショット 2023-01-14 22.30.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/673db5f3-9911-594c-46c6-8e27b14894df.png)

### 振る舞い
各テストの詳細を閲覧できます
テストのdocstring、異常テストのログも確認できます

![スクリーンショット 2023-01-14 22.28.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/eee50717-21f6-9f8d-59c5-6f4bedd25667.png)

また、セットアップ作業なども確認できます
![スクリーンショット 2023-01-14 22.32.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24b240b2-c6ab-3e93-791b-2431fd5ccca2.png)

Allure Reportの使い方は以上です

## Makefileを作成してコマンド一つでテストレボートの作成から表示まで行おう！
手順が多いうえにコマンドが長いので覚えられないです
そこでMakefileを使って楽にテストレポートを作成しましょう
ルートディレクトリにMakefileを作成し、以下のように記載します

```makefile:Makefile
CONTAINER_NAME = app
PROJECT = test-proj
RUN_APP = docker compose exec $(CONTAINER_NAME)
RUN_POETRY =  $(RUN_APP) poetry run
RUN_PYTEST = $(RUN_POETRY) pytest

make_report:
	-@ $(RUN_PYTEST) --alluredir=allure-results
	sh send_results.sh
	echo "Generating test report. This may take a while..."
	curl -X GET "http://127.0.0.1:5050/allure-docker-service/generate-report?project_id=$(PROJECT)" -H  "accept: */*"
	echo "Successfully generated test report. Redirecting to allure server."
	open http://127.0.0.1:5050/allure-docker-service/projects/$(PROJECT)/reports/latest/index.html

show_report:
	open http://127.0.0.1:5050/allure-docker-service/projects/$(PROJECT)/reports/latest/index.html
```

-@をつけることでテストが失敗しても処理を続行させます

```
make make_report
```
と打つと
http://127.0.0.1:5050/allure-docker-service/projects/test-proj/reports/latest/index.html
に遷移します

![スクリーンショット 2023-01-15 13.04.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f7088831-55e7-b952-af03-bfb58f594b50.png)

コマンド1つでレポートが表示される上にエラーが出た箇所が分かりやすく表示されていい感じですね！
![スクリーンショット 2023-01-15 13.05.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a047505-1d39-29d6-bd02-b1caefaf49a0.png)

今回はレポートは生成しなくていいから見るたけでいいよ！と思ったら以下のコマンドを実行します
```
make show_report
```

## Allure Docker Service UI
http://127.0.0.1:5252/
にアクセスするとAllure Docker Service UIを開くこともできます
該当するプロジェクトを開くとこちらもAllure Reportと同様の使い方ができます

![スクリーンショット 2023-01-14 22.33.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3fff9cab-b679-aa48-77dc-6a1a2f127807.png)

![スクリーンショット 2023-01-14 22.35.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9903f9d5-e98b-0500-4638-1df76af5ce35.png)

## 413エラーが出た場合は？
send_results.shを使ってレポートを作成する場合、量が多すぎると413エラーを出力してしまいます

https://github.com/fescobar/allure-docker-service/issues/247

先ほどのシェルスクリプトを確認すると1回のリクエストで一気にレポートを作成してしまっています
```sh
FILES=''
for FILE in $FILES_TO_SEND; do
  FILES+="-F files[]=@$FILE "
done

set -o xtrace
echo "------------------SEND-RESULTS------------------"
curl -X POST "$ALLURE_SERVER/allure-docker-service/send-results?project_id=$PROJECT_ID" -H 'Content-Type: multipart/form-data' $FILES -ik
```

そのため、下記のように小分けにAPIへリクエストを送るようにすれば解決します

```send_results.sh
#!/bin/bash

# This directory is where you have all your results locally, generally named as `allure-results`
ALLURE_RESULTS_DIRECTORY='allure-results'
# This url is where the Allure container is deployed. We are using localhost as example
ALLURE_SERVER='http://localhost:5050'
# Project ID according to existent projects in your Allure container - Check endpoint for project creation >> `[POST]/projects`
PROJECT_ID='test-proj'

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
FILES_TO_SEND=$(ls -dp $DIR/$ALLURE_RESULTS_DIRECTORY/* | grep -v /$)

if [ -z "$FILES_TO_SEND" ]; then
  exit 1
fi

FILES=''
COUNT=0
for FILE in $FILES_TO_SEND; do
  FILES+="-F files[]=@$FILE "
  COUNT+=1
  if [ $COUNT -gt 99 ]; then
    set -x
    echo "------------------SEND-RESULTS------------------"
    curl -X POST "$ALLURE_SERVER/allure-docker-service/send-results?project_id=$PROJECT_ID" -H 'Content-Type: multipart/form-data' $FILES -ik
    set +x
    FILES=''
    COUNT=0
  fi
done

#set -o xtrace
#echo "------------------SEND-RESULTS------------------"
#curl -X POST "$ALLURE_SERVER/allure-docker-service/send-results?project_id=$PROJECT_ID" -H 'Content-Type: multipart/form-data' $FILES -ik


#If you want to generate reports on demand use the endpoint `GET /generate-report` and disable the Automatic Execution >> `CHECK_RESULTS_EVERY_SECONDS: NONE`
#echo "------------------GENERATE-REPORT------------------"
#EXECUTION_NAME='execution_from_my_bash_script'
#EXECUTION_FROM='http://google.com'
#EXECUTION_TYPE='bamboo'

#You can try with a simple curl
#RESPONSE=$(curl -X GET "$ALLURE_SERVER/allure-docker-service/generate-report?project_id=$PROJECT_ID&execution_name=$EXECUTION_NAME&execution_from=$EXECUTION_FROM&execution_type=$EXECUTION_TYPE" $FILES)
#ALLURE_REPORT=$(grep -o '"report_url":"[^"]*' <<< "$RESPONSE" | grep -o '[^"]*$')

#OR You can use JQ to extract json values -> https://stedolan.github.io/jq/download/
#ALLURE_REPORT=$(echo $RESPONSE | jq '.data.report_url')
```

## GitHub PagesへAllure Reportをデプロイするには
GitHub Pagesへアップロードするとローカル上で環境構築できないステークホルダーやPMもテストレポートを閲覧しやすくなるので便利です

今回は
- テストを実行し、レポートを生成するワークフロー
- 生成したレポートをGitHub Pagesへアップロードするワークフロー

の2種類を作成します
使用する流れとしては以下の通りです
- PRを作成し、テストを実行し、レポートを生成
- PRをdevelopへmerge後、レポートをGitHub Pagesへアップロード

### テストを実行し、レポートを生成するワークフローの作成
DjangoのプロジェクトでPytestを実行するワークフローを例に出します
Pytestを実行する際に`--alluredir=allure-results`のオプションを付与します
テスト実行後、以下のActionを使って`allure-history`配下にレポートを生成します

https://github.com/simple-elf/allure-report-action

その後、公式の`upload-pages-artifact`のActionを使ってレポートをArtifactにアップロードします

```test.yml
name: Run Pytest
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings
  ALLOWED_HOSTS: 127.0.0.1
  POSTGRES_NAME: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_HOST: 127.0.0.1
  POSTGRES_PORT: 5432

jobs:
  Setup:
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    name: Run Test Code
    runs-on: ubuntu-22.04
    services:
      db:
        image: postgres:16.2
        ports:
          - 5432:5432
        env:
          POSTGRES_NAME: ${{ env.POSTGRES_NAME }}
          POSTGRES_USER: ${{ env.POSTGRES_USER }}
          POSTGRES_PASSWORD: ${{ env.POSTGRES_PASSWORD }}
        options: >-
          --health-cmd "pg_isready"
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    steps:
      - name: Chekcout code
        uses: actions/checkout@v6
      - name: Install poetry
        run: pipx install poetry
      - name: Use cache dependencies
        uses: actions/setup-python@v6
        with:
          python-version-file: pyproject.toml
          cache: 'poetry'
      - name: Install Packages
        run: poetry install
      - name: Run migration
        run: |
          poetry run python manage.py makemigrations
          poetry run python manage.py migrate
      - name: Run Pytest
        run: poetry run pytest --alluredir=allure-results
      - name: Build test report
        uses: simple-elf/allure-report-action@v1.7
        with:
          allure_results: allure-results
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v3
        with:
          # 絶対パスを指定
          path: allure-history

```

### 生成したレポートをGitHub Pagesへアップロードするワークフローの作成
`dawidd6/action-download-artifact@v3`を使用し、test.ymlで生成したArtifactをダウンロードします

https://github.com/dawidd6/action-download-artifact

公式の`download-artifact`を使用しないのは異なるワークフロー間のArtifactの受け渡しをサポートしてないからです

> Let's suppose you have a workflow with a job in it that at the end uploads an artifact using actions/upload-artifact action and you want to download this artifact in another workflow that is run after the first one. Official actions/download-artifact does not allow this. That's why I decided to create this action. By knowing only the workflow name and commit SHA or other details, you can download the previously uploaded artifact from different workflow associated with that commit or other criteria and use it.

`dawidd6/action-download-artifact@v3`を使って`artifact.tar`ファイルをダウンロードした後、deploy-to-github-pages.yml内に`artifact.tar`ファイルをArtifactとしてアップロードします
その後、公式の`deploy-pages`を使用してGitHub Pagesへデプロイします

```deploy-to-github-pages.yml
name: Upload Allure Report to GitHub Pages

on:
  push:
    branches:
      - develop

jobs:
  deploy:
    name: Upload To GitHub Pages
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - name: Download Artifact
        uses: dawidd6/action-download-artifact@v3
        with:
          name: github-pages
          workflow: test.yml
      - name: Upload Artifact
        uses: actions/upload-artifact@v4
        with:
          name: github-pages
          path: artifact.tar
      - id: deployment
        uses: actions/deploy-pages@v4

```

### GitHub Pagesの設定
GitHub Pagesを有効化します
Settings>PagesからSourceをGitHub Actionsにします

![スクリーンショット 2024-05-28 17.35.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/de9452a3-9292-7dbf-4c9f-13def723043d.png)

### 実際に実行してみよう！
PRを作成し、以下のようにテストが実行され、Artifactが作成されたら成功です
![スクリーンショット 2024-05-28 17.36.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d0a56bd5-3e99-577d-8394-318165bcfb67.png)

![スクリーンショット 2024-05-28 17.37.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/08e73a17-2a18-d8e8-2330-9e501e145208.png)

PRをmergeした後、以下のようにワークフローが正常終了し、GitHub Pagesへアップロードされたら成功です
![スクリーンショット 2024-05-28 17.37.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2e838ab0-30fa-b3ba-0a5b-024d61bd9d0f.png)

![スクリーンショット 2024-05-28 17.19.34.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/91545ab9-d430-8179-ebb5-7f7a75180843.png)

![スクリーンショット 2024-05-28 17.19.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/38cadffd-7cb9-f3dc-4dad-2fb1b585b33e.png)

### Resource not accessible by integrationと表示されてしまった場合は
権限が足りてないので以下のように変更してみてください
```yaml
    permissions:
      pages: write
      id-token: write
    　　　　pull-requests: write
    　　　　actions: read
```

https://github.com/dawidd6/action-download-artifact/issues/222

## まとめ
最初は設定が多いのとREADMEの内容を読むのに時間がかかって大変でした
やり方さえわかれば簡単にいい感じのテストレポートを作成できることがわかったので大満足です

## 記事の紹介
以下の記事も作成してみたのでよかったら読んでいただけると幸いです

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/2ce000b5b9f1818a16d5

https://qiita.com/shun198/items/35c97c95079ecbe80e9d

https://qiita.com/shun198/items/318847d7e0be59108f22

## 参考
https://note.com/shift_tech/n/naec43294ebd0

https://github.com/fescobar/allure-docker-service

https://pypi.org/project/allure-pytest/

https://docs.qameta.io/allure/

https://allurereport.org/docs/integrations-github-action/

https://github.com/actions/deploy-pages

