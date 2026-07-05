---
title: EventBridge Schedulerを使ってECSタスクを自動で起動・停止してみよう！
tags:
  - AWS
  - CloudFormation
  - ECS
  - EventBridge
private: false
updated_at: '2024-10-26T21:06:21+09:00'
id: f1c765e1170924f2bb66
organization_url_name: null
slide: false
---
## 概要
コストカットの観点で例えば平日のみECSを起動させたい、などのユースケースがあるかと思います
今回はEventBridge Schedulerを使って行う方法についてCloudFormationのテンプレートを交えて解説します

## 前提
- ECS Cluster及びECSタスクを作成済み

## 実装
以下がEventBridge Scheduler用のテンプレートです

```yaml
# 本テンプレートの使用方法
# ECS Service の複数指定は不可のため、複数 Service のスケジュール設定を
# 行いたい場合は Service 単位で Stack をデプロイすること

AWSTemplateFormatVersion: 2010-09-09
Description: "EventBridge Scheduler Stack For ECS Auto Start And Stop"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    # パラメータの並び順を記載
    ParameterGroups:
      - Label:
          default: "Project Configuration"
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: "EventBridge Scheduler Configuration"
        Parameters:
          - ECSClusterName
          - ECSServiceName
          - ECSTaskDesiredCount
          - ScheduleStartTime
          - ScheduleStopTime
          - ScheduleTimeZone
      - Label:
          default: "SQS Configuration"
        Parameters:
          - MessageRetentionPeriod
      - Label:
          default: "CloudWatch For SNS Topic configuration"
        Parameters:
          - WarningTopicName

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Enter the project name. (ex: my-project)"
    Type: String
    MinLength: 1
    ConstraintDescription: "ProjectName must be entered."
    Default: my-project
  Environment:
    Description: "Select a environment name."
    Type: String
    AllowedValues:
      - dev
      - stg
    ConstraintDescription: "Environment name must be entered."
  ECSClusterName:
    Description: "Enter the ECS cluster name. (ex: my-project-dev-cluster)"
    Type: String
  ECSServiceName:
    Description: "Enter the ECS service name. (ex: my-project-dev-back-service)"
    Type: String
  ECSTaskDesiredCount:
    Description: "Number of ECS Tasks to be started at any time."
    Type: Number
    Default: 1
  ScheduleStartTime:
    Description: "Enter the schedule to stop ECS with cron expression."
    Type: String
    Default: cron(0 7 ? * Mon-Fri *)
  ScheduleStopTime:
    Description: "Enter the schedule to start ECS with cron expression."
    Type: String
    Default: cron(0 22 ? * Mon-Fri *)
  ScheduleTimeZone:
    Description: "Enter the time zone for Eventbridge Scheduler. (default: Asia/Tokyo)"
    Type: String
    Default: Asia/Tokyo
  MessageRetentionPeriod:
    Description: "Enter the time to hold messages as a queue. (default: 3600)"
    Type: Number
    Default: 3600
    MinValue: 60
    MaxValue: 1209600
    ConstraintDescription: "MessageRetentionPeriod must be entered between the values 60 - 1209600."
  WarningTopicName:
    Description: "Enter the SNS Topic name for warning notification."
    Type: String
    Default: warning

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  EventBridgeRoleForECSAutoStartStop:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub EventBridgeRoleForECSAutoStartStop
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - scheduler.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: !Sub EventBridgeAccessForECSAutoStartStop
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - ecs:DescribeServices
                  - ecs:UpdateService
                Resource: "*"
              - Effect: Allow
                Action:
                  - sqs:SendMessage
                Resource: !GetAtt DeadLetterQueue.Arn

  # -------------------------------------
  # EventBridge
  # -------------------------------------
  # 自動起動スケジューラー
  ECSStartSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: !Sub ecs-auto-start-for-${ECSServiceName}
      Description: "Scheduler to auto start ECS"
      ScheduleExpression: !Ref ScheduleStartTime
      ScheduleExpressionTimezone: !Ref ScheduleTimeZone
      FlexibleTimeWindow:
        Mode: "OFF"
      State: ENABLED
      Target:
        Arn: arn:aws:scheduler:::aws-sdk:ecs:updateService
        Input: !Sub |-
          {
            "Cluster": "${ECSClusterName}",
            "Service": "${ECSServiceName}",
            "DesiredCount": ${ECSTaskDesiredCount}
          }
        RoleArn: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
        DeadLetterConfig:
          Arn: !GetAtt DeadLetterQueue.Arn
  ECSStopSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: !Sub ecs-auto-stop-for-${ECSServiceName}
      Description: "Scheduler to auto stop ECS"
      ScheduleExpression: !Ref ScheduleStopTime
      ScheduleExpressionTimezone: !Ref ScheduleTimeZone
      FlexibleTimeWindow:
        Mode: "OFF"
      State: ENABLED
      Target:
        Arn: arn:aws:scheduler:::aws-sdk:ecs:updateService
        Input: !Sub |-
          {
            "Cluster": "${ECSClusterName}",
            "Service": "${ECSServiceName}",
            "DesiredCount": 0
          }
        RoleArn: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
        DeadLetterConfig:
          Arn: !GetAtt DeadLetterQueue.Arn

  # -------------------------------------
  # SQS
  # -------------------------------------
  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub dead-letter-queue-cloudwatch-alarm-auto-start-and-stop-for-backend
      MessageRetentionPeriod: !Ref MessageRetentionPeriod
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  DeadLetterQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              AWS: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
            Action:
              - sqs:SendMessage
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
            Resource: !GetAtt DeadLetterQueue.Arn
      Queues:
        - !Ref DeadLetterQueue

  # -------------------------------------
  # CloudWatch Alarm
  # -------------------------------------
  # DLQ にメッセージが入ったことを検知するアラーム
  # ref: https://dev.classmethod.jp/articles/sqs-dead-letter-queue-metrics-for-alert/
  ApproximateNumberOfMessagesVisibleOver1:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub
        - Custom_${DeadLetterQueueName}_ApproximateNumberOfMessagesVisible-Over1
        - { DeadLetterQueueName: !GetAtt DeadLetterQueue.QueueName }
      AlarmDescription: !Sub "${ECSServiceName} の自動起動 / 停止スケジューラーが正常に実行できていないおそれがあります、${ECSServiceName} の稼働状況および EventBridge Scheduler の設定を確認してください"
      Namespace: AWS/SQS
      MetricName: ApproximateNumberOfMessagesVisible
      Dimensions:
        - Name: QueueName
          Value: !GetAtt DeadLetterQueue.QueueName
      AlarmActions:
        - !Sub arn:aws:sns:${AWS::Region}:${AWS::AccountId}:${WarningTopicName}
      ComparisonOperator: GreaterThanOrEqualToThreshold
      EvaluationPeriods: 1
      Period: 300
      Statistic: Sum
      Threshold: 1
```

1つずつ解説します

### ロールの作成
- EventBridge用のECSタスクの詳細表示、更新用のロール
- 後述するデッドSQS用のメッセージの送信、削除、取得用のロール

を作成します

```yaml
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  EventBridgeRoleForECSAutoStartStop:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub EventBridgeRoleForECSAutoStartStop
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service:
                - scheduler.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: !Sub EventBridgeAccessForECSAutoStartStop
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - ecs:DescribeServices
                  - ecs:UpdateService
                Resource: "*"
              - Effect: Allow
                Action:
                  - sqs:SendMessage
                Resource: !GetAtt DeadLetterQueue.Arn


  # -------------------------------------
  # SQS
  # -------------------------------------
  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub dead-letter-queue-cloudwatch-alarm-auto-start-and-stop-for-backend
      MessageRetentionPeriod: !Ref MessageRetentionPeriod
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  DeadLetterQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              AWS: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
            Action:
              - sqs:SendMessage
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
            Resource: !GetAtt DeadLetterQueue.Arn
      Queues:
        - !Ref DeadLetterQueue
```

### DeadLetterQueue
EventBridge実行後、失敗したイベントをQueueに送信することができるので専用のQueue(デッドレターキュー)を作成します

https://docs.aws.amazon.com/ja_jp/eventbridge/latest/userguide/eb-rule-dlq.html

```yml
  # -------------------------------------
  # SQS
  # -------------------------------------
  DeadLetterQueue:
    Type: AWS::SQS::Queue
    Properties:
      QueueName: !Sub dead-letter-queue-cloudwatch-alarm-auto-start-and-stop-for-backend
      MessageRetentionPeriod: !Ref MessageRetentionPeriod
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  DeadLetterQueuePolicy:
    Type: AWS::SQS::QueuePolicy
    Properties:
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              AWS: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
            Action:
              - sqs:SendMessage
              - sqs:ReceiveMessage
              - sqs:DeleteMessage
            Resource: !GetAtt DeadLetterQueue.Arn
      Queues:
        - !Ref DeadLetterQueue
```

### EventBridge Schedulerの作成
ECSタスクの起動、削除用のSchedulerを作成します
今回は以下の条件下での起動、停止を行います

- 平日7時から22時の間はタスクを1つ起動
- 平日7時から22時以外の時間帯(土日、営業時間外)にタスクを0にする

どちらも失敗時はDLQへメッセージが届くよう設定します

```yaml
  # -------------------------------------
  # EventBridge
  # -------------------------------------
  # 自動起動スケジューラー
  ECSStartSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: !Sub ecs-auto-start-for-${ECSServiceName}
      Description: "Scheduler to auto start ECS"
      ScheduleExpression: !Ref ScheduleStartTime
      ScheduleExpressionTimezone: !Ref ScheduleTimeZone
      FlexibleTimeWindow:
        Mode: "OFF"
      State: ENABLED
      Target:
        Arn: arn:aws:scheduler:::aws-sdk:ecs:updateService
        Input: !Sub |-
          {
            "Cluster": "${ECSClusterName}",
            "Service": "${ECSServiceName}",
            "DesiredCount": ${ECSTaskDesiredCount}
          }
        RoleArn: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
        DeadLetterConfig:
          Arn: !GetAtt DeadLetterQueue.Arn
  ECSStopSchedule:
    Type: AWS::Scheduler::Schedule
    Properties:
      Name: !Sub ecs-auto-stop-for-${ECSServiceName}
      Description: "Scheduler to auto stop ECS"
      ScheduleExpression: !Ref ScheduleStopTime
      ScheduleExpressionTimezone: !Ref ScheduleTimeZone
      FlexibleTimeWindow:
        Mode: "OFF"
      State: ENABLED
      Target:
        Arn: arn:aws:scheduler:::aws-sdk:ecs:updateService
        Input: !Sub |-
          {
            "Cluster": "${ECSClusterName}",
            "Service": "${ECSServiceName}",
            "DesiredCount": 0
          }
        RoleArn: !GetAtt EventBridgeRoleForECSAutoStartStop.Arn
        DeadLetterConfig:
          Arn: !GetAtt DeadLetterQueue.Arn
```

## 実際に作成してみよう！
上記のCloudFormationテンプレートをデプロイします

![スクリーンショット 2024-10-26 20.47.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fae8e2cf-7d8a-9a78-f3b0-4acf2b4575a1.png)

以下のようにEventBridge Schedulerが作成され、平日以外の時間帯だとタスク数が0になったら成功です

![スクリーンショット 2024-10-26 20.50.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f9c3a81a-1a4e-7eed-291c-d130697c2333.png)

![スクリーンショット 2024-10-26 20.49.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/466d88ce-b041-fdde-89d6-30360281b493.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-scheduler-schedule.html

https://dev.classmethod.jp/articles/eventbridge-scheduler-regularly-start-and-stop-ecs-tasks/

https://qiita.com/KureyonChan/items/95cb6b2d35c0acff935c
