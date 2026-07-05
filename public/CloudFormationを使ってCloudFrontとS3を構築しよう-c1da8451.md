---
title: CloudFormationを使ってCloudFrontとS3を構築しよう！
tags:
  - AWS
  - S3
  - CloudFormation
  - route53
  - CloudFront
private: false
updated_at: '2024-01-15T11:18:04+09:00'
id: c1da8451e80e6526025d
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
CloudFormationを使ってCloudFrontとS3を構築する方法について解説します

## 前提
- Route53にドメインを登録済み
- ACMを発行済み(リージョンはバージニア北部)

## ディレクトリ構成
```
tree
.
└── templates
    ├── network
    |   └── cloudfront.yml
    └── storages
        ├── s3-bucket-for-frontend.yml   
        └── s3-bucket-policy-for-frontend.yml
```

## S3作成用のスタック
静的ファイルを格納するS3を作成します

```s3-bucket-for-frontend.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Stack"

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

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # S3
  # -------------------------------------
  # For Static Website Hosting
  AssetsBucket:
    Type: AWS::S3::Bucket
    Properties:
      BucketName: !Join
        - "-"
        - - !Sub "${ProjectName}-${Environment}-assets-with-origin-access-control"
          - !Select [0, !Split ["-", !Select [2, !Split ["/", !Ref AWS::StackId]]]]
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      VersioningConfiguration:
        Status: Enabled

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  AssetsBucketName:
    Value: !Ref AssetsBucket
  AssetsBucketArn:
    Value: !GetAtt AssetsBucket.Arn
  AssetsBucketDomainName:
    Value: !GetAtt AssetsBucket.RegionalDomainName

```

### S3のアクセス許可の設定
今回はCloudFront経由でS3へアクセスしたいので
- BlockPublicAcls
    - ストレージへのパブリックアクセスをブロック
- BlockPublicPolicy
    - 指定されたバケットポリシーでパブリックアクセスが許可されている場合、S3はPUT Bucketポリシーへの呼び出しを拒否
- IgnorePublicAcls
    - Amazon S3 はバケットとそれに含まれるオブジェクトのすべてのパブリックACLを無視
- RestrictPublicBuckets
    - アクセスをバケット所有者のアカウントおよびアクセスポイント所有者のアカウント内のAWSのサービスプリンシパルと承認されたユーザーのみに制限

を全てTrueにします

```yml
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
```

https://docs.aws.amazon.com/ja_jp/AmazonS3/latest/userguide/access-control-block-public-access.html

### S3の暗号化設定
S3バケットの暗号化設定を行います

```yml
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
```

https://docs.aws.amazon.com/ja_jp/AmazonS3/latest/userguide/serv-side-encryption.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-bucketencryption.html#cfn-s3-bucket-bucketencryption-serversideencryptionconfiguration

### S3のバージョニング
今回はバージョニングを有効にします

```yml
      VersioningConfiguration:
        Status: Enabled
```

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-properties-s3-bucket-publicaccessblockconfiguration.html

## S3のバケットポリシー作成用のスタック
CloudFrontからのアクセスを許可するためのバケットポリシーを作成します

```s3-bucket-policy-for-frontend.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Policy Stack"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "S3 Configuration"
        Parameters:
          - AssetsBucketName
          - AssetsBucketArn
          - CloudFrontAssetsDistributionID

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  AssetsBucketName:
    Description: "Enter the S3 assets bucket name (ex: example-assets-with-oac-xxxxxxxx)"
    Type: String
  AssetsBucketArn:
    Description: "Enter the S3 assets bucket ARN (ex: arn:aws:s3:::example-assets-with-oac-xxxxxxxx)"
    Type: String
  CloudFrontAssetsDistributionID:
    Description: "Enter the CloudFront Distribution ID for assets bucket (ex: XXXXXXXXXXXXXX)"
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # S3 Bucket Policy
  # -------------------------------------
  AssetsBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref AssetsBucketName
      PolicyDocument:
        Statement:
          - Effect: Allow
            Principal:
              Service: cloudfront.amazonaws.com
            Action:
              - s3:GetObject
              - s3:ListBucket
            Resource:
              - !Sub ${AssetsBucketArn}/*
              - !Ref AssetsBucketArn
            Condition:
              StringEquals:
                AWS:SourceArn: !Sub arn:aws:cloudfront::${AWS::AccountId}:distribution/${CloudFrontAssetsDistributionID}

```

### バケットポリシー
今回は指定したCloudFrontのディストリビューションがバケット自体をListできるポリシーとバケット内のオブジェクトをGetできるポリシーを付与します

```json
{
    "Version": "2008-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": [
                "s3:GetObject",
                "s3:ListBucket"
            ],
            "Resource": [
                "arn:aws:s3:::{バケット名}/*",
                "arn:aws:s3:::{バケット名}"
            ],
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::{アカウントID}:distribution/{ディストリビューションID}"
                }
            }
        }
    ]
}
```

https://docs.aws.amazon.com/ja_jp/AmazonCloudFront/latest/DeveloperGuide/private-content-restricting-access-to-s3.html

## CloudFrontのディストリビューション作成用のスタック
CloudFrontのディストリビューションを作成します

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
    Type: String
  # https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-properties-route53-recordset-aliastarget.html#cfn-route53-recordset-aliastarget-hostedzoneid
  # Specify Z2FDTNDATAQYW2. This is always the hosted zone ID when you create an alias record that routes traffic to a CloudFront distribution.
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

### Route53の設定
Route53内にAレコードを作成し、トラフィックのルーティング先をCloudFrontのディストリビューションに指定します

```yml
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
```

### CloudFrontのディストリビューションの設定
#### Origins
CloudFrontのオリジンの設定を行います
オリジンはS3に指定し、後ほど作成するOACの設定を行います

#### DefaultRootObject
ドメインにアクセスする際のルートページをindex.htmlに指定します

#### CustomErrorResponses
404を返す際はカスタムの404ページを表示させます

#### DefaultCacheBehavior
ビヘイビアの設定を行います
今回はビューワープロトコルポリシーをRedirect HTTP to HTTPSにします

#### ViewerCertificate
HTTPS通信ができるようSSL証明書の設定を行います

#### Aliases
代替ドメイン名の設定を行います

```yml
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
```

### OriginAccessControl(OAC)の設定
OACの設定を行うS3バケットを指定します

```yml
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
```

## 実際に作成してみよう！
### S3の作成
CloudFormationのコンソールからスタックを作成します
今回はスタック名をMyS3Frontend、environmentをdevにします

![スクリーンショット 2024-01-13 9.17.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9870dbd0-6cc8-99d9-6e0f-edf689aaee36.png)

以下のようにS3が作成されていたら成功です

![スクリーンショット 2024-01-13 9.16.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f7e98575-0831-fa85-acbc-a8f0191fd0d4.png)

S3を作成したらバケット内に静的ファイルをアップロードしましょう

![スクリーンショット 2024-01-15 11.06.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d5eddc1f-ee0d-4ea3-9f16-becf2a62d252.png)

### CloudFrontのディストリビューションの作成
CloudFormationのコンソールからスタックを作成します

![スクリーンショット 2024-01-13 9.34.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/09f26e83-98df-cc88-3393-e96b49084525.png)

AssestBucketDomainNameに以下のように記載します
```
my-project-dev-assets-with-origin-access-control-c2fa7500.s3.ap-northeast-1.amazonaws.com
```
![スクリーンショット 2024-01-13 10.51.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d6918fbc-9fe0-ef00-cef5-425ef9a69f87.png)

以下のようにCloudFrontのディストリビューションが作成されたら成功です
![distribution.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/efaa568b-8d00-b262-783e-090196a05cd3.png)


以下のようにCloudFrontのディストリビューションを紐づいたAレコードが作成されたら成功です

![route53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/26e91ab1-9069-8e56-e5d4-01e6992734f5.png)

### S3のバケットポリシーの作成
S3のバケットポリシーを作成します
![スクリーンショット 2024-01-13 9.21.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4d527b3d-b4f0-f692-5065-9b9462d97262.png)

以下のように作成されたら成功です
![スクリーンショット 2024-01-13 11.12.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ee4c3723-611b-bde3-57a0-3cf103c05a35.png)

## 実際にディストリビューションとドメインからアクセスしてみよう！
先ほど作成したS3バケットにindex.htmlをはじめとした静的ファイルをアップロードします
今回はCloudFrontにデフォルトルートオブジェクトをindex.htmlを設定するのでindex.htmlを忘れずにアップロードします

![スクリーンショット 2024-01-12 10.42.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f0592dd3-4ac7-8668-cc6f-4636624c78b6.png)

以下のようにディストリビューションとドメイン名からアクセスした際にindex.htmlが表示されたら成功です

![スクリーンショット 2024-01-12 11.02.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3734a8e2-b1bd-470e-91d9-63042bfc09ab.png)

カスタムの404ページが表示されたら成功です
![スクリーンショット 2024-01-15 11.05.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/957bbf06-7103-40b5-6450-2f140edddf90.png)

## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-cloudfront-distribution.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-s3-bucket.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-s3-bucketpolicy.html

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-route53-recordset.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-properties-cloudfront-distribution-distributionconfig.html

https://qiita.com/kobanyan/items/2e8001ce393a6c426861

