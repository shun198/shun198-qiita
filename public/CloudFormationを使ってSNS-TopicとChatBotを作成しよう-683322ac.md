---
title: CloudFormationを使ってSNS TopicとChatBotを作成しよう！
tags:
  - AWS
  - CloudFormation
  - SNS
  - chatbot
private: false
updated_at: '2024-05-22T09:44:59+09:00'
id: 683322acfd49496abb0d
organization_url_name: null
slide: false
---
## 概要
SNSとChatbotを使ってSlack通知を受け取りたいのでCloudFormationを使って実装する方法について解説していきたいと思います

## 前提
- Slackのワークスペースを作成済み

## 実装
以下のファイルを作成します
- sns-topic.yml
- chatbot.yml

## SNS Topicの作成
SNS Topicを作成します
今回は
- Alert
- Warning
- Security

の3種類のTopicを作成していますがTopic数はプロジェクトの要件に応じて調整してください
KMSを使って暗号化したいので以下のように各Topicに応じてKmsMasterKeyIdを設定します

```yml
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: shun198-alert
      TopicName: shun198-alert
      KmsMasterKeyId: !Ref KMSKeyAliasName
```

```sns-topic.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "SNS Topic Stack"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "KMS Key Configutation"
        Parameters:
          - PendingWindowInDays
          - KMSKeyAliasName

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  PendingWindowInDays:
    Description: "Enter the number of days to wait before being removed from the stack"
    Type: Number
    Default: 30
    MinValue: 7
    MaxValue: 30
  KMSKeyAliasName:
    Description: "Enter the alias name for SNS KMS key (default: alias/cmk/sns)"
    Type: String
    Default: alias/cmk/sns

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # KMS Key for SNS
  # -------------------------------------
  SNSKMSKey:
    Type: AWS::KMS::Key
    Properties:
      Description: "KMS key for encrypting SNS"
      PendingWindowInDays: !Ref PendingWindowInDays
      KeyPolicy:
        Version: 2012-10-17
        Id: sns-key
        Statement:
          - Effect: Allow
            Principal:
              AWS: !Sub arn:aws:iam::${AWS::AccountId}:root
            Action: kms:*
            Resource: "*"
          - Effect: Allow
            Principal:
              Service:
                - events.amazonaws.com
                - cloudwatch.amazonaws.com
                - ses.amazonaws.com
            Action:
              - kms:Decrypt
              - kms:GenerateDataKey
            Resource: "*"
  KMSKeyAlias:
    Type: AWS::KMS::Alias
    Properties:
      AliasName: !Ref KMSKeyAliasName
      TargetKeyId: !Ref SNSKMSKey

  # -------------------------------------
  # SNS Topic
  # -------------------------------------
  # アラート通知用
  AlertTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: shun198-alert
      TopicName: shun198-alert
      KmsMasterKeyId: !Ref KMSKeyAliasName
  AlertTopicPolicy:
    Type: AWS::SNS::TopicPolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: AlertSNSPolicy
            Effect: Allow
            Principal:
              Service:
                - events.amazonaws.com
                - cloudwatch.amazonaws.com
            Action:
              - sns:Publish
            Resource: !Ref AlertTopic
            Condition:
              StringEquals:
                aws:SourceAccount: !Ref AWS::AccountId
      Topics:
        - !Ref AlertTopic
  # ワーニング通知用
  WarningTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: shun198-warning
      TopicName: shun198-warning
      KmsMasterKeyId: !Ref KMSKeyAliasName
  WarningTopicPolicy:
    Type: AWS::SNS::TopicPolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: WarningSNSPolicy
            Effect: Allow
            Principal:
              Service:
                - events.amazonaws.com
                - cloudwatch.amazonaws.com
            Action:
              - sns:Publish
            Resource: !Ref WarningTopic
            Condition:
              StringEquals:
                aws:SourceAccount: !Ref AWS::AccountId
      Topics:
        - !Ref WarningTopic
  # セキュリティイベント通知用
  SecurityTopic:
    Type: AWS::SNS::Topic
    Properties:
      DisplayName: shun198-security
      TopicName: shun198-security
      KmsMasterKeyId: !Ref KMSKeyAliasName
  SecurityTopicPolicy:
    Type: AWS::SNS::TopicPolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Sid: SecuritySNSPolicy
            Effect: Allow
            Principal:
              Service:
                - events.amazonaws.com
            Action:
              - sns:Publish
            Resource: !Ref SecurityTopic
            Condition:
              StringEquals:
                aws:SourceAccount: !Ref AWS::AccountId
      Topics:
        - !Ref SecurityTopic

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  AlertTopicArn:
    Value: !Ref AlertTopic
  WarningTopicArn:
    Value: !Ref WarningTopic
  SecurityTopicArn:
    Value: !Ref SecurityTopic

```

## Chatbotの設定
コンソール画面からChatbotを設定します

まず、Slackを選択します
![スクリーンショット 2024-05-21 9.36.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cce01721-2a94-a4bd-0a58-e94c3e296c97.png)

`クライアントを設定`を押すとSlackの認証ページにリダイレクトされます
![スクリーンショット 2024-05-21 9.36.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc0b5c78-6505-1e8d-c0b7-6214721e53a2.png)

`許可する`を選択します
![スクリーンショット 2024-05-21 9.37.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/83d5452b-ab8d-af35-1908-aeddd96d6760.png)

以下のように設定できたら成功です
![スクリーンショット 2024-05-21 9.38.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79532522-1a8d-6c49-897c-6bf7ab8fe7d8.png)

## Chatbotの作成
Chatbotを設定する際は以下のように
- SlackのワークスペースID
- SlackのチャンネルID
- SNSトピックのArn

を指定します

```yml
  ChatbotForAlert:
    # Condition: IsPrdEnv
    Type: AWS::Chatbot::SlackChannelConfiguration
    Properties:
      ConfigurationName: shun198-notice-aws-alert
      IamRoleArn: !GetAtt ChatbotRole.Arn
      LoggingLevel: ERROR
      SlackWorkspaceId: !Ref SlackWorkspaceID
      SlackChannelId: !Ref SlackChannelIDForAlert
      SnsTopicArns:
        - !Sub arn:aws:sns:ap-northeast-1:${AWS::AccountId}:${AlertTopicName}

```

```chatbot.yml
# 本テンプレートのデプロイ条件は以下の 2 つ
# 1. Chatbot 経由で Slack ワークスペース承認済み
# 2. 使用予定リージョンに SNS Topic をデプロイ済み

AWSTemplateFormatVersion: 2010-09-09
Description: "Chatbot Stack"

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
          default: "Chatbot Configuration"
        Parameters:
          - ChatbotRoleName
      - Label:
          default: "Slack Configuration"
        Parameters:
          - SlackWorkspaceID
          - SlackChannelIDForAlert
          - SlackChannelIDForWarning
          - SlackChannelIDForSecurity
      - Label:
          default: "SNS Configuration"
        Parameters:
          - AlertTopicName
          - WarningTopicName
          - SecurityTopicName

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
  ChatbotRoleName:
    Description: "Enter the Chatbot Role name (default: AWSChatbotRole)"
    Type: String
    Default: AWSChatbotRole
  # Slack ワークスペース ID
  SlackWorkspaceID:
    Description: "Enter the Slack Workspace ID"
    Type: String
  # アラート通知先の Slack Channel ID
  SlackChannelIDForAlert:
    Description: "Enter the Slack channel ID for individual alert notification"
    Type: String
  # ワーニング通知先の Slack Channel ID
  SlackChannelIDForWarning:
    Description: "Enter the Slack channel ID for warning notification"
    Type: String
  # セキュリティ関連通知先の Slack Channel ID
  SlackChannelIDForSecurity:
    Description: "Enter the Slack channel ID for security notification"
    Type: String
  # アラート通知先 SNS TopicName
  AlertTopicName:
    Description: "Enter the SNS Topic name for alert"
    Type: String
    Default: shun198-alert
  # ワーニング通知先 SNS TopicName
  WarningTopicName:
    Description: "Enter the SNS Topic name for warning"
    Type: String
    Default: shun198-warning
  # セキュリティ関連通知先 SNS TopicName
  SecurityTopicName:
    Description: "Enter the SNS Topic name for security"
    Type: String
    Default: shun198-security

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  # AWS Chatbot による Slack 連携時に必要な IAM ロール
  ChatbotRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Ref ChatbotRoleName
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: chatbot.amazonaws.com
            Action: sts:AssumeRole
      Path: /service-linked-role/
      Policies:
        - PolicyName: AWSChatbotNotificationsOnlyAccess
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - cloudwatch:Describe*
                  - cloudwatch:Get*
                  - cloudwatch:List*
                Resource:
                  - "*"

  # -------------------------------------
  # Chatbot
  # -------------------------------------
  ChatbotForAlert:
    Type: AWS::Chatbot::SlackChannelConfiguration
    Properties:
      ConfigurationName: shun198-notice-aws-alert
      IamRoleArn: !GetAtt ChatbotRole.Arn
      LoggingLevel: ERROR
      SlackWorkspaceId: !Ref SlackWorkspaceID
      SlackChannelId: !Ref SlackChannelIDForAlert
      SnsTopicArns:
        - !Sub arn:aws:sns:ap-northeast-1:${AWS::AccountId}:${AlertTopicName}
  ChatbotForWarning:
    Type: AWS::Chatbot::SlackChannelConfiguration
    Properties:
      ConfigurationName: shun198-notice-aws-warning
      IamRoleArn: !GetAtt ChatbotRole.Arn
      LoggingLevel: ERROR
      SlackWorkspaceId: !Ref SlackWorkspaceID
      SlackChannelId: !Ref SlackChannelIDForWarning
      SnsTopicArns:
        - !Sub arn:aws:sns:ap-northeast-1:${AWS::AccountId}:${WarningTopicName}
  ChatbotForSecurity:
    Type: AWS::Chatbot::SlackChannelConfiguration
    Properties:
      ConfigurationName: shun198-notice-aws-security
      IamRoleArn: !GetAtt ChatbotRole.Arn
      LoggingLevel: ERROR
      SlackWorkspaceId: !Ref SlackWorkspaceID
      SlackChannelId: !Ref SlackChannelIDForSecurity
      SnsTopicArns:
        - !Sub arn:aws:sns:ap-northeast-1:${AWS::AccountId}:${SecurityTopicName}

```

## 実際に作成してみよう！
### SNS Topicの作成
以下のように作成されたら成功です
![スクリーンショット 2024-05-22 7.52.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2e7a74eb-ca9c-abe0-b788-646dfdd72ac7.png)

### Chatbotの作成
Chatbotを作成する際に
- SlackのワークスペースのID
- 通知したいチャンネルのID

を指定します
ワークスペースIDはブラウザ版のURL内にあるTから始まるIDです

https://app.slack.com/client/TXXXXXXXX/XXXXXXXXXXX

https://slack.com/intl/ja-jp/help/articles/221769328-Slack-URL-%E3%81%BE%E3%81%9F%E3%81%AF-ID-%E3%82%92%E7%A2%BA%E8%AA%8D%E3%81%99%E3%82%8B#01H8J8QHHEXMJYV14HVZDRR337

チャンネルIDはチャンネル情報の一番下に記載されています

![スクリーンショット 2024-05-22 8.07.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/31698d5e-ed0b-5b1a-28b4-7e2bb80507ad.png)

SNSのコンソールから作成したトピックを選択し、以下のようにサブスクリプションが作成されたら成功です

![スクリーンショット 2024-05-22 8.55.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/699b0b77-fb33-50ff-db63-897401bb6979.png)

Chatbotのコンソールから設定済みチャネルが登録されていることを確認できたら成功です
![スクリーンショット 2024-05-22 8.59.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2d9c80d3-0ab2-78e2-827c-a14c607bafc5.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-sns-topic.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-chatbot-slackchannelconfiguration.html

https://dev.classmethod.jp/articles/cloudformation-chatbot-alarm-to-slack/

https://techblog.cartaholdings.co.jp/entry/archives/6411
