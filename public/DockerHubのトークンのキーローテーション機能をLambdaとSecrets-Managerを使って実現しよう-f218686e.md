---
title: DockerHubのトークンのキーローテーション機能をLambdaとSecrets Managerを使って実現しよう！
tags:
  - AWS
  - CloudFormation
  - lambda
  - DockerHub
  - SecretsManager
private: false
updated_at: '2024-07-08T11:46:30+09:00'
id: f218686e22488a5427a3
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
LambdaとSecrets Managerを使うと秘匿情報のキーローテーションを実現できます
今回はDockerHubのトークンを使ってキーローテーションします
また、リソースはCloudFormationを使ってコード化します

## 前提
- DockerHubのアカウントを作成済み

## Lambda用のバケットの作成
Lambdaをzipファイルからデプロイする用のS3バケットを作成します

```yml
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
    ConstraintDescription: "ProjectName must be enter"
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

## Lambdaの実装
DockerHubのトークンを更新するためのLambdaを実装します
処理の流れは以下の通りです

ログイン→トークンの作成→前のトークンの無効化→Secrets Manager内のsecretの更新

各APIの詳細は以下のドキュメントに記載してます

https://docs.docker.com/docker-hub/api/latest/

また、処理中にエラーが発生したらSlack通知を送るようにしてます

### Lambda関数の作成
```lambda_function.py
import datetime
import json
import logging
import os
import urllib

import boto3
import requests
from botocore.exceptions import ClientError

logger = logging.getLogger(__name__)

url = "https://hub.docker.com/v2/access-tokens"


def lambda_handler(event, context):
    """Lambdaのエントリーポイント"""
    login_token = login()
    headers = {"Authorization": f"Bearer {login_token}"}
    create_data = create_token(headers=headers)
    token = create_data["token"]
    disable_token(headers=headers, uuid=create_data["uuid"])
    get_secret(token=token)
    return "DockerHubのPATのキーローテーションに成功しました"


def login():
    """ログイン用メソッド"""
    try:
        login_url = "https://hub.docker.com/v2/users/login"
        login_data = {
            "username": getParameterStoreValue(os.environ.get("DOCKER_HUB_USERNAME")),
            "password": getParameterStoreValue(os.environ.get("DOCKER_HUB_PASSWORD")),
        }
        response = requests.post(login_url, json=login_data).content.decode()
        login_token = json.loads(response.strip("\n"))["token"]
        logger.info("ログイン成功")
        return login_token
    except BaseException as e:
        logger.error(f"ログイン失敗:{e}")
        slack_notifier(f"ログイン失敗:{e}")


def create_token(headers: str):
    """トークン生成用メソッド"""
    try:
        create_data = {
            "token_label": f"Token:{datetime.datetime.now()}",
            "scopes": ["repo:admin"],
        }
        response = json.loads(
            requests.post(url, headers=headers, json=create_data).content.decode()
        )
        logger.info("トークン作成成功")
        return response
    except BaseException as e:
        logger.error(f"トークン作成失敗:{e}")
        slack_notifier(f"トークン作成失敗:{e}")


def list_token(headers: str):
    """トークン一覧表示用メソッド"""
    response = json.loads(requests.get(url, headers=headers).content.decode())
    return response["results"]


def disable_token(headers: str, uuid: str):
    """トークン無効化用メソッド"""
    try:
        list_data = list_token(headers=headers)
        for value in list_data:
            if value["uuid"] != uuid:
                uuid = value["uuid"]
                update_url = f"{url}/{uuid}"
    
                disable_token_data = {"is_active": False}
                response = json.loads(
                    requests.patch(
                        update_url, headers=headers, json=disable_token_data
                    ).content.decode()
                )
        logger.info("トークンの無効化成功")
    
        if len(list_data) >= 3:
            uuid_list = list_data[2:]
            for value in uuid_list:
                uuid = value["uuid"]
                delete_url = f"{url}/{uuid}"
                response = requests.delete(delete_url, headers=headers)
            logger.info("トークンの削除成功")
    except BaseException as e:
        logger.error(f"トークンの削除失敗:{e}")
        slack_notifier(f"トークンの削除失敗:{e}")


def get_secret(token: str):
    """Secrets Managerの値更新用メソッド"""
    secret_name = "docker-pat"
    region_name = "ap-northeast-1"

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name="secretsmanager", region_name=region_name
    )
    logger.info("Secrets Manager内のトークンの更新開始")
    try:
        response = client.update_secret(
            SecretId=secret_name,
            Description="DockerHub PAT",
            SecretString=token,
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        logger.error(f"Secrets Manager内のトークンの更新に失敗:{e}")
        slack_notifier(f"Secrets Manager内のトークンの更新に失敗:{e}")
        raise e
    logger.info("Secrets Manager内のトークンの更新終了")


def slack_notifier(value):
    url = getParameterStoreValue(os.environ.get("DOCKER_HUB_SLACK_WEBHOOK_URL"))
    post_json = {
        "attachments": [
        {
            "text": f":no_entry_sign: エラーが発生しました :no_entry_sign:",
        },
        {
            "fields": [
                {
                    "title": "トークン更新中にエラー発生",
                    "value": value,
                }],
          }]
    }
    requests.post(url, data = json.dumps(post_json))


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


# コマンドライン呼び出しの場合のみ、明示的にlambda_handler関数を呼び出す（local環境テストのため）
if __name__ == "__main__":
    lambda_handler("", "")

```

### Lambda用テンプレートスタックの作成
Lambda本体の設定を行います
パラメータストア内の環境変数へアクセスする権限とSecrets Manager内のシークレットを更新する権限の付与も行います
スタックを作成する前に
- DOCKER_HUB_USERNAME
- DOCKER_HUB_PASSWORD
- DOCKER_HUB_SLACK_WEBHOOK_URL

をパラメータストアに登録しましょう

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack For Rotate DockerHub Token"

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
  RotateDockerHubTokenLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        S3Key: !Ref LambdaArchiveBucketObjectKey
      FunctionName: !Sub ${ProjectName}-rotate-dockerhub-token
      Description: "DockerHubのトークンをキーローテーションするための Lambda 関数"
      Handler: !Ref LambdaHandler
      MemorySize: !Ref LambdaMemorySize
      Role: !GetAtt RotateDockerHubTokenLambdaExecutionRole.Arn
      Runtime: !Ref LambdaRuntime
      Timeout: !Ref LambdaTimeout
      Layers:
        - !Ref ParametersSecretsLambdaExtensionArn
        - !Ref PythonRequestsLambdaExtensionArn
      Environment:
        Variables:
          DOCKER_HUB_PASSWORD: DOCKER_HUB_PASSWORD
          DOCKER_HUB_SLACK_WEBHOOK_URL: DOCKER_HUB_SLACK_WEBHOOK_URL
          DOCKER_HUB_USERNAME: DOCKER_HUB_USERNAME
      PackageType: Zip
  RotateDockerHubTokenFunctionPermissions:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt RotateDockerHubTokenLambdaFunction.Arn
      Principal: secretsmanager.amazonaws.com

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  RotateDockerHubTokenLambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRoleForRotateDockerHubToken-${ProjectName}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      Policies:
        - PolicyName: !Sub LambdaAccessForRotateDockerHubToken-${ProjectName}
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
                  - {LambdaFunctionName: !Sub "${ProjectName}-rotate-dockerhub-token"}
              - Effect: Allow
                Action:
                  - ssm:GetParameter
                  - kms:Decrypt
                Resource:
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/DOCKER_HUB_PASSWORD
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/DOCKER_HUB_SLACK_WEBHOOK_URL
                  - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/DOCKER_HUB_USERNAME
                  - !Sub arn:aws:kms:${AWS::Region}:${AWS::AccountId}:key/xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
              - Effect: Allow
                Action:
                  - secretsmanager:UpdateSecret
                Resource:
                  - !Sub arn:aws:secretsmanager:${AWS::Region}:${AWS::AccountId}:*
```

## Secrets Manager
DockerHubのトークンを格納するSecrets Managerを作成します
今回は毎月第一月曜日にLambdaを実行するようローテーションスケジュールを設定します

```yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Secrets Manager Stack"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    # パラメータの並び順
    ParameterGroups:
      - Label:
          default: "Project Configuration"
        Parameters:
          - ProjectName
      - Label:
          default: "Secrets Manager Configutation"
        Parameters:
          - DockerHubToken
          - RotationSchedule
          - DockerHubTokenRotateLambdaArn
      - Label:
          default: "KMS Key Configutation"
        Parameters:
          - PendingWindowInDays
          - KMSKeyAliasName

# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be enter."
    Default: my-project
  DockerHubToken:
    Description: "Enter the DockerHub token."
    Type: String
    NoEcho: true
    MinLength: 30
    ConstraintDescription: "DockerHub Token must be enter."
  RotationSchedule:
    Description: "Enter the rotation schedule using cron. (ex: cron(0 0 ? 1/1 2#1 *))"
    Type: String
    ConstraintDescription: "Rotation Schedule must be enter."
  RotateDockerHubTokenLambdaArn:
    Description: "Enter the arn of DockerHub token rotation Lambda Arn. (ex: arn:aws:lambda:ap-northeast-1:012345678901:function:lambda-name)"
    Type: String
    ConstraintDescription: "Lambda Arn must be enter."
  KMSKeyAliasName:
    Description: "Enter the alias name for SecretsManager KMS key (default: alias/cmk/secretsmanager)"
    Type: String
    Default: alias/cmk/secretsmanager
  PendingWindowInDays:
    Description: "Enter the number of days to wait before being removed from the stack"
    Type: Number
    Default: 30
    MinValue: 7
    MaxValue: 30
# -------------------------------------
# Resources
# -------------------------------------
Resources:
  SecretManager:
    Type: AWS::SecretsManager::Secret
    Properties:
      Description: DockerHub PAT
      KmsKeyId: !Ref SecretsManagerKMSKey
      Name: dockerhub-pat
      SecretString: !Ref DockerHubToken
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-rotate-docker-pat
        - Key: ProjectName
          Value: !Ref ProjectName
  SecretManagerRotationSchedule:
    Type: AWS::SecretsManager::RotationSchedule
    Properties:
      RotateImmediatelyOnUpdate: true
      RotationLambdaARN: !Ref RotateDockerHubTokenLambdaArn
      RotationRules:
        ScheduleExpression: !Ref RotationSchedule
      SecretId: !Ref SecretManager

  # -------------------------------------
  # KMS Key for SecretsManager
  # -------------------------------------
  SecretsManagerKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: "KMS key for encrypting SNS"
      PendingWindowInDays: !Ref PendingWindowInDays
      KeyPolicy:
        Version: 2012-10-17
        Id: sns-key
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub arn:aws:iam::${AWS::AccountId}:root
            Action: kms:*
            Resource: "*"
          - Effect: Allow
            Principal:
              Service:
                - secretsmanager.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: "*"
  KMSKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Ref KMSKeyAliasName
      TargetKeyId: !Ref SecretsManagerKMSKey
Outputs:
  SecretManager:
    Value: !Ref SecretManager
  SecretManagerRotationSchedule:
    Value: !Ref SecretManagerRotationSchedule
```

## 実際に作成してみよう！
以下のようにLambdaとSecrets Managerが作成され、DockerHubのトークンのキーローテーションができるようになったら成功です

![スクリーンショット 2024-07-08 11.43.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/84570347-36bd-2f86-aa71-05df0263e282.png)

![スクリーンショット 2024-07-08 11.42.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a45f5605-cae4-5880-2176-561fdb405c68.png)


![スクリーンショット 2024-07-08 11.44.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7bb4c8e0-be16-f9e7-7eaa-e07be68fef23.png)

## 参考
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/AWS_SecretsManager.html

https://docs.aws.amazon.com/ja_jp/kms/latest/developerguide/services-secrets-manager.html
