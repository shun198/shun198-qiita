---
title: CloudFormationを使ってALBとRoute53とACMを連携してHTTPS接続しよう！
tags:
  - AWS
  - CloudFormation
  - route53
  - ALB
private: false
updated_at: '2024-01-26T08:38:57+09:00'
id: 3848ed073235ef106cde
organization_url_name: null
slide: false
---
## 概要
CloudFormationを使ってHTTPS用のListnerとTarget Groupを作成し、HTTPS通信できるよう設定する方法について解説します

## 前提
- ECSを作成済み
- ドメインをRoute53に作成済み
- ACMを作成済み

以下の記事でECSとALBを作成する方法について解説したので気になる方は読んでいただけると幸いです

https://qiita.com/shun198/items/5ea5147445a65a435231

https://qiita.com/shun198/items/971c606699d918bffa6e

## ディレクトリ構成
```
tree
.
└── templates
    └── security
        └── sg.yml
```

## 実装
ALBとRoute53の設定を行います

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
          - HostZoneID
          - ALBPublicSubnet1
          - ALBPublicSubnet2
          - ALBSecurityGroupID
          - ACMCertificateArn
          - HealthCheckPath
          - DeletionProtectionEnabled
          - IdleTimeoutSeconds
          - ELBSecurityPolicy

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
  HostZoneID:
    Type: AWS::Route53::HostedZone::Id
    Description: "Select the Route 53 hosted zone ID"
  DomainName:
    Description: "Enter the Route 53 domain name"
    Default: api.shun-practice.com
    Type: String
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
  ACMCertificateArn:
    Description: "Enter the Certificate ARN. (ex: arn:aws:acm:<AWS_REGION>:<AWS_ACCOUNT_ID>:certificate/<ACMCertificateID>)"
    Type: String
  # ALB からのヘルスチェックに応答するパス
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
  # https://docs.aws.amazon.com/ja_jp/elasticloadbalancing/latest/application/create-https-listener.html
  ELBSecurityPolicy:
    Description: "Select the ELB security policies."
    Type: String
    AllowedValues:
      - ELBSecurityPolicy-TLS-1-2-Ext-2018-06
      - ELBSecurityPolicy-TLS13-1-2-2021-06

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Target Groups
  # -------------------------------------
  ALBTargetGroupBlue:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg-blue
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
  ALBTargetGroupGreen:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg-green
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
  ALBListenerHTTPS:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroupBlue
      LoadBalancerArn: !Ref InternetALB
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: !Ref ACMCertificateArn
      SslPolicy: !Ref ELBSecurityPolicy
  ALBListenerHTTPTest:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroupBlue
      LoadBalancerArn: !Ref InternetALB
      Port: 8080
      Protocol: HTTP


  # -------------------------------------
  # Route 53
  # -------------------------------------
  ALBAliasRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostZoneID
      Name: !Ref DomainName
      Type: A
      AliasTarget:
        HostedZoneId: !GetAtt InternetALB.CanonicalHostedZoneID
        DNSName: !GetAtt InternetALB.DNSName

# -------------------------------------
# Output parameters
# -------------------------------------
Outputs:
  InternetALBArn:
    Value: !Ref InternetALB
  InternetALBName:
    Value: !GetAtt InternetALB.LoadBalancerName

  ALBTargetGroupBlueArn:
    Value: !Ref ALBTargetGroupBlue
  ALBTargetGroupBlueName:
    Value: !GetAtt ALBTargetGroupBlue.TargetGroupName
  ALBTargetGroupGreenArn:
    Value: !Ref ALBTargetGroupGreen
  ALBTargetGroupGreenName:
    Value: !GetAtt ALBTargetGroupGreen.TargetGroupName

```

### ターゲットグループ
今回はBlue/Greenデプロイ用にターゲットグループを2つ作成します

```yml
  # -------------------------------------
  # Target Groups
  # -------------------------------------
  ALBTargetGroupBlue:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg-blue
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
  ALBTargetGroupGreen:
    Type: AWS::ElasticLoadBalancingV2::TargetGroup
    DependsOn: InternetALB
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-tg-green
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

### リスナー
HTTPS通信用にALBListenerHTTPS、Blue/Greenデプロイ用にALBListenerHTTPTestを作成します
ALBListenerHTTPSにACMの設定を行うことでHTTPSで通信できるようになります
また、今回はALBListenerHTTPTestのリスナーのポートを8080に指定します

```yml
  # -------------------------------------
  # Listener
  # -------------------------------------
  ALBListenerHTTPS:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroupBlue
      LoadBalancerArn: !Ref InternetALB
      Port: 443
      Protocol: HTTPS
      Certificates:
        - CertificateArn: !Ref ACMCertificateArn
      SslPolicy: !Ref ELBSecurityPolicy
  ALBListenerHTTPTest:
    Type: AWS::ElasticLoadBalancingV2::Listener
    Properties:
      DefaultActions:
        - Type: forward
          TargetGroupArn: !Ref ALBTargetGroupBlue
      LoadBalancerArn: !Ref InternetALB
      Port: 8080
      Protocol: HTTP
```

### Route53
API用のサブドメインの設定を行います
Route53のAレコードにサブドメインのURLが作成されます

```yml
  # -------------------------------------
  # Route 53
  # -------------------------------------
  ALBAliasRecord:
    Type: AWS::Route53::RecordSet
    Properties:
      HostedZoneId: !Ref HostZoneID
      Name: !Ref DomainName
      Type: A
      AliasTarget:
        HostedZoneId: !GetAtt InternetALB.CanonicalHostedZoneID
        DNSName: !GetAtt InternetALB.DNSName
```

## 実際に作成してみよう！
ALBを作成します
ACMを指定する際はALBと同じRegionのものを指定する必要があるので注意が必要です

![スクリーンショット 2024-01-15 12.58.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5a75c23a-f3a1-86e5-27e7-44c5dbe70b31.png)

![alb_stack.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/10e18b5c-50bc-6247-9ae3-6c15ea614b3d.png)

以下のようにALBのリスナーとターゲットグループが作成され、ヘルスチェックがHealthyになっていたら成功です

![スクリーンショット 2024-01-26 8.38.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d05105cd-5837-43f5-d10f-c02c38bee2f1.png)

![スクリーンショット 2024-01-15 13.49.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/06603e2b-369b-d525-52bc-f370bdb3707a.png)

## 参考
https://dev.classmethod.jp/articles/alb-route53-acm-build2/
