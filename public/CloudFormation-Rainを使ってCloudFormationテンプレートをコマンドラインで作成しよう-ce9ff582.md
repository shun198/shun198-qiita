---
title: CloudFormation Rainを使ってCloudFormationテンプレートをコマンドラインで作成しよう！
tags:
  - AWS
  - CloudFormation
private: false
updated_at: '2024-07-12T16:41:40+09:00'
id: ce9ff58229933d7b13b9
organization_url_name: null
slide: false
---
## CloudFormation Rainとは
CloudFormationのテンプレートやスタックをcliで操作するツールです

## インストール
以下のコマンドでインストールできます
```
brew install rain
```

## テンプレートのデプロイ
 今回は試しにS3バケットを作成するCloudFormationテンプレートをデプロイしてみます

```yaml
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
        Status: Suspended
      LifecycleConfiguration:
        Rules:
          - Id: ExpiresAfter1DaysForOneOlderVersion
            Status: Enabled
            NoncurrentVersionExpiration:
              NewerNoncurrentVersions: 1
              NoncurrentDays: 1
  UploadZIPBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref UploadZIPBucket
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Deny
            Principal: "*"
            Action:
              - s3:*
            Resource:
              - !Sub arn:aws:s3:::${ProjectName}-${Environment}-upload-zip
              - !Sub arn:aws:s3:::${ProjectName}-${Environment}-upload-zip/*
            Condition:
              Bool:
                aws:SecureTransport: false
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

rainを使ってスタックの新規作成および更新をする際は以下のようにコマンドを実行します
スイッチロールまたはSSOを使用している場合は以下のように--profileオプションを使って指定できます
```
rain deploy <テンプレートのパス> <指定するスタック名> --profile <プロファイル名>
```

以下のようにMFA、パラメータを入力していきます
スタックの新規作成できれば成功です

```
rain deploy cloudformation/templates/storage/s3-bucket-for-backend.yml shun198-s3-backend --profile admin
MFA Token: 449121

Enter a value for parameter 'ProjectName' "Enter the project name (ex: my-project)" (default value: my-project):
Enter a value for parameter 'Environment' "Select the environment": dev
CloudFormation will make the following changes:
Stack shun198-s3-backend:
  + AWS::S3::BucketPolicy UploadZIPBucketPolicy
  + AWS::S3::Bucket UploadZIPBucket
Do you wish to continue? (Y/n) Y
Deploying template 's3-bucket-for-backend.yml' as stack 'shun198-s3-backend' in ap-northeast-1.
Stack shun198-s3-backend: CREATE_COMPLETE
  Outputs:
    UploadZIPBucket: my-project-dev-upload-zip
    UploadZIPBucketArn: arn:aws:s3:::my-project-dev-upload-zip
    UploadZIPBucketDomainName: my-project-dev-upload-zip.s3.ap-northeast-1.amazonaws.com
Successfully deployed shun198-s3-backend
```

![スクリーンショット 2024-07-12 16.40.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dcfa447d-79ff-7112-8997-bb5b3a364de1.png)

## テンプレートの削除
以下のコマンドを使ってテンプレートを削除できます
```
rain rm <指定するスタック名> --profile <プロファイル名>
```

以下のようにMFAを入力し、スタックが削除されたら成功です

```
rain rm shun198-s3-backend --profile admin
MFA Token: 935354

Stack info: CREATE_COMPLETE
Are you sure you want to delete this stack? (y/N) y
Successfully deleted stack 'shun198-s3-backend'
```

## スタックセットのデプロイ
スタックセットのデプロイもCloudFormation Rainを使って作成できます
複数リージョンで作成する場合は
```
--regions ap-northeast-1,us-east-1
```
という風に間にカンマを入れて指定します

```
rain stackset deploy <テンプレートのパス> <指定するスタック名> --profile <プロファイル名> --regions <作成するリージョン> --accounts "<アカウントID>"
```

```
rain stackset deploy cloudformation/templates/notifications/sns-topic-for-stacksets.yml SNSTopicStack --profile admin --regions ap-northeast-1,us-east-1 --accounts "012345678901"
```

以下のようにStacksetを作成できれば成功です

![スクリーンショット 2024-07-12 16.40.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9a9cbba1-d176-2d28-3133-09e3ee6bf85b.png)

## 参考
https://www.youtube.com/watch?v=pAmP3WFQ2Ss

https://dev.classmethod.jp/articles/aws-cloudformation-rain/

https://github.com/aws-cloudformation/rain/blob/main/docs/rain_deploy.md

