---
title: SES+SNS+Lambdaを使ってバウンスメール通知機能を実装しよう！
tags:
  - AWS
  - ses
  - CloudFormation
  - SNS
  - lambda
private: false
updated_at: '2024-08-30T11:06:51+09:00'
id: cebe32599233e1e89372
organization_url_name: null
slide: false
---
## 概要
SESを使ってメールを送信した際に存在しないメールアドレスの場合に検知できる機能をSES+SNS+Lambdaを使って実装する方法について解説します

## 前提
- Pythonを使ってLambdaのコードを作成します

## 実装
今回は
- S3
- Lambda
- SNS

の3種類のリソースをCloudFormationを使って構築します

### S3の構築
Lambda用のzipファイルを格納するS3バケットを作成します

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Factory Settings Stack"

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
          - Environment

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: shun198)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered."
    Default: shun198
  Environment:
    Description: "Select a environment name."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment name must be selected."

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
      BucketName: !Sub ${ProjectName}-${Environment}-lambda-archive-${AWS::Region}
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
    Value: !GetAtt LambdaArchiveBucket.Arn
```

### SNSとLambdaの構築
バウンスメールを通知するLambdaをバウンスを検知するSNSを構築します
- SSMParameterNameForFromAdminEmail(バウンスメールの送信元)
- SSMParameterNameForToEmail(バウンスメール受取先)

をパラメータストアから取得するので忘れずに作成しておきましょう
Lambda用のロールにはパラメータストアの環境変数の取得とSESを使ったメール送信用の権限を付与します

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack For SES Bounce"

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
          - Environment
      - Label:
          default: "Lambda Configuration"
        Parameters:
          - LambdaArchiveBucketName
          - LambdaArchiveBucketObjectKey
          - LambdaArchiveObjectVersionID
          - ParametersSecretsLambdaExtensionArn
          - LambdaHandler
          - LambdaMemorySize
          - LambdaTimeout
          - LambdaRuntime
      - Label:
          default: "SSM Parameter Store Configuration"
        Parameters:
          - SSMParameterNameForFromAdminEmail
          - SSMParameterNameForToEmail
      - Label:
          default: "KMS Key Configuration"
        Parameters:
          - KMSKeyAliasName

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: shun198)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered."
    Default: shun198
  Environment:
    Description: "Select a environment name."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment name must be selected."
  LambdaArchiveBucketName:
    Description: "Enter the S3 Bucket name for Lambda zip archive."
    Type: String
  LambdaArchiveBucketObjectKey:
    Description: "Enter the S3 Bucket object key for Lambda zip archive."
    Type: String
  LambdaArchiveObjectVersionID:
    Description: "Enter the S3 object version ID for Lambda zip archive."
    Type: String
  # @see https://docs.aws.amazon.com/ja_jp/systems-manager/latest/userguide/ps-integration-lambda-extensions.html#ps-integration-lambda-extensions-add
  ParametersSecretsLambdaExtensionArn:
    Description: "Enter the Lambda Extension ARN for AWS Parameters and Secrets."
    Type: String
    Default: arn:aws:lambda:ap-northeast-1:133490724326:layer:AWS-Parameters-and-Secrets-Lambda-Extension:11
  LambdaHandler:
    Description: "Enter the Lambda function handler."
    Type: String
    Default: lambda_function.lambda_handler
  LambdaMemorySize:
    Description: "Enter the Lambda function memory size. (MiB)"
    Type: Number
    Default: 128
    MinValue: 128
    MaxValue: 10240
  LambdaTimeout:
    Description: "Enter the Lambda function timeout second."
    Type: Number
    Default: 30
    MinValue: 1
    MaxValue: 900
  LambdaRuntime:
    Description: "Enter the Lambda function runtime."
    Type: String
    AllowedValues:
      - python3.12
    Default: python3.12
  SSMParameterNameForFromAdminEmail:
    Description: "Enter the Systems Manager parameter store name defined as 'FROM_ADMIN_EMAIL'. (ex: /shun198/dev/back/FROM_ADMIN_EMAIL)"
    Type: String
  SSMParameterNameForToEmail:
    Description: "Enter the Systems Manager parameter store name defined as 'TO_EMAIL'. (ex: /shun198/dev/back/TO_EMAIL)"
    Type: String
  KMSKeyAliasName:
    Description: "Enter the alias name for SNS KMS key."
    Type: String
    Default: alias/cmk/sns

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Lambda Function
  # -------------------------------------
  SESBounceNotificationLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        S3Key: !Ref LambdaArchiveBucketObjectKey
        S3ObjectVersion: !Ref LambdaArchiveObjectVersionID
      Environment:
        Variables:
          FROM_ADMIN_EMAIL: !Ref SSMParameterNameForFromAdminEmail
          TO_EMAIL: !Ref SSMParameterNameForToEmail
      FunctionName: !Sub ${ProjectName}-${Environment}-notify-ses-email-bounce
      Description: "SES で発生した Bounce (不達) のメール情報を通知するための Lambda 関数"
      Layers:
        - !Ref ParametersSecretsLambdaExtensionArn
      Handler: !Ref LambdaHandler
      MemorySize: !Ref LambdaMemorySize
      Role: !GetAtt LambdaForSESBounceRole.Arn
      Runtime: !Ref LambdaRuntime
      Timeout: !Ref LambdaTimeout
      PackageType: Zip

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  LambdaForSESBounceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRoleForSESBounce-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      Policies:
        - PolicyName: !Sub LambdaAccessForSESBounce-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - ssm:GetParameters
                  - ses:SendEmail
                Resource: "*"
              - Effect: Allow
                Action: logs:CreateLogGroup
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*
              - Effect: Allow
                Action:
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !Sub
                  - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${LambdaFunction}:*
                  - {LambdaFunction: !Sub "${ProjectName}-${Environment}-notify-ses-email-bounce"}

  # -------------------------------------
  # SNS Topic
  # -------------------------------------
  # SES バウンスの通知用
  SESBounceTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: shun198-lambda-notify-ses-bounce
      TopicName: shun198-lambda-notify-ses-bounce
      KmsMasterKeyId: !Ref KMSKeyAliasName
  SESBounceTopicPolicy:
    Type: AWS::SNS::TopicPolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: NotifySESBounceSNSPolicy
            Effect: Allow
            Principal:
              Service:
                - ses.amazonaws.com
            Action:
              - sns:Publish
            Resource: !Ref SESBounceTopic
            Condition:
              StringEquals:
                AWS:SourceAccount: !Ref AWS::AccountId
              StringLike:
                AWS:SourceArn: arn:aws:ses:*
      Topics:
        - !Ref SESBounceTopic

  # SES Topic Subscription
  SESTopicSubscription:
    Type: AWS::SNS::Subscription
    Properties:
      TopicArn: !Ref SESBounceTopic
      Endpoint: !GetAtt SESBounceNotificationLambdaFunction.Arn
      Protocol: lambda
```

バウンスメール通知用のLambdaを作成します
SNSをトリガーに実行されるのでeventから対象のメールアドレス、件名などを取得していきます

```lambda_function.py
import json
import logging
import os

import boto3

# ロガーの設定
logger = logging.getLogger()
logger.setLevel(logging.INFO)


# メールの件名をデコード
def decode_subject(encoded_subject):
    try:
        subject_bytes = encoded_subject.encode('utf-8')
        subject = subject_bytes.decode('utf-8')
        return subject
    except Exception as e:
        logger.info(f"メールの件名のデコードに失敗しました: {e}")
        return encoded_subject


# SSM ParameterStore から指定されたパラメーター名で値を取得
def getParameterStoreValue(parameter_name):
    ssm = boto3.client('ssm')
    response = ssm.get_parameter(Name=parameter_name, WithDecryption=False)
    return response['Parameter']['Value']


# Bounce 処理
def lambda_handler(event, context):
    region_name = os.environ.get("AWS_DEFAULT_REGION")
    ses = boto3.client('ses', region_name=region_name)
    message_json = json.loads(event['Records'][0]['Sns']['Message'])
    destination_email = message_json['mail']['destination'][0]
    sender_email = getParameterStoreValue(os.environ.get("FROM_ADMIN_EMAIL"))
    recipient_email = getParameterStoreValue(os.environ.get("TO_EMAIL"))

    email_subject = '送信したメールが受信者に届きませんでした'
    subject = decode_subject(message_json['mail']['commonHeaders']['subject'])
    email_body = (
        "以下のメールを送信しましたが、受信者に届きませんでした。\n\n"
        f"• メールアドレス: {destination_email}\n"
        f"• メールの件名: {subject}\n\n"
        "本通知を受けて、お客様へのご確認をお願いします。\n\n"
    )

    response = ses.send_email(
        Source=sender_email,
        Destination={'ToAddresses': [recipient_email]},
        Message={
            'Subject': {'Data': email_subject},
            'Body': {'Text': {'Data': email_body}}
        }
    )

    logger.info(f"メールが送信されました: {response['MessageId']}")
```

### コンソール上での設定
記事執筆の段階でSNSとSESの紐付けはCloudFormationでサポートされてないため、以下の作業をコンソール上で実施する必要があります

#### Lambda
Lambdaのトリガーの設定にCloudFormationで作成したSNSトピックを指定します
![スクリーンショット 2024-08-30 10.38.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a79e89d3-d32a-b9ac-8118-cf1ad1dd05ea.png)

#### SES
SESのバウンスフィードバックにCloudFormationで作成したSNSトピックを指定します
選択後、元のEメールヘッダーを含めるにチェックをつけます
![スクリーンショット 2024-08-30 10.44.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/42432660-75e6-de66-ec74-241031dde065.png)

![スクリーンショット 2024-08-30 10.39.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/758c2115-9078-815e-01ac-20f518912abc.png)

## 実際に実行してみよう！
SESを使って存在しないメールアドレスへ送信するとSNSが検知し、SNSをトリガーにLambdaが実行されます
![スクリーンショット 2024-08-30 10.41.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5dbd3f02-e405-a2c5-9756-1c63cd1cad23.png)

以下のようにメールを受信できれば成功です
![スクリーンショット 2024-08-30 10.42.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62691d8d-0914-2d14-4ad6-f3f943aea787.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-function.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-sns-topic.html


