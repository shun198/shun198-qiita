---
title: S3へアップロードされたことをトリガーに実行されるLambdaをCloudFormationで構築しよう！
tags:
  - Python
  - AWS
  - S3
  - CloudFormation
  - lambda
private: false
updated_at: '2024-06-26T08:01:40+09:00'
id: a0db3f7fe445b1293ac8
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はS3へzipファイルがアップロードされたことをトリガーにzipファイルをLambdaで解凍する時に使用するS3とLambdaをCloudFormationを使って構築していきたいと思います

## 前提
- VPCを作成済み
- 今回はLambda用のPrivate Subnetを使用するのでNATゲートウェイを構築済み

## Lambdaを格納するS3バケットの作成
S3内のzipファイルからLambdaを実行するためのS3バケットを作成します
S3内のファイル群は公開したくないのでPublic Accessを全てブロックします

```lambda-archive-s3.yml
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
          - Environment

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
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select"

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
    Value: !GetAtt  LambdaArchiveBucket.Arn

```

以下のように作成できれば成功です
![スクリーンショット 2024-05-16 10.38.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e4f2578d-aa6d-4c04-850b-548d5ed1d6e9.png)

## zipファイルを解凍するコードをzipファイルとしてアップロードする
以下のzipファイルを解凍するコードをzipファイルとして圧縮します

```lambda_function.py
import os
import tempfile
import zipfile

import boto3

s3_client = boto3.client('s3')

def lambda_handler(event, context):
    bucket_name = event['Records'][0]['s3']['bucket']['name']
    key = event['Records'][0]['s3']['object']['key']
    print(event['Records'][0]['s3'])
    with tempfile.TemporaryDirectory() as tmpdir:
        download_path = os.path.join(tmpdir, os.path.basename(key))
        s3_client.download_file(bucket_name, key, download_path)
        with zipfile.ZipFile(download_path, 'r') as zip_ref:
            zip_ref.extractall(tmpdir)
        for file in os.listdir(tmpdir):
            if file != os.path.basename(key):  # Don't upload the original zip file
                s3_client.upload_file(os.path.join(tmpdir, file), bucket_name, file)

```

zipファイルに圧縮後、作成したバケットのunzip-zip-fileフォルダの配下に設置します

![スクリーンショット 2024-05-16 10.58.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e2d513e0-d11d-3b55-a1a8-82c874a87a5f.png)

## zipファイルをアップロードするS3バケットの作成
zipファイルをアップロードするS3バケットを作成します
今回はS3→Lambdaの順で作成するのでNotificationConfigurationを後から追加する形で作成します

```upload-zip-s3.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Stack For Backend"

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
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select"
  # UnzipZipFile:
  #   Description: "Enter the UnzipZipFile Lambda ARN"
  #   Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # zipファイルアップロード用 S3 Bucket
  UploadZIPBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub ${ProjectName}-${Environment}-upload-zip
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      # NotificationConfiguration:
      #   LambdaConfigurations:
      #     - Event: "s3:ObjectCreated:Put"
      #       Filter:
      #         S3Key:
      #           Rules:
      #             - Name: suffix
      #               Value: .zip
      #       Function: ${UnzipZipFile}

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  UploadZIPBucket:
    Value: !Ref UploadZIPBucket
  UploadZIPBucketArn:
    Value: !GetAtt UploadZIPBucket.Arn
  UploadZIPBucketDomainName:
    Value: !GetAtt UploadZIPBucket.RegionalDomainName

```

以下のように作成できれば成功です
![スクリーンショット 2024-05-16 8.29.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8b776cf2-f82c-8839-312a-1469b25a9c2d.png)

## Lambdaの作成
zipファイルを解凍するLambdaを作成します
今回はS3からzipを取得する権限と更新する権限が必要なので以下のポリシーを付与します
```yaml
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub arn:aws:s3:::${UploadZIPBucket}/*
```

また、VPC Lambdaを作成する場合はVPCに接続する権限が必要なので以下のポリシーを付与します
```yaml
              - Effect: Allow
                Action:
                  - ec2:CreateNetworkInterface
                  - ec2:DescribeNetworkInterfaces
                  - ec2:DeleteNetworkInterface
                Resource: "*"
```

```unzip-zip-file-lambda.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack For Unzip Zip File API Call"

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
          - LambdaProtectedSubnet1
          - LambdaProtectedSubnet2
          - LambdaSecurityGroupID
          - LambdaArchiveBucketName
          - LambdaArchiveBucketObjectKey
          - LambdaHandler
          - LambdaMemorySize
          - LambdaTimeout
          - LambdaRuntime
          - UploadZIPBucket

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
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select"
  LambdaProtectedSubnet1:
    Description: "Enter the Subnet ID for Lambda in the selected VPC"
    Type: AWS::EC2::Subnet::Id
  LambdaProtectedSubnet2:
    Description: "Enter the Subnet ID for Lambda in the selected VPC"
    Type: AWS::EC2::Subnet::Id
  LambdaSecurityGroupID:
    Description: "Select the Security Group ID for Lambda"
    Type: AWS::EC2::SecurityGroup::Id
  LambdaArchiveBucketName:
    Type: String
    Description: "Enter the S3 Bucket name for Lambda zip archive"
  LambdaArchiveBucketObjectKey:
    Type: String
    Description: "Enter the S3 Bucket object key for Lambda zip archive"
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
  UploadZIPBucket:
    Description: "Enter the S3 bucket name (ex: my-project-dev-upload-zip)"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Lambda Function
  # -------------------------------------
  UnzipZipFile:
    Type: AWS::Lambda::Function
    Properties:
      VpcConfig:
        SubnetIds:
          - !Ref LambdaProtectedSubnet1
          - !Ref LambdaProtectedSubnet2
        SecurityGroupIds:
          - !Ref LambdaSecurityGroupID
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        # zipファイルのパスを入力する
        # 今回だとunzip-zip-file/lambda_function.py.zip
        S3Key: !Ref LambdaArchiveBucketObjectKey
      FunctionName: !Sub ${ProjectName}-${Environment}-unzip-zip-file
      Description: !Sub "${ProjectName}-${Environment}のS3内のzipファイルを解凍するLambda関数"
      Handler: !Ref LambdaHandler
      MemorySize: !Ref LambdaMemorySize
      Role: !GetAtt UnzipZipFileLambdaRole.Arn
      Runtime: !Ref LambdaRuntime
      Timeout: !Ref LambdaTimeout
      PackageType: Zip
  UnzipZipFileFunctionPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt UnzipZipFile.Arn
      Principal: cloudformation.amazonaws.com

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  UnzipZipFileLambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRoleForUnzipZipFile-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      Policies:
        - PolicyName: !Sub LambdaAccessForUnzipZipFile-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - ec2:CreateNetworkInterface
                  - ec2:DescribeNetworkInterfaces
                  - ec2:DeleteNetworkInterface
                Resource: "*"
              - Effect: Allow
                Action: logs:CreateLogGroup
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:*
              - Effect: Allow
                Action:
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                Resource: !Sub
                  - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${LambdaFunctionName}:*
                  - {LambdaFunctionName: !Sub "${ProjectName}-${Environment}-unzip-zip-file"}
              - Effect: Allow
                Action:
                  - s3:GetObject
                  - s3:PutObject
                Resource:
                  - !Sub arn:aws:s3:::${UploadZIPBucket}/*

```

以下のように作成できたら成功です

![スクリーンショット 2024-05-16 11.02.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/453562fb-dd69-a869-5d25-e07cd02b4352.png)

## S3バケットにトリガーを追加
S3バケットにzipがputされたことをトリガーに実行するようテンプレートを更新します

```upload-zip-s3.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Stack For Backend"

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
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select"
  UnzipZipFile:
    Description: "Enter the UnzipZipFile Lambda ARN"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # zipファイルアップロード用 S3 Bucket
  UploadZIPBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub ${ProjectName}-${Environment}-upload-zip
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      NotificationConfiguration:
        LambdaConfigurations:
          - Event: "s3:ObjectCreated:Put"
            Filter:
              S3Key:
                Rules:
                  - Name: suffix
                    Value: .zip
            Function: !Sub ${UnzipZipFile}

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  UploadZIPBucket:
    Value: !Ref UploadZIPBucket
  UploadZIPBucketArn:
    Value: !GetAtt UploadZIPBucket.Arn
  UploadZIPBucketDomainName:
    Value: !GetAtt UploadZIPBucket.RegionalDomainName

```

以下のように更新されたら成功です

![スクリーンショット 2024-05-16 11.04.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/384cba57-84b0-9c1a-2e3a-34bc2eea21c5.png)

## ZIPファイルをアップロードしてみよう！
作成したS3にZIPファイルをアップロードします
![スクリーンショット 2024-05-16 10.12.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24bc67cc-08ee-fcad-d1f9-b809f7e5905c.png)

以下のように解凍されたら成功です
![スクリーンショット 2024-05-16 10.14.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/09c3e5b5-00f3-56de-84be-26d5955d7bf0.png)


## 参考
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-notificationconfiguration.html

https://dev.classmethod.jp/articles/cloudformation-s3-put-event/

https://zenn.dev/mn87/articles/755378b10896ba

https://stackoverflow.com/questions/64634401/aws-s3-creation-error-the-event-is-not-supported-for-notifications-service-a


