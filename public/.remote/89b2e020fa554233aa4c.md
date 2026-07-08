---
title: 【Python】GitHub ActionsとOpenID Connectを使ってLambdaを自動デプロイしよう！
tags:
  - Python
  - AWS
  - lambda
  - openidconnect
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: 89b2e020fa554233aa4c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsを使ってPythonの必要なパッケージとソースコードをzipファイルに圧縮してLambdaに自動デプロイする方法について解説します
また、今回はOpenID Connectを使ってデプロイするのでIAMロールの設定等についても解説します

## 前提
- 言語・パッケージはPythonを使用
- Pythonのパッケージ管理にPoetryを使用
- GitHub ActionsおよびLambdaに関する基本的な知識を有していること

## ディレクトリ構成
ファイル構成は以下のとおりです
```
❯ tree
.
├── .github
│   └── workflows
│       └── lambda-deploy.yml
└── application
    ├── lambda_function.py
    ├── poetry.lock
    └── pyproject.toml
```

## OpenID Connect
OpenID Connectを使用することでAWSの
- シークレットキー
- アクセスキー

を使わずにIAMロールを使ってよりセキュアにGitHub Actionsを実行できますので設定していきます

### OpenID Connectとは
簡単にいうと認証を行うための仕組みです
GitHub Actions内でOpenID Connectを使うメリットは以下の通りです

- GitHub Secretsでアクセスキーとシークレットキーを管理する必要がないため、AWS関連の秘匿情報を管理するコストがなくなる
- IAMロールを使った運用になるため、ロールに応じた細かい権限別のワークフローを実行できる
- OpenID Connectを使う際に生成されるJWTトークンが1つのジョブに対してのみ有効であり、自動的に失効する有効期間が短いトークンを使用できるためセキュリティリスクが低い

### OpenID Connectの仕組み
仕組みをざっと説明すると
- AWSなどのクラウドプロバイダにOpenID Connect(OIDC Trust)を設定
- GitHub Actionsのワークフロー内のjobを実行するたびにGitHubがJWTトークンを生成し、クラウドプロバイダへ渡す
- クラウドプロバイダが受け取ったJWTトークンを使って認証が成功したらGitHubのOpenID Connectのプロバイダがクラウドプロバイダからアクセストークンを受け取る
- 受け取ったアクセストークンを使用してaws cliコマンドをIAMロールを使って実行する

という流れになっています

詳細は以下の公式ドキュメントを参照してください

https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

### OpenID Connectの設定
AWS上でOpenID Connectの設定をしていきます
IAMのID プロバイダを開き、プロバイダの追加を押します
![スクリーンショット 2023-07-13 6.41.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/244ee90f-c15d-b03a-5d16-a2e3df87e81d.png)

OpenID Connectを選択し、画像のとおり
- プロバイダのURL:　https://token.actions.githubusercontent.com
- 対象者：　sts.amazonaws.com

を入力します

![スクリーンショット 2023-07-13 6.43.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ccee9dc6-6b8d-e168-4e77-c56c5054b7af.png)

以下のようにプロバイダが作成されたら成功です
![スクリーンショット 2023-07-13 7.05.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3171e724-4839-dad4-6a02-f886f2e9aafc.png)

## IAMロールの作成と割り当て
GitHub Actionsを使ってLambdaをデプロイできるIAMロールを作成していきます
IAMロールを作成する際に
- Lambda用のIAMポリシー
- OpenID Connect用の信頼されたエンティティ

の設定を行います
今回は以下の通りに設定します
|AWSリソース|Action|説明|指定のリソース|
|---|---|---|---|
|Lambda|CreateFunction|Lambdaの作成|lambda-deploy-demo関数|
|Lambda|UpdateFunction|Lambdaの更新|lambda-deploy-demo関数
|Lambda|GetFunction|Lambdaの更新|lambda-deploy-demo関数|
|CloudWatchLogs|CreateLogGroup|新しいロググループの作成|CloudWatch内にロググループを作成|
|CloudWatchLogs|CreateLogStream|新しいログストリームの作成|CloudWatch内の/aws/lambda/lambda-deploy-demo配下|
|CloudWatchLogs|PutLogEvents|ログを指定したログストリームへアップロード|CloudWatch内の/aws/lambda/lambda-deploy-demo配下|
|IAM|PassRole|指定のAWSリソース(今回だとLambda)にロールを渡す|lambda-deploy-demoのロール|

```json
{
	"Version": "2012-10-17",
	"Statement": [
		{
			"Effect": "Allow",
			"Action": [
				"lambda:CreateFunction",
				"lambda:UpdateFunctionCode",
				"lambda:GetFunction"
			],
			"Resource": [
				"arn:aws:lambda:ap-northeast-1:XXXXXXXXXXXX:function:lambda-deploy-demo"
			]
		},
        {
            "Effect": "Allow",
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:ap-northeast-1:XXXXXXXXXXXX:*"
        },
		{
			"Effect": "Allow",
			"Action": [
				"logs:CreateLogStream",
				"logs:PutLogEvents"
			],
			"Resource": [
				"arn:aws:logs:ap-northeast-1:XXXXXXXXXXXX:log-group:/aws/lambda/lambda-deploy-demo:*"
			]
		},
		{
			"Effect": "Allow",
			"Action": [
				"iam:PassRole"
			],
			"Resource": [
				"arn:aws:iam::XXXXXXXXXXXX:role/lambda-deploy-demo"
			]
		}		
	]
}
```

ロールに付与するエンティティの設定
Principal内のFederatedに作成したOpenID ConnectのプロバイダのARNを記載します
Condition内のStringLikeにロールを使用するリポジトリを記載します
今回はmainブランチでのみ実行したいので
```
{GitHubのリポジトリ名}:ref:refs/heads/main
```
と指定していますが全てのブランチで実行したいのであれば
```
{GitHubのリポジトリ名}:*
```
という風にワイルドカードを設定します

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::XXXXXXXXXXXX:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                },
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:shun198/github-actions-playground:*"
                }
            }
        },
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "lambda.amazonaws.com"
            },
            "Action": "sts:AssumeRole"
        }
    ]
}
```

## GitHub Actionsのワークフローの作成
- Lambda
- IAM

関連の設定が終わったのでワークフローを作成していきます

```.github/workflows/lambda-deploy.yml
name: lambda-deploy

on:
  push:
    branches:
      - main

env:
  REGION_NAME: ap-northeast-1
  FUNCTION_NAME: lambda-deploy-demo
  LAMBDA_WORKING_DIRECTORY: application
  LAMBDA_EXECUTION_ROLE: arn:aws:iam::XXXXXXXXXXXX:role/lambda-deploy-demo

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write # This is required for requesting the JWT
      contents: read # This is required for actions/checkout
    defaults:
      run:
        working-directory: ${{ env.LAMBDA_WORKING_DIRECTORY }}
    steps:
      - name: Checkout repository
        uses: actions/checkout@v6
      # Poetryのインストール
      - name: Install poetry
        run: pipx install poetry
      # Python3.11を使用したいので設定
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      - name: Configure aws credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ env.LAMBDA_EXECUTION_ROLE }}
          role-session-name: samplerolesession
          aws-region: ${{ env.REGION_NAME }}
      - name: Create Zip File
        run: |
          poetry install
          poetry export -f requirements.txt --without-hashes -o requirements.txt
          pip install --upgrade pip && pip install -r requirements.txt --target .
          rm pyproject.toml poetry.lock requirements.txt
          zip -r lambda.zip .
      # Lambdaが存在するか確認する
      - name: Check Function if Exists
        id: check-function
        continue-on-error: true
        run: |
          aws lambda get-function --function-name ${{ env.FUNCTION_NAME }}
      # Lambdaが存在しない場合は新規作成し、デプロイする
      - name: Create and Deploy Lambda Function
        if: steps.check-function.outcome == 'failure'
        run: |
          aws lambda create-function \
          --function-name ${{ env.FUNCTION_NAME }} \
          --runtime python3.11 \
          --handler lambda_function.lambda_handler \
          --zip-file fileb://lambda.zip \
          --timeout 60 \
          --role ${{ env.LAMBDA_EXECUTION_ROLE }}
      - name: Deploy Lambda Function
        if: steps.check-function.outcome == 'success'
        run: |
          aws lambda update-function-code \
          --function-name ${{ env.FUNCTION_NAME }} \
          --zip-file fileb://lambda.zip
```

### 権限の設定
JWTトークンを使って認証を行いますがGitHub Actionsのid-tokenのデフォルトのpermissionがNoneなのでid-tokenのpermissionsはwriteに変更します
また、GitHub Actionsの仕様上、1つのpermissionsを変更するとその他のpermissionがNoneになってしまうので、checkoutを実行できるよう追加でcontentsのpermissionsをreadに変更します

```yml
    permissions:
      id-token: write # This is required for requesting the JWT
      contents: read # This is required for actions/checkout
```

### Pythonのセットアップ
今回はPythonで作成したLambda関数をデプロイするのでPythonの設定をGitHub Actions内で行います

```yml
      # Poetryのインストール
      - name: Install poetry
        run: pipx install poetry
      # Python3.11を使用したいので設定
      - name: Setup Python
        uses: actions/setup-python@v6
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
```

### OpenID Connectの設定
OpenID Connectを使用する際はAWSが出している公式のActionを使用します

https://github.com/aws-actions/configure-aws-credentials

role-to-assumeに自身で作成されたIAM Roleを記載します
今回は東京リージョンを使用するのでaws-regionはap-northeast-1に設定します
デフォルトのrole-session-nameはGitHubActionsですが、任意の名前に設定しても大丈夫です
また、ワークフロー内で複数回`aws-actions/configure-aws-credentials@v6`を使用する際は一意の名前にする必要があります

```yml
      - name: Configure aws credentials
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ env.LAMBDA_EXECUTION_ROLE }}
          role-session-name: samplerolesession
          aws-region: ${{ env.REGION_NAME }}
```

### Zipファイルの作成
必要な外部パッケージをrequirementx.txtに出力し、requirements.txt内のパッケージをインストールします
LambdaにアップロードするZipファイル内で不要になるファイルを削除した後に指定した名前のZipファイルに圧縮します

```yml
      - name: Create Zip File
        run: |
          poetry install
          poetry export -f requirements.txt --without-hashes -o requirements.txt
          pip install --upgrade pip && pip install -r requirements.txt --target .
          rm pyproject.toml poetry.lock requirements.txt
          zip -r lambda.zip .
```

### 指定したLambdaが存在するか確認
まず、idを付与してLambdaを
- 新規作成
- 更新

するか判断する際に使用します
aws cliを使ってLambdaの関数名を検索し、あれば更新しなければ新規作成します
該当する関数名がない場合はexit code 254を返すので
```
continue-on-error: true
```
を設定し、ワークフローを続行させます

```yml
      # Lambdaが存在するか確認する
      - name: Check Function if Exists
        id: check-function
        continue-on-error: true
        run: |
          aws lambda get-function --function-name ${{ env.FUNCTION_NAME }}
```

### 指定したLambdaが存在しない場合は新規作成してデプロイする
前述のget_functionの結果で該当するLambdaが存在しないことを確認したらaws cliで新規作成してデプロイします
必要になるオプションは以下の通りです

|オプション名|説明|
|--|--|
|--function-name|関数名|
|--runtime|関数のランタイム(実行する言語)今回はPythonを指定<br>Zipファイルを使ってアップロードする際に必須になります|
|--handler|Lambda関数を実行する際に使用しているメソッド名<br>Zipファイルを使ってアップロードする際に必須になります<br>今回はlambda_function.lambda_handlerを指定します|
|--zip-file|Zipファイル<br>fileb://の後ろにZipファイルの名前を指定します|
|--timeout|Lambdaが実行できる時間(デフォルトが3秒なのでそれ以上かかる場合は指定する必要がある)|
|--role|実行するロールのarn<br>OpenID Connectを使用していても発行したJWT Tokenを使ってないと思われるので必要です|

```yml
      - name: Create and Deploy Lambda Function
        if: steps.check-function.outcome == 'failure'
        run: |
          aws lambda create-function \
          --function-name ${{ env.FUNCTION_NAME }} \
          --runtime python3.11 \
          --handler lambda_function.lambda_handler \
          --zip-file fileb://lambda.zip \
          --timeout 60 \
          --role ${{ env.LAMBDA_EXECUTION_ROLE }}
```

### 指定したLambdaが存在する場合は更新してデプロイする
前述のget_functionの結果で該当するLambdaが存在することを確認したらaws cliで更新してデプロイします
必要になるオプションは以下の通りです

```yml
      - name: Deploy Lambda Function
        if: steps.check-function.outcome == 'success'
        run: |
          aws lambda update-function-code \
          --function-name ${{ env.FUNCTION_NAME }} \
          --zip-file fileb://lambda.zip
```

## ワークフローを実行してデプロイしよう！
上記で作成したワークフローを実行し、以下のようになったら成功です

### 新規作成時
![スクリーンショット 2023-08-23 17.15.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f4a21f6-be0e-c3e1-089f-b4aabfc6edfe.png)

### 更新時
![スクリーンショット 2023-08-23 17.16.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b75dc906-54a3-b590-9c07-8eefbec96c64.png)

### Lambdaのコンソール画面
![スクリーンショット 2023-08-23 17.17.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3a196867-0983-3059-f3ef-5d8f4606a306.png)

## まとめ
今回の調査でLambdaが存在してない時のデプロイも成功しました
ただし、以下のようにResourceNotFoundException以外のExceptionが存在するので
仮に別のExceptionがあると現状のワークフローではCatchできないので代替案も追記していきたいと思います

- Lambda.Client.exceptions.ServiceException
- Lambda.Client.exceptions.InvalidParameterValueException
- Lambda.Client.exceptions.ResourceNotFoundException
- Lambda.Client.exceptions.ResourceConflictException
- Lambda.Client.exceptions.TooManyRequestsException
- Lambda.Client.exceptions.CodeStorageExceededException
- Lambda.Client.exceptions.CodeVerificationFailedException
- Lambda.Client.exceptions.InvalidCodeSignatureException
- Lambda.Client.exceptions.CodeSigningConfigNotFoundException

## 参考
https://techblog.sakurug.co.jp/article/automation-deploy/

https://qiita.com/hasegit/items/746b20ed9941ad4bed71

https://geelive-inc.jp/cf_blog/aws-lambda-github-actions-auto-deploy/

https://soypocket.com/it/github-actions-aws-lambda-deploy/

https://docs.aws.amazon.com/cli/latest/reference/lambda/create-function.html

https://docs.aws.amazon.com/cli/latest/reference/lambda/update-function-code.html

https://docs.aws.amazon.com/cli/latest/reference/lambda/wait/function-exists.html

https://stackoverflow.com/questions/36419442/the-role-defined-for-the-function-cannot-be-assumed-by-lambda

https://qiita.com/ho-rai/items/1a3a872cd85c414d9c24

https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/reference_identifiers.html

https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/reference_policies_elements_resource.html

https://docs.aws.amazon.com/ja_jp/IAM/latest/UserGuide/id_roles_use_passrole.html

https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/lambda-api-permissions-ref.html

https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/lambda-intro-execution-role.html#permissions-executionrole-console

https://boto3.amazonaws.com/v1/documentation/api/latest/reference/services/lambda/client/create_function.html


