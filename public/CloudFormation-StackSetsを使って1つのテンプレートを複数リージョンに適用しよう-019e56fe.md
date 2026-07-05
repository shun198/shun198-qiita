---
title: CloudFormation StackSetsを使って1つのテンプレートを複数リージョンに適用しよう！
tags:
  - AWS
  - CloudFormation
  - StackSets
private: false
updated_at: '2026-07-05T20:53:20+09:00'
id: 019e56fef7a1d995e00d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
CloudFormation StackSetsを使って1つのテンプレートを複数リージョンに適用する方法について解説します

## 前提
- CloudFormationのスタックに関する基礎知識を有している

## StackSetとは
CloudFormation StackSetsを使うことで、1つのテンプレートから複数のAWSアカウント、リージョンに対しStackを作成することが可能になります

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html

ただし、複数のリージョンにスタックセットをデプロイする場合、デフォルトで有効になっていないリージョンを除外もしくは手動で有効化する必要があります
2024/06/20執筆時点では以下のリージョンではサポートされていません

|リージョン名|コード|
|---|---|
|アフリカ (ケープタウン)|af-south-1|
|アジア・パシフィック (香港)|ap-east-1|
|アジア・パシフィック (ハイデラバード)|ap-south-2|
|アジア・パシフィック (ジャカルタ)|ap-southeast-3|
|アジア・パシフィック (メルボルン)|ap-southeast-4|
|カナダ西部 (カルガリー)|ca-west-1|
|欧州 (チューリッヒ)|eu-central-2|
|欧州 (ミラノ)|eu-south-1|
|欧州 (スペイン)|eu-south-2|
|イスラエル (テルアビブ)|il-central-1|
|中東 (アラブ首長国連邦)|me-central-1|
|中東 (バーレーン)|me-south-1|

## StackSetを実行するためのロールの作成
### CloudFormationテンプレートの作成
StackSetを作成するロールと実行するロールの2種類が必要になるのでCloudFormationを使って作成します

```yaml
AWSTemplateFormatVersion: 2010-09-09
Description: "IAM Factory Settings Stack"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          Default: "StackSet Role Configuration"
        Parameters:
          - MasterAccountId

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  MasterAccountId:
    Type: String
    Description: "AWS Account ID of the master account (the account in which StackSets will be created)"
    MaxLength: 12
    MinLength: 12

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # IAM Role
  # -------------------------------------
  # CloudFormation が StackSet を作成する際に必要な IAM ロール
  StackSetAdminRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: AWSCloudFormationStackSetAdministrationRole
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: cloudformation.amazonaws.com
            Action:
              - sts:AssumeRole
      Path: /
      Policies:
        - PolicyName: AssumeExecutionRole
          PolicyDocument:
            Version: 2012-10-17
            Statement:
              - Effect: Allow
                Action:
                  - sts:AssumeRole
                Resource:
                  - arn:aws:iam::*:role/AWSCloudFormationStackSetExecutionRole

  # CloudFormation が StackSet を実行する際に必要な IAM ロール
  StackSetExecRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: AWSCloudFormationStackSetExecutionRole
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              AWS:
                - !Ref MasterAccountId
            Action:
              - sts:AssumeRole
      Path: /
      ManagedPolicyArns:
        - arn:aws:iam::aws:policy/AdministratorAccess

# -------------------------------------
# Output
# -------------------------------------
Outputs:
  StackSetAdminRoleArn:
    Value: !GetAtt StackSetAdminRole.Arn
  StackSetExecRoleArn:
    Value: !GetAtt StackSetExecRole.Arn

```

### 実際にロールを作成しよう！
以下のように
- AWSCloudFormationStackSetAdministrationRole
- AWSCloudFormationStackSetExecutionRole

の2種類のロールが作成されたら成功です

![スクリーンショット 2024-06-20 15.47.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/807caf85-9b23-878e-40b2-5a356be06aed.png)

![スクリーンショット 2024-06-20 15.50.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f2488fe5-45f8-ca5a-a501-c4390f38f6cc.png)

![スクリーンショット 2024-06-20 15.50.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fe11a2fe-36ec-149a-9575-6ab354efcd07.png)

## StackSetの作成
CloudFormation コンソールの左サイドペインから [StackSets] メニューを選択した後、画面右部の `StackSet の作成` ボタンをクリックします

![スクリーンショット 2024-06-20 15.53.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24b7c3df-82ba-8516-8775-f194bfa01011.png)

### テンプレートの選択
IAM管理ロールに先ほど作成した`AWSCloudFormationStackSetAdministrationRole`、IAM 実行ロール名には`AWSCloudFormationStackSetExecutionRole`を設定します
![スクリーンショット 2024-06-21 8.05.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/af0182e8-1faa-f944-d424-f59665deffc7.png)

作成するテンプレートを選択して`次へ`を押します
![スクリーンショット 2024-06-21 8.17.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c6d634ea-1865-e365-ba4e-d9053b81a4d3.png)

### StackSetの詳細設定
StackSet名、説明、テンプレートに設定したパラメータを記載していきます
![スクリーンショット 2024-06-21 8.17.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0ae2b48b-abad-8cc6-2b75-bbf3d1da91f9.png)

### StackSetのオプションの設定

今回は何も指定せずにそのまま`次へ`を押します
![スクリーンショット 2024-06-21 8.19.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/34fa1908-4e3c-6d4a-386a-c0b5ac60375c.png)

### デプロイオプションの設定
今回は`新しいスタックのデプロイ`、`スタックをアカウントにデプロイ`を選択し、アカウント番号を入力します

![スクリーンショット 2024-06-21 8.21.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/57579958-479c-a67d-2a31-81c9181e1707.png)

リージョンの指定では`すべてのリージョンを追加` ボタンを押し、デフォルトで有効になっていないリージョンを除外します
![スクリーンショット 2024-06-21 8.23.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bd7e64be-4d40-78ba-74a9-de03b7de97cb.png)

デプロイオプションでは以下の通りに設定します
- 同時アカウントの最大数: 100% (`割合 (%)` を選択し `100` と入力)
- 障害耐性: 100% (`割合 (%)` を選択し `100` と入力)
- リージョンの同時実行: どちらでも可 (リージョンの展開順序を考慮する必要がない場合は `並行` が早い)

### 確認画面 (レビュー)
内容に不備がないことを確認できたら、ページ最下部の `送信` ボタンを押します
![スクリーンショット 2024-06-21 8.27.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1f03a406-cec6-a659-32b4-786b9515f294.png)

## 実際に実行してみよう！
以下のようにStackが正常に作成されることが確認できたら成功です
![スクリーンショット 2024-06-21 8.29.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e9cec0f2-8215-399c-4032-85a88b6b3709.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/what-is-cfnstacksets.html
