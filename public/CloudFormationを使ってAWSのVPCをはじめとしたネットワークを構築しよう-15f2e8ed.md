---
title: CloudFormationを使ってAWSのVPCをはじめとしたネットワークを構築しよう！
tags:
  - AWS
  - CloudFormation
  - vpc
private: false
updated_at: '2024-02-06T07:47:15+09:00'
id: 15f2e8edc57629416ae7
organization_url_name: null
slide: false
---
## 概要
今回はCloudFormationを使って

- VPC
- パブリックサブネットとプライベートサブネット
- IGW
- ルートテーブルおよびルーティングの設定

を構築したいと思います

## 前提
- 東京リージョンを使用
- AWSを使用
- ネットワークに関する基本的な知識をある程度持っている

## ディレクトリ構成
構成は以下の通りです

```
tree
.
└── templates
    └── network
        └── vpc.yml
```

## vpc.yml
```vpc.yml
AWSTemplateFormatVersion: 2010-09-09
Description: 'VPC Stack'

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  # 入力パラメータのグループ化と順序を指定
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "Common Configuration"
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: "VPC Configuration"
        Parameters:
          - VPCCIDR
          - ELBPublicSubnet1CIDR
          - ELBPublicSubnet2CIDR
          - ECSPublicSubnet1CIDR
          - ECSPublicSubnet2CIDR
          - RDSPrivateSubnet1CIDR
          - RDSPrivateSubnet2CIDR

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Please type the ProjectName. (ex: my-project)"
    Type: String
    Default: my-project
    ConstraintDescription: "ProjectName is required."
    MinLength: 1
  Environment:
    Description: "Please select Environment."
    Type: String
    Default: dev
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."
  VPCCIDR:
    Description: "Please type the VPC CIDR."
    Type: String
    Default: 10.0.0.0/16
  ELBPublicSubnet1CIDR:
    Description: "Please type the ELB Public Subnet 1 CIDR."
    Type: String
    Default: 10.0.1.0/24
  ELBPublicSubnet2CIDR:
    Description: "Please type the ELB Public Subnet 2 CIDR."
    Type: String
    Default: 10.0.2.0/24
  ECSPublicSubnet1CIDR:
    Description: "Please type the ECS Public Subnet 1 CIDR."
    Type: String
    Default: 10.0.3.0/24
  ECSPublicSubnet2CIDR:
    Description: "Please type the ECS Public Subnet 2 CIDR."
    Type: String
    Default: 10.0.4.0/24
  RDSPrivateSubnet1CIDR:
    Description: "Please type the RDS Private Subnet 1 CIDR."
    Type: String
    Default: 10.0.5.0/24
  RDSPrivateSubnet2CIDR:
    Description: "Please type the RDS Private Subnet 2 CIDR."
    Type: String
    Default: 10.0.6.0/24

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # VPC
  # -------------------------------------
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCIDR
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-vpc
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # VPC内にインターネットゲートウェイがないとパブリックサブネットからインターネットへアクセスできないので作成
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          # Parametersで入力した値を対応する変数に置き換える
          # https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-sub.html
          Value: !Sub ${ProjectName}-${Environment}-igw
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # インターネットゲートウェイをVPCにアタッチする
  AttachInternetGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId : !Ref InternetGateway

  # -------------------------------------
  # Public Subnet
  # -------------------------------------
  ELBPublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: !Select [0, !GetAZs ""]
      VpcId: !Ref VPC
      CidrBlock: !Ref ELBPublicSubnet1CIDR
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-alb",
                !Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ELBPublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: !Select [1, !GetAZs ""]
      VpcId: !Ref VPC
      CidrBlock: !Ref ELBPublicSubnet2CIDR
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-alb",
                !Select [2, !Split ["-", !Select [1, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ECSPublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: !Ref ECSPublicSubnet1CIDR
      # パブリックIPv4アドレスの自動割り当て
      # パブリックなのでtrueにする
      MapPublicIpOnLaunch: true
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs ""]
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-ecs",
                !Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ECSPublicSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      CidrBlock: !Ref ECSPublicSubnet2CIDR
      MapPublicIpOnLaunch: true
      VpcId: !Ref VPC
      AvailabilityZone: !Select [1, !GetAZs ""]
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-ecs",
                !Select [2, !Split ["-", !Select [1, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  RDSPrivateSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      # パブリックIPv4アドレスの自動割り当て
      # プライベートなのでfalseにする
      CidrBlock: !Ref RDSPrivateSubnet1CIDR
      MapPublicIpOnLaunch: false
      # VPCのLogicalIDを!Refで参照してあげることでVPCのIDを自動的に当てはめる
      VpcId: !Ref VPC
      AvailabilityZone: !Select [0, !GetAZs ""]
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-priv-rds",
                !Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
              ],
            ]
  RDSPrivateSubnet2:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: !Select [1, !GetAZs ""]
      VpcId: !Ref VPC
      CidrBlock: !Ref RDSPrivateSubnet2CIDR
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-priv-rds",
                !Select [2, !Split ["-", !Select [1, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  # -------------------------------------
  # Public Route Table
  # -------------------------------------
  ELBPublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      # どのVPCと紐づけるか定義する
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-pub-alb-rtb
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  # ELBのルーティング
  ELBPublicRoute:
    Type: AWS::EC2::Route
    # インターネットゲートウェイと紐付ける
    DependsOn: AttachInternetGateway
    Properties:
      RouteTableId: !Ref ELBPublicRouteTable
      # インターネット(0.0.0.0/0)へのアクセスを許可
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
  # ルートテーブルとサブネットを紐づける
  ELBPublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref ELBPublicSubnet1
      RouteTableId: !Ref ELBPublicRouteTable
  ELBPublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref ELBPublicSubnet2
      RouteTableId: !Ref ELBPublicRouteTable
  ECSPublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-pub-ecs-rtb
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  ECSPublicRoute:
    Type: AWS::EC2::Route
    DependsOn: AttachInternetGateway
    Properties:
      RouteTableId: !Ref ECSPublicRouteTable
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
  ECSPublicSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref ECSPublicSubnet1
      RouteTableId: !Ref ECSPublicRouteTable
  ECSPublicSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref ECSPublicSubnet2
      RouteTableId: !Ref ECSPublicRouteTable
  # -------------------------------------
  # Private Route Table
  # -------------------------------------
  RDSPrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-priv-rds-rtb
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  RDSPrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref RDSPrivateSubnet1
      RouteTableId: !Ref RDSPrivateRouteTable
  RDSPrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref RDSPrivateSubnet2
      RouteTableId: !Ref RDSPrivateRouteTable

# -------------------------------------
# Outputs
# -------------------------------------
# https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/outputs-section-structure.html
Outputs:
  VPC:
    Description: "A reference to the created VPC."
    Value: !Ref VPC
  PublicSubnets:
    Description: "A list of the public subnets."
    Value:
      !Join [
        ",",
        [
          !Ref ECSPublicSubnet1,
          !Ref ECSPublicSubnet2,
          !Ref ELBPublicSubnet1,
          !Ref ELBPublicSubnet2,
        ],
      ]
  PrivateSubnets:
    Description: "A list of the private subnets."
    Value: !Join [",", [!Ref RDSPrivateSubnet1, !Ref RDSPrivateSubnet2]]
  ELBPublicSubnet1:
    Description: "A reference to the public subnet in the 1st Availability Zone."
    Value: !Ref ELBPublicSubnet1
  ELBPublicSubnet2:
    Description: "A reference to the public subnet in the 2nd Availability Zone."
    Value: !Ref ELBPublicSubnet2
  ECSPublicSubnet1:
    Description: "A reference to the public subnet in the 1st Availability Zone."
    Value: !Ref ECSPublicSubnet1
  ECSPublicSubnet2:
    Description: "A reference to the public subnet in the 2nd Availability Zone."
    Value: !Ref ECSPublicSubnet2
  RDSPrivateSubnet1:
    Description: "A reference to the private subnet in the 1st Availability Zone."
    Value: !Ref RDSPrivateSubnet1
  RDSPrivateSubnet2:
    Description: "A reference to the private subnet in the 2nd Availability Zone."
    Value: !Ref RDSPrivateSubnet2
```

1つずつ解説していきます

### Metadata
Metadataを使用する際に
```
AWS::CloudFormation::Interface:
```
と記載することで後述するParametersをグループ分けして見やすくすることができます
今回は
- Common Configuration(汎用的な設定)
    - プロジェクト名や環境(dev,stg,prd)などタグ付けに必要な変数
- VPC Configuration(VPCの設定)
    - VPC,ALB,ECS,RDSのCIDRの設定

2種類に分類します

```vpc.yml
# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  # 入力パラメータのグループ化と順序を指定
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "Common Configuration"
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: "VPC Configuration"
        Parameters:
          - VPCCIDR
          - ELBPublicSubnet1CIDR
          - ELBPublicSubnet2CIDR
          - ECSPublicSubnet1CIDR
          - ECSPublicSubnet2CIDR
          - RDSPrivateSubnet1CIDR
          - RDSPrivateSubnet2CIDR
```

### Parameters
Metadataで説明したパラメータのデフォルト値の設定などを行います
```vpc.yml
# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  ProjectName:
    Description: "Please type the ProjectName. (ex: my-project)"
    Type: String
    Default: my-project
    ConstraintDescription: "ProjectName is required."
    MinLength: 1
  Environment:
    Description: "Please select Environment."
    Type: String
    Default: dev
    # AllowedValuesを設定することでパラメータ指定時にドロップダウン形式で選択できる
    AllowedValues:
      - dev
      - stg
      - prd
    ConstraintDescription: "Environment must be select."
  VPCCIDR:
    Description: "Please type the VPC CIDR."
    Type: String
    Default: 10.0.0.0/16
  ELBPublicSubnet1CIDR:
    Description: "Please type the ELB Public Subnet 1 CIDR."
    Type: String
    Default: 10.0.1.0/24
  ELBPublicSubnet2CIDR:
    Description: "Please type the ELB Public Subnet 2 CIDR."
    Type: String
    Default: 10.0.2.0/24
  ECSPublicSubnet1CIDR:
    Description: "Please type the ECS Public Subnet 1 CIDR."
    Type: String
    Default: 10.0.3.0/24
  ECSPublicSubnet2CIDR:
    Description: "Please type the ECS Public Subnet 2 CIDR."
    Type: String
    Default: 10.0.4.0/24
  RDSPrivateSubnet1CIDR:
    Description: "Please type the RDS Private Subnet 1 CIDR."
    Type: String
    Default: 10.0.5.0/24
  RDSPrivateSubnet2CIDR:
    Description: "Please type the RDS Private Subnet 2 CIDR."
    Type: String
    Default: 10.0.6.0/24
```

### VPC
VPCを作成します
```vpc.yml
Resources:
  # -------------------------------------
  # VPC
  # -------------------------------------
  VPC:
    Type: AWS::EC2::VPC
    Properties:
      CidrBlock: !Ref VPCCIDR
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-vpc
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

### Internet Gateway
パブリックサブネットからインターネットへアクセスできるようにするためにVPC内にインターネットゲートウェイを作成します

```vpc.yml
  InternetGateway:
    Type: AWS::EC2::InternetGateway
    Properties:
      Tags:
        - Key: Name
          # Parametersで入力した値を対応する変数に置き換える
          # https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-sub.html
          Value: !Sub ${ProjectName}-${Environment}-igw
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # インターネットゲートウェイをVPCにアタッチする
  AttachInternetGateway:
    Type: AWS::EC2::VPCGatewayAttachment
    Properties:
      VpcId: !Ref VPC
      InternetGatewayId : !Ref InternetGateway
```

### パブリックサブネット
```vpc.yml
  ELBPublicSubnet1:
    Type: AWS::EC2::Subnet
    Properties:
      AvailabilityZone: !Select [0, !GetAZs ""]
      VpcId: !Ref VPC
      CidrBlock: !Ref ELBPublicSubnet1CIDR
      MapPublicIpOnLaunch: false
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-alb",
                !Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
              ],
            ]
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

ELBのパブリックサブネットを例に説明します
AvailabilityZoneをハードコーディングするのは推奨されていないので
```
!Select [0, !GetAZs ""]
```
を使用するとリージョン内のAZの配列のうち指定した配列のindex番号を取得します
(東京リージョンだと仮定してap-northeast-1aが指定されます)

詳細はAWSの公式ドキュメントを参照してください

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-select.html

タグについても説明します
```
!Select [0, !GetAZs ""]
```
でAZ(ap-norteast-1aと仮定します)を取得し、
!Split関数を使って"-"でAZを配列にして分離します
```
["ap","northeast","1a"]
```
その後、
```
!Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
```
をすることで
```
["ap","northeast","1a"]
```
の2番目のindexの値(1a)を取得します
最後に!Join関数を使って
"${ProjectName}-${Environment}-pub-alb"と"1a"を"-"で合体させます
- ProjectNameがmy-project
- Environmentがdev

と仮定すると、Nameタグの値が
```
my-project-dev-pub-albー1a
```
になり、AZに応じたより汎用的なタグ名になります

```
      Tags:
        - Key: Name
          Value:
            !Join [
              "-",
              [
                !Sub "${ProjectName}-${Environment}-pub-alb",
                !Select [2, !Split ["-", !Select [0, !GetAZs ""]]],
              ],
            ]
```

他のパブリックサブネットもプライベートサブネットも同様に作成します

### パブリックルートテーブル
ELBを例に説明します
ルートテーブルをどの

- サブネット
- VPC
- インタネットゲートウェイ
と紐づけるかと

ルーティング(パブリックなのですべてのIPアドレスを許可)
を設定する必要があります

```vpc.yml
  # -------------------------------------
  # Public Route Table
  # -------------------------------------
  ELBPublicRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      # どのVPCと紐づけるか定義する
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-pub-alb-rtb
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  # ELBのルーティング
  ELBPublicRoute:
    Type: AWS::EC2::Route
    # インターネットゲートウェイと紐付ける
    DependsOn: AttachInternetGateway
    Properties:
      RouteTableId: !Ref ELBPublicRouteTable
      # インターネット(0.0.0.0/0)へのアクセスを許可
      DestinationCidrBlock: 0.0.0.0/0
      GatewayId: !Ref InternetGateway
```

ECSも同様の設定を行います

### プライベートルートテーブル
プライベートルートテーブルからインターネットへアクセスすることはないのでInternetGatewayの設定は不要です

```vpc.yml
  # -------------------------------------
  # Private Route Table
  # -------------------------------------
  RDSPrivateRouteTable:
    Type: AWS::EC2::RouteTable
    Properties:
      VpcId: !Ref VPC
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-priv-rds-rtb
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
  RDSPrivateSubnet1RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref RDSPrivateSubnet1
      RouteTableId: !Ref RDSPrivateRouteTable
  RDSPrivateSubnet2RouteTableAssociation:
    Type: AWS::EC2::SubnetRouteTableAssociation
    Properties:
      SubnetId: !Ref RDSPrivateSubnet2
      RouteTableId: !Ref RDSPrivateRouteTable
```

### Outputs
Stack作成後に出力する情報を記載し、他のスタックでも利用できるようにします

```vpc.yml
# -------------------------------------
# Outputs
# -------------------------------------
# https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/outputs-section-structure.html
Outputs:
  VPC:
    Description: "A reference to the created VPC."
    Value: !Ref VPC
  PublicSubnets:
    Description: "A list of the public subnets."
    Value:
      !Join [
        ",",
        [
          !Ref ECSPublicSubnet1,
          !Ref ECSPublicSubnet2,
          !Ref ELBPublicSubnet1,
          !Ref ELBPublicSubnet2,
        ],
      ]
  PrivateSubnets:
    Description: "A list of the private subnets."
    Value: !Join [",", [!Ref RDSPrivateSubnet1, !Ref RDSPrivateSubnet2]]
  ELBPublicSubnet1:
    Description: "A reference to the public subnet in the 1st Availability Zone."
    Value: !Ref ELBPublicSubnet1
  ELBPublicSubnet2:
    Description: "A reference to the public subnet in the 2nd Availability Zone."
    Value: !Ref ELBPublicSubnet2
  ECSPublicSubnet1:
    Description: "A reference to the public subnet in the 1st Availability Zone."
    Value: !Ref ECSPublicSubnet1
  ECSPublicSubnet2:
    Description: "A reference to the public subnet in the 2nd Availability Zone."
    Value: !Ref ECSPublicSubnet2
  RDSPrivateSubnet1:
    Description: "A reference to the private subnet in the 1st Availability Zone."
    Value: !Ref RDSPrivateSubnet1
  RDSPrivateSubnet2:
    Description: "A reference to the private subnet in the 2nd Availability Zone."
    Value: !Ref RDSPrivateSubnet2
```

## 実際に作成してみよう！
今回作成したvpc.ymlを選択します
![スクリーンショット 2023-09-10 10.39.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7a812298-88a3-5986-f3e1-c3ef089b6860.png)

スタック名を記載します
今回はmyVPCにします
![スクリーンショット 2023-09-10 14.44.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2d963a19-a9f1-b3fb-c1df-24125f1ee663.png)

Parametersで作成したパラメータとデフォルト値が表示されていることを確認できます
また、Metadataを定義したことでパラメータが
- Common Configuration
- VPC Configuration

の2つに分類されていることが確認できました

![スクリーンショット 2023-09-10 15.29.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/905e219c-9572-5040-e132-88265e1d15ef.png)
![スクリーンショット 2023-09-10 15.29.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1e2ee0a8-84ab-550a-f2ca-6aeec9f41060.png)

スタックのオプションは特に何も選択せずに次へを押します
![スクリーンショット 2023-09-10 14.48.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dab71a62-f7bd-d40b-33e9-33ee2c6f403b.png)

問題なければ送信を押します
![スクリーンショット 2023-09-10 14.48.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1eef56a6-58c7-5a01-1b8d-e2e36d15b167.png)

以下のように全てのリソースの作成が完了したら成功です
![スクリーンショット 2023-09-10 14.52.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3aacd6c9-506d-b1bc-0ce6-c961ef357aba.png)

出力も確認できました
![スクリーンショット 2023-09-10 14.53.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b98b25f0-9a71-f70e-03ab-d5f198abf2dd.png)

## リソースを確認しよう！
以下のようにリソースが作成されたら成功です

### VPC
![スクリーンショット 2023-09-10 15.35.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f248c1a3-9e38-5062-916f-bd29b75e1ca1.png)

### サブネット
![スクリーンショット 2023-09-10 15.37.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c8c3903f-e4d8-e977-09d1-fad8e833e486.png)

### インターネットゲートウェイ
![スクリーンショット 2023-09-10 15.38.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fbd9f0a8-69f9-9962-2b29-75105c00f428.png)

## 不要なリソースを削除しよう！
不要な課金を防ぐために使用しないリソースは削除しましょう
![スクリーンショット 2023-09-10 15.07.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/11b0b1af-098b-10c3-0257-b1aebcddda26.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-ec2-vpc.html

https://zenn.dev/tmasuyama1114/articles/aws-cloudformation-basics#%E3%83%86%E3%83%B3%E3%83%97%E3%83%AC%E3%83%BC%E3%83%88%E3%83%95%E3%82%A1%E3%82%A4%E3%83%AB%E3%81%AE%E5%85%A8%E6%96%87

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-select.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-join.html

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/intrinsic-function-reference-getavailabilityzones.html

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudformation-interface.html

https://zenn.dev/ano/articles/c5eedcc31b30e2
