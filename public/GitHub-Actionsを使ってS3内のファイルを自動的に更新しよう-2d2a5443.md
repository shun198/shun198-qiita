---
title: GitHub Actionsを使ってS3内のファイルを自動的に更新しよう！
tags:
  - AWS
  - S3
  - CloudFormation
  - IAM
  - GitHubActions
private: false
updated_at: '2026-09-05T08:55:28+09:00'
id: 2d2a54434b84a809bb92
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsを使ってS3内のファイルを自動更新する方法についてNested Stackを使用する際に使用するS3内のCloudFormationテンプレートの自動更新を例に解説します
デプロイする用のロールとS3についてはCloudFormationを使って構築します

## 前提
- OIDCの設定済み
- CloudFormation、OIDCに関する知見を有している

## 実装
### CloudFormationを使ったS3とIAMロールの作成
まず、S3とIAMロールをCloudFormationを使って作成します
以下がS3用のテンプレートです

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
    Description: "Enter the project name. (ex: lc-inquiry-pro)"
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
  # For CloudFormation Templates
  CloudFormationTemplatesBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub cf-templates-${ProjectName}-${Environment}-${AWS::Region}
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
  CloudFormationTemplatesBucketName:
    Value: !Ref CloudFormationTemplatesBucket
  CloudFormationTemplatesBucketArn:
    Value: !GetAtt CloudFormationTemplatesBucket.Arn
```

続いてS3内のファイルを更新する用のIAMロールを作成します
AssumeRolePolicyDocumentのPrincipalには作成したOIDCのArnを指定します
ConditionのStringLikeの箇所には該当するリポジトリとブランチ、StringEqualsにはsts.amazonaws.comを指定します
今回は指定したリポジトリの全ブランチを指定したいので`RepositoryName:`の後ろにワイルドカードで`*`を記載します

```yaml
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref OIDCArn
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringLike:
                token.actions.githubusercontent.com:sub: !Sub repo:${RepositoryName}:*
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
```

また、ポリシーについてはS3バケットとS3バケット内のリソースを対象にしており、今回は更新のみなのでs3.PutObjectのみ付与してます

```yaml
      Policies:
        - PolicyName: !Sub S3DeployAccessPolicy-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                Resource:
                  - !Sub arn:aws:s3:::${CloudFormationTemplateBucketName}
                  - !Sub arn:aws:s3:::${CloudFormationTemplateBucketName}/*
```

作成するテンプレートファイルは以下の通りです

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "IAM Role For Deployment"

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
      - Label:
          default: "IAM Configuration"
        Parameters:
          - CloudFormationTemplateBucketName
          - RepositoryName
          - OIDCArn

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: lc-inquiry-pro)"
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
  CloudFormationTemplateBucketName:
    Description: "Enter the cloudformation template S3 bucket name."
    Type: String
    MinLength: 1
    ConstraintDescription: "S3 bucket name must be entered."
  RepositoryName:
    Description: "Enter the repository name."
    Type: String
    MinLength: 1
    ConstraintDescription: "Repository name must be entered."
  OIDCArn:
    Description: "Enter the OIDC Arn. (ex: arn:aws:iam::XXXXXXXXXXXX:oidc-provider/token.actions.githubusercontent.com)"
    Type: String
    MinLength: 1
    ConstraintDescription: "OIDC Arn must be entered."

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  S3DeployIAMRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub S3RoleForGitHubActions-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref OIDCArn
            Action: sts:AssumeRoleWithWebIdentity
            Condition:
              StringLike:
                token.actions.githubusercontent.com:sub: !Sub repo:${RepositoryName}:*
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
      Path: /service-role/
      Policies:
        - PolicyName: !Sub S3DeployAccessPolicy-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                Resource:
                  - !Sub arn:aws:s3:::${CloudFormationTemplateBucketName}
                  - !Sub arn:aws:s3:::${CloudFormationTemplateBucketName}/*

```

### ワークフローの作成
commit履歴を見て追加、変更されたテンプレートファイルのみを検知してS3内のファイルを更新するワークフローを作成します
その際にcheckoutの`fetch-depth: 0`のオプションを付与します

```yaml
      - name: Checkout code
        uses: actions/checkout@v7
        with:
          fetch-depth: 0
```

diffコマンドを使って変更されたテンプレート数を検知して個数を他のステップで使用できるよう`$GITHUB_OUTPUT`へ出力します

```yaml
      - name: Check how many templates changed
        id: templates
        run: |
          changed_templates=$(git diff HEAD^ --name-only | grep -c ${{ env.WORKING_DIRECTORY }}/)
          echo changed_templates=$changed_templates >> "$GITHUB_OUTPUT"
```

変更されたテンプレートの数が1つ以上の場合はGitHub ActionsとAWS間で認証設定を行います
```yaml
      - name: configure aws credentials
        if: ${{ steps.templates.outputs.changed_templates > 0 }}
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ secrets.UPLOAD_TEMPLATE_ROLE }}
          aws-region: ${{ env.REGION_NAME }}
```

変更されたテンプレートの数が1つ以上の場合はdiffコマンドでテンプレート名を取得し、for文を使って順番にaws s3 cpコマンドで更新していきます

```yaml
      - name: Upload to S3
        if: ${{ steps.templates.outputs.changed_templates > 0 }}
        run: |
          templates=$(git diff HEAD^ --name-status | grep ${{ env.WORKING_DIRECTORY }}/ | grep "^M\|^A" | cut -f2)
          for template in $templates; do
            aws s3 cp $template ${{ secrets.S3_BUCKET_URI }}
          done
```

作成したワークフローは以下の通りです
```yaml
name: Deploy CloudFormation Templates to S3

on:
  push:
    branches:
      - develop
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]
    branches-ignore:
      - "release/**"
      - "doc/**"

env:
  WORKING_DIRECTORY: cloudformation/templates
  REGION_NAME: ap-northeast-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write
      contents: read
    steps:
      - name: Checkout code
        uses: actions/checkout@v7
        with:
          fetch-depth: 0
      - name: Check how many templates changed
        id: templates
        run: |
          changed_templates=$(git diff HEAD^ --name-only | grep -c ${{ env.WORKING_DIRECTORY }}/)
          echo changed_templates=$changed_templates >> "$GITHUB_OUTPUT"
      - name: configure aws credentials
        if: ${{ steps.templates.outputs.changed_templates > 0 }}
        uses: aws-actions/configure-aws-credentials@v6
        with:
          role-to-assume: ${{ secrets.UPLOAD_TEMPLATE_ROLE }}
          aws-region: ${{ env.REGION_NAME }}
      - name: Upload to S3
        if: ${{ steps.templates.outputs.changed_templates > 0 }}
        run: |
          templates=$(git diff HEAD^ --name-status | grep ${{ env.WORKING_DIRECTORY }}/ | grep "^M\|^A" | cut -f2)
          for template in $templates; do
            aws s3 cp $template ${{ secrets.S3_BUCKET_URI }}
          done
```

## 実際に実行してみよう！
以下のようにワークフローが正常に実行され、S3内のファイルが自動更新されたら成功です

![スクリーンショット 2024-08-27 10.29.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc0439b6-01e4-7608-3d1d-51f8bcbde4e4.png)

![スクリーンショット 2024-08-27 10.29.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b49dc8a5-1bac-297d-f9f1-82b20eb1f4b8.png)


## 参考
https://github.com/aws-actions/configure-aws-credentials

https://docs.github.com/ja/actions/writing-workflows/choosing-what-your-workflow-does/evaluate-expressions-in-workflows-and-actions
