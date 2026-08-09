---
title: AWS LambdaとEventBridgeを使ってOrganization内のGitHub Actionsの使用状況をSlackで通知するには
tags:
  - AWS
  - CloudFormation
  - lambda
  - GitHubActions
  - EventBridge
private: false
updated_at: '2026-07-05T20:53:20+09:00'
id: 2230efe50007cb54dbfa
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
AWS LambdaとEventBridgeを使ってOrganization内のGitHub Actionsの使用状況をSlackで通知する方法について解説します
記事の後半ではCloudFormationを使ってLambdaとEventBridgeを構築する方法についても解説します

## 前提
- Pythonを使用
- GitHubのAPIを使用するため、GitHub Tokenを発行済み
- Incomming Webhookを作成済み

## Organization内のGitHub Actionsの使用状況を取得するAPI
今回は以下のAPIを使って毎月の無料枠(分)と当月使用したGitHub Actionsの使用時間(分)を取得します
orgにはOrganization名を指定します

```
GET /orgs/{org}/settings/billing/actions
```

```json:response
{
  "total_minutes_used": 305,
  "total_paid_minutes_used": 0,
  "included_minutes": 3000,
  "minutes_used_breakdown": {
    "UBUNTU": 205,
    "MACOS": 10,
    "WINDOWS": 90
  }
}
```

https://docs.github.com/en/rest/billing/billing?apiVersion=2022-11-28#get-github-actions-billing-for-an-organization

## Lambdaの設定
本Lambdaを実装するには
- Layer
- Lambda本体のソースコード
- 環境変数
- IAM Role

が必要になるので順番に解説します

### Layerの指定
Pythonのrequestsなどの外部パッケージを使用する際はLayerを設定する必要があります
今回は以下のリポジトリからLayerのArnを取得します

https://github.com/keithrozario/Klayers/tree/master/deployments/python3.12

```json
{
    "packageVersion": "2.32.3",
    "arn": "arn:aws:lambda:ap-northeast-1:770693421928:layer:Klayers-p312-requests:5",
    "package": "requests"
}
```

Layerを追加する際はLambdaのコンソールの`コード`の一番下にあるレイヤーの`レイヤーの追加`を押します

![スクリーンショット 2024-06-18 9.55.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/32c970d1-b893-d61a-d52a-1df62f64a5ec.png)

`ARNを指定`を選択し、requestsのArnを直接指定します
![スクリーンショット 2024-06-18 9.54.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9df69a9c-9b0c-846f-9de9-c98bdc712930.png)

以下のようにrequestsのLayerが追加されたら成功です
![スクリーンショット 2024-06-06 9.44.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4485d55f-f9da-a72b-f474-745e59699140.png)

### コードの実装
GitHub Actionsの使用状況をSlackで通知するロジックをlambda_function.py内に記載します
仕組みは簡単でGitHubのAPIから無料枠と当月の使用時間を取得し、当月の使用時間/無料枠の値ごとにSlackへ通知するメッセージを変えてます

```lambda_function.py
import json
import logging
import os

import requests

def lambda_handler(event, context):
    headers = {"Authorization": f"Bearer {os.environ.get("GITHUB_TOKEN")}"}
    url = os.environ.get("GITHUB_ACTIONS_BILLING_API")
    response = json.loads(
        requests.get(url, headers=headers).content.decode()
    )
    total_minutes_used = response["total_minutes_used"]
    included_minutes = response["included_minutes"]
    usage = total_minutes_used / included_minutes * 100
    if usage >= 80:
        usage_msg = f":alert: 現在のGitHub Actionsの使用状況は{usage}%です\n 不要なワークフローがないか見直しましょう"
    else:
        usage_msg = f"現在のGitHub Actionsの使用状況は{usage}%です"
    url = os.environ.get("NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL")
    post_json = {'text': usage_msg}
    requests.post(url, data = json.dumps(post_json))
    return "GitHub Actionsの使用量の通知に成功しました"


```

### 環境変数の設定
設定>環境変数から環境変数のキーと値を設定します

![スクリーンショット 2024-06-18 10.26.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ca3037b7-66ee-c942-13d7-b747e49858b1.png)

### IAM Role
Lambda用のIAM Roleを作成します

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Action": "logs:CreateLogGroup",
            "Resource": "arn:aws:logs:ap-northeast-1:XXXXXXXXXXXX:*",
            "Effect": "Allow"
        },
        {
            "Action": [
                "logs:CreateLogStream",
                "logs:PutLogEvents"
            ],
            "Resource": "arn:aws:logs:ap-northeast-1:XXXXXXXXXXXX:log-group:/aws/lambda/notice-github-actions-usage:*",
            "Effect": "Allow"
        }
    ]
}
```

## 実際に実行してみよう！
コンソールからLambdaを実行します

![スクリーンショット 2024-06-18 12.59.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc23ddce-cbed-0c4b-8323-cb2f96384276.png)

以下のようにSlackの通知が送信されたら成功です
- 80%を下回った時
![スクリーンショット 2024-06-06 9.48.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/14307f41-2b0a-48af-3f87-e406b6484550.png)

- 80%を超えた時
![スクリーンショット 2024-06-06 10.41.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d24213b8-a00e-36da-78d3-ed6718376a3e.png)

## EventBridgeの設定
EventBridgeを使ってJSTの平日朝10時にLambdaを実行するよう指定します

![スクリーンショット 2024-06-06 9.43.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a3275e8-f8ca-d569-701e-dccc4625ccaa.png)

以下のように設定できたら成功です

![スクリーンショット 2024-06-06 9.43.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fb0b53db-97b9-8587-b0d2-0496f3bc36d4.png)

## 環境変数をパラメータストアで管理したい時
Lambda内の環境変数をよりセキュアに管理したいのでパラメータストアから参照するようにします

### 環境変数の作成
環境変数をパラメータストア内に作成していきます

![スクリーンショット 2024-06-18 13.02.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fdd7807e-57f4-3dc5-6014-68b1b3e9c9e2.png)

### Lambdaの修正
以下のようにパラメータストアの環境変数を取得するよう修正します

```lambda_function.py
import json
import logging
import os

import requests
import urllib

def lambda_handler(event, context):
    token = getParameterStoreValue(os.environ.get("GITHUB_TOKEN"))
    headers = {"Authorization": f"Bearer {token}"}
    url = getParameterStoreValue(os.environ.get("GITHUB_ACTIONS_BILLING_API"))
    response = json.loads(
        requests.get(url, headers=headers).content.decode()
    )
    total_minutes_used = response["total_minutes_used"]
    included_minutes = response["included_minutes"]
    usage = total_minutes_used / included_minutes * 100
    if usage >= 80:
        usage_msg = f":alert: 現在のGitHub Actionsの使用状況は{usage}%です\n 不要なワークフローがないか見直しましょう"
    else:
        usage_msg = f"現在のGitHub Actionsの使用状況は{usage}%です"
    url = getParameterStoreValue(os.environ.get("NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL"))
    post_json = {'text': usage_msg}
    requests.post(url, data = json.dumps(post_json))
    return "GitHub Actionsの使用量の通知に成功しました"

def getParameterStoreValue(parameter_path: str):
    """パラメータストアに設定されている値を取得する
    パラメータストアのパスを指定して、対応する設定値を取得する
    前提:
        - AWS-Parameters-and-Secrets-Lambda-Extension レイヤーが存在する
    参考:
        - https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/ps-integration-lambda-extensions.html
    Args:
        parameter_path (str): SSMパラメータストアのパス
    Returns:
        _type_: パラメータストアに登録されている値
    """
    port = "2773"
    encoded_parameter_path = urllib.parse.quote_plus(parameter_path)
    parameter_store_url = (
        "http://localhost:"
        + port
        + "/systemsmanager/parameters/get/?name="
        + encoded_parameter_path
        + "&withDecryption=true"
    )
    aws_session_token = os.environ.get("AWS_SESSION_TOKEN")
    headers = {"X-Aws-Parameters-Secrets-Token": aws_session_token}
    r = requests.get(parameter_store_url, headers=headers)
    return json.loads(r.text)["Parameter"]["Value"]

```

https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/ps-integration-lambda-extensions.html

### Layerの追加
パラメータストア用のLayerを追加します

![スクリーンショット 2024-06-18 13.05.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0df29152-05f3-14ed-c5d0-88728edfa137.png)

### IAM Roleの修正
IAM Roleにパラメータストアの取得とKMSによる複合化の権限を付与します

```json
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "",
            "Effect": "Allow",
            "Action": [
                "ssm:GetParameter",
                "kms:Decrypt"
            ],
            "Resource": [
                "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/GITHUB_TOKEN",
                "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/GITHUB_ACTIONS_BILLING_API",
                "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL",
                "arn:aws:kms:ap-northeast-1:XXXXXXXXXXXX:key/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
            ]
        }
    ]
}
```

## CloudFormationを使って構築
CloudFormationを使うことでLambdaとEvent Bridgeをコードで管理することができます
今回は
- Lambdaを格納するS3バケット
- LambdaとEventBridge

用のテンプレートを作成します

### Lambdaを格納するS3バケット
LambdaをCloudFormationで作成する際に必要なので以下のようにLambdaを格納するS3バケットを先に作成します

```s3-factory-stacksets.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Stack For Account Setup"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "Project Configuration"
        Parameters:
          - ProjectName

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name (ex: my-project)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered"
    Default: my-project

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # S3
  # -------------------------------------
  # For Lambda Archive
  LambdaArchiveBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub ${ProjectName}-lambda-archive-${AWS::Region}
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: ExpiresAfter365DaysFor4thOlderVersion
            Status: Enabled
            NoncurrentVersionExpiration:
              NewerNoncurrentVersions: 3
              NoncurrentDays: 365

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  LambdaArchiveBucketName:
    Value: !Ref LambdaArchiveBucket
  LambdaArchiveBucketArn:
    Value: !GetAtt  LambdaArchiveBucket.Arn
```

作成完了後、notice-github-action-usageのフォルダ内にLambda関数を圧縮したzipファイルを格納します

![スクリーンショット 2024-06-18 13.07.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a4261dc3-0552-2816-116c-43d9e599e206.png)

### LambdaとEvent Bridgeの作成
以下のようにLambdaとEvent Bridgeを作成します
S3内のzipファイルからデプロイするので
- LambdaArchiveBucketName(バケット名)
- LambdaArchiveBucketObjectKey(zipファイルのパス、今回だとnotice-github-actions-usage/lambda_function.py.zip)

をパラメータに指定します

```notice-github-actions-usage.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack For Notice GitHub Actions Usage"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "Project Configuration"
        Parameters:
          - ProjectName
      - Label:
          default: "EventBridge Configuration"
        Parameters:
          - EventBridgeRuleNameForNoticeGitHubActionsUsage
      - Label:
          default: "Lambda Configuration"
        Parameters:
          - LambdaArchiveBucketName
          - LambdaArchiveBucketObjectKey
          - PythonRequestsLambdaExtensionArn
          - ParametersSecretsLambdaExtensionArn
          - LambdaHandler
          - LambdaMemorySize
          - LambdaTimeout
          - LambdaRuntime

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name (ex: my-project)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be enter"
    Default: my-project
  EventBridgeRuleNameForNoticeGitHubActionsUsage:
    Description: "Enter the EventBridge rule name of Lambda function for notice github actions usage (ex: notice-github-actions-daily-jst-1000)"
    Type: String
  LambdaArchiveBucketName:
    Type: String
    Description: "Enter the S3 Bucket name for Lambda zip archive"
  LambdaArchiveBucketObjectKey:
    Type: String
    Description: "Enter the S3 Bucket object key for Lambda zip archive"
  PythonRequestsLambdaExtensionArn:
    Type: String
    Description: "Enter the Python 3.12 Request Module Extension ARN"
    Default: arn:aws:lambda:ap-northeast-1:770693421928:layer:Klayers-p312-requests:5
  ParametersSecretsLambdaExtensionArn:
    Type: String
    Description: "Enter the Lambda Extension ARN for AWS Parameters and Secrets"
    Default: arn:aws:lambda:ap-northeast-1:133490724326:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11
  LambdaHandler:
    Type: String
    Description: "Enter the Lambda function handler (default: lambda_function.lambda_handler)"
    Default: lambda_function.lambda_handler
  LambdaMemorySize:
    Type: Number
    Description: "Enter the Lambda function memory size (MiB) (default: 128)"
    Default: 128
    MinValue: 128
    MaxValue: 10240
  LambdaTimeout:
    Type: Number
    Description: "Enter the Lambda function timeout second (default: 30)"
    Default: 30
    MinValue: 1
    MaxValue: 900
  LambdaRuntime:
    Type: String
    Description: "Enter the Lambda function runtime (default: python3.12)"
    AllowedValues:
      - python3.12
    Default: python3.12

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Lambda Function
  # -------------------------------------
  NoticeGitHubActionsUsageLambda:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        S3Key: !Ref LambdaArchiveBucketObjectKey
      FunctionName: !Sub ${ProjectName}-notice-github-actions-usage
      Description: "GitHub Actionsの利用状況をSlackで通知するための Lambda 関数"
      Handler: !Ref LambdaHandler
      MemorySize: !Ref LambdaMemorySize
      Role: !GetAtt NoticeGitHubActionsUsageLambdaExecutionRole.Arn
      Runtime: !Ref LambdaRuntime
      Timeout: !Ref LambdaTimeout
      Layers:
        - !Ref ParametersSecretsLambdaExtensionArn
        - !Ref PythonRequestsLambdaExtensionArn
      Environment:
        Variables:
          GITHUB_ACTIONS_BILLING_API: GITHUB_ACTIONS_BILLING_API
          GITHUB_TOKEN: GITHUB_TOKEN
          NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL: NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL
      PackageType: Zip
  NoticeGitHubActionsUsageFunctionPermissions:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !Ref NoticeGitHubActionsUsageLambda
      Principal: events.amazonaws.com
      SourceArn: !GetAtt NoticeGitHubActionsUsageEventRule.Arn

  # -------------------------------------
  # EventBridge
  # -------------------------------------
  NoticeGitHubActionsUsageEventRule:
    Type: AWS::Events::Rule
    Properties:
      Name: !Ref EventBridgeRuleNameForNoticeGitHubActionsUsage
      Description: !Sub "毎日 (JST) 10:00 の時間検知 Event をトリガーに Lambda function (${NoticeGitHubActionsUsageLambda}) を起動"
      ScheduleExpression: cron(0 1 ? * MON-FRI *)
      State: ENABLED
      Targets:
        - Arn: !GetAtt NoticeGitHubActionsUsageLambda.Arn
          Id: NoticeGitHubActionsUsageLambda

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  NoticeGitHubActionsUsageLambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRoleForNoticeGitHubActionsUsage-${ProjectName}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      Policies:
        - PolicyName: !Sub LambdaRoleForNoticeGitHubActionsUsage-${ProjectName}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action: logs:CreateLogGroup
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*
              - Effect: Allow
                Action:
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !Sub
                  - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${LambdaFunctionName}:*
                  - {LambdaFunctionName: !Sub "${ProjectName}-notice-github-actions-usage"}
              - Effect: Allow
                Action:
                  - ssm:GetParameter
                  - kms:Decrypt
                Resource:
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/GITHUB_TOKEN
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/GITHUB_ACTIONS_BILLING_API
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/NOTICE_GITHUB_ACTIONS_USAGE_SLACK_WEBHOOK_URL
                  - !Sub arn:aws:kms:${AWS::Region}:${AWS::AccountId}:key/XXXXXXXXXXXX:key/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

以上です

## 参考
https://github.com/keithrozario/Klayers

https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/ps-integration-lambda-extensions.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html

