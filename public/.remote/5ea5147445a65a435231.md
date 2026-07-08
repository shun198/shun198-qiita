---
title: '[Django+Nginx]CloudFormationを使ってECSを構築しよう！'
tags:
  - Django
  - nginx
  - AWS
  - CloudFormation
  - ECS
private: false
updated_at: '2026-07-05T22:24:14+09:00'
id: 5ea5147445a65a435231
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はCloudFormationを使ってECS Fargateを構築します
かなり長い記事になっていて難易度が高いですが一緒に頑張っていきましょう

## 前提
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- RDSを構築済み
- Djangoのプロジェクトを作成済み
- パッケージ管理はPoetryを使って行います
- アプリケーションサーバはGunicornを使用します

## ディレクトリ構成
```
tree
.
├── application
|   ├── application
|   ├── project
|   ├── manage.py
|   ├── poetry.lock
|   └── pyproject.toml
├── containers
|   ├── django
|   |   ├── Dockerfile.prd
|   |   └── entrypoint.prd.sh
|   └── nginx
|   |   ├── Dockerfile.prd
|   |   └── nginx.prd.conf
└── templates
    ├── containers
    |   ├── ecr.yml
    |   ├── ecs-cluster.yml
    |   └── ecs-fargate.yml
    ├── logs
    |   └── cloudwatch-logs.yml
    ├── network
    |   └── vpc.yml
    ├── databases
    |   └── rds.yml
    └── security
        └── sg.yml
```

## ecr.yml
DjangoとNginx用のDocker imageを格納するECRリポジトリの設定を記載します

```ecr.yml
AWSTemplateFormatVersion: 2010-09-09
Description: 'ECR Stack'

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: 'Project Configuration'
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: 'ECR Configuration'
        Parameters:
          - BackEndAppRepositorySuffix
          - BackEndWebRepositorySuffix

# -------------------------------------
# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: 'Enter the project name. (ex: my-project)'
    Type: String
    Default: my-project
    ConstraintDescription: 'ProjectName must be enter.'
    MinLength: 1
  Environment:
    Description: 'Select the environment.'
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: 'Environment must be select.'
  BackEndAppRepositorySuffix:
    Description: 'Repository name suffix of the application container image. (ex: django)'
    Type: String
    Default: django
  BackEndWebRepositorySuffix:
    Description: 'Repository name suffix of the webserver container image. (ex: nginx)'
    Type: String
    Default: nginx

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  BackEndAppRepository:
    # スタックを削除する際に、リソースやコンテンツを削除せず保持する
    # 検証のたびにDocker imageまで削除すると検証が大変なので今回はRetainを選択します
    DeletionPolicy: Retain
    # スタックを更新してもリソースやコンテンツを保持する
    UpdateReplacePolicy: Retain
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: !Sub ${ProjectName}/${Environment}/back/${BackEndAppRepositorySuffix}
      # ScanOnPush: trueでimageをECRへpushしてからimageをscanする
    　　　　# Docker imageのタグを上書きしないようにする
      ImageScanningConfiguration:
        ScanOnPush: true
      ImageTagMutability: IMMUTABLE
      Tags:
        - Key: ProjectName
          Value: !Sub ${ProjectName}
        - Key: Environment
          Value: !Sub ${Environment}
  BackEndWebRepository:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::ECR::Repository
    Properties:
      RepositoryName: !Sub ${ProjectName}/${Environment}/back/${BackEndWebRepositorySuffix}
      ImageScanningConfiguration:
        ScanOnPush: true
      ImageTagMutability: IMMUTABLE
      Tags:
        - Key: ProjectName
          Value: !Sub ${ProjectName}
        - Key: Environment
          Value: !Sub ${Environment}

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  BackEndAppRepository:
    Value: !Ref BackEndAppRepository
  BackEndWebRepository:
    Value: !Ref BackEndWebRepository

```

## ecs-cluster.yml
ECSのクラスターの設定をします
本ファイル内で
- タスクロール
- タスク実行ロール

が特に重要なのでこの2点について説明します

```ecs-cluster.yml
AWSTemplateFormatVersion: 2010-09-09
Description: 'ECS Cluster Stack'

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: 'Project Configuration'
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: 'ECS Cluster Configuration'
        Parameters:
          - ContainerInsightsEnabled

# -------------------------------------
# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: 'Enter the project name. (ex: my-project)'
    Type: String
    Default: my-project
    MinLength: 1
    ConstraintDescription: 'ProjectName must be enter.'
  Environment:
    Description: 'Select the environment.'
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
  ContainerInsightsEnabled:
    Description: 'Select whether to enable ECS container insights.'
    Type: String
    AllowedValues:
      - disabled
      - enabled
    Default: disabled

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # ECS Cluster
  # -------------------------------------
  ECSCluster:
    Type: AWS::ECS::Cluster
    Properties:
      ClusterName: !Sub ${ProjectName}-${Environment}-cluster
      ClusterSettings:
        - Name: containerInsights
          Value: !Ref ContainerInsightsEnabled
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-cluster
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # IAM
  # -------------------------------------
  # ECS タスク実行 (起動) 時に必要な IAM ロール
  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ecs-tasks.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        # カスタムメトリクス出力用
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        # ECSTaskExecutionRole が使用できるデフォルトの権限
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      RoleName: !Sub ECSTaskExecutionRole-${ProjectName}-${Environment}
      Path: /service-role/

  ECSTaskExecutionRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub ECSTaskExecutionRolePolicy-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              # ECR リポジトリおよびイメージの情報取得用
              - ecr:BatchCheckLayerAvailability
              - ecr:BatchGetImage
              - ecr:DescribeImages
              - ecr:GetAuthorizationToken
              - ecr:GetDownloadUrlForLayer
              - ecr:GetLifecyclePolicyPreview
              - ecr:GetLifecyclePolicy
              - ecr:GetRepositoryPolicy
              - ecr:ListTagsForResource
            Resource:
              - "*"
          - Effect: Allow
            Action:
              # 環境変数の取得用
              - ssm:GetParameters
              - secretsmanager:GetSecretValue
              - kms:Decrypt
            Resource:
              - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/*
      Roles:
        - Ref: ECSTaskExecutionRole

  # ECS アプリケーション実行に必要な IAM ロール
  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ecs-tasks.amazonaws.com
                - events.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        # ECS Exec用ポリシー
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      RoleName: !Sub ECSTaskRole-${ProjectName}-${Environment}
      Path: /service-role/

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  ECSClusterName:
    Value: !Ref ECSCluster
  ECSTaskExecutionRoleArn:
    Value: !GetAtt ECSTaskExecutionRole.Arn
  ECSTaskRoleArn:
    Value: !GetAtt ECSTaskRole.Arn

```

### IAMRoleの作成と設定
ECSをデプロイする際は
- タスクロール
- タスク実行ロール

の2つが必要になります

- タスクロール
    - コンテナの中のアプリケーションからAWSのサービスを利用する場合に設定するロール
    - 例えばコンテナ内にメール送信機能があればSES、画像をS3にアップロードする機能があればS3のポリシーをアタッチします
- タスク実行ロール
    - 　ECS(タスク)を実行させる場合に設定するロール
    - 　例えばECR内のイメージをpullしたりCloudWatchにログを保存したりパラメータストア内の環境変数を使うときのポリシーをアタッチします

今回はSESやS3を使うロジックを作成してないのでタスクロールにECS Execができるよう、AmazonSSMManagedInstanceCoreというポリシーを付与します
タスク実行ロールに
- ECRとECSの実行
- CloudWatch
- パラメータストア

用のポリシーをアタッチします

```ecs-cluster.yml
  # -------------------------------------
  # IAM
  # -------------------------------------
  # ECS タスク実行 (起動) 時に必要な IAM ロール
  ECSTaskExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ecs-tasks.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        # カスタムメトリクス出力用
        - arn:aws:iam::aws:policy/CloudWatchAgentServerPolicy
        # ECSTaskExecutionRole が使用できるデフォルトの権限
        - arn:aws:iam::aws:policy/service-role/AmazonECSTaskExecutionRolePolicy
      RoleName: !Sub ECSTaskExecutionRole-${ProjectName}-${Environment}
      Path: /service-role/

  ECSTaskExecutionRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub ECSTaskExecutionRolePolicy-${ProjectName}-${Environment}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              # ECR リポジトリおよびイメージの情報取得用
              - ecr:BatchCheckLayerAvailability
              - ecr:BatchGetImage
              - ecr:DescribeImages
              - ecr:GetAuthorizationToken
              - ecr:GetDownloadUrlForLayer
              - ecr:GetLifecyclePolicyPreview
              - ecr:GetLifecyclePolicy
              - ecr:GetRepositoryPolicy
              - ecr:ListTagsForResource
            Resource:
              - "*"
          - Effect: Allow
            Action:
              # 環境変数の取得用
              - ssm:GetParameters
              - secretsmanager:GetSecretValue
              - kms:Decrypt
            Resource:
              - !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/*
      Roles:
        - Ref: ECSTaskExecutionRole

  # ECS アプリケーション実行に必要な IAM ロール
  ECSTaskRole:
    Type: AWS::IAM::Role
    Properties:
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - ecs-tasks.amazonaws.com
                - events.amazonaws.com
            Action:
              - sts:AssumeRole
      ManagedPolicyArns:
        # ECS Exec用ポリシー
        - arn:aws:iam::aws:policy/AmazonSSMManagedInstanceCore
      RoleName: !Sub ECSTaskRole-${ProjectName}-${Environment}
      Path: /service-role/
```

## ecs-fargate.yml
ECS自体の設定とECSのタスク定義の設定を行います
どちらも非常に重要なので説明します

```ecs-fargate.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "ECS Fargate Service Stack"

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
          default: "ECS Configuration"
        Parameters:
          - ECSClusterName
          - ECSPublicSubnet1
          - ECSPublicSubnet2
          - ECSSecurityGroupID
          - ECSTaskCPUUnit
          - ECSTaskMemory
          - ECSTaskDesiredCount
          - ECSTaskRoleArn
          - ECSTaskExecutionRoleArn
          - ApplicationRootPath
      - Label:
          default: "ECR Configuration"
        Parameters:
          - ECRAppContainerImageURI
          - ECRWebContainerImageURI
      - Label:
          default: "CloudWatch Logs Configuration"
        Parameters:
          - AppLogGroupName
          - WebLogGroupName

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
    Default: dev
  ECSClusterName:
    Description: "Enter the ECS cluster name. (ex: my-project-dev-cluster)"
    Type: String
    Default: my-project-dev-cluster
  ECSPublicSubnet1:
    Description: "Enter the Subnet ID for ECS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  ECSPublicSubnet2:
    Description: "Enter the Subnet ID for ECS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  ECSSecurityGroupID:
    Description: "Select the Security Group ID for ECS."
    Type: AWS::EC2::SecurityGroup::Id
  ECSTaskCPUUnit:
    Description: "Enter a numeric CPU size used by ECS Tasks."
    Type: Number
    Default: 512
    AllowedValues:
      - 256
      - 512
      - 1024
      - 2048
      - 4096
  ECSTaskMemory:
    Description: "Enter a numeric memory size used by ECS Tasks."
    Type: Number
    Default: 1024
    AllowedValues:
      - 256
      - 512
      - 1024
      - 2048
      - 4096
  # ECS サービス上で常時起動するタスク数
  ECSTaskDesiredCount:
    Description: "Enter a number of tasks to always keep running."
    Type: Number
    Default: 1
  ECSTaskRoleArn:
    Description: "Specify the IAM Role ARN required to run the application. (ex: arn:aws:iam::XXXXXXXXXXXX:role/ECSTaskRole)"
    Type: String
  ECSTaskExecutionRoleArn:
    Description: "Specify the IAM Role ARN required to execute the task. (ex: arn:aws:iam::XXXXXXXXXXXX:role/ECSTaskExecutionRole)"
    Type: String
  EntrypointPath:
    Description: "Enter the path of the entrypoint to be executed at ECS task startup. (default: /usr/local/bin/entrypoint.prd.sh)"
    Type: String
    Default: /usr/local/bin/entrypoint.prd.sh
  ApplicationRootPath:
    Description: "Enter the application root path as defined in the Dockerfile. (ex: /code)"
    Type: String
    Default: /code
  ECRAppContainerImageURI:
    Description: "Enter the ECR image URI for application."
    Type: String
  ECRWebContainerImageURI:
    Description: "Enter the ECR image URI for webserver."
    Type: String
  AppLogGroupName:
    Description: "Enter the CloudWatch Logs log-group name for application. (ex: /ecs/project/dev/back/django)"
    Type: String
    Default: /ecs/my-project/dev/back/django
  WebLogGroupName:
    Description: "Enter the CloudWatch Logs log-group name for webserver. (ex: /ecs/project/dev/back/nginx)"
    Type: String
    Default: /ecs/my-project/dev/back/nginx

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # ECS Fargate
  # -------------------------------------
  # ECS Task Definition
  ECSTaskDefinition:
    Type: AWS::ECS::TaskDefinition
    Properties:
      # タスク定義名
      Family: !Sub ${ProjectName}-${Environment}-back-taskdef
      # タスク定義で起動できる ECS タイプの指定
      RequiresCompatibilities:
        - FARGATE
      # Fargate の場合は `awsvpc` で固定
      NetworkMode: awsvpc
      TaskRoleArn: !Ref ECSTaskRoleArn
      ExecutionRoleArn: !Ref ECSTaskExecutionRoleArn
      # タスクが使用する CPU と Memory を指定
      Cpu: !Ref ECSTaskCPUUnit
      Memory: !Ref ECSTaskMemory
      # タスク内のコンテナ定義
      ContainerDefinitions:
        # Application
        - Name: app
          Image: !Ref ECRAppContainerImageURI
          PortMappings:
            - ContainerPort: 8000
              HostPort: 8000
              Protocol: tcp
          EntryPoint:
            - !Ref EntrypointPath
          # 環境変数
          Secrets:
            # -------------------------------------
            # Specific Environment
            # -------------------------------------
            - Name: POSTGRES_NAME
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/POSTGRES_NAME
            - Name: POSTGRES_USER
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/POSTGRES_USER
            - Name: POSTGRES_PASSWORD
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/POSTGRES_PASSWORD
            - Name: POSTGRES_PORT
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/POSTGRES_PORT
            - Name: POSTGRES_HOST
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/POSTGRES_HOST
            - Name: SECRET_KEY
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/SECRET_KEY
            - Name: ALLOWED_HOSTS
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/ALLOWED_HOSTS
            - Name: DJANGO_SETTINGS_MODULE
              ValueFrom: !Sub arn:aws:ssm:${AWS::Region}:${AWS::AccountId}:parameter/${ProjectName}/${Environment}/DJANGO_SETTINGS_MODULE
          MountPoints:
            - SourceVolume: tmp-data
              ContainerPath: !Sub ${ApplicationRootPath}/tmp
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-region: !Ref AWS::Region
              awslogs-group: !Ref AppLogGroupName
              awslogs-stream-prefix: !Sub ${ProjectName}
          Essential: true
        # Web Server
        - Name: web
          Image: !Ref ECRWebContainerImageURI
          PortMappings:
            - ContainerPort: 80
              HostPort: 80
              Protocol: tcp
          DependsOn:
            - ContainerName: app
              Condition: START
          MountPoints:
            - SourceVolume: tmp-data
              ContainerPath: !Sub ${ApplicationRootPath}/tmp
          LogConfiguration:
            LogDriver: awslogs
            Options:
              awslogs-region: !Ref AWS::Region
              awslogs-group: !Ref WebLogGroupName
              awslogs-stream-prefix: !Sub ${ProjectName}
          Essential: true
      Volumes:
        - Name: tmp-data
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      LaunchType: FARGATE
      TaskDefinition: !Ref ECSTaskDefinition
      Cluster: !Ref ECSClusterName
      ServiceName: !Sub ${ProjectName}-${Environment}-back-service
      SchedulingStrategy: REPLICA
      DesiredCount: !Ref ECSTaskDesiredCount
      NetworkConfiguration:
        AwsvpcConfiguration:
          # PublicSubnet を利用する場合は ENABLED にする
          # PrivateSubnet を利用する (PrivateLink or NAT 経由で ECR や SSM パラメータストアにアクセスさせたい) 場合は DISABLED にする
          AssignPublicIp: ENABLED
          SecurityGroups:
            - !Ref ECSSecurityGroupID
          Subnets:
            - !Ref ECSPublicSubnet1
            - !Ref ECSPublicSubnet2
      # ECS Exec の有効化 (Fargate に SSM Session Manager 経由で SSH 接続出来るようにする)
      EnableExecuteCommand: true
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  ECSTaskDefinitionName:
    Value: !Ref ECSTaskDefinition
  ECSServiceArn:
    Value: !Ref ECSService
```

### タスク定義
コンテナの設定を記載するタスク定義を作成します
また、コンテナを起動させる際に環境変数が必要になるので今回はAWSのパラメータストアに環境変数を格納していきます

#### 環境変数の作成
作成する環境変数は以下のとおりです
今回作成するパスは/my-project/dev/{環境変数名}にします

|環境変数|説明|
|--|--|
|DJANGO_SETTINGS_MODULE|Djangoの設定ファイルを指定するための環境変数<br>今回はdev環境をデプロイするのでproject.settings.devを指定します|
|SECRET_KEY|Djangoのシークレットキー|
|ALLOWED_HOSTS|Djangoのアプリケーションへのアクセスを許可するオリジン<br>今回は*(ワイルドカード)を指定します|
|POSTGRES_NAME|PostgresのDB名|
|POSTGRES_USER|Postgresのユーザ名|
|POSTGRES_PASSWORD|Postgresのパスワード|
|POSTGRES_HOST|Postgresのホスト名|
|POSTGRES_PORT|Postgresのポート番号|

### ECS Fargateの設定
ECSの設定のために以下を記載します

- 使用するクラスター
- 使用するタスク定義
- 起動するタスク数
- 使用するタスクロールとタスク実行ロール
- 起動タイプ(今回はFargate)
- ネットワークの設定
    - 今回はパブリックサブネットにECSを配置します)
    - ECS用のセキュリティグループを適用します
- ECS Execの有効か

```ecs-fargate.yml
  # ECS Service
  ECSService:
    Type: AWS::ECS::Service
    Properties:
      LaunchType: FARGATE
      TaskDefinition: !Ref ECSTaskDefinition
      Cluster: !Ref ECSClusterName
      ServiceName: !Sub ${ProjectName}-${Environment}-back-service
      # 使用するスケジュール戦略
      # クラスター全体で必要数のタスクを配置して維持する
      SchedulingStrategy: REPLICA
      DesiredCount: !Ref ECSTaskDesiredCount
      NetworkConfiguration:
        AwsvpcConfiguration:
          # PublicSubnet を利用する場合は ENABLED にする
          # PrivateSubnet を利用する (PrivateLink or NAT 経由で ECR や SSM パラメータストアにアクセスさせたい) 場合は DISABLED にする
          AssignPublicIp: ENABLED
          SecurityGroups:
            - !Ref ECSSecurityGroupID
          Subnets:
            - !Ref ECSPublicSubnet1
            - !Ref ECSPublicSubnet2
      # ECS Exec の有効化 (Fargate に SSM Session Manager 経由で SSH 接続出来るようにする)
      EnableExecuteCommand: true
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

### セキュリティグループ
ECSのセキュリティの設定を行います
HTTPのインバウンドアクセスに関しましては本来はALBからのアクセスのみ許可しないといけませんが未作成なので一旦全てのアクセスを許可します

|プロトコル/サービス|in/out|ポート番号|CIDR|
|--|--|--|--|
|HTTP|inbound|80|全てのアクセス|
|RDS(Postgres)|outbound|5432|プライベートサブネットAとCのCIDRブロック内|
|HTTPS|inbound|443|全てのアクセス|

ALBを使ったヘルスチェックの設定等は別記事で紹介します

```sg.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Security Group Stack"

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
          default: "Security Group Configuration"
        Parameters:
          - VPCID

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
  VPCID:
    Description: "Enter the VPC ID for create security groups."
    Type: AWS::EC2::VPC::Id

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # For ECS Fargate
  FargateSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub ${ProjectName}-${Environment}-fargate-sg
      GroupDescription: "Security Group For ECS Fargate"
      VpcId: !Ref VPCID
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-fargate-sg
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  FargateSGIngressHTTP:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref FargateSG
      IpProtocol: tcp
      FromPort: 80
      ToPort: 80
      CidrIp: 0.0.0.0/0
      Description: "from alb health check"
  FargateSGIngressHTTPS:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref FargateSG
      IpProtocol: tcp
      FromPort: 443
      ToPort: 443
      CidrIp: 0.0.0.0/0
      Description: "from alb"
  # For RDS (PostgreSQL)
  RDSForPostgreSQLSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      VpcId: !Ref VPCID
      GroupName: !Sub ${ProjectName}-${Environment}-rds-sg
      GroupDescription: "Security Group For RDS (PostgreSQL)"
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-rds-sg
  RDSForPostgreSQLSGIngress:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref RDSForPostgreSQLSG
      IpProtocol: tcp
      FromPort: 5432
      ToPort: 5432
      SourceSecurityGroupId: !GetAtt FargateSG.GroupId
      Description: "from fargate"

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  FargateSG:
    Description: "Security Group For ECS Fargate with ALB"
    Value: !Ref FargateSG
  RDSForPostgreSQLSG:
    Description: "Security Group For RDS (PostgreSQL)"
    Value: !Ref RDSForPostgreSQLSG
```

## 実際に作成してみよう！
### ecrを作成しよう！
まずはECRを作成します

![スクリーンショット 2023-09-15 17.24.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9927cbbd-e6ab-d722-d394-f0b49874d86a.png)

下記のように作成されたら成功です
![スクリーンショット 2023-09-15 17.27.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bc71a416-5646-e231-3467-ee3c71258d89.png)

### Dockerfileの作成
- Django
- Nginx

の2種類のDockerfileを作成します
#### Django
Terraformのタスク定義にも記載しましたがentrypoint.shを使ってコンテナを起動させます
また、コンテナのVolumeは`/code/tmp`に設定します
タスク定義に記載されている内容と統一しないとECSが起動しないので注意です

```Dockerfile:containers/django/Dockerfile.prd
FROM --platform=linux/x86_64 python:3.14

# 公開するポートを明示的に定義
EXPOSE 8000

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

ENV APP_ROOT=/code

WORKDIR ${APP_ROOT}

COPY application/ ${APP_ROOT}/
RUN pip install --upgrade pip && pip install poetry
RUN poetry install --without dev

# コンテナ起動時に必ず実行したいコマンドを定義した entrypoint.sh をコピー
COPY ./containers/django/entrypoint.prd.sh /usr/local/bin/entrypoint.prd.sh
# 実行権限を付与
RUN chmod +x /usr/local/bin/entrypoint.prd.sh
ENTRYPOINT ["entrypoint.prd.sh"]

VOLUME ["${APP_ROOT}/tmp"]
```

続いてentrypoint.prd.shを作成します
通常のDjangoの開発では開発用のサーバーのrunserverを使いますが
今回は本番用の想定で有名なアプリケーションサーバであるGunicornを使って起動させます

```shell:containers/django/entrypoint.prd.sh
#!/bin/sh
set -eu

mkdir -p ${APP_ROOT}/tmp/gunicorn_sockets

# Execute migration
poetry run python manage.py migrate

# Run Django application
poetry run gunicorn project.wsgi:application --bind=unix://${APP_ROOT}/tmp/gunicorn_socket

exec "$@"
```

#### Nginx
NginxのDockerfileとnginx.confファイルを作成します
その際に注意しておくべきことが2つあります
- プラットフォームの指定
    - M1MacでDockerfileをbuildする場合はArmのアーキテクチャになってしまいます
    - ECSのコンテナがx86_64で実行されるのでimageとECSのアーキテクチャが違うことによって実行されなくなってしまいます
    - そこで`--platform=linux/x86_64`と指定する必要があります
- フォアグラウンドモードで実行させる
    - Nginxはデフォルトでバックグラウンド(daemon)モードで実行されます
    - CloudWatch内でログを見れるようにするにはバックグラウンドモードをoffにする必要があります

```Dockerfile:containers/nginx/Dockerfile
FROM --platform=linux/x86_64 nginx:stable-alpine

RUN rm -f /etc/nginx/conf.d/*
COPY ./containers/nginx/nginx.prd.conf /etc/nginx/conf.d/

CMD /usr/sbin/nginx -g 'daemon off;' -c /etc/nginx/nginx.conf
```

Nginxの設定ファイルです
```nginx:containers/nginx/nginx.prd.conf
upstream gunicorn {
    # Unixドメインソケットを通じてGunicornにリクエストを転送する
    # NginxがリバースプロキシとしてGunicornと連携
    server unix:///code/tmp/gunicorn_socket;
}

server {
    listen 80;
    # Nginxのバージョン情報を非表示にする
    # サーバ情報を隠すことでセキュリティ上のリスクを軽減させる
    server_tokens off;

    # ファイルサイズの変更、デフォルト値は1M
    client_max_body_size 5M;

    # HTTP レスポンスヘッダの Content_Type に付与する文字コード
    charset utf-8;

    # ログ設定
    access_log /var/log/nginx/access.log;
    error_log /var/log/nginx/error.log;

    # API 通信
    location /api {
        # X-Real-IPヘッダにクライアントのIPアドレスを設定
        proxy_set_header X-Real-IP $remote_addr;
        # X-Forwarded-Forヘッダにリクエストを送ったクライアントまたはプロキシのIPアドレスの履歴(リスト)を設定
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        # Hostヘッダにクライアントのホスト名を設定
        proxy_set_header Host $http_host;
        # タイムアウトの設定(3600s)
        proxy_read_timeout 3600;
        # 上記のヘッダの情報がGunicornに転送される
        proxy_pass http://gunicorn;
    }

    # ヘルスチェック
    location /api/health {
        empty_gif;
        access_log off;
        break;
    }

    # HTTP 通信をタイムアウトせずに待つ秒数
    keepalive_timeout 60;
}
```

### DockerfileのbuildからECRへpushするまで
aws cliがDockerを使ってpushコマンドを実行できるよう認証トークンを以下のコマンドで取得します
```
aws ecr get-login-password --region ap-northeast-1 | docker login --username AWS --password-stdin XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com
```

ログインに成功後、
- Dockerfileのbuild
- buildしたDockerfileのタグづけ
- タグづけしたDockerfileをECRへpush

を順番に行います
```
docker build -t my-project/dev/back/django -f containers/django/Dockerfile.prd .
docker tag my-project/django:latest XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/my-project/dev/back/django:latest
docker push XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/my-project/django:latest
```

Nginxも同様に行います
```
docker build -t my-project/dev/back/nginx -f containers/nginx/Dockerfile.prd .
docker tag my-project/nginx:latest XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/my-project/dev/back/nginx:latest
docker push XXXXXXXXXXXX.dkr.ecr.ap-northeast-1.amazonaws.com/my-project/nginx:latest
```

以下のように作成したDockerfileをECRリポジトリにpushできたら成功です

![スクリーンショット 2023-09-15 17.56.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/aaee4e60-a7b8-88d3-4be0-ff6687273439.png)

![スクリーンショット 2023-09-15 17.55.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cb42f80c-d0ca-8f1e-1bc5-ed0279c6ab87.png)

## ECS クラスターの作成
クラスターを作成します

![スクリーンショット 2023-09-19 21.04.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ec35d741-d671-34dd-e88d-7322478eea25.png)

下記のように作成されたら成功です

![スクリーンショット 2023-09-19 21.05.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/66889a4d-4456-eb2f-93dd-fe8439e6a025.png)

## SGの作成
SGを作成します

![スクリーンショット 2023-09-23 18.06.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9ef80bb3-f982-cdc4-de6e-e226f4c59635.png)

下記のように作成されたら成功です

![スクリーンショット 2023-09-23 18.05.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f4c48cbb-34f2-7deb-3ad7-90ee43708b07.png)

![スクリーンショット 2023-09-23 18.05.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d1bb0afe-9e56-b605-1d2c-822224eab331.png)

## ECS Fargateの作成
ECS Fargateを作成します

![スクリーンショット 2023-09-19 21.16.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/587d658b-7fc4-1e32-b5d2-de6f324c4160.png)

下記のように作成されたら成功です
![スクリーンショット 2023-09-23 12.30.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b523fb2b-9d39-0a9c-0b7c-fd695076e9e0.png)


## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-ecr-repository.html


