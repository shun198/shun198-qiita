---
title: CloudFormationを使ってLambdaとSQSを作成しよう！
tags:
  - AWS
  - S3
  - CloudFormation
  - lambda
  - sqs
private: false
updated_at: '2024-08-27T15:02:15+09:00'
id: 658137693060d4f8503e
organization_url_name: null
slide: false
---
## 概要
CloudFormationを使って非同期処理でよく使用するLambdaとSQSを作成する方法について解説していきます

## 実装
- Lambdaを格納するS3
- SQS
- SQSのメッセージをトリガーに実行するLambda

の3種類のリソースをCloudFormationで作成します

## Lambdaを格納するS3
Lambdaを格納するS3を作成していきます
バケット内のオブジェクトは非公開にします

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket For Lambda"

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
# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: shun198)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be enter."
    Default: shun198
  Environment:
    Description: "Select the environment."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."

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
# Output Parameters
# -------------------------------------
Outputs:
  LambdaArchiveBucketName:
    Value: !Ref LambdaArchiveBucket
  LambdaArchiveBucketArn:
    Value: !GetAtt  LambdaArchiveBucket.Arn

```

### SQSの作成
SQSのqueueとロールを作成していきます

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "SQS Stack For Lambda Function"

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
          default: "SQS Configuration"
        Parameters:
          - SQSQueueName

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name (ex: shun198)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered"
    Default: shun198
  Environment:
    Description: "Select the environment"
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be selected"
  SQSQueueName:
    Description: "Enter the queue name (ex: shun198-dev-sqs.fifo)"
    Type: String
  MessageRetentionPeriod:
    Description: "Enter the time to hold messages as a queue (default: 3600)"
    Type: Number
    Default: 3600
    MinValue: 60
    MaxValue: 1209600
    ConstraintDescription: "MessageRetentionPeriod must be entered between the values 60 - 1209600"

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # For SQS
  Queue:
    Type: AWS::SQS::Queue
    Properties:
      FifoQueue: true
      ContentBasedDeduplication: true
      QueueName: !Ref SQSQueueName
      MessageRetentionPeriod: !Ref MessageRetentionPeriod
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  # For SQS Access Policy
  QueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - sqs:SendMessage
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
            Resource: !GetAtt Queue.Arn
      Queues:
        - !Ref Queue

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  QueueArn:
    Value: !GetAtt Queue.Arn
  QueueUrl:
    Value: !Ref Queue
```

### Lambdaの作成
SQSをトリガーに実行するLambdaを作成します
その際は`AWS::Lambda::EventSourceMapping`を使用して作成したSQSのArnを指定します

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "Lambda Function Stack"

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
          - Handler
          - MemorySize
          - Timeout
          - Runtime

# -------------------------------------
# Input parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: shun198)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered."
    Default: shun198
  Environment:
    Description: "Select the environment."
    Type: String
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be selected."
  LambdaArchiveBucketName:
    Description: "Enter the S3 bucket name for Lambda zip archive."
    Type: String
  LambdaArchiveBucketObjectKey:
    Description: "Enter the S3 bucket object key for Lambda zip archive."
    Type: String
  Handler:
    Description: "Enter the Lambda function name to delete data. (default: lambda_function.lambda_handler)"
    Type: String
    Default: lambda_function.lambda_handler
  MemorySize:
    Description: "Enter the Lambda function memory size. (MiB) (default: 128)"
    Type: Number
    Default: 128
    MinValue: 128
    MaxValue: 10240
  Timeout:
    Description: "Enter the Lambda function timeout second. (default: 30)"
    Type: Number
    Default: 30
    MinValue: 1
    MaxValue: 900
  Runtime:
    Description: "Enter the Lambda function runtime."
    Type: String
    AllowedValues:
      - python3.11
    Default: python3.11
  QueueArn:
    Description: "Enter the SQS queue ARN (ex: arn:aws:sqs:<aws_region>:<aws_account_id>:shun198-dev-sqs.fifo)"
    Type: String
# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Lambda Function
  # -------------------------------------
  Lambda:
    Type: AWS::Lambda::Function
    Properties:
      Code:
        S3Bucket: !Ref LambdaArchiveBucketName
        S3Key: !Ref LambdaArchiveBucketObjectKey
      FunctionName: !Sub ${ProjectName}-${Environment}
      Description: "サンプル用Lambda 関数"
      Handler: !Ref Handler
      MemorySize: !Ref MemorySize
      Role: !GetAtt LambdaRole.Arn
      Runtime: !Ref Runtime
      Timeout: !Ref Timeout
      PackageType: Zip
  LambdaPermission:
    Type: AWS::Lambda::Permission
    Properties:
      Action: lambda:InvokeFunction
      FunctionName: !GetAtt Lambda.Arn
      Principal: cloudformation.amazonaws.com

  # -------------------------------------
  # Lambda Trigger
  # -------------------------------------
  LambdaTrigger:
    Type: AWS::Lambda::EventSourceMapping
    Properties:
      FunctionName: !GetAtt Lambda.Arn
      BatchSize: 1
      EventSourceArn: !Ref QueueArn

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  LambdaRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub LambdaRole-${ProjectName}-${Environment}-sample
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: lambda.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/service-role/AWSLambdaSQSQueueExecutionRole
      Policies:
        - PolicyName: !Sub LambdaAccess-${ProjectName}-${Environment}
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
                  - arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/lambda/${Lambda}:*
                  - {
                      Lambda: !Sub "${ProjectName}-${Environment}",
                    }

```

今回は試しにメッセージを取得できているか確かめるために以下のようにコードを記載します
`event["Records"][0]["body"]`からSQSのqueueに送られたメッセージを取得できます

```lambda_function.py
def lambda_handler(event, context) -> str:
    """Lambdaのエントリーポイント
    """
    print(event)
    print(event["Records"][0]["body"])
    return "finish lambda"

```

SQSのメッセージをトリガーにLambdaを実行すると、eventの中身は以下のようになります

```
{'Records': [{'messageId': 'f4fbf98f-6938-4a50-bf89-b8baf721091a', 'receiptHandle': 'AQEBre6LuLkgQ+CyxggTIbqj2UKUldXQOiexYg4pcJ6cd8noQ+XErrT0AxZQLJX6i/vWFvB3/2Nmwn/lEhoOAEerGNO4V3l8bfzshwpHPfHoA+M5SelfMnw+EpU/pbhQ4mubAbYeBEfyLr+uBdI6s5WnTlwnNmaNgWPNhwemQkGeCIp0FhWQ7NrnZ6O4DITYfJ+wSbk/SC912oR5xBrnFe1567hk5Rxm9Ni7E0KSlxpjOnNTV57JHrn53yTxr1af3jYAHrprmnUo7WJD1diUNaivkMx5udPW9WaqWHzij0VZ/DQ=', 'body': 'サンプルテスト', 'attributes': {'ApproximateReceiveCount': '1', 'SentTimestamp': '1724737745977', 'SequenceNumber': '18888276936679663616', 'MessageGroupId': 'sample', 'SenderId': 'ABCABCABCABCABCABCABC:sample-user', 'MessageDeduplicationId': 'a327ec022f273f96eae95dc47bc07b894e7facf9400542fb85e946d0a56d8b30', 'ApproximateFirstReceiveTimestamp': '1724737745977'}, 'messageAttributes': {}, 'md5OfBody': 'cab883bbf802ce03b8002ceefbc0a9ad', 'eventSource': 'aws:sqs', 'eventSourceARN': 'arn:aws:sqs:ap-northeast-1:012345678901:shun198-dev-sqs.fifo', 'awsRegion': 'ap-northeast-1'}]}
```

## 実際に作成してみよう！
必要なリソースをCloudFormationを使って作成します
![スクリーンショット 2024-08-27 13.44.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9251eab0-ccf2-d61f-b6c7-28a8185bbdee.png)

![スクリーンショット 2024-08-27 14.59.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24b16ff5-f539-9458-546f-e3c7f0b2ae40.png)

## SQSにメッセージを送信してみよう！
以下のようにコンソール上でSQSのqueueにメッセージを送信します
![スクリーンショット 2024-08-27 14.18.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/666eaa3f-3598-9bca-7f7d-3c444dfb06ca.png)

送信後、CloudWatchでログを確認します
![スクリーンショット 2024-08-27 14.38.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9dcb481e-78d5-8707-d544-538c618efff9.png)

以下のようにSQSをトリガーにLambdaが実行され、送信したメッセージが出力されたら成功です
![スクリーンショット 2024-08-27 14.49.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0ddb7075-c2d1-4c81-813d-68a05ad65b44.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html

https://docs.aws.amazon.com/ja_jp/lambda/latest/dg/with-sqs.html

https://zenn.dev/shimo_s3/articles/d191b878bac4c7
