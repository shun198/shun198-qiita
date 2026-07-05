---
title: CloudFormationでManaged Preflix Listを作成しよう！
tags:
  - AWS
  - CloudFormation
  - IPアドレス
  - ManagedPrefixList
private: false
updated_at: '2024-07-05T15:08:56+09:00'
id: abc2cc555bcd39f65a74
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
CloudFormationでManaged Preflix Listを作成する方法について解説します

## Managed Prefix Listとは
簡単に説明するとIPアドレスを格納するリスト群です


## Managed Prefix Listの作成
今回はPrefix Listの作成とUserAとUserBのIPv4のIPアドレスを登録するCloudFormationのテンプレートを作成します
主に

- セキュリティグループおよびネットワークACLのIPアドレスの管理
- WAFが許可、拒否するIPアドレスの管理

などで使用されます

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "Managed Prefix List for my-project"

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
      - Label:
          default: "Managed Prefix List Configuration"
        Parameters:
          - UserA
          - UserB

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
  UserA:
    Description: "Enter the IP addresses for UserA (ex: 0.0.0.0/32)"
    Type: String
  UserB:
    Description: "Enter the IP addresses for UserB (ex: 1.1.1.1/32)"
    Type: String

Resources:
  # -------------------------------------
  # Managed Prefix List
  # -------------------------------------
  PrefixList:
    Type: AWS::EC2::PrefixList
    Properties:
      PrefixListName: "IP Address Lists For Remote Developers"
      AddressFamily: "IPv4"
      MaxEntries: 10
      Entries:
        - Cidr: !Ref UserA
          Description: "UserA Remote User IP List"
        - Cidr: !Ref UserB
          Description: "UserB Remote User IP List"
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  PrefixList:
    Value: !Ref PrefixList

```

## 実際に作成してみよう！
以下のようにPrefix Listが作成され、指定したIPアドレスが登録されたら成功です

![スクリーンショット 2024-07-05 15.00.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f1dbbd2-11c6-e189-fae6-d933c74c592a.png)

![スクリーンショット 2024-07-05 15.00.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/35ba0892-3ca2-ff67-1981-29b7551f44b0.png)

![スクリーンショット 2024-07-05 15.01.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6fbf6c38-a053-766b-534a-cf8eca572f6b.png)


## まとめ
Managed Preflix Listをコード化できるのは便利なものの、IPアドレスを配列として複数以上登録できるようにしてほしいですよねー
CloudFormationで実現できる方法がわかり次第追記していきたいと思います

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-prefixlist.html#cfn-ec2-prefixlist-entries

https://www.idnet.co.jp/column/page_188.html
