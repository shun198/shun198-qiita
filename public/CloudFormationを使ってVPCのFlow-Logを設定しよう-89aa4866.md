---
title: CloudFormationを使ってVPCのFlow Logを設定しよう！
tags:
  - AWS
  - S3
  - CloudFormation
  - vpc
  - FlowLogs
private: false
updated_at: '2024-04-08T10:48:17+09:00'
id: 89aa4866cf0bcf5efd2b
organization_url_name: null
slide: false
---
## 概要
CloudFormationを使ってVPCのFlow Logを作成し、ログを
- CloudWatch
- S3

へ保存する方法について解説します

## 前提
- VPCを作成済み

## VPC Flow Logとは
VPCのネットワークインターフェイスとの間で行き来するIPトラフィックに関する情報をキャプチャできるようにする機能です
フローログデータは
- CloudWatch
- S3またはAmazon Data Firehose

に発行できます
フローログを作成したら、設定した
- ロググループ
- バケット、または配信ストリーム

のフローログレコードを取得して表示できます

VPC Flow Logを設定すると以下のメリットがあります
- 制限の過度に厳しいセキュリティグループルールを診断できる
- インスタンスに到達するトラフィックをモニタリングできる
- ネットワークインターフェイスに出入りするトラフィックの方向を決定できる

## 実装
- CloudWatch
- S3

用のFlow Logの作成方法の順に説明します

```vpc-flow-log.yml
  # -------------------------------------
  # VPC FlowLogs
  # -------------------------------------
  # For CW Logs
  VPCFlowLogToCWLog:
    Type: AWS::EC2::FlowLog
    Properties:
      DeliverLogsPermissionArn: !GetAtt VPCFlowLogsRoleForCWLogs.Arn
      LogDestinationType: cloud-watch-logs
      LogGroupName: !Ref VPCFlowLogGroup
      ResourceId: !Ref VPC
      ResourceType: VPC
      TrafficType: ALL
  VPCFlowLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub /aws/vpc/flowlogs/${ProjectName}-${Environment}-vpc
      RetentionInDays: 30
  VPCFlowLogsRoleForCWLogs:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub VPCFlowLogsRoleForCWLogs-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - vpc-flow-logs.amazonaws.com
            Action:
              - sts:AssumeRole
      Policies:
        - PolicyName: !Sub VPCFlowLogsRoleAccessForCWLogs-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - logs:DescribeLogGroups
                  - logs:DescribeLogStreams
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/vpc/flowlogs/${ProjectName}-${Environment}-vpc:*

  # For S3
  VPCFlowLogToS3:
    DependsOn: VPCFlowLogBucket
    Type: AWS::EC2::FlowLog
    Properties:
      LogDestinationType: s3
      LogDestination: !GetAtt VPCFlowLogBucket.Arn
      ResourceId: !Ref VPC
      ResourceType: VPC
      TrafficType: ALL
  VPCFlowLogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${ProjectName}-${Environment}-vpc-flowlogs
      OwnershipControls:
        Rules:
          - ObjectOwnership: ObjectWriter
      AccessControl: LogDeliveryWrite
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: TransitionToGlacierAfter365Days
            Status: Enabled
            Transitions:
              - TransitionInDays: 365
                StorageClass: GLACIER
          - Id: ExpireAfter5Years
            Status: Enabled
            ExpirationInDays: 1825
```

### CloudWatch
CloudWatchにFlow Logを保存するのでCloudWatchのロググループとCloudWatch用のロール及びポリシーを作成します
LogDestinationTypeをcloud-watch-logsにします
また、DeliverLogsPermissionArnをCloudWatch用のロールのArnを指定します
CloudWatch、S3ともにResourceTypeをVPCにします

```yaml
  # For CW Logs
  VPCFlowLogToCWLog:
    Type: AWS::EC2::FlowLog
    Properties:
      DeliverLogsPermissionArn: !GetAtt VPCFlowLogsRoleForCWLogs.Arn
      LogDestinationType: cloud-watch-logs
      LogGroupName: !Ref VPCFlowLogGroup
      ResourceId: !Ref VPC
      ResourceType: VPC
      TrafficType: ALL
  VPCFlowLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub /aws/vpc/flowlogs/${ProjectName}-${Environment}-vpc
      RetentionInDays: 30
  VPCFlowLogsRoleForCWLogs:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub VPCFlowLogsRoleForCWLogs-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - vpc-flow-logs.amazonaws.com
            Action:
              - sts:AssumeRole
      Policies:
        - PolicyName: !Sub VPCFlowLogsRoleAccessForCWLogs-${ProjectName}-${Environment}
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - logs:CreateLogGroup
                  - logs:CreateLogStream
                  - logs:PutLogEvents
                  - logs:DescribeLogGroups
                  - logs:DescribeLogStreams
                Resource: !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:/aws/vpc/flowlogs/${ProjectName}-${Environment}-vpc:*
```

### S3
S3にFlow Logを保存するのでS3用のバケットとS3用のロール及びポリシーを作成します
LogDestinationTypeをs3にします
また、LogDestinationをS3のArnを指定します
今回はバケットを公開したくないのでBucketEncryptionやPublicAccessBlockConfigurationなどの設定を行います
余談ですが、LifecycleConfigurationを使って1年間はS3に保存され、1年を経過したらGlacierに4年間保存する設定を行なっております

```yaml
  # For S3
  VPCFlowLogToS3:
    DependsOn: VPCFlowLogBucket
    Type: AWS::EC2::FlowLog
    Properties:
      LogDestinationType: s3
      LogDestination: !GetAtt VPCFlowLogBucket.Arn
      ResourceId: !Ref VPC
      ResourceType: VPC
      TrafficType: ALL
  VPCFlowLogBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub ${ProjectName}-${Environment}-vpc-flowlogs
      OwnershipControls:
        Rules:
          - ObjectOwnership: ObjectWriter
      AccessControl: LogDeliveryWrite
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      LifecycleConfiguration:
        Rules:
          - Id: TransitionToGlacierAfter365Days
            Status: Enabled
            Transitions:
              - TransitionInDays: 365
                StorageClass: GLACIER
          - Id: ExpireAfter5Years
            Status: Enabled
            ExpirationInDays: 1825
```

## 実際にログを確認してみよう！
VPCのフローログにアクセスし、以下のようにフローログが作成されたら成功です
![スクリーンショット 2024-04-08 10.24.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6b238018-c29d-d611-d1d3-1bbfbdfd084e.png)

### CloudWatch
cloud-watch-logsの連絡先をクリックすると以下の画面に遷移します
![logstream.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a0ed2581-b5a2-dfa2-5f45-b2eee7e25fab.png)

以下のようにFlow Logが表示されたら成功です
![log-event.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/823c9101-fd19-53b3-8850-dd56fb1de754.png)

### S3
S3の連絡先をクリックすると以下の画面に遷移します
![スクリーンショット 2024-04-08 10.27.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b234f5fd-5f2a-311b-faf4-405abcefc94f.png)

最新のフォルダにアクセスし、以下のようにFlow Logが表示されたら成功です
![スクリーンショット 2024-04-08 10.28.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/324c078a-96e6-72e1-afc4-75e9b3e26396.png)

## 参考
https://docs.aws.amazon.com/ja_jp/vpc/latest/userguide/flow-logs.html

https://www.sunnycloud.jp/column/20221115-01/
