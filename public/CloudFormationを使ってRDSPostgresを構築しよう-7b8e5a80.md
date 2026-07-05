---
title: CloudFormationを使ってRDS(Postgres)を構築しよう！
tags:
  - AWS
  - PostgreSQL
  - RDS
  - CloudFormation
private: false
updated_at: '2024-04-10T16:01:03+09:00'
id: 7b8e5a80a40d7c9fb125
organization_url_name: null
slide: false
---
## 概要
今回はCloudFormationを使ってRDS(Postgres)を構築する方法について解説していきたいと思います

## 前提
- VPC、プライベートサブネットをはじめとするネットワークを構築済み
- 今回はPostgresのDBインスタンスを作成します

VPCをCloudFormationで作成されたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/15f2e8edc57629416ae7

## ディレクトリ構成
構成は以下のとおりです
```
tree
.
└── templates
    ├── network
    |   └── vpc.yml
    ├── databases
    |   └── rds.yml
    └── security
        └── sg.yml
```

## rds.yml
```rds.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "RDS (PostgreSQL) Stack"

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
          default: "RDS (PostgreSQL) Configuration"
        Parameters:
          - PostgreSQLMajorVersion
          - PostgreSQLMinorVersion
          - RDSDBInstanceClass
          - RDSDBInstanceStorageSize
          - RDSDBInstanceStorageType
          - RDSDBName
          - RDSDBMasterUserName
          - RDSDBMasterUserPassword
          - MultiAZEnabled
          - RDSPrivateSubnet1
          - RDSPrivateSubnet2
          - RDSDBSecurityGroupID
          - EnablePerformanceInsights
          - BackupRetentionPeriod
          - PreferredBackupWindow
          - PreferredMaintenanceWindow
          - AutoMinorVersionUpgradeEnabled
          - DeletionProtectionEnabled

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
    Type: String
    Default: my-project
    ConstraintDescription: "ProjectName is required."
    MinLength: 1
  Environment:
    Description: "Select the environment."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."
  PostgreSQLMajorVersion:
    Description: "Select the PostgreSQL engine major version. (default: 15)"
    Type: String
    Default: 15
    AllowedValues: [15]
  PostgreSQLMinorVersion:
    Description: "Select the PostgreSQL engine minor version."
    Type: String
    Default: 2
    AllowedValues: [2]
  RDSDBInstanceClass:
    Description: "Select the DB Instance class. (default: db:t3.small)"
    Type: String
    Default: db.t3.small
    AllowedValues:
      - db.m5.large
      - db.r5.large
      - db.t3.micro
      - db.t3.small
      - db.t3.medium
  RDSDBInstanceStorageSize:
    Description: "Enter the DB Instance storage size. (default: 20 GiB)"
    Type: String
    Default: 20
  RDSDBInstanceStorageType:
    Description: "Enter the DB Instance storage type. (default: gp3)"
    Type: String
    Default: gp3
    AllowedValues: [gp3, io1]
  RDSDBName:
    Description: "Enter the database name. (default: postgres)"
    Type: String
    Default: postgres
  RDSDBMasterUserName:
    Description: "Enter the master username."
    Type: String
    Default: postgres
  RDSDBMasterUserPassword:
    Description: "Enter the master password."
    Type: String
    Default: postgres
    NoEcho: true
  MultiAZEnabled:
    Description: "Select whether you want to enable Multi-AZ or not. (default: false)"
    Type: String
    Default: false
    AllowedValues: [true, false]
  RDSPrivateSubnet1:
    Description: "Enter the Subnet ID for RDS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  RDSPrivateSubnet2:
    Description: "Enter the Subnet ID for RDS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  RDSDBSecurityGroupID:
    Description: "Select the Security Group ID for RDS."
    Type: AWS::EC2::SecurityGroup::Id
  EnablePerformanceInsights:
    Description: "Select whether to enable performance insights. "
    Type: String
    Default: true
    AllowedValues: [true, false]
  BackupRetentionPeriod:
    Description: "Select the backup retention period."
    Type: String
    Default: 35
    AllowedValues: [0, 1, 3, 7, 14, 21, 30, 35]
  PreferredBackupWindow:
    Description: "Enter the time of day to perform backups, separated by 30 minutes. (format/UTC: hh24:mi-hh24:mi)"
    Type: String
    Default: 19:00-19:30
  PreferredMaintenanceWindow:
    Description: "Enter the time of day to perform maintenances, separated by 30 minutes. (format/UTC: ddd:hh24:mi-ddd:hh24:mi)"
    Type: String
    Default: sun:20:00-sun:20:30
  AutoMinorVersionUpgradeEnabled:
    Description: "Select whether to enable RDS DB Instance minor version auto upgrade."
    Type: String
    Default: true
    AllowedValues: [true, false]
  DeletionProtectionEnabled:
    Description: "Select whether to enable deletion protection."
    Type: String
    Default: false
    AllowedValues: [true, false]

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  RDSMonitoringRole:
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub RDSMonitoringRole-${ProjectName}-${Environment}
      Path: /service-role/
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: monitoring.rds.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole

  # -------------------------------------
  # DB SubnetGroup
  # -------------------------------------
  RDSDBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupName: !Sub ${ProjectName}-${Environment}-rds-sbng
      DBSubnetGroupDescription: !Sub ${ProjectName}-${Environment}-rds-sbng
      SubnetIds:
        - !Ref RDSPrivateSubnet1
        - !Ref RDSPrivateSubnet2
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-rds-sbng
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  
  # -------------------------------------
  # DB ParameterGroup
  # -------------------------------------
  RDSDBParameterGroup:
    Type: AWS::RDS::DBParameterGroup
    Properties:
      Description: !Sub ${ProjectName}-${Environment}-rds-pg
      Family: !Sub postgres${PostgreSQLMajorVersion}
      Parameters:
        log_duration: 1
        log_min_duration_statement: 10000
        log_statement: all
        timezone: Asia/Tokyo

  # -------------------------------------
  # DB Instance
  # -------------------------------------
  RDSDBInstance:
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: !Sub ${PostgreSQLMajorVersion}.${PostgreSQLMinorVersion}
      DBInstanceIdentifier: !Sub ${ProjectName}-${Environment}-rds
      MasterUsername: !Ref RDSDBMasterUserName
      MasterUserPassword: !Ref RDSDBMasterUserPassword
      DBInstanceClass: !Ref RDSDBInstanceClass
      StorageType: !Ref RDSDBInstanceStorageType
      AllocatedStorage: !Ref RDSDBInstanceStorageSize
      MultiAZ: !Ref MultiAZEnabled
      DBSubnetGroupName: !Ref RDSDBSubnetGroup
      PubliclyAccessible: false
      VPCSecurityGroups:
        - !Ref RDSDBSecurityGroupID
      DBName: !Ref RDSDBName
      DBParameterGroupName: !Ref RDSDBParameterGroup
      BackupRetentionPeriod: !Ref BackupRetentionPeriod
      PreferredBackupWindow: !Ref PreferredBackupWindow
      CopyTagsToSnapshot: true
      StorageEncrypted: true
      EnablePerformanceInsights: !Ref EnablePerformanceInsights
      MonitoringInterval: 60
      MonitoringRoleArn: !GetAtt RDSMonitoringRole.Arn
      EnableCloudwatchLogsExports: [postgresql]
      AutoMinorVersionUpgrade: !Ref AutoMinorVersionUpgradeEnabled
      PreferredMaintenanceWindow: !Ref PreferredMaintenanceWindow
      DeletionProtection: !Ref DeletionProtectionEnabled
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-rds
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

# ------------------------------------------------------------
# Output
# ------------------------------------------------------------
Outputs:
  RDSDBInstanceID:
    Value: !Ref RDSDBInstance
  RDSDBInstanceEndpoint:
    Value: !GetAtt RDSDBInstance.Endpoint.Address
  RDSDBName:
    Value: !Ref RDSDBName
```

一つずつ解説します

### MetaData
Metadataを使用する際に
```
AWS::CloudFormation::Interface:
```
と記載することで後述するParametersをグループ分けして見やすくすることができます
今回は

- Common Configuration(汎用的な設定)
    - プロジェクト名や環境(dev,stg,prd)などタグ付けに必要な変数
- RDS (PostgreSQL) Configuration(RDSの設定)

の2種類に分類します

```rds.yml
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
          default: "RDS (PostgreSQL) Configuration"
        Parameters:
          - PostgreSQLMajorVersion
          - PostgreSQLMinorVersion
          - RDSDBInstanceClass
          - RDSDBInstanceStorageSize
          - RDSDBInstanceStorageType
          - RDSDBName
          - RDSDBMasterUserName
          - RDSDBMasterUserPassword
          - MultiAZEnabled
          - RDSPrivateSubnet1
          - RDSPrivateSubnet2
          - RDSDBSecurityGroupID
          - EnablePerformanceInsights
          - BackupRetentionPeriod
          - PreferredBackupWindow
          - PreferredMaintenanceWindow
          - AutoMinorVersionUpgradeEnabled
          - DeletionProtectionEnabled
```

### Parameters
Metadataで説明したパラメータのデフォルト値の設定などを行います
Paratemerの詳細は後述するRDSDBInstanceでも説明します
```rds.yml
# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
    Type: String
    Default: my-project
    ConstraintDescription: "ProjectName is required."
    MinLength: 1
  Environment:
    Description: "Select the environment."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."
  PostgreSQLMajorVersion:
    Description: "Select the PostgreSQL engine major version. (default: 15)"
    Type: String
    Default: 15
    AllowedValues: [15]
  PostgreSQLMinorVersion:
    Description: "Select the PostgreSQL engine minor version."
    Type: String
    Default: 2
    AllowedValues: [2]
  RDSDBInstanceClass:
    Description: "Select the DB Instance class. (default: db:t3.small)"
    Type: String
    Default: db.t3.small
    AllowedValues:
      - db.m5.large
      - db.r5.large
      - db.t3.micro
      - db.t3.small
      - db.t3.medium
  RDSDBInstanceStorageSize:
    Description: "Enter the DB Instance storage size. (default: 20 GiB)"
    Type: String
    Default: 20
  RDSDBInstanceStorageType:
    Description: "Enter the DB Instance storage type. (default: gp3)"
    Type: String
    Default: gp3
    AllowedValues: [gp3, io1]
  RDSDBName:
    Description: "Enter the database name. (default: postgres)"
    Type: String
    Default: postgres
  RDSDBMasterUserName:
    Description: "Enter the master username."
    Type: String
    Default: postgres
  RDSDBMasterUserPassword:
    Description: "Enter the master password."
    Type: String
    Default: postgres
    NoEcho: true
  MultiAZEnabled:
    Description: "Select whether you want to enable Multi-AZ or not. (default: false)"
    Type: String
    Default: false
    AllowedValues: [true, false]
  # ドロップダウンから自身が作成したプライベートサブネットを選択する
  RDSPrivateSubnet1:
    Description: "Enter the Subnet ID for RDS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  RDSPrivateSubnet2:
    Description: "Enter the Subnet ID for RDS in the selected VPC."
    Type: AWS::EC2::Subnet::Id
  RDSDBSecurityGroupID:
    Description: "Select the Security Group ID for RDS."
    Type: AWS::EC2::SecurityGroup::Id
  EnablePerformanceInsights:
    Description: "Select whether to enable performance insights. "
    Type: String
    Default: true
    AllowedValues: [true, false]
  BackupRetentionPeriod:
    Description: "Select the backup retention period."
    Type: String
    Default: 35
    AllowedValues: [0, 1, 3, 7, 14, 21, 30, 35]
  PreferredBackupWindow:
    Description: "Enter the time of day to perform backups, separated by 30 minutes. (format/UTC: hh24:mi-hh24:mi)"
    Type: String
    Default: 19:00-19:30
  PreferredMaintenanceWindow:
    Description: "Enter the time of day to perform maintenances, separated by 30 minutes. (format/UTC: ddd:hh24:mi-ddd:hh24:mi)"
    Type: String
    Default: sun:20:00-sun:20:30
  AutoMinorVersionUpgradeEnabled:
    Description: "Select whether to enable RDS DB Instance minor version auto upgrade."
    Type: String
    Default: true
    AllowedValues: [true, false]
  DeletionProtectionEnabled:
    Description: "Select whether to enable deletion protection."
    Type: String
    # 今回は検証用でfalseにします
    Default: false
    AllowedValues: [true, false]
```

### RDSMonitoringRole
RDSの拡張モニタリングの設定をします
デフォルトではfalseになってますが下記のように設定することで
AmazonRDSEnhancedMonitoringRoleを使ってCloudWatchにログを保存できます

https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/USER_Monitoring.OS.overview.html

https://docs.aws.amazon.com/ja_jp/aws-managed-policy/latest/reference/AmazonRDSEnhancedMonitoringRole.html


```rds.yml
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  RDSMonitoringRole:
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub RDSMonitoringRole-${ProjectName}-${Environment}
      Path: /service-role/
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: monitoring.rds.amazonaws.com
            Action: sts:AssumeRole
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AmazonRDSEnhancedMonitoringRole
```

### RDSDBSubnetGroup
RDSのサブネットグループの設定を行います
すでに作成したVPC内のプライベートサブネットと紐付けます

```rds.yml
  # -------------------------------------
  # DB SubnetGroup
  # -------------------------------------
  RDSDBSubnetGroup:
    Type: AWS::RDS::DBSubnetGroup
    Properties:
      DBSubnetGroupName: !Sub ${ProjectName}-${Environment}-rds-sbng
      DBSubnetGroupDescription: !Sub ${ProjectName}-${Environment}-rds-sbng
      SubnetIds:
        - !Ref RDSPrivateSubnet1
        - !Ref RDSPrivateSubnet2
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-rds-sbng
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

### RDSDBParameterGroup
RDSのパラメータグループの設定です
パラメータグループを指定してDBインスタンスを作成するのが一般的です
今回はPostgresを使用しているのでパラメータの一覧は以下の記事に記載されています

https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/Appendix.PostgreSQL.CommonDBATasks.Parameters.html

```rds.yml
  # -------------------------------------
  # DB ParameterGroup
  # -------------------------------------
  RDSDBParameterGroup:
    Type: AWS::RDS::DBParameterGroup
    Properties:
      Description: !Sub ${ProjectName}-${Environment}-rds-pg
      Family: !Sub postgres${PostgreSQLMajorVersion}
      Parameters:
        # SQLの経過時間をログとして残す
        # 1なのでTrue
        log_duration: 1
        # SQLの実行に要した時間をログに記録
        # 10000を指定したので10000msもしくはそれ以上長くかかった全てのSQL文がログとして残る
        log_min_duration_statement: 10000
        # どのSQL文をログに記録するか決める。allなので全て
        log_statement: all
        # タイムゾーン
        timezone: Asia/Tokyo
```

### RDSDBInstance
RDSインスタンスの設定を行います
```rds.yml
  # -------------------------------------
  # DB Instance
  # -------------------------------------
  RDSDBInstance:
    DeletionPolicy: Delete
    UpdateReplacePolicy: Delete
    Type: AWS::RDS::DBInstance
    Properties:
      Engine: postgres
      EngineVersion: !Sub ${PostgreSQLMajorVersion}.${PostgreSQLMinorVersion}
      DBInstanceIdentifier: !Sub ${ProjectName}-${Environment}-rds
      MasterUsername: !Ref RDSDBMasterUserName
      MasterUserPassword: !Ref RDSDBMasterUserPassword
      DBInstanceClass: !Ref RDSDBInstanceClass
      StorageType: !Ref RDSDBInstanceStorageType
      AllocatedStorage: !Ref RDSDBInstanceStorageSize
      MultiAZ: !Ref MultiAZEnabled
      DBSubnetGroupName: !Ref RDSDBSubnetGroup
      PubliclyAccessible: false
      VPCSecurityGroups:
        - !Ref RDSDBSecurityGroupID
      DBName: !Ref RDSDBName
      DBParameterGroupName: !Ref RDSDBParameterGroup
      BackupRetentionPeriod: !Ref BackupRetentionPeriod
      PreferredBackupWindow: !Ref PreferredBackupWindow
      CopyTagsToSnapshot: true
      StorageEncrypted: true
      EnablePerformanceInsights: !Ref EnablePerformanceInsights
      MonitoringInterval: 60
      MonitoringRoleArn: !GetAtt RDSMonitoringRole.Arn
      EnableCloudwatchLogsExports: [postgresql]
      AutoMinorVersionUpgrade: !Ref AutoMinorVersionUpgradeEnabled
      PreferredMaintenanceWindow: !Ref PreferredMaintenanceWindow
      DeletionProtection: !Ref DeletionProtectionEnabled
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-rds
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

#### Property
前述で設定したParametersの値を踏まえてRDSDBInstanceのPropertyの一覧を記載します
今回はあくまで一例ですのでプロジェクトに応じて値を設定していただければと思います

|パラメータ名|説明|値・デフォルト値|
|--|--|--|
|Engine|DBの種類|postgres|
|EngineVersion|DBのバージョン|15.2|
|MasterUsername|DBのマスターユーザ名|postgres|
|MasterUserPassword|DBのマスターパスワード|postgres|
|DBInstanceClass|DBインスタンスのクラス(例:db.m4.large)|db.t3.small|
|StorageType|DB用のストレージの種類(例:gp2)|gp3|
|AllocatedStorage|DBインスタンスに割り当てるストレージの容量|20GB|
|MultiAZ|複数のAZでインスタンスを生成するかどうか|false|
|DBSubnetGroupName|サブネットグループの設定|サブネットグループ|
|PubliclyAccessible|RDSがインターネットからアクセス可能かどうか|false|
|VPCSecurityGroups|RDSのセキュリティグループ|後述のsg.ymlで作成したSGのID|
|DBName|DB名|postgres|
|DBParameterGroupName|パラメータグループの設定|パラメータグループ|
|BackupRetentionPeriod|自動バックアップを保持する日数|35日|
|PreferredBackupWindow|自動バックアップが作成される毎日の時間帯|19:00-19:30|
|CopyTagsToSnapshot|DBインスタンスのスナップショットにタグをコピーするかどうか|true|
|StorageEncrypted|DBインスタンスを暗号化するかどうか|今回はtrueにします|
|EnablePerformanceInsights|パフォーマンスインサイトを有効にするかどうか<br>Postgresだと全てのインスタンスタイプをサポートしていますが、MySQLとMariaDBだとインスタンスによってサポートされていなかったりするので注意が必要です<br>https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/USER_PerfInsights.Overview.Engines.html|true|
|MonitoringInterval|DB インスタンスまたはリードレプリカのメトリクスが収集される間隔 (秒単位) |60|
|MonitoringRoleArn|モニタリング用のロールのArn|モニタリング用のロールのArn|
|EnableCloudwatchLogsExports|RDSのログをCloudWatchに出力する設定|[postgresql]
|AutoMinorVersionUpgrade|マイナーバージョンへのアップグレードの有効化|true|
|PreferredMaintenanceWindow|システムメンテナンスが可能な時間帯|sun:20:00-sun:20:30|
|DeletionProtection|DBの削除保護を有効化するかどうか|false|



## sg.yml
今回はECS FagrateとRDS用のセキュリティグループを作成します
ECSからRDSへ5432番ポートへのインバウンドアクセスを許可します

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
### SG
RDS用のSGのStackを作成します
その際にすでにVPCを作成されているのであればドロップダウンから選択します
![スクリーンショット 2023-09-14 19.27.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/42f76457-c1f9-4d04-2594-b47b6aad7d66.png)

RDSのSGが以下のように作成されたら成功です
![スクリーンショット 2023-09-14 19.29.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/71793124-48f2-575c-4de7-6f8ca782d5cc.png)
![スクリーンショット 2023-09-14 19.46.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f8678f7b-1209-fd9f-6071-76504899045f.png)
![スクリーンショット 2023-09-14 19.46.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3d9d03d5-7bc5-bb3a-7420-d5e6582ff358.png)

### RDS
RDSのStackを作成します
![スクリーンショット 2023-09-10 15.52.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0e3c60ba-877e-da20-ffea-d2935c3c9309.png)

以下のように作成されたら成功です
![スクリーンショット 2023-09-14 19.54.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bdb97ee4-d439-2e24-ffeb-3ec9402686df.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/quickref-rds.html

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-rds-dbinstance.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-rds-dbparametergroup.html

https://docs.aws.amazon.com/ja_jp/AmazonRDS/latest/UserGuide/parameter-groups-overview.html
