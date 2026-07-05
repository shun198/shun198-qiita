---
title: CloudFormationを使ってAmplifyとCloudFrontを構築してNext.jsのアプリケーションを自動デプロイしよう！
tags:
  - AWS
  - CloudFormation
  - CloudFront
  - Next.js
  - amplify
private: false
updated_at: '2024-02-27T15:04:02+09:00'
id: c1e7c192a98e2c42000c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
CloudFormationを使ってAmplifyを構築する方法について解説します

## 前提
- Next.jsのアプリケーションを作成済み
- Route53にドメインを設定済み

## ディレクトリ構成
```
tree
・
├── application # Next.jsのアプリケーションの格納先
└── templates
    └── network
        ├── amplify.yml
        └── cloudfront.yml
```

## 実装
- amplify.yml
- cloudfront.yml

を順番に実装します
また、今回はCloudFrontについて詳しく説明しないので詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/312031d80455418d1e8d

https://qiita.com/shun198/items/c1da8451e80e6526025d

```amplify.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Amplify Admin Frontend Hosting Stack"

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
          default: "Amplify Configuration"
        Parameters:
          # GitHubへのread write権限を付与するため
          - GitHubAccessToken
          - GitHubRepoURL
          - SourceBranchName
          # For Amplify
          - AmplifyDomainName
          - AmplifySubDomainPrefix
          - AmplifyPlatform

# -------------------------------------
# Parameters
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
  GitHubAccessToken:
    Description: "Enter the Github personal access token. (ex: ghp_xxxxxxxxxx)"
    Type: String
    NoEcho: true
  GitHubRepoURL:
    Description: "Enter the Github repository URL."
    Type: String
  SourceBranchName:
    Description: "Enter the source branch name in GitHub frontend repository. (ex: main)"
    Type: String
  AmplifyDomainName:
    Description: "Enter the custom Amplify domain name. (Alias) (ex: example.com)"
    Type: String
  AmplifySubDomainPrefix:
    Description: "Enter the custom Amplify domain name subdomain prefix. (ex: amplify)"
    Type: String
  # SSRを使用する際はWEB_COMPUTEを選択
  AmplifyPlatform:
    Description: "Select the Amplify app platform. (when using SSR: WEB_COMPUTE)"
    Type: String
    Default: WEB_COMPUTE
    AllowedValues:
      - WEB
      - WEB_COMPUTE
      - WEB_DYNAMIC

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Amplify Hosting
  # -------------------------------------
  AmplifyFrontHosting:
    Type: AWS::Amplify::App
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-admin-front-amplify
      # GitHubにアクセスするために必要
      AccessToken: !Ref GitHubAccessToken
      Repository: !Ref GitHubRepoURL
      Platform: !Ref AmplifyPlatform
      # Automatically disconnect a branch in Amplify Hosting when you delete a branch from your Git repository
      EnableBranchAutoDeletion: true
      IAMServiceRole: !Ref AmplifyServiceRole
      # 環境変数
      EnvironmentVariables:
        - Name: _DISABLE_L2_CACHE
          Value: true
        - Name: AMPLIFY_MONOREPO_APP_ROOT
          Value: application
      BuildSpec: |
        version: 1
        applications:
          - appRoot: application
            frontend:
              phases:
                preBuild:
                  commands:
                    - npm ci
                build:
                  commands:
                    - npm run build
              artifacts:
                baseDirectory: .next
                files:
                  - "**/*"
              cache:
                paths:
                  - "node_modules/**/*"
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-front-amplify
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment

  # -------------------------------------
  # Amplify Branch
  # -------------------------------------
  AmplifyBranch:
    Type: AWS::Amplify::Branch
    Properties:
      AppId: !GetAtt AmplifyFrontHosting.AppId
      BranchName: !Ref SourceBranchName
      EnableAutoBuild: true
      EnablePullRequestPreview: false
      Framework: Next.js - SSR
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
        - Key: BranchName
          Value: !Ref SourceBranchName

  # -------------------------------------
  # Amplify Custom Domain
  # -------------------------------------
  AmplifyCustomDomain:
    DependsOn: AmplifyBranch
    Type: AWS::Amplify::Domain
    Properties:
      AppId: !GetAtt AmplifyFrontHosting.AppId
      DomainName: !Ref AmplifyDomainName
      SubDomainSettings:
        - Prefix: !Ref AmplifySubDomainPrefix
          BranchName: !Ref SourceBranchName

  # -------------------------------------
  # Amplify Service Role
  # -------------------------------------
  AmplifyServiceRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub AmplifyServiceRoleForCWL-${ProjectName}-${Environment}-front
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Service: amplify.amazonaws.com
            Action:
              - sts:AssumeRole
  AmplifyServiceRolePolicy:
    Type: AWS::IAM::Policy
    Properties:
      PolicyName: !Sub AmplifyAccessForCWL-${ProjectName}-${Environment}-front
      PolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Action:
              - logs:CreateLogStream
              - logs:CreateLogGroup
              - logs:DescribeLogGroups
              - logs:PutLogEvents
            Resource: "*"
      Roles:
        - Ref: AmplifyServiceRole

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  AmplifyAppID:
    Value: !GetAtt AmplifyFrontHosting.AppId
  AmplifyCustomDomainURL:
    Value: !Sub ${AmplifySubDomainPrefix}.${AmplifyCustomDomain.DomainName}

```

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
          - AmplifyURL
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
    Default: example.com
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
  AmplifyURL:
    Type: String
    Description: "Enter the Amplify URL. (ex: <branch name>.<random number>.amplifyapp.com)"
  CachePolicy:
    Description: "Select the CloudFront cache policy"
    Type: String
    Default: CachingDisabled
    AllowedValues:
      - CachingOptimized
      - CachingDisabled
      - CachingOptimizedForUncompressedObjects
      - Elemental-MediaPackage
      - Amplify
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
        - Id: Amplify
          DomainName: !Ref AmplifyURL
          CustomOriginConfig:
            OriginProtocolPolicy: https-only
        Enabled: true
        Comment: "Amplify Hosting Distribution"
        CustomErrorResponses:
          - ErrorCachingMinTTL: 0
            ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /404/index.html
        DefaultCacheBehavior:
          CachePolicyId: !FindInMap [CachePolicyIds, !Ref CachePolicy , Id]
          ResponseHeadersPolicyId: !FindInMap [ResponseHeadersPolicyIds, !Ref ResponseHeadersPolicy, Id]
          TargetOriginId: Amplify
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
# Outputs
# -------------------------------------
Outputs:
  AssetsDistributionID:
    Value: !Ref AssetsDistribution

```

### Amplifyの作成
Amplifyのアプリケーションを作成する設定を記載します

```yml
  AmplifyFrontHosting:
    Type: AWS::Amplify::App
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-admin-front-amplify
      # GitHubにアクセスするために必要
      AccessToken: !Ref GitHubAccessToken
      Repository: !Ref GitHubRepoURL
      Platform: !Ref AmplifyPlatform
      # Automatically disconnect a branch in Amplify Hosting when you delete a branch from your Git repository
      EnableBranchAutoDeletion: true
      IAMServiceRole: !Ref AmplifyServiceRole
      # 環境変数
      EnvironmentVariables:
        - Name: _DISABLE_L2_CACHE
          Value: true
        - Name: AMPLIFY_MONOREPO_APP_ROOT
          Value: application
      BuildSpec: |
        version: 1
        applications:
          - appRoot: application
            frontend:
              phases:
                preBuild:
                  commands:
                    - npm ci
                build:
                  commands:
                    - npm run build
              artifacts:
                baseDirectory: .next
                files:
                  - "**/*"
              cache:
                paths:
                  - "node_modules/**/*"
      Tags:
        - Key: Name
          Value: !Sub ${ProjectName}-${Environment}-front-amplify
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
```

今回はGitHubと連携するので後ほど作成するアクセストークンとリポジトリのURLを連携します

```yml
AccessToken: !Ref GitHubAccessToken
Repository: !Ref GitHubRepoURL
```

今回はNext.js(SSR)のデプロイを行うのでプラットフォームをWEB_COMPUTEにします
```yml
Platform: !Ref AmplifyPlatform
```

環境変数の設定を行います
- AMPLIFY_MONOREPO_APP_ROOT


```yml
  EnvironmentVariables:
    - Name: AMPLIFY_MONOREPO_APP_ROOT
      Value: application
```

アプリケーションが起動するリポジトリ内のルートに今回はapplicationを指定します

https://docs.aws.amazon.com/ja_jp/amplify/latest/userguide/monorepo-configuration.html

アプリケーションのbuildを行うためのBuildSpecの設定を行います
フロントエンドのソースコードをbuildするのでfrontendと記載します
また、applicationフォルダ内にコードを格納している場合はappRootを指定するとappRoot内のコードをbuildすることができます

```yml
  BuildSpec: |
    version: 1
    applications:
      - appRoot: application
        frontend:
          phases:
            preBuild:
              commands:
                - npm ci
            build:
              commands:
                - npm run build
          artifacts:
            baseDirectory: .next
            files:
              - "**/*"
          cache:
            paths:
              - "node_modules/**/*"
```

### ブランチの設定
ブランチの設定を行います
フレームワークに`Next.js - SSR`を指定します

```yml
  AmplifyBranch:
    Type: AWS::Amplify::Branch
    Properties:
      AppId: !GetAtt AmplifyFrontHosting.AppId
      BranchName: !Ref SourceBranchName
      EnableAutoBuild: true
      EnablePullRequestPreview: false
      Framework: Next.js - SSR
      Tags:
        - Key: ProjectName
          Value: !Ref ProjectName
        - Key: Environment
          Value: !Ref Environment
        - Key: BranchName
          Value: !Ref SourceBranchName
```

### ドメインの設定
Route53に設定したドメインとの連携とAmplifyのドメインの設定を行います

```yml
  AmplifyCustomDomain:
    DependsOn: AmplifyBranch
    Type: AWS::Amplify::Domain
    Properties:
      AppId: !GetAtt AmplifyFrontHosting.AppId
      DomainName: !Ref AmplifyDomainName
      SubDomainSettings:
        - Prefix: !Ref AmplifySubDomainPrefix
          BranchName: !Ref SourceBranchName
```

## CloudFrontの作成
CloudFrontのディストリビューションのオリジンにAmplifyのオリジンを指定します

```yml
  # -------------------------------------
  # CloudFront Distribution
  # -------------------------------------
  AssetsDistribution:
    Type: AWS::CloudFront::Distribution
    Properties:
      DistributionConfig:
        Origins:
        - Id: Amplify
          DomainName: !Ref AmplifyURL
          CustomOriginConfig:
            OriginProtocolPolicy: https-only
        Enabled: true
        Comment: "Amplify Hosting Distribution"
        CustomErrorResponses:
          - ErrorCachingMinTTL: 0
            ErrorCode: 404
            ResponseCode: 200
            ResponsePagePath: /404/index.html
        DefaultCacheBehavior:
          CachePolicyId: !FindInMap [CachePolicyIds, !Ref CachePolicy , Id]
          ResponseHeadersPolicyId: !FindInMap [ResponseHeadersPolicyIds, !Ref ResponseHeadersPolicy, Id]
          TargetOriginId: Amplify
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

## GitHubのアクセストークンの作成
AmplifyとGitHubを連携するためのアクセストークンを作成します
今回は有効期限を設定せず、全スコープを選択します

![スクリーンショット 2024-02-16 10.19.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ad9f9314-6a4c-93f3-4b67-15dffb7e08e3.png)

## 実際に作成してみよう！
CloudFormationでAmplifyを作成します

![amplify_cloudformation.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a8bbf793-ea71-a25c-9d7d-a5de11869374.png)

以下のように作成されたら成功です

![amplify_general_settings.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b7c0e32b-90c7-5e7e-1146-10077f5f13a2.png)

ドメイン管理でカスタムドメインとAmplifyのドメインが設定されていることを確認します

![amplify_domain.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3ca5fd10-6dc1-0060-b5e0-8127361c7ff8.png)

ビルドの設定でCloudFormationに設定したbuildspecの記述がamplify.ymlに反映されていることを確認します

![スクリーンショット 2024-02-16 11.41.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/46dd5b6c-2060-c72a-0c0e-bf1dc05a1fe1.png)

今回はNode.jsのv20.10.0を使用していますが、バージョンは以下のように手動で設定する必要があります

![スクリーンショット 2024-02-16 11.42.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc185599-5706-1a07-e3ff-b2fa45fda14a.png)

設定した環境変数が反映されていることを確認します

![スクリーンショット 2024-02-27 11.47.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/521378fd-c748-fea7-ba60-0fae85fb6f62.png)

続いてCloudFormationでCloudFrontを作成します

![cloudfront_conf_1.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a910fac7-6601-64ec-eebc-981e9832f2b7.png)

![cloudfront_conf_2.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/912a0d6c-aa85-783b-5929-f39d941e844d.png)

以下のようにAmplifyのオリジンをCloudFrontに登録できたら成功です

![cloudfront_general.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fb7f1b59-3218-ef2f-7ad2-5bbceab33ccf.png)

![cloudfront_origin.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/95d7664e-d27a-0f64-df2c-40544effb1a2.png)


## デプロイしてみよう！
初回は手動でデプロイを実行します
![スクリーンショット 2024-02-27 11.48.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fcc42b16-61ec-2c45-050d-d169349d34fe.png)

以下のようにデプロイが成功し、アプリケーションが表示されたら成功です

![スクリーンショット 2024-02-16 11.41.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8d71ea61-f61b-9b2d-fc3e-631018cab4e2.png)

![スクリーンショット 2024-02-20 10.45.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/75d6d1a2-dedc-fe9b-5e6d-d3a71e19bf86.png)


## 参考
https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-amplify-app.html

https://zenn.dev/cureapp/articles/amplify-hosting-troubleshooting

https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-amplify-branch.html
