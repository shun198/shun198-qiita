---
title: CloudFormationとPyplateを使ってSecurityGroupのIngressに指定したIPアドレスを登録しよう！
tags:
  - AWS
  - S3
  - CloudFormation
  - SecurityGroup
  - lambda
private: false
updated_at: '2024-05-16T15:47:16+09:00'
id: 9c992e54fb656a0e9dfe
organization_url_name: null
slide: false
---
## 概要
CloudFormationマクロの一つであるPyplateを使うことでCloudFormationテンプレート(yaml)内にPythonのコードを実行することができます
今回はPyplateを使ってSecurityGroupのIngressに指定したIPアドレスを登録する方法を例に解説します

## 前提
- VPCを作成済み
- 今回はPythonを使用します

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

## Pyplate用のコードを作成
Pyplateのマクロを実行するコードです
コードは以下のものを使用しています

https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/CloudFormation/MacrosExamples/PyPlate/handler.py

こちらをzipファイルとして圧縮します

```lambda_function.py
import traceback
import json

def obj_iterate(obj, params):
    if isinstance(obj, dict):
        # 辞書の各キーと値に対して再帰的に処理を行う
        for k, v in obj.items():
            obj[k] = obj_iterate(v, params)
    elif isinstance(obj, list):
        # リスト内の各要素に対して再帰的に処理を行う
        for i, v in enumerate(obj):
            obj[i] = obj_iterate(v, params)
    elif isinstance(obj, str) and obj.startswith("#!PyPlate"):
        # 特定の条件を満たす文字列を処理
        params['output'] = None
        exec(obj, params)
        obj = params['output']
    return obj

def lambda_handler(event, context):
    # 受け取ったイベント情報を出力
    print(json.dumps(event))
    macro_response = {
        "requestId": event["requestId"],
        "status": "success"
    }
    try:
        params = {
            "params": event["templateParameterValues"],
            "template": event["fragment"],
            "account_id": event["accountId"],
            "region": event["region"]
        }
        # 入力のテンプレートを処理して更新
        macro_response["fragment"] = obj_iterate(event["fragment"], params)
    except Exception as e:
        # エラーが発生した場合、エラーメッセージを記録
        traceback.print_exc()
        macro_response["status"] = "failure"
        macro_response["errorMessage"] = str(e)
    return macro_response
```

後ほど作成するLambdaを実行するためにLambda用のS3`lambda-pyplate-transform`フォルダを作成し、そこにPyplateのコードが格納されたzipファイルをに格納します

![スクリーンショット 2024-05-01 14.00.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/425d86e4-3b12-27ce-07a7-dbf718cd1244.png)

![スクリーンショット 2024-05-01 14.01.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2091eb25-c1bd-d80d-3a9a-9d1cb794ff68.png)

## Pyplate用Lambdaの作成
Pyplateを実行するLambdaを作成します
以下のようにCloudFormationテンプレート内のマクロが実行された際に呼ばれてほしいLambdaを指定します

```yml
  PyPlateTransform:
    Type: AWS::CloudFormation::Macro
    Properties:
      Name: PyPlate
      Description: "Processes inline python in templates"
      FunctionName: !GetAtt PyPlateTransformLambdaFunction.Arn
```

```lambda-for-pyplate-transform-factory.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack For PyPlate Transform Factory"

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
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select"
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

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Lambda Function
  # -------------------------------------
  PyPlateTransformLambdaFunction:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        # lambda-pyplate-transform/lambda_function.py.zipを指定
        S3Key: !Ref LambdaArchiveBucketObjectKey
      FunctionName: !Sub ${ProjectName}-${Environment}-pyplate-transform
      Description: "CloudFormation で PyPlate マクロを使用するための Lambda 関数"
      Handler: !Ref LambdaHandler
      MemorySize: !Ref LambdaMemorySize
      Role: !GetAtt TransformLambdaExecutionRole.Arn
      Runtime: !Ref LambdaRuntime
      Timeout: !Ref LambdaTimeout
      PackageType: Zip
  PyPlateTransformFunctionPermissions:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt PyPlateTransformLambdaFunction.Arn
      Principal: cloudformation.amazonaws.com
  PyPlateTransform:
    Type: AWS::CloudFormation::Macro
    Properties:
      Name: PyPlate
      Description: "Processes inline python in templates"
      FunctionName: !GetAtt PyPlateTransformLambdaFunction.Arn

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  TransformLambdaExecutionRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRoleForPyPlateTransform-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      Policies:
        - PolicyName: !Sub LambdaAccessForPyPlateTransform-${ProjectName}-${Environment}
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
                  - {LambdaFunctionName: !Sub "${ProjectName}-${Environment}-pyplate-transform"}
```

以下のように作成できたら成功です
![スクリーンショット 2024-05-01 14.13.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/94ed0fed-6e40-e974-5a37-22ba1033adb7.png)

## セキュリティグループ
今回はALBのセキュリティグループ内にインバウンドルールを許可するIPアドレスを登録したいのでセキュリティグループ用のテンプレートを作成します
まず、Pyplateのマクロを有効化するために以下の記述を記載します
```yml
# カスタムマクロの有効化
Transform: PyPlate
```

セキュリティグループのインバウンドルールに指定したIPアドレスとその詳細(desc)をPyplateを使用して追加するよう設定します
for文内で使用してパラメータとして指定したManagementIPAddressとManagementIPDescriptionの値がoutput内に代入されていきます
このようにPyplateを使うことで複数以上のIPアドレスをSecurityGroupIngressに追加したい場合でも下記の記述だけで完結する上にコードで管理できます

```yml
      SecurityGroupIngress: |
          #!PyPlate
          import json
          output = [
              {
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "CidrIp": ip,
                "Description": desc
              }
              for ip, desc in zip(params["ManagementIPAddress"], params["ManagementIPDescription"])
          ]
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-alb-for-fargate-sg
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

```sg.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Security Group Stack"
# カスタムマクロの有効化
Transform: PyPlate

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
          default: "Security Group Configuration"
        Parameters:
          - VPCID
          - ManagementIPAddress
          - ManagementIPDescription

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
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
  VPCID:
    Description: "Enter the VPC ID for create security groups"
    Type: AWS::EC2::VPC::Id
  ManagementIPAddress:
    Description: "Enter the IP addresses for management separated by commas (ex: 0.0.0.0/32,1.1.1.1/32)"
    Type: CommaDelimitedList
  ManagementIPDescription:
    Description: "Enter the descriptions for the management IP addresses separated by commas (ex: from xxxx,from xxxx)"
    Type: CommaDelimitedList

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
      SecurityGroupIngress: |
          #!PyPlate
          import json
          output = [
              {
                "IpProtocol": "tcp",
                "FromPort": 8080,
                "ToPort": 8080,
                "CidrIp": ip,
                "Description": desc
              }
              for ip, desc in zip(params["ManagementIPAddress"], params["ManagementIPDescription"])
          ]
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-alb-for-fargate-sg
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ALBSGIngressHTTPS:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref ALBSG
      IpProtocol: tcp
      FromPort: 443
      ToPort: 443
      CidrIp: 0.0.0.0/0
      Description: "from client"

  # For Fargate
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
  FargateSGIngressHTTPS:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref FargateSG
      IpProtocol: tcp
      FromPort: 443
      ToPort: 443
      SourceSecurityGroupId: !Ref ALBSG
      Description: "from alb"
  FargateSGIngressForInternalALBHTTPS:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref FargateSG
      IpProtocol: tcp
      FromPort: 443
      ToPort: 443
      SourceSecurityGroupId: !Ref InternalALBSG
      Description: "from internal alb"

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
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  RDSForPostgreSQLSGIngress:
    Type: AWS::EC2::SecurityGroupIngress
    Properties:
      GroupId: !Ref RDSForPostgreSQLSG
      IpProtocol: tcp
      FromPort: 5432
      ToPort: 5432
      SourceSecurityGroupId: !Ref FargateSG
      Description: "from fargate"

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  ALBSG:
    Description: "Security Group For ALB"
    Value: !Ref ALBSG
  FargateSG:
    Description: "Security Group For ECS Fargate with ALB"
    Value: !Ref FargateSG
  RDSForPostgreSQLSG:
    Description: "Security Group For RDS (PostgresSQL)"
    Value: !Ref RDSForPostgreSQLSG

```

## 実際に実装してみよう！
セキュリティグループを作成します
今回はtest_user01が使用する0.0.0.0/32のIPアドレス、test_user02が使用する1.1.1.1/32のIPアドレスを登録してみます

![スクリーンショット 2024-05-16 15.15.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7f61b72a-c8ff-191e-e6e2-c7bd9f07debf.png)

以下のようにIPアドレスと説明が動的に適用されていたら成功です
![スクリーンショット 2024-05-16 15.45.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1ae20d2a-2481-858f-5ffc-9da1b44b4ace.png)

## 参考
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudformation-macro.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-securitygroupingress.html

https://github.com/aws-cloudformation/aws-cloudformation-templates/blob/main/CloudFormation/MacrosExamples/PyPlate/handler.py

https://qiita.com/TS_Koike/items/95135e112760ab6d6f91
