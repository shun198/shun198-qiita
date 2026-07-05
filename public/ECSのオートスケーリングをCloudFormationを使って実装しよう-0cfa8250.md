---
title: ECSのオートスケーリングをCloudFormationを使って実装しよう！
tags:
  - AWS
  - CloudWatch
  - CloudFormation
  - ECS
private: false
updated_at: '2024-07-03T15:41:35+09:00'
id: 0cfa825010035245c4cf
organization_url_name: null
slide: false
---
## 概要
AWS ECSにはアクセス数の増減に応じてECSサービスのタスクの数を自動的に増減するオートスケーリング機能があります
今回はCloudFormationを使ってオートスケーリングの設定をする方法について解説します

## 前提
- ECSクラスター、サービス、タスクを作成済み

## 実装
オートスケーリング用のテンプレートを作成していきます
今回は
- スケールイン
- スケールアウト

の2種類を作成します

```ecs-fargate-auto-scaling.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "ECS Fargate Service Auto Scaling Stack"

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
          default: "ECS Auto Scaling Configuration"
        Parameters:
          - TargetECSClusterName
          - TargetECSServiceName
          - ServiceScaleEvaluationPeriods
          - ServiceCPUScaleOutThreshold
          - ServiceCPUScaleInThreshold
          - TaskMinContainerCount
          - TaskMaxContainerCount

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
  TargetECSClusterName:
    Description: "Enter the ECS cluster name for CloudWatch monitoring. (ex: my-project-dev-cluster)"
    Type: String
  TargetECSServiceName:
    Description: "Enter the ECS service name for CloudWatch monitoring. (ex: my-project-dev-service)"
    Type: String
  ServiceScaleEvaluationPeriods:
    Description: "The number of periods over which data is compared to the specified threshold."
    Type: Number
    Default: 1
    MinValue: 1
  ServiceCPUScaleOutThreshold:
    Description: "Average CPU value to trigger auto scaling out."
    Type: Number
    Default: 50
    MinValue: 0
    MaxValue: 100
    ConstraintDescription: "ServiceCPUScaleOutThreshold Value must be between 0 and 100."
  ServiceCPUScaleInThreshold:
    Description: "Average CPU value to trigger auto scaling in."
    Type: Number
    Default: 30
    MinValue: 0
    MaxValue: 100
    ConstraintDescription: "ServiceCPUScaleInThreshold Value must be between 0 and 100."
  TaskMinContainerCount:
    Description: "Minimum number of containers to run for the service."
    Type: Number
    Default: 1
    MinValue: 1
    ConstraintDescription: "TaskMinContainerCount Value must be at least one."
  TaskMaxContainerCount:
    Description: "Maximum number of containers to run for the service when auto scaling out."
    Type: Number
    Default: 2
    MinValue: 1
    ConstraintDescription: "TaskMaxContainerCount Value must be at least one."

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # ECS Service Auto Scaling
  # -------------------------------------
  ServiceAutoScalingRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub ECSServiceAutoScalingRole-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: application-autoscaling.amazonaws.com
            Action: sts:AssumeRole
      Policies:
        - PolicyName: !Sub ECSServiceAutoScalingRoleAccess-${ProjectName}-${Environment}
          PolicyDocument:
            Statement:
              - Effect: Allow
                Action:
                  - application-autoscaling:*
                  - cloudwatch:DescribeAlarms
                  - cloudwatch:PutMetricAlarm
                  - ecs:DescribeServices
                  - ecs:UpdateService
                Resource: "*"

  ServiceScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MinCapacity: !Ref TaskMinContainerCount
      MaxCapacity: !Ref TaskMaxContainerCount
      ResourceId: !Sub service/${TargetECSClusterName}/${TargetECSServiceName}
      RoleARN: !GetAtt ServiceAutoScalingRole.Arn
      ScalableDimension: ecs:service:DesiredCount
      ServiceNamespace: ecs

  ServiceScaleOutPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: ECSServiceScaleOutPolicy
      PolicyType: StepScaling
      ScalingTargetId: !Ref ServiceScalingTarget
      StepScalingPolicyConfiguration:
        AdjustmentType: ChangeInCapacity
        Cooldown: 60
        MetricAggregationType: Average
        StepAdjustments:
          - ScalingAdjustment: 1
            MetricIntervalLowerBound: 0

  ServiceScaleInPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: ECSServiceScaleInPolicy
      PolicyType: StepScaling
      ScalingTargetId: !Ref ServiceScalingTarget
      StepScalingPolicyConfiguration:
        AdjustmentType: ChangeInCapacity
        Cooldown: 60
        MetricAggregationType: Average
        StepAdjustments:
          - ScalingAdjustment: -1
            MetricIntervalUpperBound: 0

  ServiceScaleOutAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${TargetECSServiceName}_ScaleOutAlarm
      EvaluationPeriods: !Ref ServiceScaleEvaluationPeriods
      Statistic: Average
      TreatMissingData: notBreaching
      Threshold: !Ref ServiceCPUScaleOutThreshold
      AlarmDescription: !Sub CPU 使用率が上昇したため、ECS サービス ${TargetECSServiceName} のスケールアウトを実行
      Period: 60
      AlarmActions:
        - !Ref ServiceScaleOutPolicy
      Namespace: AWS/ECS
      Dimensions:
        - Name: ClusterName
          Value: !Ref TargetECSClusterName
        - Name: ServiceName
          Value: !Ref TargetECSServiceName
      ComparisonOperator: GreaterThanThreshold
      MetricName: CPUUtilization

  ServiceScaleInAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${TargetECSServiceName}_ScaleInAlarm
      EvaluationPeriods: !Ref ServiceScaleEvaluationPeriods
      Statistic: Average
      TreatMissingData: notBreaching
      Threshold: !Ref ServiceCPUScaleInThreshold
      AlarmDescription: !Sub CPU 使用率が低下したため、ECS サービス ${TargetECSServiceName} のスケールインを実行
      Period: 300
      AlarmActions:
        - !Ref ServiceScaleInPolicy
      Namespace: AWS/ECS
      Dimensions:
        - Name: ClusterName
          Value: !Ref TargetECSClusterName
        - Name: ServiceName
          Value: !Ref TargetECSServiceName
      ComparisonOperator: LessThanThreshold
      MetricName: CPUUtilization
```

### ScalableTargetの設定
ECSをオートスケールするための設定を行います
今回はスケールインの最小値をTaskMinContainerCountで指定した値、スケールアウトの最大値をTaskMaxContainerCountで指定した値に設定します
ScalableDimensionをecs:service:DesiredCount(ECSタスクの個数)に設定します
ServiceNamespaceをecsに設定します

```yaml
  ServiceScalingTarget:
    Type: AWS::ApplicationAutoScaling::ScalableTarget
    Properties:
      MinCapacity: !Ref TaskMinContainerCount
      MaxCapacity: !Ref TaskMaxContainerCount
      ResourceId: !Sub service/${TargetECSClusterName}/${TargetECSServiceName}
      RoleARN: !GetAtt ServiceAutoScalingRole.Arn
      ScalableDimension: ecs:service:DesiredCount
      ServiceNamespace: ecs
```

### スケールイン・スケールアウトのポリシーの設定
スケールイン・スケールアウトのポリシーにServiceScalingTargetを紐付けさせます
Cooldownではスケーリング・アクティビティが有効になるまでの待ち時間を60秒にします
StepAdjustmentsではスケールアウトの場合はECSのタスク数を+1、スケールインの場合はECSのタスク数を-1するよう設定します

```yaml
  ServiceScaleOutPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: ECSServiceScaleOutPolicy
      PolicyType: StepScaling
      ScalingTargetId: !Ref ServiceScalingTarget
      StepScalingPolicyConfiguration:
        AdjustmentType: ChangeInCapacity
        Cooldown: 60
        MetricAggregationType: Average
        StepAdjustments:
          - ScalingAdjustment: 1
            MetricIntervalLowerBound: 0

  ServiceScaleInPolicy:
    Type: AWS::ApplicationAutoScaling::ScalingPolicy
    Properties:
      PolicyName: ECSServiceScaleInPolicy
      PolicyType: StepScaling
      ScalingTargetId: !Ref ServiceScalingTarget
      StepScalingPolicyConfiguration:
        AdjustmentType: ChangeInCapacity
        Cooldown: 60
        MetricAggregationType: Average
        StepAdjustments:
          - ScalingAdjustment: -1
            MetricIntervalUpperBound: 0
```

### CloudWatch Alarmの設定
スケールイン・スケールアウトのCloudWatch Alarmの設定を行います
ServiceScaleOutAlarmではServiceCPUScaleOutThresholdをデフォルトで50、ComparisonOperatorをGreaterThanThresholdにしているので、CPU使用率が50%を超えたら自動でスケールアウトするよう設定され、CloudWatch Alarmに表示されます

ServiceScaleInAlarmではServiceCPUScaleInThresholdをデフォルトで30、ComparisonOperatorをLessThanThresholdにしているので、CPU使用率が30%を下回ったら自動でスケールインするよう設定され、CloudWatch Alarmに表示されます

```yaml
  ServiceScaleOutAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${TargetECSServiceName}_ScaleOutAlarm
      EvaluationPeriods: !Ref ServiceScaleEvaluationPeriods
      Statistic: Average
      TreatMissingData: notBreaching
      Threshold: !Ref ServiceCPUScaleOutThreshold
      AlarmDescription: !Sub CPU 使用率が上昇したため、ECS サービス ${TargetECSServiceName} のスケールアウトを実行
      Period: 60
      AlarmActions:
        - !Ref ServiceScaleOutPolicy
      Namespace: AWS/ECS
      Dimensions:
        - Name: ClusterName
          Value: !Ref TargetECSClusterName
        - Name: ServiceName
          Value: !Ref TargetECSServiceName
      ComparisonOperator: GreaterThanThreshold
      MetricName: CPUUtilization

  ServiceScaleInAlarm:
    Type: AWS::CloudWatch::Alarm
    Properties:
      AlarmName: !Sub ${TargetECSServiceName}_ScaleInAlarm
      EvaluationPeriods: !Ref ServiceScaleEvaluationPeriods
      Statistic: Average
      TreatMissingData: notBreaching
      Threshold: !Ref ServiceCPUScaleInThreshold
      AlarmDescription: !Sub CPU 使用率が低下したため、ECS サービス ${TargetECSServiceName} のスケールインを実行
      Period: 300
      AlarmActions:
        - !Ref ServiceScaleInPolicy
      Namespace: AWS/ECS
      Dimensions:
        - Name: ClusterName
          Value: !Ref TargetECSClusterName
        - Name: ServiceName
          Value: !Ref TargetECSServiceName
      ComparisonOperator: LessThanThreshold
      MetricName: CPUUtilization
```

## 実際に作成してみよう！
以下のようにオートスケーリングの設定がECSに適用できれば成功です

![スクリーンショット 2024-07-01 15.31.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9cb02777-b994-c13d-c151-9d869743bf7e.png)

![スクリーンショット 2024-07-01 15.34.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/41bb518a-8b2b-8a97-0437-a9520c566d40.png)

![スクリーンショット 2024-07-01 15.35.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/95421d2b-3b2a-f015-e89b-16d5ffd42785.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AmazonECS/latest/developerguide/service-auto-scaling.html#:~:text=%E3%82%AA%E3%83%BC%E3%83%88%E3%82%B9%E3%82%B1%E3%83%BC%E3%83%AA%E3%83%B3%E3%82%B0%E3%81%AF%E3%80%81%E9%9C%80%E8%A6%81%E3%81%AB,%E6%A9%9F%E8%83%BD%E3%82%92%E6%8F%90%E4%BE%9B%E3%81%97%E3%81%BE%E3%81%99%E3%80%82

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-cloudwatch-alarm.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/AWS_ApplicationAutoScaling.html
