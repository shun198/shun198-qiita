---
title: CloudFormationを使ってALBとCloudFront用のWAFを作成しよう！
tags:
  - AWS
  - CloudFormation
  - CloudFront
  - Kinesis
  - ALB
private: false
updated_at: '2024-06-21T08:12:25+09:00'
id: 53ab052ac6d576e6fd35
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はCloudFormationを使って
- ALB
- CloudFront

用のWAFを作成します

## 前提
- ALBとCloudFrontを構築済み

## ディレクトリ構成
```
tree
.
└── templates
    ├── network
    |   └── cloudfront.yml
    └── security
        ├── waf-for-alb.yml
        └── waf-for-cloudfront.yml
```

## WAF
### ALB用のWAFの作成

```waf-for-alb.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "WAFv2 For ALB"

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
          default: "WAF Configuration"
        Parameters:
          - AllowIPAddresses
          - WebACLAssociationArn
          - TargetALBName

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
  AllowIPAddresses:
    Description: "Enter the IP address for IP whitelist separated by commas (ex: 0.0.0.0/32,1.1.1.1/32,2.2.2.2/32)"
    Type: CommaDelimitedList
  WebACLAssociationArn:
    Description: "Enter the Target ARN for WAFv2 Web ACL Association (ex: arn:aws:elasticloadbalancing:ap-northeast-1:12345678)"
    Type: String
  TargetALBName:
    Description: "Enter the target ALB Name for WAFv2 Web ACL Association"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # WAFv2 S3 Bucket
  # -------------------------------------
  WAFLogsS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub aws-waf-logs-for-${TargetALBName}
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

  # -------------------------------------
  # WAFv2 ACL
  # -------------------------------------
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-alb-waf
      DefaultAction:
        Allow: {}
      Scope: REGIONAL
      VisibilityConfig:
        CloudWatchMetricsEnabled: true
        MetricName: !Sub ${ProjectName}-${Environment}-waf
        SampledRequestsEnabled: true
      Rules:
        - Name: IPAddressWhitelistRule
          Priority: 10
          Statement:
            RateBasedStatement:
              AggregateKeyType: IP
              Limit: 100
              ScopeDownStatement:
                NotStatement:
                  Statement:
                    IPSetReferenceStatement:
                      Arn: !GetAtt IPWhitelist.Arn
          Action:
            Count: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: IPAddressWhitelistRule
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesAmazonIpReputationList
          Priority: 20
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesAmazonIpReputationList
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesAmazonIpReputationList
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesAnonymousIpList
          Priority: 30
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesAnonymousIpList
              ExcludedRules:
                - Name: HostingProviderIPList
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesAnonymousIpList
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesCommonRuleSet
          Priority: 40
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesCommonRuleSet
              ExcludedRules:
                - Name: SizeRestrictions_BODY
                - Name: CrossSiteScripting_BODY
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesCommonRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesKnownBadInputsRuleSet
          Priority: 50
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesKnownBadInputsRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesKnownBadInputsRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesLinuxRuleSet
          Priority: 60
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesLinuxRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesLinuxRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesUnixRuleSet
          Priority: 70
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesUnixRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesUnixRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesSQLiRuleSet
          Priority: 80
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesSQLiRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesSQLiRuleSet
            SampledRequestsEnabled: true

  # -------------------------------------
  # White IP Address
  # -------------------------------------
  IPWhitelist:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: Custom-IPAddress-Whitelist-Prd
      Scope: REGIONAL
      IPAddressVersion: IPV4
      Addresses: !Ref AllowIPAddresses

  # -------------------------------------
  # WebACLAssociation
  # -------------------------------------
  WebACLAssociation:
    Type: AWS::WAFv2::WebACLAssociation
    Properties:
      ResourceArn: !Ref WebACLAssociationArn
      WebACLArn: !GetAtt WebACL.Arn

  # -------------------------------------
  # CloudWatch Logs Log Group (WAFv2)
  # -------------------------------------
  WAFLogsDeliveryStreamLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub aws-waf-logs-for-${TargetALBName}
      RetentionInDays: 90
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  WAFLogsSubscriptionFilter:
    Type: AWS::Logs::SubscriptionFilter
    Properties:
      RoleArn: !GetAtt CloudWatchLogsRole.Arn
      LogGroupName: !Ref WAFLogsDeliveryStreamLogGroup
      FilterPattern: ""
      DestinationArn: !GetAtt WAFv2ForALBDeliveryStream.Arn

  # -------------------------------------
  # WAFv2 Log Config
  # -------------------------------------
  WAFLogsConfig:
    DependsOn: WebACLAssociation
    Type: AWS::WAFv2::LoggingConfiguration
    Properties:
      LogDestinationConfigs:
        - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-${TargetALBName}
      ResourceArn: !GetAtt WebACL.Arn

  # -------------------------------------
  # Kinesis Data Firehose Delivery Stream
  # -------------------------------------
  WAFv2ForALBDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: !Sub kinesis-s3-for-aws-waf-logs-${TargetALBName}
      DeliveryStreamEncryptionConfigurationInput:
        KeyType: AWS_OWNED_CMK
      ExtendedS3DestinationConfiguration:
        RoleARN: !GetAtt KinesisDataFirehoseRole.Arn
        BucketARN: !GetAtt WAFLogsS3Bucket.Arn
        BufferingHints:
          IntervalInSeconds: 300
          SizeInMBs: 5
        CompressionFormat: GZIP
        Prefix: ""
        ProcessingConfiguration:
          Enabled: false
        CloudWatchLoggingOptions:
          Enabled: true
          LogGroupName: /aws/kinesisfirehose/s3-delivery-stream
          LogStreamName: !Sub s3-delivery-waf-${TargetALBName}
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  CloudWatchLogsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CWLogsRoleForKinesisFirehose-aws-waf-${TargetALBName}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: !Sub logs.${AWS::Region}.amazonaws.com
            Action:
              - sts:AssumeRole
      Path: /service-role/
  CloudWatchLogsRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub CWLogsAccessForKinesisFirehose-aws-waf-${TargetALBName}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - firehose:*
            Resource:
              - !Sub arn:aws:firehose:${AWS::Region}:${AWS::AccountId}:*
          - Effect: Allow
            Action:
              - iam:PassRole
            Resource:
              - !GetAtt CloudWatchLogsRole.Arn
      Roles:
        - !Ref CloudWatchLogsRole
  # For Kinesis Data Firehose
  KinesisDataFirehoseRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub KinesisFirehoseRoleForS3-aws-waf-${TargetALBName}
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - firehose.amazonaws.com
            Action:
              - sts:AssumeRole
            Condition:
              StringEquals:
                sts:ExternalId: !Ref AWS::AccountId
      Path: /service-role/
      Policies:
        - PolicyName: !Sub KinesisFirehoseAccessForS3-aws-waf-${TargetALBName}
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:PutObject
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - logs:PutLogEvents
                Resource:
                  - !Sub arn:aws:s3:::aws-waf-logs-for-${TargetALBName}
                  - !Sub arn:aws:s3:::aws-waf-logs-for-${TargetALBName}/*
                  - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-${TargetALBName}:log-stream:*

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  WAFLogsS3BucketArn:
    Value: !GetAtt WAFLogsS3Bucket.Arn
  WebACLArn:
    Value: !GetAtt WebACL.Arn

```

1つずつ説明します

#### WAFのログを格納するS3の作成
ログを格納するS3を作成します
バケットの暗号化設定を有効化します
今回はAES256を使用します
S3の中にログが入るのでPublicAccessBlockConfiguration内にパブリックアクセスをブロックする設定を記載します
また、LifecycleConfigurationを使ってログのライフサイクルイベントを作成します
ログが生成されてから1年経過したらGLACIERへ移行し、5年経過したら無効化する設定をします

```yml
  # -------------------------------------
  # WAFv2 S3 Bucket
  # -------------------------------------
  WAFLogsS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub aws-waf-logs-for-${TargetALBName}
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

#### WebACLの作成
WebACLを作成します
ACLはAccess Control Listの略でネットワーク上のリソースなどへのアクセス可否の設定をリストとして列挙したものです
WebACLのRulesにアクセス可否の設定であるマネージドルールを記載します
Priorityはルールを適用する優先順位を表したもので数字が低いほど優先されます
PriorityはOSI参照モデルを基に決めるのが一般的で低レイヤーのルールから順に適用します
IPAddressWhitelistRuleを除く全てのルールはAWSが提供しているマネージドルールです
今回適用するルールは以下のとおりです

|ルール|グループ|説明|Priority|
|--|--|--|--|
|IPAddressWhitelistRule|カスタムルール|指定したIPアドレスからのアクセスを許可する|10|
|AWSManagedRulesAmazonIpReputationList|IP 評価ルールグループ|Amazon 内部脅威インテリジェンスに基づくルール<br>ボットやその他の脅威に関連付けられている IP アドレスをブロックする場合に便利|20|
|AWSManagedRulesAnonymousIpList|IP 評価ルールグループ|ビューワーIDの難読化を許可するサービスからのリクエストをブロックするルール|30|
|AWSManagedRulesCommonRuleSet|ベースラインルールグループ|ウェブアプリケーションに一般的に適用可能なルール<br>OWASP Top 10 などの OWASP の出版物に記載されている、リスクが高く一般的に発生するいくつかの脆弱性を含む、さまざまな脆弱性の悪用に対する保護が提供される|40|
|AWSManagedRulesKnownBadInputsRuleSet|ベースラインルールグループ|無効であることがわかっており脆弱性の悪用または発見に関連するリクエストパターンをブロックするルール|50|
|AWSManagedRulesLinuxRuleSet|ユースケース固有のルールグループ|Linux 固有のローカルファイルインクルージョン (LFI) 攻撃など、Linux 固有の脆弱性の悪用に関連するリクエストパターンをブロックするルール|60|
|AWSManagedRulesUnixRuleSet|ユースケース固有のルールグループ|POSIX および POSIX と同等のオペレーティングシステムに固有の脆弱性の悪用 (ローカルファイルインクルージョン (LFI) 攻撃など) に関連するリクエストパターンをブロックするルール|70|
|AWSManagedRulesSQLiRuleSet|ユースケース固有のルールグループ|SQL インジェクション攻撃などの SQL データベースの悪用に関連するリクエストパターンをブロックするルール|80|

```yml
  # -------------------------------------
  # WAFv2 ACL
  # -------------------------------------
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-alb-waf
      DefaultAction:
        Allow: {}
      Scope: REGIONAL
      VisibilityConfig:
        CloudWatchMetricsEnabled: true
        MetricName: !Sub ${ProjectName}-${Environment}-waf
        SampledRequestsEnabled: true
      Rules:
        - Name: IPAddressWhitelistRule
          Priority: 10
          Statement:
            RateBasedStatement:
              AggregateKeyType: IP
              Limit: 100
              ScopeDownStatement:
                NotStatement:
                  Statement:
                    IPSetReferenceStatement:
                      Arn: !GetAtt IPWhitelist.Arn
          Action:
            Count: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: IPAddressWhitelistRule
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesAmazonIpReputationList
          Priority: 20
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesAmazonIpReputationList
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesAmazonIpReputationList
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesAnonymousIpList
          Priority: 30
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesAnonymousIpList
              ExcludedRules:
                - Name: HostingProviderIPList
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesAnonymousIpList
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesCommonRuleSet
          Priority: 40
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesCommonRuleSet
              ExcludedRules:
                - Name: SizeRestrictions_BODY
                - Name: CrossSiteScripting_BODY
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesCommonRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesKnownBadInputsRuleSet
          Priority: 50
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesKnownBadInputsRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesKnownBadInputsRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesLinuxRuleSet
          Priority: 60
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesLinuxRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesLinuxRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesUnixRuleSet
          Priority: 70
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesUnixRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesUnixRuleSet
            SampledRequestsEnabled: true
        - Name: AWS-AWSManagedRulesSQLiRuleSet
          Priority: 80
          Statement:
            ManagedRuleGroupStatement:
              VendorName: AWS
              Name: AWSManagedRulesSQLiRuleSet
          OverrideAction:
            None: {}
          VisibilityConfig:
            CloudWatchMetricsEnabled: true
            MetricName: AWSManagedRulesSQLiRuleSet
            SampledRequestsEnabled: true

```

#### IPアドレスのホワイトリストの作成
IPAddressWhitelistRuleを作成します
IPAddressWhitelistRuleではアクセスを許可するIPアドレスを設定します
CloudFormationで作成するときに入力したIPアドレスでのアクセスが許可されます

```yml
  # -------------------------------------
  # White IP Address
  # -------------------------------------
  IPWhitelist:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: Custom-IPAddress-Whitelist
      Scope: REGIONAL
      IPAddressVersion: IPV4
      Addresses: !Ref AllowIPAddresses
```

#### WebACLAssociationの作成
WebACLとALB(リージョナルアプリケーション)を連携する設定を行います
ただし、CloudFrontではWebACLAssociationを使用しないので後ほど説明します

```yml
  # -------------------------------------
  # WebACLAssociation
  # -------------------------------------
  WebACLAssociation:
    Type: AWS::WAFv2::WebACLAssociation
    Properties:
      ResourceArn: !Ref WebACLAssociationArn
      WebACLArn: !GetAtt WebACL.Arn

```

#### WAFのログの設定
ALBのWAF用のCloudWatch LogsのロググループとSubscriptionFilterを作成します
SubscriptionFilterに後ほど説明するKinesisを設定します
また、ALBとWebACLとの関連付けを行うためにWAFLogsConfigを設定します

```yml
  # -------------------------------------
  # CloudWatch Logs Log Group (WAFv2)
  # -------------------------------------
  WAFLogsDeliveryStreamLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub aws-waf-logs-for-${TargetALBName}
      RetentionInDays: 90
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  WAFLogsSubscriptionFilter:
    Type: AWS::Logs::SubscriptionFilter
    Properties:
      RoleArn: !GetAtt CloudWatchLogsRole.Arn
      LogGroupName: !Ref WAFLogsDeliveryStreamLogGroup
      FilterPattern: ""
      DestinationArn: !GetAtt WAFv2ForALBDeliveryStream.Arn

  # -------------------------------------
  # WAFv2 Log Config
  # -------------------------------------
  WAFLogsConfig:
    DependsOn: WebACLAssociation
    Type: AWS::WAFv2::LoggingConfiguration
    Properties:
      LogDestinationConfigs:
        - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-${TargetALBName}
      ResourceArn: !GetAtt WebACL.Arn
```


#### Kinesisの設定
Kinesisを使ってあるALBのWAFのログをCloudWatchからS3に保存する設定をします

```yml
  # -------------------------------------
  # Kinesis Data Firehose Delivery Stream
  # -------------------------------------
  WAFv2ForALBDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: !Sub kinesis-s3-for-aws-waf-logs-${TargetALBName}
      # 暗号化設定。今回はデフォルトのAWS_OWNED_CMKを指定
      DeliveryStreamEncryptionConfigurationInput:
        KeyType: AWS_OWNED_CMK
      ExtendedS3DestinationConfiguration:
        RoleARN: !GetAtt KinesisDataFirehoseRole.Arn
        BucketARN: !GetAtt WAFLogsS3Bucket.Arn
        BufferingHints:
          # 受信データを宛先に配信する前にバッファリングする時間の長さ (秒単位)
          IntervalInSeconds: 300
          # 宛先に配信する前に受信データに使用するバッファのサイズ (MB 単位)
          SizeInMBs: 5
        # 圧縮形式。今回はGZIPを使用
        CompressionFormat: GZIP
        Prefix: ""
        ProcessingConfiguration:
          Enabled: false
        CloudWatchLoggingOptions:
          Enabled: true
          LogGroupName: /aws/kinesisfirehose/s3-delivery-stream
          LogStreamName: !Sub s3-delivery-waf-${TargetALBName}
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

#### IAMロールの設定
- CloudWatch
- Kinesis

用のIAMロールを作成します
CloudWatchにはKinesisを許可するポリシーを付与し、
KinesisにはS3の
- s3:AbortMultipartUpload
- s3:PutObject
- s3:GetBucketLocation
- s3:GetObject
- s3:ListBucket
- s3:ListBucketMultipartUploads

CloudWatchの
- logs:PutLogEvents

をを許可するポリシーを付与します

```yml
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  CloudWatchLogsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CWLogsRoleForKinesisFirehose-aws-waf-${TargetALBName}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: !Sub logs.${AWS::Region}.amazonaws.com
            Action:
              - sts:AssumeRole
      Path: /service-role/
  CloudWatchLogsRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub CWLogsAccessForKinesisFirehose-aws-waf-${TargetALBName}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - firehose:*
            Resource:
              - !Sub arn:aws:firehose:${AWS::Region}:${AWS::AccountId}:*
          - Effect: Allow
            Action:
              - iam:PassRole
            Resource:
              - !GetAtt CloudWatchLogsRole.Arn
      Roles:
        - !Ref CloudWatchLogsRole
  # For Kinesis Data Firehose
  KinesisDataFirehoseRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub KinesisFirehoseRoleForS3-aws-waf-${TargetALBName}
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - firehose.amazonaws.com
            Action:
              - sts:AssumeRole
            Condition:
              StringEquals:
                sts:ExternalId: !Ref AWS::AccountId
      Path: /service-role/
      Policies:
        - PolicyName: !Sub KinesisFirehoseAccessForS3-aws-waf-${TargetALBName}
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:PutObject
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - logs:PutLogEvents
                Resource:
                  - !Sub arn:aws:s3:::aws-waf-logs-for-${TargetALBName}
                  - !Sub arn:aws:s3:::aws-waf-logs-for-${TargetALBName}/*
                  - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-${TargetALBName}:log-stream:*
```

### CloudFrontのWAFの作成
ALBのWAFと同様に作成していきます

```waf-for-cloudfront.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "WAFv2 For CloudFront"

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
          default: "WAF Configuration"
        Parameters:
          - Route53HealthCheckerIPs
          - IPWhiteList
          - CloudFrontDistributionID
          - CWLogsRetentionInDays

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
  # ref: https://docs.aws.amazon.com/Route53/latest/DeveloperGuide/route-53-ip-addresses.html
  Route53HealthCheckerIPs:
    Description: "Enter the IP address for Route53 HealthChecker separated by commas. (ex: 0.0.0.0/32,1.1.1.1/32,2.2.2.2/32)"
    Type: CommaDelimitedList
  IPWhiteList:
    Description: "Enter the IP address for IP whitelist separated by commas (ex: 1.1.1.1/32,2.2.2.2/32)"
    Type: CommaDelimitedList
  CloudFrontDistributionID:
    Type: String
    Description: "Enter the CloudFront DistributionID for configuring WAFv2"
  CWLogsRetentionInDays:
    Description: "Enter the data retention period for CloudWatch Logs. (ex: 30)"
    Type: String
    AllowedValues: [30,60,90,120,150,180,365]

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # WAFv2 S3 Bucket
  # -------------------------------------
  WAFLogsS3Bucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Sub aws-waf-logs-for-cloudfront-${ProjectName}-${Environment}
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

  # -------------------------------------
  # WAFv2 ACL
  # -------------------------------------
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-waf
      Scope: CLOUDFRONT
      DefaultAction:
        Block: {}
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: !Sub ${ProjectName}-${Environment}-waf
      Rules:
        - Name: IPAddressWhitelistRule
          Priority: 0
          Action:
            Allow: {}
          Statement:
            IPSetReferenceStatement:
              Arn: !GetAtt IPAddressWhitelistSet.Arn
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: IPAddressWhitelistRule
        - Name: Route53IPAddressWhitelist
          Priority: 20
          Action:
            Allow: {}
          Statement:
            IPSetReferenceStatement:
              Arn: !GetAtt Route53IPAddressWhitelist.Arn
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: Route53IPAddressWhitelist
  # -------------------------------------
  # White IP Address
  # -------------------------------------
  IPAddressWhitelistSet:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: IPAddressWhitelist
      Description: "This List of IP addresses accessible to the application"
      Scope: CLOUDFRONT
      IPAddressVersion: IPV4
      Addresses: !Ref IPWhiteList
  Route53IPAddressWhitelist:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: !Sub Route53IPAddressWhitelist
      Description: "This List of IP addresses that are used for AWS Route53 Health Checks."
      Scope: CLOUDFRONT
      IPAddressVersion: IPV4
      Addresses: !Ref Route53HealthCheckerIPs

  # -------------------------------------
  # CloudWatch Logs Log Group (WAFv2)
  # -------------------------------------
  WAFLogsDeliveryStreamLogGroup:
    Type: AWS::Logs::LogGroup
    Properties:
      LogGroupName: !Sub aws-waf-logs-for-cf-${CloudFrontDistributionID}
      RetentionInDays: !Ref CWLogsRetentionInDays
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # WAFv2 Log Subscription
  # -------------------------------------
  WAFLogsSubscriptionFilter:
    DependsOn: CloudWatchLogsRolePolicy
    Type: AWS::Logs::SubscriptionFilter
    Properties:
      RoleArn: !GetAtt CloudWatchLogsRole.Arn
      LogGroupName: !Ref WAFLogsDeliveryStreamLogGroup
      FilterPattern: ""
      DestinationArn: !GetAtt WAFv2ForCFDeliveryStream.Arn

  # -------------------------------------
  # WAFv2 Log Config
  # -------------------------------------
  WAFLogsConfig:
    Type: AWS::WAFv2::LoggingConfiguration
    Properties:
      LogDestinationConfigs:
        - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-cf-${CloudFrontDistributionID}
      ResourceArn: !GetAtt WebACL.Arn

  # -------------------------------------
  # Kinesis Data Firehose Delivery Stream
  # -------------------------------------
  WAFv2ForCFDeliveryStream:
    Type: AWS::KinesisFirehose::DeliveryStream
    Properties:
      DeliveryStreamName: !Sub kinesis-s3-for-aws-waf-logs-cf-${CloudFrontDistributionID}
      DeliveryStreamEncryptionConfigurationInput:
        KeyType: AWS_OWNED_CMK
      ExtendedS3DestinationConfiguration:
        RoleARN: !GetAtt KinesisDataFirehoseRole.Arn
        BucketARN: !GetAtt WAFLogsS3Bucket.Arn
        BufferingHints:
          IntervalInSeconds: 300
          SizeInMBs: 5
        CompressionFormat: GZIP
        Prefix: ""
        ProcessingConfiguration:
          Enabled: false
        CloudWatchLoggingOptions:
          Enabled: true
          LogGroupName: /aws/kinesisfirehose/s3-delivery-stream
          LogStreamName: s3-delivery-waf-cf-${CloudFrontDistributionID}
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # IAM Role
  # -------------------------------------
  # For CloudWatch Logs
  CloudWatchLogsRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub CWLogsRoleForKinesisFirehose-aws-waf-cf-${CloudFrontDistributionID}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: !Sub logs.${AWS::Region}.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-role/
  CloudWatchLogsRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub CWLogsAccessForKinesisFirehose-aws-waf-cf-${CloudFrontDistributionID}
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - firehose:PutRecord
              - firehose:PutRecordBatch
            Resource:
              - !GetAtt WAFv2ForCFDeliveryStream.Arn
          - Effect: Allow
            Action:
              - iam:PassRole
            Resource:
              - !GetAtt CloudWatchLogsRole.Arn
      Roles:
        - !Ref CloudWatchLogsRole
  # For Kinesis Data Firehose
  KinesisDataFirehoseRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub KinesisFirehoseRoleForS3-aws-waf-cf-${CloudFrontDistributionID}
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - firehose.amazonaws.com
            Action:
              - sts:AssumeRole
            Condition:
              StringEquals:
                sts:ExternalId: !Ref AWS::AccountId
      Path: /service-role/
      Policies:
        - PolicyName: !Sub KinesisFirehoseAccessForS3-aws-waf-cf-${CloudFrontDistributionID}
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - s3:AbortMultipartUpload
                  - s3:PutObject
                  - s3:GetBucketLocation
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:ListBucketMultipartUploads
                  - logs:PutLogEvents
                Resource:
                  - !Sub arn:aws:s3:::aws-waf-logs-for-cloudfront-${ProjectName}-${Environment}
                  - !Sub arn:aws:s3:::aws-waf-logs-for-cloudfront-${ProjectName}-${Environment}/*
                  - !Sub arn:aws:logs:${AWS::Region}:${AWS::AccountId}:log-group:aws-waf-logs-for-cf-${CloudFrontDistributionID}:log-stream:*

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  CloudFrontWAF:
    Value: !GetAtt WebACL.Arn
  WAFLogsS3BucketArn:
    Value: !GetAtt WAFLogsS3Bucket.Arn

```

一つずつ解説していきます

#### WebACLの作成
ALBの時のScopeをREGIONALに設定していましたが、
ScopeにCloudFrontを設定します

```
Scope: CLOUDFRONT
```

```yml
  # -------------------------------------
  # WAFv2 ACL
  # -------------------------------------
  WebACL:
    Type: AWS::WAFv2::WebACL
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-waf
      Scope: CLOUDFRONT
      DefaultAction:
        Block: {}
      VisibilityConfig:
        SampledRequestsEnabled: true
        CloudWatchMetricsEnabled: true
        MetricName: !Sub ${ProjectName}-${Environment}-waf
      Rules:
        - Name: IPAddressWhitelistRule
          Priority: 0
          Action:
            Allow: {}
          Statement:
            IPSetReferenceStatement:
              Arn: !GetAtt IPAddressWhitelistSet.Arn
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: IPAddressWhitelistRule
        - Name: Route53IPAddressWhitelist
          Priority: 20
          Action:
            Allow: {}
          Statement:
            IPSetReferenceStatement:
              Arn: !GetAtt Route53IPAddressWhitelist.Arn
          VisibilityConfig:
            SampledRequestsEnabled: true
            CloudWatchMetricsEnabled: true
            MetricName: Route53IPAddressWhitelist
```

#### ホワイトリストの設定
- IPAddressWhitelistSet
- Route53IPAddressWhitelist

の2つを作成します

```yml
  # -------------------------------------
  # White IP Address
  # -------------------------------------
  IPAddressWhitelistSet:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: IPAddressWhitelist
      Description: "This List of IP addresses accessible to the application"
      Scope: CLOUDFRONT
      IPAddressVersion: IPV4
      Addresses: !Ref IPWhiteList
  Route53IPAddressWhitelist:
    Type: AWS::WAFv2::IPSet
    Properties:
      Name: !Sub Route53IPAddressWhitelist
      Description: "This List of IP addresses that are used for AWS Route53 Health Checks."
      Scope: CLOUDFRONT
      IPAddressVersion: IPV4
      Addresses: !Ref Route53HealthCheckerIPs
```

## CloudFront
CloudFrontに作成したWAFのWebACLと連携する設定を記載します

```cloudfront.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "CloudFront Stack"

# -------------------------------------
# Mappings
# -------------------------------------
Mappings:
  # CachePolicyIdは以下の記事を参照
  # https://docs.aws.amazon.com/ja_jp/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html
  CachePolicyIds:
    CachingOptimized:
      Id: 658327ea-f89d-4fab-a63d-7e88639e58f6
    CachingDisabled:
      Id: 4135ea2d-6df8-44a3-9df3-4b5a84be39ad
    CachingOptimizedForUncompressedObjects:
      Id: b2884449-e4de-46a7-ac36-70bc7f1ddd6d
    Elemental-MediaPackage:
      Id: 08627262-05a9-4f76-9ded-b50ca2e3a84f
    Amplify:
      Id: 2e54312d-136d-493c-8eb9-b001f22f67d2
  # ResponseHeadersPolicyIdは以下の記事を参照
  # https://docs.aws.amazon.com/ja_jp/AmazonCloudFront/latest/DeveloperGuide/using-managed-response-headers-policies.html
  ResponseHeadersPolicyIds:
    CORS-and-SecurityHeadersPolicy:
      Id: e61eb60c-9c35-4d20-a928-2b84e02af89c
    CORS-With-Preflight:
      Id: 5cc3b908-e619-4b99-88e5-2cf7f45965bd
    CORS-with-preflight-and-SecurityHeadersPolicy:
      Id: eaab4381-ed33-4a86-88ca-d9558dc6cd63
    SecurityHeadersPolicy:
      Id: 67f7725c-6f97-4210-82d7-5512b31e9d03
    SimpleCORS:
      Id: 60669652-455b-4ae9-85a4-c4c02393f86c

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
          default: "Route 53 Configuration"
        Parameters:
          - HostZoneID
      - Label:
          default: "CloudFront Configuration"
        Parameters:
          - CloudFrontHostZoneID
          - ACMPublicCertificateArn
          - CachePolicy
          - ResponseHeadersPolicy
          - AssetsBucketDomainName

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
    AllowedValues: [dev, stg, prd]
    ConstraintDescription: "Environment must be select"
  HostZoneID:
    Description: "Select the Route 53 Hosted Zone ID"
    Type: AWS::Route53::HostedZone::Id
  DomainName:
    Description: "Enter the Route 53 domain name"
    Default: shun-practice.com
    Type: String
  # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-recordset-aliastarget.html#cfn-route53-recordset-aliastarget-hostedzoneid
  CloudFrontHostZoneID:
    Type: String
    Description: "Select the CloudFront hosted zone ID. (fixed value: Z2FDTNDATAQYW2)"
    Default: Z2FDTNDATAQYW2
    AllowedValues:
      - Z2FDTNDATAQYW2
  ACMPublicCertificateArn:
    Description: "Enter the ACM public certificate ARN for global region"
    Type: String
  CachePolicy:
    Description: "Select the CloudFront cache policy (Recommended for S3: CachingOptimized)"
    Type: String
    Default: CachingOptimized
    AllowedValues:
      - CachingOptimized
      - CachingDisabled
      - CachingOptimizedForUncompressedObjects
      - Elemental-MediaPackage
  ResponseHeadersPolicy:
    Description: "Select the CloudFront response headers policy"
    Type: String
    Default: SecurityHeadersPolicy
    AllowedValues:
      - CORS-and-SecurityHeadersPolicy
      - CORS-With-Preflight
      - CORS-with-preflight-and-SecurityHeadersPolicy
      - SecurityHeadersPolicy
      - SimpleCORS
  WebACLArn:
    Description: "Enter the ARN of the WAFv2 to apply to CloudFront (ex: arn:aws:wafv2:us-east-1:012345678910:global/webacl/example/xxxxx)"
    Type: String
  AssetsBucketDomainName:
    Description: "Enter the S3 bucket region domain name for static web hosting (ex: example-assets-bucket.s3.ap-northeast-1.amazonaws.com)"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Route 53
  # -------------------------------------
  CloudFrontAliasRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostZoneID
      Name: !Ref DomainName
      Type: A
      # CloudFront用の設定
      AliasTarget:
        HostedZoneId: !Ref CloudFrontHostZoneID
        DNSName: !GetAtt AssetsDistribution.DomainName
  # -------------------------------------
  # CloudFront Distribution
  # -------------------------------------
  AssetsDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
        - Id: S3Origin
          DomainName: !Ref AssetsBucketDomainName
          S3OriginConfig:
            OriginAccessIdentity: ""
          OriginAccessControlId: !GetAtt CloudFrontOriginAccessControl.Id
        Enabled: true
        DefaultRootObject: index.html
        Comment: "S3 Static Website Hosting Distribution"
        CustomErrorResponses:
          - ErrorCachingMinTTL: 0
            ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /404/index.html
        DefaultCacheBehavior:
          CachePolicyId: !FindInMap [CachePolicyIds, !Ref CachePolicy , Id]
          ResponseHeadersPolicyId: !FindInMap [ResponseHeadersPolicyIds, !Ref ResponseHeadersPolicy, Id]
          TargetOriginId: S3Origin
          ViewerProtocolPolicy: redirect-to-https
        HttpVersion: http2
        ViewerCertificate:
          AcmCertificateArn: !Ref ACMPublicCertificateArn
          MinimumProtocolVersion: TLSv1.2_2021
          SslSupportMethod: sni-only
        # 代替ドメイン名の設定に必要
        Aliases:
          - !Ref DomainName
        IPV6Enabled: false
        WebACLId: !Ref WebACLArn

  # -------------------------------------
  # CloudFront OAC
  # -------------------------------------
  CloudFrontOriginAccessControl:
    Type: AWS::CloudFront::OriginAccessControl
    Properties:
      OriginAccessControlConfig:
        Description: "Origin Access Control For S3 Static Website Hosting"
        Name: !Sub ${ProjectName}-${Environment}-S3OAC
        OriginAccessControlOriginType: s3
        SigningBehavior: always
        SigningProtocol: sigv4

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  AssetsDistributionID:
    Value: !Ref AssetsDistribution

```

## 実際に作成してみよう！
### ALB用のWAF
必要な情報を入力した上で作成します
![スクリーンショット 2024-02-01 13.39.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62399e3e-4932-9aef-2a1e-538e89447ab1.png)

以下のように作成できたら成功です
![https___qiita-image-store.s3.ap-northeast-1.amazonaws.com_0_625980_7d58d678-4cf5-4700-0814-07601b0d892fのコピー.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6041c6ca-358a-4177-9cf1-8f484b1d4540.png)


ロードバランサーの統合タブから作成したWAFと連携できていることを確認できました
![スクリーンショット 2024-02-06 15.58.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/51b2e6e1-5598-0964-35f6-b8131684c7d3.png)

以下がALB用のWAFの設定画面です
![スクリーンショット 2024-02-06 15.58.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f3873dc-4c85-aa72-91a3-35e63f45d7cc.png)

![スクリーンショット 2024-02-06 16.16.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fd02ae9d-839a-2713-e97e-1a4cd2cc15ee.png)

![スクリーンショット 2024-02-06 16.16.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6dbf60a9-6a79-994b-5a2f-854d739d1ea0.png)

![スクリーンショット 2024-02-06 16.17.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1faa4c17-3ba2-a38a-9af3-f07db6f0bd0b.png)

### CloudFront用のWAF
必要な情報を入力した上で作成します
CloudFrontのWAFを作成する際はバージニア北部(us-east-1)で作成する必要があるので注意が必要です

![スクリーンショット 2024-02-06 16.26.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c540bc41-b119-bb67-c01a-5f69f8561d03.png)

以下のように作成できたら成功です
![68747470733a2f2f71696974612d696d6167652d73746f72652e73332e61702d6e6f727468656173742d312e616d617a6f6e6177732e636f6d2f302f3632353938302f32613338396636332d373862392d336139352d343238652d3861326461393234653766392e706e67.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/41e12c3c-f268-671f-e84c-33ed6379793d.png)

また、CloudFrontにWAFを適用する設定を行います
WebACLArnを設定します

![cloudfront-template.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f3613fba-7ae5-fab3-86a8-3bf1ba1a5387.png)

WebACLArnは先ほど作成したCloudFrontのWAFの出力に記載されているCloudFrontWAFの値を適用します

![cloudfront-output.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b4413b1a-f89c-c574-c10a-73e33bbfd401.png)

作成したWAFと連携できていることを確認できました
![スクリーンショット 2024-02-06 17.55.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/07d4bec2-fe50-8feb-2a31-657056060f5e.png)

以下がCloudFront用のWAFの設定画面です
![スクリーンショット 2024-02-06 17.56.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/96a7759f-bc56-e617-d33e-ab2e04be7587.png)

![スクリーンショット 2024-02-07 10.33.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2739ea2f-60a2-77dd-0eb3-a1ff3358e07d.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/AWS_WAFv2.html

https://docs.aws.amazon.com/ja_jp/waf/latest/developerguide/web-acl-processing.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-kinesisfirehose-deliverystream.html

https://dev.classmethod.jp/articles/cloudformation-webacl-cloudfront-error/#toc-3
