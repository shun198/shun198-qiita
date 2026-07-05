---
title: >-
  [Django+Nginx] CloudFormationを使ってECS
  FargateをBlue/GreenデプロイするCodePipelineを構築しよう！
tags:
  - Django
  - nginx
  - CloudFormation
  - ECS
  - CodePipeline
private: false
updated_at: '2024-06-21T08:13:49+09:00'
id: fc1e9d1250c79c140423
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
ECS FargateのBlue/Greenデプロイを自動化するCodePipelineの構築方法について解説します

## 前提
- リージョンはap-northeast-1を使用
- VPC、ECS、RDS(Postgres)、ALBを作成済み
- ECRリポジトリ内にNginxとDjangoのDocker imageがあること
- Blue/Greenデプロイ用のターゲットグループとリスナーを設定済み
- DjangoのプロジェクトをECSへデプロイ済み
- 対象プロジェクトのGitHubリポジトリを作成済み
- AWS CodeStarと接続済み

## ディレクトリ構成
```
tree
・
├── backend # バックエンドのソースコード
├── codebuild
│   ├── buildspec_django.yml
│   └── buildspec_nginx.yml
├── codedeploy
│   └── appspec.yml
├── containers
│   ├── django
│   │   ├── Dockerfile.prd
│   │   └── entrypoint.prd.sh
│   └── nginx
│       ├── Dockerfile.prd
│       └── nginx.prd.conf
└── ecs
    └── taskdef.json

```

## CodePipelineの作成
```codepipeline-for-backend.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "CodePipeline Stack For Backend (ECS Fargate) Stack"

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
          default: "GitHub Configuration"
        Parameters:
          - BackEndRepositoryName
          - SourceBranchName
          - DjangoDockerfilePath
          - NginxDockerfilePath
          - TaskDefinitionTemplatePath
          - AppSpecTemplatePath
      - Label:
          default: "CodeBuild Configuration"
        Parameters:
          - ECRBackEndDjangoRepositoryName
          - ECRBackEndNginxRepositoryName
      - Label:
          default: "CodeDeploy Configuration"
        Parameters:
          - CodeDeployApplicationName
          - CodeDeployDeploymentGroupName
          - CodeDeployDeploymentConfigName
          - ECSClusterName
          - ECSServiceName
          - ALBTargetGroupBlueName
          - ALBTargetGroupGreenName
          - ALBProductionListenerArn
          - ALBTestListenerArn
      - Label:
          default: "CodePipeline Configuration"
        Parameters:
          - CodeStarConnectionArn

# -------------------------------------
# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be enter."
    Default: my-project
  Environment:
    Description: "Select the environment."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."
  BackEndRepositoryName:
    Description: "Enter the target GitHub backend full repository name. (ex: shun198/cloud-formation-playground)"
    Type: String
    Default: shun198/cloud-formation-playground
  SourceBranchName:
    Description: "Enter the source branch name in GitHub backend repository. (ex: develop or main)"
    Type: String
    AllowedValues:
      - develop
      - main
  DjangoDockerfilePath:
    Description: "Enter the Django Dockerfile path in GitHub backend repository. (ex: containers/django/Dockerfile.prd)"
    Type: String
  NginxDockerfilePath:
    Description: "Enter the Nginx Dockerfile path in GitHub backend repository. (ex: containers/nginx/Dockerfile.prd)"
    Type: String
  TaskDefinitionTemplatePath:
    Description: "Enter the ECS Task Definition template path in GitHub backend repository. (ex: ecs/taskdef.json)"
    Type: String
  AppSpecTemplatePath:
    Description: "Enter the Codedeploy Appspec template path in GitHub backend repository. (ex: codedeploy/appspec.yml)"
    Type: String
  ECRBackEndDjangoRepositoryName:
    Description: "Enter the ECR backend application repository name. (ex: my-project/dev/back/django)"
    Type: String
  ECRBackEndNginxRepositoryName:
    Description: "Enter the ECR backend webserver repository name. (ex: my-project/dev/back/nginx)"
    Type: String
  CodeDeployApplicationName:
    Description: "Enter the CodeDeploy application name. (ex: my-project-dev-cdapp)"
    Type: String
  CodeDeployDeploymentGroupName:
    Description: "Enter the CodeDeploy deployment group name. (ex: my-project-dev-cdg)"
    Type: String
  CodeDeployDeploymentConfigName:
    Description: "Enter the CodeDeploy deployment config name."
    Type: String
    AllowedValues:
      - CodeDeployDefault.ECSLinear10PercentEvery1Minutes
      - CodeDeployDefault.ECSLinear10PercentEvery3Minutes
      - CodeDeployDefault.ECSCanary10Percent5Minutes
      - CodeDeployDefault.ECSCanary10Percent15Minutes
      - CodeDeployDefault.ECSAllAtOnce
  ECSClusterName:
    Description: "Enter the ECS cluster name. (ex: my-project-dev-cluster)"
    Type: String
  ECSServiceName:
    Description: "Enter the ECS cluster name. (ex: my-project-dev-back-service)"
    Type: String
  ALBTargetGroupBlueName:
    Description: "Enter the ALB Target Group Name for Blue / Green Deployment. (ex: my-project-dev-tg-blue)"
    Type: String
  ALBTargetGroupGreenName:
    Description: "Enter the ALB Target Group Name for Blue / Green Deployment. (ex: my-project-dev-tg-green)"
    Type: String
  ALBProductionListenerArn:
    Description: "Enter the ALB Production Listener ARN for Blue / Green Deployment."
    Type: String
  ALBTestListenerArn:
    Description: "Enter the ALB Test Listener ARN for Blue / Green Deployment."
    Type: String
  CodeStarConnectionArn:
    Description: "Enter the CodeStar connection ARN. (ex: arn:aws:codestar-connections:<aws_region>:<aws_account_id>:connection/<connection_id>)"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM
  # -------------------------------------
  # CodeBuild 用の IAM Policy
  CodeBuildServiceRolePolicy:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: !Sub CodeBuildServiceRolePolicyForBackEnd-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - logs:CreateLogGroup
              - logs:CreateLogStream
              - logs:PutLogEvents
            Resource:
              - !Sub
                - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/${CodeBuildProjectName}
                - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
              - !Sub
                - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/${CodeBuildProjectName}:*
                - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - s3:GetBucketAcl
              - s3:GetBucketLocation
            Resource: !Sub arn:aws:s3:::${ArtifactBucket}*
          - Effect: Allow
            Action:
              - s3:PutObject
              - s3:GetObject
              - s3:GetObjectVersion
            Resource: !Sub arn:aws:s3:::${ArtifactBucket}/*
          - Effect: Allow
            Action:
              - codebuild:CreateReportGroup
              - codebuild:CreateReport
              - codebuild:UpdateReport
              - codebuild:BatchPutTestCases
              - codebuild:BatchPutCodeCoverages
            Resource: !Sub
              - arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:report-group/${CodeBuildProjectName}*
              - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - codebuild:StartBuild
              - codebuild:StopBuild
              - codebuild:RetryBuild
            Resource: !Sub
              - arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:project/${CodeBuildProjectName}
              - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - ecr:GetAuthorizationToken
              - ecr:BatchCheckLayerAvailability
              - ecr:GetDownloadUrlForLayer
              - ecr:GetRepositoryPolicy
              - ecr:DescribeRepositories
              - ecr:ListImages
              - ecr:DescribeImages
              - ecr:BatchGetImage
              - ecr:GetLifecyclePolicy
              - ecr:GetLifecyclePolicyPreview
              - ecr:ListTagsForResource
              - ecr:DescribeImageScanFindings
              - ecr:InitiateLayerUpload
              - ecr:UploadLayerPart
              - ecr:CompleteLayerUpload
              - ecr:PutImage
            Resource: "*"

  # CodeBuild に適用する IAM Role
  CodeBuildServiceRole:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodeBuildServiceRoleForBackEnd-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
        - !Ref CodeBuildServiceRolePolicy

  # CodeDeploy Blue/Green Deployment 用 IAM Role
  CodeDeployServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodeDeployServiceRoleForBackEnd-${ProjectName}-${Environment}
      Path: /service-role/
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codedeploy.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS

  # CodePipeline 用の IAM Policy
  CodePipelineServiceRolePolicy:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: !Sub CodePipelineServiceRolePolicyForBackEnd-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          # アクセス許可はデプロイ対象リソースに応じて変更する
          - Effect: Allow
            Action:
              - iam:PassRole
            Condition:
              StringEqualsIfExists:
                iam:PassedToService:
                  - ecs-tasks.amazonaws.com
            Resource: "*"
          - Effect: Allow
            Action:
              - s3:*
            Resource:
              - !Sub arn:aws:s3:::${ArtifactBucket}*
          - Effect: Allow
            Action:
              - codedeploy:CreateDeployment
              - codedeploy:GetApplication
              - codedeploy:GetApplicationRevision
              - codedeploy:GetDeployment
              - codedeploy:GetDeploymentConfig
              - codedeploy:RegisterApplicationRevision
            Resource: "*"
          - Effect: Allow
            Action:
              - codestar-connections:UseConnection
            Resource: "*"
          - Effect: Allow
            Action:
              - codebuild:BatchGetBuilds
              - codebuild:StartBuild
              - codebuild:BatchGetBuildBatches
              - codebuild:StartBuildBatch
            Resource: "*"
          - Effect: Allow
            Action:
              - ecr:DescribeImages
              - ecs:RegisterTaskDefinition
            Resource: "*"
          - Effect: Allow
            Action:
              - sns:Publish
            Resource: "*"

  # CodePipeline に適用する IAM Role
  CodePipelineServiceRole:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodePipelineServiceRoleForBackEnd-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      ManagedPolicyArns:
        - !Ref CodePipelineServiceRolePolicy

  # -------------------------------------
  # S3 Bucket
  # -------------------------------------
  # For CodePipeline Artifact
  ArtifactBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${ProjectName}-${Environment}-back-artifact
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true

  # -------------------------------------
  # CodeBuild
  # -------------------------------------
  CodeBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-back-cbpj
      ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      BuildBatchConfig:
        ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          batch:
            build-list:
              - identifier: BuildBackEndDjangoArtifact
                buildspec: codebuild/buildspec_django.yml
              - identifier: BuildBackEndNginxArtifact
                buildspec: codebuild/buildspec_nginx.yml
      Environment:
        PrivilegedMode: true
        ComputeType: BUILD_GENERAL1_SMALL
        Image: aws/codebuild/amazonlinux2-x86_64-standard:5.0
        Type: LINUX_CONTAINER
        EnvironmentVariables:
          - Name: AWS_DEFAULT_ACCOUNT
            Value: !Ref AWS::AccountId
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: DOCKER_BUILDKIT
            Value: 1
          - Name: DOCKERHUB_TOKEN
            Type: PARAMETER_STORE
            Value: !Sub /${ProjectName}/common/DOCKERHUB_TOKEN
          - Name: DOCKERHUB_USER
            Type: PARAMETER_STORE
            Value: !Sub /${ProjectName}/common/DOCKERHUB_USER
          - Name: ECR_DJANGO_REPOSITORY_URI
            Value: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRBackEndDjangoRepositoryName}
          - Name: ECR_NGINX_REPOSITORY_URI
            Value: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRBackEndNginxRepositoryName}
          - Name: ENVIRONMENT
            Value: !Ref Environment
          - Name: DJANGO_DOCKERFILE_PATH
            Value: !Ref DjangoDockerfilePath
          - Name: NGINX_DOCKERFILE_PATH
            Value: !Ref NginxDockerfilePath
          - Name: PROJECT_NAME
            Value: !Ref ProjectName
  # -------------------------------------
  # CodeDeploy
  # -------------------------------------
  CodeDeployApplication:
    Type: AWS::CodeDeploy::Application
    Properties:
      ApplicationName: !Ref CodeDeployApplicationName
      ComputePlatform: ECS
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  CodeDeployDeploymentGroup:
    Type: AWS::CodeDeploy::DeploymentGroup
    Properties:
      ApplicationName: !Ref CodeDeployApplication
      AutoRollbackConfiguration:
        Enabled: true
        Events:
          - DEPLOYMENT_FAILURE
      BlueGreenDeploymentConfiguration:
        DeploymentReadyOption:
          ActionOnTimeout: CONTINUE_DEPLOYMENT
        TerminateBlueInstancesOnDeploymentSuccess:
          Action: TERMINATE
          TerminationWaitTimeInMinutes: 30
      DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
      ServiceRoleArn: !GetAtt CodeDeployServiceRole.Arn
      ECSServices:
        - ClusterName: !Ref ECSClusterName
          ServiceName: !Ref ECSServiceName
      LoadBalancerInfo:
        TargetGroupPairInfoList:
          - ProdTrafficRoute:
              ListenerArns:
                - !Ref ALBProductionListenerArn
            TargetGroups:
              - Name: !Ref ALBTargetGroupBlueName
              - Name: !Ref ALBTargetGroupGreenName
            TestTrafficRoute:
              ListenerArns:
                - !Ref ALBTestListenerArn
      DeploymentStyle:
        DeploymentOption: WITH_TRAFFIC_CONTROL
        DeploymentType: BLUE_GREEN
      DeploymentConfigName: !Ref CodeDeployDeploymentConfigName
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # CodePipeline
  # -------------------------------------
  CodePipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      Name: !Sub ${ProjectName}-${Environment}-back-pipeline
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeStarSourceConnection
                Version: 1
              Configuration:
                FullRepositoryId: !Ref BackEndRepositoryName
                ConnectionArn: !Ref CodeStarConnectionArn
                BranchName: !Ref SourceBranchName
                DetectChanges: true
              OutputArtifacts:
                - Name: SourceArtifact
              RunOrder: 1
        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Version: 1
                Provider: CodeBuild
              Configuration:
                ProjectName: !Ref CodeBuildProject
                PrimarySource: SourceArtifact
                BatchEnabled: true
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
              OutputArtifacts:
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
        - Name: Deploy
          Actions:
            - Name: DeployAction
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Version: 1
                Provider: CodeDeployToECS
              Configuration:
                AppSpecTemplateArtifact: SourceArtifact
                AppSpecTemplatePath: !Ref AppSpecTemplatePath
                TaskDefinitionTemplateArtifact: SourceArtifact
                TaskDefinitionTemplatePath: !Ref TaskDefinitionTemplatePath
                ApplicationName: !Ref CodeDeployApplicationName
                DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
                Image1ArtifactName: BuildBackEndDjangoArtifact
                Image1ContainerName: DJANGO_IMAGE_NAME
                Image2ArtifactName: BuildBackEndNginxArtifact
                Image2ContainerName: NGINX_IMAGE_NAME
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
              Region: !Ref AWS::Region

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  CodePipelineLogicalID:
    Value: !Ref CodePipeline
  CodeBuildServiceRoleArn:
    Value: !GetAtt CodeBuildServiceRole.Arn
  CodeBuildProjectArn:
    Value: !GetAtt CodeBuildProject.Arn
  CodeBuildProjectName:
    Value: !Ref CodeBuildProject
  CodeDeployDeploymentGroupArn:
    Value: !Ref CodeDeployDeploymentGroup
  ArtifactBucketArn:
    Value: !GetAtt ArtifactBucket.Arn
  ArtifactBucketName:
    Value: !Ref ArtifactBucket

```

一つずつ解説していきます

### Artifactの設定
今回はCodePipelineを実行する際に
- BuildArtifact
- SourceArtifact

の2種類を使用し、Artifactを格納するためのS3バケットを作成します
今回はパブリックアクセスをプロックするよう設定します

```yml
  # -------------------------------------
  # S3 Bucket
  # -------------------------------------
  # For CodePipeline Artifact
  ArtifactBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${ProjectName}-${Environment}-back-artifact
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
```

バケットを作成し、CodePipelineを実行すると以下のようにArtifactが格納されます

![スクリーンショット 2024-01-31 21.41.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4e352c99-4248-bf25-9d1c-de40a1a1738b.png)


### IAM
#### CodeBuild
CodeBuild実行用のIAMロールとポリシーを作成します
パラメータストアの値を取得できるAmazonSSMManagedInstanceCoreと以下のことができるカスタムポリシーを今回作成するIAMロールに付与します

- CodeBuildの実行、停止、再実行、レポート関連の操作
- S3に格納されたArtifactの操作
- CloudWatchを有効化してBuild時のログを出力
- ECRからImageを取得

```yml
  # -------------------------------------
  # IAM
  # -------------------------------------
  # CodeBuild 用の IAM Policy
  CodeBuildServiceRolePolicy:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: !Sub CodeBuildServiceRolePolicyForBackEnd-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - logs:CreateLogGroup
              - logs:CreateLogStream
              - logs:PutLogEvents
            Resource:
              - !Sub
                - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/${CodeBuildProjectName}
                - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
              - !Sub
                - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/codebuild/${CodeBuildProjectName}:*
                - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - s3:GetBucketAcl
              - s3:GetBucketLocation
            Resource: !Sub arn:aws:s3:::${ArtifactBucket}*
          - Effect: Allow
            Action:
              - s3:PutObject
              - s3:GetObject
              - s3:GetObjectVersion
            Resource: !Sub arn:aws:s3:::${ArtifactBucket}/*
          - Effect: Allow
            Action:
              - codebuild:CreateReportGroup
              - codebuild:CreateReport
              - codebuild:UpdateReport
              - codebuild:BatchPutTestCases
              - codebuild:BatchPutCodeCoverages
            Resource: !Sub
              - arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:report-group/${CodeBuildProjectName}*
              - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - codebuild:StartBuild
              - codebuild:StopBuild
              - codebuild:RetryBuild
            Resource: !Sub
              - arn:aws:codebuild:${AWS::Region}:${AWS::AccountId}:project/${CodeBuildProjectName}
              - { CodeBuildProjectName: !Sub "${ProjectName}-${Environment}-back-cbpj" }
          - Effect: Allow
            Action:
              - ecr:GetAuthorizationToken
              - ecr:BatchCheckLayerAvailability
              - ecr:GetDownloadUrlForLayer
              - ecr:GetRepositoryPolicy
              - ecr:DescribeRepositories
              - ecr:ListImages
              - ecr:DescribeImages
              - ecr:BatchGetImage
              - ecr:GetLifecyclePolicy
              - ecr:GetLifecyclePolicyPreview
              - ecr:ListTagsForResource
              - ecr:DescribeImageScanFindings
              - ecr:InitiateLayerUpload
              - ecr:UploadLayerPart
              - ecr:CompleteLayerUpload
              - ecr:PutImage
            Resource: "*"

  # CodeBuild に適用する IAM Role
  CodeBuildServiceRole:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodeBuildServiceRoleForBackEnd-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codebuild.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
        - !Ref CodeBuildServiceRolePolicy
```

#### CodeDeploy
AWSCodeDeployRoleForECSのポリシーが付与されたCodeDeployのロールを作成します

```yml
  # CodeDeploy Blue/Green Deployment 用 IAM Role
  CodeDeployServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodeDeployServiceRoleForBackEnd-${ProjectName}-${Environment}
      Path: /service-role/
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codedeploy.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AWSCodeDeployRoleForECS
```

#### CodePipeline
CodePipeline実行用のIAMロールとポリシーを作成します
以下のことができるカスタムポリシーを今回作成するIAMロールに付与します

- S3に格納されたArtifactの操作
- CodeStarとの接続
- CodeBuildのビルドとバッチビルドの開始と情報の取得
- CodeDeployのアプリケーションやデプロイグループの情報の取得、デプロイの作成、デプロイ設定の作成など
- ECSの新しいタスク定義の登録
- ECR内のイメージに関するメタデータ(イメージサイズ、イメージタグ、作成日)の取得

SNS通知の実装については別記事で解説したいと思います

```yml
  # CodePipeline 用の IAM Policy
  CodePipelineServiceRolePolicy:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::ManagedPolicy
    Properties:
      ManagedPolicyName: !Sub CodePipelineServiceRolePolicyForBackEnd-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          # アクセス許可はデプロイ対象リソースに応じて変更する
          - Effect: Allow
            Action:
              - iam:PassRole
            Condition:
              StringEqualsIfExists:
                iam:PassedToService:
                  - ecs-tasks.amazonaws.com
            Resource: "*"
          - Effect: Allow
            Action:
              - s3:*
            Resource:
              - !Sub arn:aws:s3:::${ArtifactBucket}*
          - Effect: Allow
            Action:
              - codedeploy:CreateDeployment
              - codedeploy:GetApplication
              - codedeploy:GetApplicationRevision
              - codedeploy:GetDeployment
              - codedeploy:GetDeploymentConfig
              - codedeploy:RegisterApplicationRevision
            Resource: "*"
          - Effect: Allow
            Action:
              - codestar-connections:UseConnection
            Resource: "*"
          - Effect: Allow
            Action:
              - codebuild:BatchGetBuilds
              - codebuild:StartBuild
              - codebuild:BatchGetBuildBatches
              - codebuild:StartBuildBatch
            Resource: "*"
          - Effect: Allow
            Action:
              - ecr:DescribeImages
              - ecs:RegisterTaskDefinition
            Resource: "*"
          - Effect: Allow
            Action:
              - sns:Publish
            Resource: "*"

  # CodePipeline に適用する IAM Role
  CodePipelineServiceRole:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CodePipelineServiceRoleForBackEnd-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: codepipeline.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      ManagedPolicyArns:
        - !Ref CodePipelineServiceRolePolicy
```

### CodeBuildの設定
CodeBuildプロジェクトを作成します

```yml
  # -------------------------------------
  # CodeBuild
  # -------------------------------------
  CodeBuildProject:
    Type: AWS::CodeBuild::Project
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-back-cbpj
      ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      BuildBatchConfig:
        ServiceRole: !GetAtt CodeBuildServiceRole.Arn
      Artifacts:
        Type: CODEPIPELINE
      Source:
        Type: CODEPIPELINE
        BuildSpec: |
          version: 0.2
          batch:
            build-list:
              - identifier: BuildBackEndDjangoArtifact
                buildspec: codebuild/buildspec_django.yml
              - identifier: BuildBackEndNginxArtifact
                buildspec: codebuild/buildspec_nginx.yml
      Environment:
        PrivilegedMode: true
        ComputeType: BUILD_GENERAL1_SMALL
        Image: aws/codebuild/amazonlinux2-x86_64-standard:5.0
        Type: LINUX_CONTAINER
        EnvironmentVariables:
          - Name: AWS_DEFAULT_ACCOUNT
            Value: !Ref AWS::AccountId
          - Name: AWS_DEFAULT_REGION
            Value: !Ref AWS::Region
          - Name: DOCKER_BUILDKIT
            Value: 1
          - Name: DOCKERHUB_TOKEN
            Type: PARAMETER_STORE
            Value: !Sub /${ProjectName}/common/DOCKERHUB_TOKEN
          - Name: DOCKERHUB_USER
            Type: PARAMETER_STORE
            Value: !Sub /${ProjectName}/common/DOCKERHUB_USER
          - Name: ECR_DJANGO_REPOSITORY_URI
            Value: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRBackEndDjangoRepositoryName}
          - Name: ECR_NGINX_REPOSITORY_URI
            Value: !Sub ${AWS::AccountId}.dkr.ecr.${AWS::Region}.amazonaws.com/${ECRBackEndNginxRepositoryName}
          - Name: ENVIRONMENT
            Value: !Ref Environment
          - Name: DJANGO_DOCKERFILE_PATH
            Value: !Ref DjangoDockerfilePath
          - Name: NGINX_DOCKERFILE_PATH
            Value: !Ref NginxDockerfilePath
          - Name: PROJECT_NAME
            Value: !Ref ProjectName
```

#### プロパティ
プロパティの設定では
- サービスロール
- バッチビルド用ロール

を設定します
また、今回はDjangoとNginxの2種類のbuildspecファイルを使ってbuildをするので以下のようにbuild-listを指定します
- BuildBackEndDjangoArtifact
- BuildBackEndNginxArtifact

の詳細はCodePipelineの箇所でもう一度説明します

```yml
        BuildSpec: |
          version: 0.2
          batch:
            build-list:
              - identifier: BuildBackEndDjangoArtifact
                buildspec: codebuild/buildspec_django.yml
              - identifier: BuildBackEndNginxArtifact
                buildspec: codebuild/buildspec_nginx.yml
```

### CodeDeployの設定
- CodeDeployアプリケーション
- CodeDeployデプロイグループ

を作成します

```yml
  # -------------------------------------
  # CodeDeploy
  # -------------------------------------
  CodeDeployApplication:
    Type: AWS::CodeDeploy::Application
    Properties:
      ApplicationName: !Ref CodeDeployApplicationName
      ComputePlatform: ECS
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  CodeDeployDeploymentGroup:
    Type: AWS::CodeDeploy::DeploymentGroup
    Properties:
      ApplicationName: !Ref CodeDeployApplication
      AutoRollbackConfiguration:
        Enabled: true
        Events:
          - DEPLOYMENT_FAILURE
      BlueGreenDeploymentConfiguration:
        DeploymentReadyOption:
          ActionOnTimeout: CONTINUE_DEPLOYMENT
        TerminateBlueInstancesOnDeploymentSuccess:
          Action: TERMINATE
          TerminationWaitTimeInMinutes: 30
      DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
      ServiceRoleArn: !GetAtt CodeDeployServiceRole.Arn
      ECSServices:
        - ClusterName: !Ref ECSClusterName
          ServiceName: !Ref ECSServiceName
      LoadBalancerInfo:
        TargetGroupPairInfoList:
          - ProdTrafficRoute:
              ListenerArns:
                - !Ref ALBProductionListenerArn
            TargetGroups:
              - Name: !Ref ALBTargetGroupBlueName
              - Name: !Ref ALBTargetGroupGreenName
            TestTrafficRoute:
              ListenerArns:
                - !Ref ALBTestListenerArn
      DeploymentStyle:
        DeploymentOption: WITH_TRAFFIC_CONTROL
        DeploymentType: BLUE_GREEN
      DeploymentConfigName: !Ref CodeDeployDeploymentConfigName
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

#### CodeDeployアプリケーション
CodeDeployアプリケーションを作成します
今回はECS FargateをデプロイするのでプラットフォームはECSにします
```yml
  CodeDeployApplication:
    Type: AWS::CodeDeploy::Application
    Properties:
      ApplicationName: !Ref CodeDeployApplicationName
      ComputePlatform: ECS
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

#### CodeDeployデプロイグループ
デプロイグループを作成します
AutoRollbackConfigurationで自動ロールバックを有効にし、DEPLOYMENT_FAILUREのイベント時に発火するよう設定します

BlueGreenDeploymentConfigurationのDeploymentReadyOptionを使ってGreen環境ができたらすぐにロードバランザーのトラフィックを変更するよう設定します

TerminateBlueInstancesOnDeploymentSuccessのオプションでBlue/Greenデプロイに成功したらBlueのインスタンスを自動で削除します
LoadBalancerInfo内に
- 本番用とテスト用のリスナー
- Blue用とGreen用のターゲットグループ

を設定します

DeploymentStyleのDeploymentOptionをWITH_TRAFFIC_CONTROL、DeploymentTypeをBLUE_GREENに設定します

```yml
  CodeDeployDeploymentGroup:
    Type: AWS::CodeDeploy::DeploymentGroup
    Properties:
      ApplicationName: !Ref CodeDeployApplication
      AutoRollbackConfiguration:
        Enabled: true
        Events:
          - DEPLOYMENT_FAILURE
      BlueGreenDeploymentConfiguration:
        DeploymentReadyOption:
          ActionOnTimeout: CONTINUE_DEPLOYMENT
        TerminateBlueInstancesOnDeploymentSuccess:
          Action: TERMINATE
          TerminationWaitTimeInMinutes: 30
      DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
      ServiceRoleArn: !GetAtt CodeDeployServiceRole.Arn
      ECSServices:
        - ClusterName: !Ref ECSClusterName
          ServiceName: !Ref ECSServiceName
      LoadBalancerInfo:
        TargetGroupPairInfoList:
          - ProdTrafficRoute:
              ListenerArns:
                - !Ref ALBProductionListenerArn
            TargetGroups:
              - Name: !Ref ALBTargetGroupBlueName
              - Name: !Ref ALBTargetGroupGreenName
            TestTrafficRoute:
              ListenerArns:
                - !Ref ALBTestListenerArn
      DeploymentStyle:
        DeploymentOption: WITH_TRAFFIC_CONTROL
        DeploymentType: BLUE_GREEN
      DeploymentConfigName: !Ref CodeDeployDeploymentConfigName
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

詳細は以下の通りです

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-codedeploy-deploymentgroup.html

### CodePipelineの作成
CodePipelineを作成します
CodePipeline自体の設定に加えて

- Source
- Build
- Deploy

の3ステージに分けて構築します

```yml
  CodePipeline:
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      Name: !Sub ${ProjectName}-${Environment}-back-pipeline
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeStarSourceConnection
                Version: 1
              Configuration:
                FullRepositoryId: !Ref BackEndRepositoryName
                ConnectionArn: !Ref CodeStarConnectionArn
                BranchName: !Ref SourceBranchName
                DetectChanges: true
              OutputArtifacts:
                - Name: SourceArtifact
              RunOrder: 1
        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Version: 1
                Provider: CodeBuild
              Configuration:
                ProjectName: !Ref CodeBuildProject
                PrimarySource: SourceArtifact
                BatchEnabled: true
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
              OutputArtifacts:
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
        - Name: Deploy
          Actions:
            - Name: DeployAction
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Version: 1
                Provider: CodeDeployToECS
              Configuration:
                AppSpecTemplateArtifact: SourceArtifact
                AppSpecTemplatePath: !Ref AppSpecTemplatePath
                TaskDefinitionTemplateArtifact: SourceArtifact
                TaskDefinitionTemplatePath: !Ref TaskDefinitionTemplatePath
                ApplicationName: !Ref CodeDeployApplicationName
                DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
                Image1ArtifactName: BuildBackEndDjangoArtifact
                Image1ContainerName: DJANGO_IMAGE_NAME
                Image2ArtifactName: BuildBackEndNginxArtifact
                Image2ContainerName: NGINX_IMAGE_NAME
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
              Region: !Ref AWS::Region
```

#### CodePipelineの設定
CodePipelineを作成します
- パイプライン名
- ロール
- Artifactを格納するバケット

を設定します

```yml
    Type: AWS::CodePipeline::Pipeline
    Properties:
      RoleArn: !GetAtt CodePipelineServiceRole.Arn
      Name: !Sub ${ProjectName}-${Environment}-back-pipeline
      ArtifactStore:
        Type: S3
        Location: !Ref ArtifactBucket
```

#### Sourceステージ
デプロイするコードを取得するSourceステージの設定を行います
今回はAWSのCodeStarを使ってGitHubリポジトリに接続するので、ProviderはCodeStarSourceConnectionにします

Configurationの箇所に
- リポジトリID
- CodeStarのarn
- ブランチ名

を指定します

OutputArtifactsにSourceArtifactを指定します
こちらはBuildステージで使用します

```yml
      Stages:
        - Name: Source
          Actions:
            - Name: SourceAction
              ActionTypeId:
                Category: Source
                Owner: AWS
                Provider: CodeStarSourceConnection
                Version: 1
              Configuration:
                FullRepositoryId: !Ref BackEndRepositoryName
                ConnectionArn: !Ref CodeStarConnectionArn
                BranchName: !Ref SourceBranchName
                DetectChanges: true
              OutputArtifacts:
                - Name: SourceArtifact
              RunOrder: 1
```

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-codepipeline-pipeline.html#aws-resource-codepipeline-pipeline--examples

#### Buildステージ
今回はCodeBuildを使ってBuildステージ内でDockerfileをbuildします
PrimarySourceとInputArtifactにSourceArtifactを指定することでソースコード内のDockerfileをbuildできるようにします

OutputArtifactに
- BuildBackEndDjangoArtifact
- BuildBackEndNginxArtifact

を指定します
こちらはこの後説明するDeployステージに使用します

```yml
        - Name: Build
          Actions:
            - Name: BuildAction
              ActionTypeId:
                Category: Build
                Owner: AWS
                Version: 1
                Provider: CodeBuild
              Configuration:
                ProjectName: !Ref CodeBuildProject
                PrimarySource: SourceArtifact
                BatchEnabled: true
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
              OutputArtifacts:
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
```

#### Deployステージ
今回はCodeDeployを使ってDeployステージ内でbuildしたDockerfileをECS FargateへBlue/Greenデプロイします

Configurationの箇所で
- appspec
    - アーティファクト(SourceArtifact)
    - appspec.ymlのパス
- タスク定義
    - アーティファクト(SourceArtifact)
    - taskdef.jsonのパス
- CodeDeploy
    - アプリケーション名
    - デプロイグループ
- Dockerイメージのアーティファクト
    - Django
        - アーティファクト名
        - Dockerfileのパス
    - Nginx
        - アーティファクト名
        - Dockerfileのパス
- InputArtifact
    - SourceArtifact
    - BuildBackEndDjangoArtifact
    - BuildBackEndNginxArtifact

を設定します

```yml
        - Name: Deploy
          Actions:
            - Name: DeployAction
              ActionTypeId:
                Category: Deploy
                Owner: AWS
                Version: 1
                Provider: CodeDeployToECS
              Configuration:
                AppSpecTemplateArtifact: SourceArtifact
                AppSpecTemplatePath: !Ref AppSpecTemplatePath
                TaskDefinitionTemplateArtifact: SourceArtifact
                TaskDefinitionTemplatePath: !Ref TaskDefinitionTemplatePath
                ApplicationName: !Ref CodeDeployApplicationName
                DeploymentGroupName: !Ref CodeDeployDeploymentGroupName
                Image1ArtifactName: BuildBackEndDjangoArtifact
                Image1ContainerName: DJANGO_IMAGE_NAME
                Image2ArtifactName: BuildBackEndNginxArtifact
                Image2ContainerName: NGINX_IMAGE_NAME
              RunOrder: 1
              InputArtifacts:
                - Name: SourceArtifact
                - Name: BuildBackEndDjangoArtifact
                - Name: BuildBackEndNginxArtifact
              Region: !Ref AWS::Region
```

## buildspecの作成
### Djangoのbuildspec
今回はcodebuildフォルダ配下にymlファイルを作成します
buildspecのphaseは
- pre_build
- build
- post_build

の3種類に分類されるので1つずつ説明します

#### pre_build
Dockerfileをbuildする前にECRへログインするフェーズです
ログインする際はCodeBuildで設定した
- DOCKERHUB_USER
- DOCKERHUB_TOKEN

の環境変数を使ってECRにログインします
また、ビルドの解決済みソースバージョンの識別子の前から7文字をIMAGE_TAGの変数に代入します

![image_tag.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/54561ad3-c170-b692-9789-7662c7c57d72.png)

#### build
DJANGO_DOCKERFILE_PATH内にあるDockerfileをbuildし、タグ付けします

#### post_build
buildが完了したDockerfileをECRへpushし、imageDetail.jsonに書き込み処理を行います

```codebuild/buildspec_django.yml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - echo Logging in to Docker Hub...
      - echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USER --password-stdin
      - IMAGE_TAG=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - cd $CODEBUILD_SRC_DIR
      - docker build -f $DJANGO_DOCKERFILE_PATH -t $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG .
      - docker tag $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG
      - echo Writing imageDetail.json...
      - printf '{"Version":"1.0","ImageURI":"%s"}' $ECR_DJANGO_REPOSITORY_URI:$IMAGE_TAG > imageDetail.json
artifacts:
  files:
    - imageDetail.json
```

### Nginxのbuildspec
Nginxのbuild_specファイルも同様に作成します

```codebuild/buildspec_nginx.yml
version: 0.2
phases:
  pre_build:
    commands:
      - echo Logging in to Amazon ECR...
      - aws ecr get-login-password --region $AWS_DEFAULT_REGION | docker login --username AWS --password-stdin $AWS_DEFAULT_ACCOUNT.dkr.ecr.$AWS_DEFAULT_REGION.amazonaws.com
      - echo Logging in to Docker Hub...
      - echo $DOCKERHUB_TOKEN | docker login -u $DOCKERHUB_USER --password-stdin
      - IMAGE_TAG=$(echo $CODEBUILD_RESOLVED_SOURCE_VERSION | cut -c 1-7)
  build:
    commands:
      - echo Build started on `date`
      - echo Building the Docker image...
      - cd $CODEBUILD_SRC_DIR
      - docker build -f $NGINX_DOCKERFILE_PATH -t $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG .
      - docker tag $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG
  post_build:
    commands:
      - echo Build completed on `date`
      - echo Pushing the Docker images...
      - docker push $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG
      - echo Writing imageDetail.json...
      - printf '{"Version":"1.0","ImageURI":"%s"}' $ECR_NGINX_REPOSITORY_URI:$IMAGE_TAG > imageDetail.json
artifacts:
  files:
    - imageDetail.json

```

## appspecの作成
今回はcodedeployフォルダ配下にymlファイルを作成します
TaskDefinitionの箇所に<TASK_DEFINITION>を設定します
CodePipeline実行時にCodeDeployで設定したECSタスクのパスが自動的に代入されます

```codedeploy/appspec.yml
version: 0.0
Resources:
  - TargetService:
      Type: AWS::ECS::Service
      Properties:
        TaskDefinition: "<TASK_DEFINITION>"
        LoadBalancerInfo:
          ContainerName: "web"
          ContainerPort: "80"
```

https://docs.aws.amazon.com/ja_jp/codepipeline/latest/userguide/tutorials-ecs-ecr-codedeploy.html

## taskdef.jsonの作成
今回はecsフォルダ配下にjsonファイルを作成します
ECSのタスク定義に以下の変数が入るようにします
- NGINX_IMAGE_NAME
- DJANGO_IMAGE_NAME

appspec.yml同様、CodeDeployの設定に追加します

```ecs/taskdef.json
{
    "taskDefinitionArn": "arn:aws:ecs:ap-northeast-1:XXXXXXXXXXXX:task-definition/my-project-dev-back-taskdef:18",
    "containerDefinitions": [
        {
            "name": "web",
            "image": "<NGINX_IMAGE_NAME>",
            "cpu": 0,
            "links": [],
            "portMappings": [
                {
                    "containerPort": 80,
                    "hostPort": 80,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "entryPoint": [],
            "command": [],
            "environment": [],
            "environmentFiles": [],
            "mountPoints": [
                {
                    "sourceVolume": "tmp-data",
                    "containerPath": "/code/tmp"
                }
            ],
            "volumesFrom": [],
            "secrets": [],
            "dependsOn": [
                {
                    "containerName": "app",
                    "condition": "START"
                }
            ],
            "dnsServers": [],
            "dnsSearchDomains": [],
            "extraHosts": [],
            "dockerSecurityOptions": [],
            "dockerLabels": {},
            "ulimits": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/my-project/dev/back/nginx",
                    "awslogs-region": "ap-northeast-1",
                    "awslogs-stream-prefix": "my-project"
                },
                "secretOptions": []
            },
            "systemControls": []
        },
        {
            "name": "app",
            "image": "<DJANGO_IMAGE_NAME>",
            "cpu": 0,
            "links": [],
            "portMappings": [
                {
                    "containerPort": 8000,
                    "hostPort": 8000,
                    "protocol": "tcp"
                }
            ],
            "essential": true,
            "entryPoint": [
                "/usr/local/bin/entrypoint.prd.sh"
            ],
            "command": [],
            "environment": [],
            "environmentFiles": [],
            "mountPoints": [
                {
                    "sourceVolume": "tmp-data",
                    "containerPath": "/code/tmp"
                }
            ],
            "volumesFrom": [],
            "secrets": [
                {
                    "name": "POSTGRES_NAME",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_NAME"
                },
                {
                    "name": "POSTGRES_USER",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_USER"
                },
                {
                    "name": "POSTGRES_PASSWORD",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_PASSWORD"
                },
                {
                    "name": "POSTGRES_PORT",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_PORT"
                },
                {
                    "name": "POSTGRES_HOST",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/POSTGRES_HOST"
                },
                {
                    "name": "SECRET_KEY",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/SECRET_KEY"
                },
                {
                    "name": "ALLOWED_HOSTS",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/ALLOWED_HOSTS"
                },
                {
                    "name": "AWS_DEFAULT_REGION_NAME",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/AWS_DEFAULT_REGION_NAME"
                },
                {
                    "name": "TRUSTED_ORIGINS",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/TRUSTED_ORIGINS"
                },
                {
                    "name": "DJANGO_SETTINGS_MODULE",
                    "valueFrom": "arn:aws:ssm:ap-northeast-1:XXXXXXXXXXXX:parameter/my-project/dev/DJANGO_SETTINGS_MODULE"
                }
            ],
            "dnsServers": [],
            "dnsSearchDomains": [],
            "extraHosts": [],
            "dockerSecurityOptions": [],
            "dockerLabels": {},
            "ulimits": [],
            "logConfiguration": {
                "logDriver": "awslogs",
                "options": {
                    "awslogs-group": "/ecs/my-project/dev/back/django",
                    "awslogs-region": "ap-northeast-1",
                    "awslogs-stream-prefix": "my-project"
                },
                "secretOptions": []
            },
            "systemControls": []
        }
    ],
    "family": "my-project-dev-back-taskdef",
    "taskRoleArn": "arn:aws:iam::XXXXXXXXXXXX:role/service-role/ECSTaskRole-my-project-dev",
    "executionRoleArn": "arn:aws:iam::XXXXXXXXXXXX:role/service-role/ECSTaskExecutionRole-my-project-dev",
    "networkMode": "awsvpc",
    "revision": 18,
    "volumes": [
        {
            "name": "tmp-data",
            "host": {}
        }
    ],
    "status": "ACTIVE",
    "requiresAttributes": [
        {
            "name": "com.amazonaws.ecs.capability.logging-driver.awslogs"
        },
        {
            "name": "ecs.capability.execution-role-awslogs"
        },
        {
            "name": "com.amazonaws.ecs.capability.ecr-auth"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.19"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.17"
        },
        {
            "name": "com.amazonaws.ecs.capability.task-iam-role"
        },
        {
            "name": "ecs.capability.container-ordering"
        },
        {
            "name": "ecs.capability.execution-role-ecr-pull"
        },
        {
            "name": "ecs.capability.secrets.ssm.environment-variables"
        },
        {
            "name": "com.amazonaws.ecs.capability.docker-remote-api.1.18"
        },
        {
            "name": "ecs.capability.task-eni"
        }
    ],
    "placementConstraints": [],
    "compatibilities": [
        "EC2",
        "FARGATE"
    ],
    "requiresCompatibilities": [
        "FARGATE"
    ],
    "cpu": "512",
    "memory": "1024",
    "registeredAt": "2024-01-05T02:48:18.158Z",
    "registeredBy": "arn:aws:sts::XXXXXXXXXXXX:assumed-role/XXXXXXXXXXXX/XXXXXXXXXXXX",
    "tags": [
        {
            "key": "ProjectName",
            "value": "my-project"
        },
        {
            "key": "Environment",
            "value": "dev"
        }
    ]
}

```

## 実際に作成してみよう！
スタック作成時に必要な情報を入力していきます

![スクリーンショット 2024-01-31 14.09.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f97a484e-062b-ba6a-388c-cc6f98880385.png)

![スクリーンショット 2024-01-31 14.10.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/77054743-fe5a-6023-9202-213334e09467.png)

![スクリーンショット 2024-01-31 14.11.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/71951cbd-4c31-c1d1-61b5-c4e1ead7de84.png)

![スクリーンショット 2024-01-31 14.11.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9c0db230-b939-a969-1ef6-d3b7a7bd47d7.png)

以下のようにスタックの作成が完了したら成功です
![68747470733a2f2f71696974612d696d6167652d73746f72652e73332e61702d6e6f727468656173742d312e616d617a6f6e6177732e636f6d2f302f3632353938302f32376564613836362d623737322d623062662d643466342d3931313735623461623866612e706e67.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/debab1e4-4095-a762-8e00-78553b0db388.png)


ECS FargateのBlue/Greenデプロイが完了したら成功です

![スクリーンショット 2024-01-31 22.09.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cf00fb97-74fb-5244-92b5-5ae3d2896151.png)

![スクリーンショット 2024-01-31 22.09.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/17dfed0f-1204-464e-8b19-0b0e0b93faa8.png)

![スクリーンショット 2024-01-31 22.10.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b8b56a7c-b2f9-590e-f08f-63b44b35bac1.png)

![スクリーンショット 2024-01-31 22.11.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c7ffd304-cfd6-773d-92a9-dd696c636daa.png)


## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/AWS_CodePipeline.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/AWS_CodeBuild.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/AWS_CodeDeploy.html
