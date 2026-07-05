---
title: 'CloudFormationを使ってAWSのALBを構築してECS[Django+Nginx]へヘルスチェックを送ろう！'
tags:
  - Django
  - nginx
  - AWS
  - CloudFormation
  - ALB
private: false
updated_at: '2023-09-23T21:02:13+09:00'
id: 971c606699d918bffa6e
organization_url_name: null
slide: false
---
## 概要
今回はCloudFormationを使ってALBを構築する方法について解説していきたいと思います

## 前提
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- ECSを構築済み
- ヘルスチェック用のAPIを作成済み
- 今回はHTTPの設定のみ解説します

## ディレクトリ構成
構成は以下の通りです

```
tree
.
└── templates
    ├── containers
    |   ├── ecr.yml
    |   ├── ecs-cluster.yml
    |   └── ecs-fargate.yml
    ├── logs
    |   └── cloudwatch-logs.yml
    ├── network
    |   ├── alb.yml
    |   └── vpc.yml
    ├── databases
    |   └── rds.yml
    └── security
        └── sg.yml
```

## sg.yml
ALBのセキュリティグループの設定を行います
ALBを使用するので80番ポートからの全てのアクセスを許可します
また、Nginxをリバースプロキシとして使用するのでアウトバウンドアクセスはNginxの80番ポートからの全てのアクセスを許可します
ECSのセキュリティグループもALBからのセキュリティグループからアクセスするよう修正します

|サービス|プロトコル|in/out|ポート番号|CIDR|
|--|--|--|--|--|
|ALB|HTTP|inbound|80|全てのアクセス|
|ALB|HTTP|outbound|80|全てのアクセス|
|ECS|HTTP|outbound|80|ALBのセキュリティグループからのアクセス|

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
  
  # For ALB
  ALBSG:
    Type: AWS::EC2::SecurityGroup
    Properties:
      GroupName: !Sub ${ProjectName}-${Environment}-alb-for-fargate-sg
      GroupDescription: "Security Group For ALB"
      VpcId: !Ref VPCID
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-alb-for-fargate-sg
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ALBSGIngressHTTP:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref ALBSG
      IpProtocol: tcp
      FromPort: 80
      ToPort: 80
      CidrIp: 0.0.0.0/0
      Description: "from my alb sg"
  ALBSGEgressHTTP:
    Type: AWS::EC2::SecurityGroupEgress
    Properties:
      GroupId: !Ref ALBSG
      IpProtocol: tcp
      FromPort: 80
      ToPort: 80
      CidrIp: 0.0.0.0/0
      Description: "from my alb sg"
  ALBSGIngressHTTPS1:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref ALBSG
      IpProtocol: tcp
      FromPort: 443
      ToPort: 443
      CidrIp: 0.0.0.0/0
      Description: "from my alb sg"
  
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
      SourceSecurityGroupId: !Ref ALBSG
      Description: "from alb health check"
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
  ALBSG:
    Description: "Security Group For ALB"
    Value: !Ref ALBSG
  FargateSG:
    Description: "Security Group For ECS Fargate with ALB"
    Value: !Ref FargateSG
  RDSForPostgreSQLSG:
    Description: "Security Group For RDS (PostgreSQL)"
    Value: !Ref RDSForPostgreSQLSG
```

## alb.yml

```alb.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "ALB Stack"

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
          default: "ELB Configuration"
        Parameters:
          - VPCID
          - ALBPublicSubnet1
          - ALBPublicSubnet2
          - ALBSecurityGroupID
          - HealthCheckPath
          - DeletionProtectionEnabled
          - IdleTimeoutSeconds

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
    Description: "Select the VPC ID."
    Type: AWS::EC2::VPC::Id
  ALBPublicSubnet1:
    Description: "Enter the Subnet ID for ALB in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  ALBPublicSubnet2:
    Description: "Enter the Subnet ID for ALB in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  ALBSecurityGroupID:
    Description: "Select the Security Group ID for ALB."
    Type: AWS::EC2::SecurityGroup::Id
  HealthCheckPath:
    Description: "Enter the path respond to health checks from ALB."
    Type: String
    Default: /api/health
  # 今回は検証用のためfalse
  DeletionProtectionEnabled:
    Description: "Select whether to enable deletion protection."
    Type: String
    Default: false
    AllowedValues:
      - false
      - true
  # アイドルタイムアウト値
  IdleTimeoutSeconds:
    Description: "Enter the ALB idle timeout seconds. (default: 60)"
    Type: String
    Default: 60

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Target Groups
  # -------------------------------------
  ALBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg
      TargetType: ip
      Protocol: HTTP
      Port: 80
      VpcId: !Ref VPCID
      HealthCheckProtocol: HTTP
      HealthCheckPath: !Ref HealthCheckPath
      HealthyThresholdCount: 5
      UnhealthyThresholdCount: 2
      HealthCheckTimeoutSeconds: 5
      HealthCheckIntervalSeconds: 30

  # -------------------------------------
  # Elastic Load Balancer
  # -------------------------------------
  InternetALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Name: !Sub ${ProjectName}-${Environment}-alb-fargate
      Scheme: internet-facing
      LoadBalancerAttributes:
        - Key: "deletion_protection.enabled"
          Value: !Ref DeletionProtectionEnabled
        - Key: "idle_timeout.timeout_seconds"
          Value: !Ref IdleTimeoutSeconds
      Subnets:
        - !Ref ALBPublicSubnet1
        - !Ref ALBPublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroupID
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # Listener
  # -------------------------------------
  ALBListenerHTTP:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroup
      LoadBalancerArn: !Ref InternetALB
      Port: 80
      Protocol: HTTP

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  InternetALBArn:
    Value: !Ref InternetALB
  InternetALBName:
    Value: !GetAtt InternetALB.LoadBalancerName
  ALBTargetGroupArn:
    Value: !Ref ALBTargetGroup
  ALBTargetGroupName:
    Value: !GetAtt ALBTargetGroup.TargetGroupName
```

### ALB本体の設定
ALB本体の設定を行います
HTTP通信を扱うので今回はload_balancer_typeをapplicationに指定します
サブネット内にはpublicサブネットを指定します
セキュリティグループにはsg.ymlで作成したALBのセキュリティグループを指定します

```alb.yml
  # -------------------------------------
  # Elastic Load Balancer
  # -------------------------------------
  InternetALB:
    Type: AWS::ElasticLoadBalancingV2::LoadBalancer
    Properties:
      Type: application
      Name: !Sub ${ProjectName}-${Environment}-alb-fargate
      Scheme: internet-facing
      LoadBalancerAttributes:
        - Key: "deletion_protection.enabled"
          Value: !Ref DeletionProtectionEnabled
        - Key: "idle_timeout.timeout_seconds"
          Value: !Ref IdleTimeoutSeconds
      Subnets:
        - !Ref ALBPublicSubnet1
        - !Ref ALBPublicSubnet2
      SecurityGroups:
        - !Ref ALBSecurityGroupID
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

### ALBのターゲットグループの設定
ターゲットグループの設定を行います
ターゲットグループはリクエストをフォワード先として指定する対象、つまりロードバランシングする対象のことです
作成する際は

- ターゲットグループが所属しているVPC
- ターゲットグループがトラフィックを待ち受けるプロトコル
- ターゲットグループがトラフィックを待ち受けるポート

を指定することで登録済みのターゲット(今回だとECS)ごとにリクエストをルーティングできます
また、ヘルスチェックは/api/health/へ向けて行います
今回はすでにヘルスチェックのパスを作成した上でECSのコンテナを作成しています

```alb.yml
  # -------------------------------------
  # Target Groups
  # -------------------------------------
  ALBTargetGroup:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg
      TargetType: ip
      Protocol: HTTP
      Port: 80
      VpcId: !Ref VPCID
      HealthCheckProtocol: HTTP
      HealthCheckPath: !Ref HealthCheckPath
      HealthyThresholdCount: 5
      UnhealthyThresholdCount: 2
      HealthCheckTimeoutSeconds: 5
      HealthCheckIntervalSeconds: 30
```

### ALBのリスナー
ALBのリスナーの設定を行います
リスナーは外部(インターネット)からアクセスするロードバランサーの入り口のことです
リスナーを作成する際はどのプロトコル・ポートを許可するか設定します
今回はHTTPの80番ポートを指定します

```alb.yml
  # -------------------------------------
  # Listener
  # -------------------------------------
  ALBListenerHTTP:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroup
      LoadBalancerArn: !Ref InternetALB
      Port: 80
      Protocol: HTTP
```

## ecs-fargate.yml
ECS本体の設定にAlbの設定を追加します

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
          - ALBTargetGroupArn
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
  ALBTargetGroupArn:
    Description: "Enter the ALB Target Group ARN."
    Type: String
  # ECR リポジトリにプッシュしているアプリケーションまたはウェブサーバのイメージタグを指定
  # CI/CD で Image URI が置き換えられている場合は Tag （コミットハッシュ） を揃えること
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
      LoadBalancers:
        - TargetGroupArn: !Ref ALBTargetGroupArn
          ContainerPort: 80
          ContainerName: web
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

## 実際に作成してみよう！
### セキュリティグループを作成しよう！
セキュリティグループを作成します
![スクリーンショット 2023-09-23 20.54.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/73ac7e19-7f31-ab36-13d4-0060ac2d293f.png)

下記のように作成されたら成功です

![スクリーンショット 2023-09-23 20.53.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7732006d-6ac1-3459-839a-bbee3fc9f733.png)

![スクリーンショット 2023-09-23 20.51.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8ee30686-81e6-0464-bcc8-80b0d1d630a6.png)

### Albを作成しよう！
Albを作成します
![スクリーンショット 2023-09-23 20.54.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/366bf1db-c50a-f1f1-5701-b1cbef08ba2a.png)

下記のように作成されたら成功です

![スクリーンショット 2023-09-23 20.57.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9417ebe8-fc5e-1a71-8d69-b48f210175b2.png)
![スクリーンショット 2023-09-23 20.58.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ed98e957-544d-273b-d362-16720b209dd1.png)

### ECSを更新しよう！
ECSを更新します

![スクリーンショット 2023-09-23 20.59.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6a606343-5feb-80b5-8268-af167f1dd2e1.png)

下記のように起動できていたら成功です

![スクリーンショット 2023-09-23 12.30.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b523fb2b-9d39-0a9c-0b7c-fd695076e9e0.png)

### ヘルスチェックを確認しよう
Albのtarget groupからヘルスチェックが成功したことを確認します

![スクリーンショット 2023-09-23 21.00.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0f9ac0ad-8e03-e5b1-84bb-7441c7a485b6.png)

## 参考
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-elasticloadbalancingv2-loadbalancer.html

https://dev.classmethod.jp/articles/alb-cfn-template-to-study/
