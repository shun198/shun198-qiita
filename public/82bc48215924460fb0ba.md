---
title: Nested Stackを使って複数以上のCloudFormationのStackをまとめて構築しよう！
tags:
  - AWS
  - S3
  - CloudFormation
private: false
updated_at: '2024-07-01T07:40:43+09:00'
id: 82bc48215924460fb0ba
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
Nested Stackを使うと複数以上のテンプレートを同時に作成できるので開発効率が上がってとても便利です
今回はフロントエンドで使用する
- Amplify
- CloudFront

をNested Stackを使って作成する方法について解説します

## 前提
- 今回はAmplifyとCloudFrontをNested Stackを使って同時に作成していきます
- ACMをus-east-1に作成済み
- GitHub用のPATを作成済み

## Nested Stackとは
CloudFormationテンプレートの中で別のCloudFormationスタックを参照し、デプロイする方法です
ネストされたスタックを使用することで複数以上のテンプレートをより管理、デプロイしやすくなります

## テンプレートを保存するS3バケットの作成
Nested Stackを使う際はS3バケット内のテンプレートファイルを参照する必要があります

```nested-stack-bucket.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket Factory Settings Stack"

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

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # S3
  # -------------------------------------
  # For CloudFormation Templates
  CloudFormationTemplatesBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub cf-templates-${ProjectName}-${Environment}-${AWS::Region}
      PublicAccessBlockConfiguration:
        BlockPublicAcls: true
        BlockPublicPolicy: true
        IgnorePublicAcls: true
        RestrictPublicBuckets: true
      VersioningConfiguration:
        Status: Enabled
      LifecycleConfiguration:
        Rules:
          - Id: ExpiresAfter365DaysFor4thOlderVersion
            Status: Enabled
            NoncurrentVersionExpiration:
              NewerNoncurrentVersions: 3
              NoncurrentDays: 365

# -------------------------------------
# Output Parameters
# -------------------------------------
Outputs:
  CloudFormationTemplatesBucketName:
    Value: !Ref CloudFormationTemplatesBucket
  CloudFormationTemplatesBucketArn:
    Value: !GetAtt CloudFormationTemplatesBucket.Arn
```

### 実際に作成してみよう！
以下のようにバケットが作成されたら成功です
![スクリーンショット 2024-06-29 21.31.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/da0a2769-a624-e430-32cc-c3bfb82518a7.png)

## Amplifyの作成
Amplify用のStackを作成します
```amplify.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Amplify Frontend Hosting Stack"

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
          - AmplifyBasicUserName
          - AmplifyBasicPassword
          - APIURL
          - FetchCredential
          - ALBHeaderAuthName
          - ALBHeaderAuthValue

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
    ConstraintDescription: "Environment must be select"
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
    Description: "Enter the custom Amplify domain name. (Alias) (ex: shun-practice.com)"
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
  AmplifyBasicUserName:
    Description: "Enter the Amplify basic auth username."
    Type: String
    MinLength: 1
    MaxLength: 255
    ConstraintDescription: "AmplifyBasicUserName must be 1 to 225 characters."
  AmplifyBasicPassword:
    Description: "Enter the Amplify basic auth password."
    Type: String
    NoEcho: true
    MinLength: 7
    MaxLength: 255
    ConstraintDescription: "AmplifyBasicPassword must be 7 to 225 characters."
  APIURL:
    Description: "Enter the API URL for backend. (ex: https://api.shun-practice.com)"
    Type: String
  FetchCredential:
    Description: "Enter the auth settings for API fetch from frontend."
    Type: String
    Default: include
  ALBHeaderAuthName:
    Description: "Enter the ALB header auth name. (ex: X-Auth-ALB)"
    Type: String
  ALBHeaderAuthValue:
    Description: "Enter the ALB header auth value."
    Type: String

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # Amplify Hosting
  # -------------------------------------
  # https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/aws-resource-amplify-app.html
  AmplifyFrontHosting:
    Type: AWS::Amplify::App
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-front-amplify
      # GitHubにアクセスするために必要
      AccessToken: !Ref GitHubAccessToken
      Repository: !Ref GitHubRepoURL
      Platform: !Ref AmplifyPlatform
      # Automatically disconnect a branch in Amplify Hosting when you delete a branch from your Git repository
      EnableBranchAutoDeletion: true
      BasicAuthConfig:
        EnableBasicAuth: true
        Username: !Ref AmplifyBasicUserName
        Password: !Ref AmplifyBasicPassword
      IAMServiceRole: !Ref AmplifyServiceRole
      # 環境変数
      EnvironmentVariables:
        - Name: NEXT_PUBLIC_API_BASE_URL
          Value: !Ref APIURL
        - Name: NEXT_PUBLIC_CREDENTIALS
          Value: !Ref FetchCredential
        - Name: NEXT_PUBLIC_AUTH_NAME
          Value: !Ref ALBHeaderAuthName
        - Name: NEXT_PUBLIC_AUTH_VALUE
          Value: !Ref ALBHeaderAuthValue
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
                    - curl https://get.volta.sh | bash
                    - source ~/.bash_profile
                    - volta install node
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
  AmplifyBasicAuthCredentials:
    Value: !Join
      - " "
      - - Basic
        - Fn::Base64: !Sub ${AmplifyBasicUserName}:${AmplifyBasicPassword}
```

## CloudFrontの作成
今回はCloudFrontにbasic認証をかけます
IDは`test`、PWは`Test012345678`です

```
echo -n "test:Test012345678" | base64
dGVzdDpUZXN0MDEyMzQ1Njc4
```

CloudFront用のStackを作成します
```cloufront.yml
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
          - DomainName
      - Label:
          default: "CloudFront Configuration"
        Parameters:
          - CloudFrontHostZoneID
          - ACMPublicCertificateArn
          - AmplifyURL
          - CachePolicy
          - ResponseHeadersPolicy
          - WebACLArn

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
  AmplifyURL:
    Type: String
    Description: "Enter the Amplify URL. (ex: <branch name>.<random number>.amplifyapp.com)"
  AuthHeaderValue:
    Description: "Enter the encoded Amplify basic auth credentials"
    Type: String
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
  WebACLArn:
    Description: "Enter the ARN of the WAFv2 to apply to CloudFront (ex: arn:aws:wafv2:us-east-1:012345678910:global/webacl/example/xxxxx)"
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
        - Id: Amplify
          DomainName: !Ref AmplifyURL
          CustomOriginConfig:
            OriginProtocolPolicy: https-only
          OriginCustomHeaders:
            - HeaderName: Authorization
              HeaderValue: !Ref AuthHeaderValue
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
          FunctionAssociations:
            - EventType: viewer-request
              FunctionARN: !Ref CloudFrontFunctionForBasicAuth
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
        WebACLId: !Ref WebACLArn

  # For CloudFront Functions
  # https://dev.classmethod.jp/articles/apply-basic-authentication-password-with-cloudfront-functions/
  CloudFrontFunctionForBasicAuth:
    Type: AWS::CloudFront::Function
    Properties:
      Name: !Sub ${ProjectName}-${Environment}-BasicAuth
      AutoPublish: true
      FunctionCode: |-
        function handler(event) {
          var request = event.request;
          var headers = request.headers;
          // echo -n user:pass | base64
          var authString = "Basic dGVzdDpUZXN0MDEyMzQ1Njc4";
          if (
            typeof headers.authorization === "undefined" ||
            headers.authorization.value !== authString
          ) {
            return {
              statusCode: 401,
              statusDescription: "Unauthorized",
              headers: {"www-authenticate": {value: "Basic"}}
            };
          }
          return request;
        }
      FunctionConfig:
        Comment: "Function for basic authentication."
        Runtime: cloudfront-js-1.0

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  AssetsDistributionID:
    Value: !Ref AssetsDistribution
```

## Nested Stackの作成
CloudFormationでは`AWS::CloudFormation::Stack`を使って
先ほど作成した子スタック(AmplifyとCloudFrontのスタック)を参照します
参照する際はS3内のURLを指定します
また、Nested Stack作成時に子スタックのパラメータを渡すよう設定します

```frontend.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "Frontend Stack (CloudFront, Amplify)"

# -------------------------------------
# Metadata
# -------------------------------------
Metadata:
  AWS::CloudFormation::Interface:
    ParameterGroups:
      - Label:
          default: "CloudFormation Configuration"
        Parameters:
          - CloudFrontTemplateURL
          - AmplifyTemplateURL
      - Label:
          default: "Project Configuration"
        Parameters:
          - ProjectName
          - Environment
      - Label:
          default: "CloudFront Configuration"
        Parameters:
          - HostZoneID
          - DomainName
          - ACMPublicCertificateArn
          - CachePolicy
          - ResponseHeadersPolicy
          - WebACLArn
      - Label:
          default: "Amplify Configuration"
        Parameters:
          - GitHubAccessToken
          - GitHubRepoURL
          - SourceBranchName
          - AmplifySubDomainPrefix
          - AmplifyPlatform
          - AmplifyBasicUserName
          - AmplifyBasicPassword
          - APIURL
          - FetchCredential
          - ALBHeaderAuthName
          - ALBHeaderAuthValue

# -------------------------------------
# Parameters
# -------------------------------------
Parameters:
  # -------------------------------------
  # CloudFormation
  # -------------------------------------
  CloudFrontTemplateURL:
    Description: "Enter the CloudFront template object URL in S3 bucket"
    Type: String
  AmplifyTemplateURL:
    Description: "Enter the Amplify template object URL in S3 bucket"
    Type: String
  # -------------------------------------
  # Project
  # -------------------------------------
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
    ConstraintDescription: "Environment must be select"
  # -------------------------------------
  # CloudFront
  # -------------------------------------
  HostZoneID:
    Description: "Select the Route 53 Hosted Zone ID"
    Type: AWS::Route53::HostedZone::Id
  DomainName:
    Description: "Enter the cloudfront domain name (Alias) (ex: shun-practice.com)"
    Type: String
  ACMPublicCertificateArn:
    Description: "Enter the ACM public certificate ARN for global region"
    Type: String
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
  WebACLArn:
    Description: "Enter the ARN of the WAFv2 to apply to CloudFront. (ex: arn:aws:wafv2:us-east-1:012345678910:global/webacl/example/xxxxx)"
    Type: String
  # -------------------------------------
  # Amplify
  # -------------------------------------
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
    Description: "Enter the custom Amplify domain name. (Alias) (ex: shun-practice.com)"
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
  AmplifyBasicUserName:
    Description: "Enter the Amplify basic auth username"
    Type: String
    MinLength: 1
    MaxLength: 255
    ConstraintDescription: "AmplifyBasicUserName must be 1 to 225 characters"
  AmplifyBasicPassword:
    Description: "Enter the Amplify basic auth password"
    Type: String
    NoEcho: true
    MinLength: 7
    MaxLength: 255
    ConstraintDescription: "AmplifyBasicPassword must be 7 to 225 characters"
  APIURL:
    Description: "Enter the API URL for backend. (ex: https://api.shun-practice.com)"
    Type: String
  FetchCredential:
    Description: "Enter the auth settings for API fetch from frontend."
    Type: String
    Default: include
  ALBHeaderAuthName:
    Description: "Enter the ALB header auth name. (ex: X-Auth-ALB)"
    Type: String
  ALBHeaderAuthValue:
    Description: "Enter the ALB header auth value."
    Type: String
Resources:
  # -------------------------------------
  # CloudFront Stack
  # -------------------------------------
  CloudFrontStack:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Ref CloudFrontTemplateURL
      Parameters:
        ProjectName: !Ref ProjectName
        Environment: !Ref Environment
        HostZoneID: !Ref HostZoneID
        DomainName: !Ref DomainName
        ACMPublicCertificateArn: !Ref ACMPublicCertificateArn
        AmplifyURL: !GetAtt AmplifyStack.Outputs.AmplifyCustomDomainURL
        AuthHeaderValue: !GetAtt AmplifyStack.Outputs.AmplifyBasicAuthCredentials
        CachePolicy: !Ref CachePolicy
        ResponseHeadersPolicy: !Ref ResponseHeadersPolicy
        WebACLArn: !Ref WebACLArn
  # -------------------------------------
  # Amplify Stack
  # -------------------------------------
  AmplifyStack:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::CloudFormation::Stack
    Properties:
      TemplateURL: !Ref AmplifyTemplateURL
      Parameters:
        ProjectName: !Ref ProjectName
        Environment: !Ref Environment
        GitHubAccessToken: !Ref GitHubAccessToken
        GitHubRepoURL: !Ref GitHubRepoURL
        SourceBranchName: !Ref SourceBranchName
        AmplifyDomainName: !Ref DomainName
        AmplifySubDomainPrefix: !Ref AmplifySubDomainPrefix
        AmplifyPlatform: !Ref AmplifyPlatform
        AmplifyBasicUserName: !Ref AmplifyBasicUserName
        AmplifyBasicPassword: !Ref AmplifyBasicPassword
        APIURL: !Ref APIURL
        FetchCredential: !Ref FetchCredential
        ALBHeaderAuthName: !Ref ALBHeaderAuthName
        ALBHeaderAuthValue: !Ref ALBHeaderAuthValue
```

## 実際に作成してみよう！
テンプレートを先ほど作成したS3へアップロードします

![スクリーンショット 2024-06-29 21.49.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2d8dcc98-45d3-783b-604f-58afdeda46cd.png)

コンソールからスタックを作成します

![スクリーンショット 2024-06-29 21.56.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f7b37110-23b7-68f3-b601-0e8fd16b98cb.png)

URLの値はS3内のyamlファイルのプロバティにあるオブジェクトURLを指定します

![スクリーンショット 2024-06-29 21.57.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4c66b8ac-a328-681b-c5ae-971e3494c360.png)

以下のようにAmplifyとCloudFrontのスタックがまとめて作成されたら成功です
![スクリーンショット 2024-06-29 22.04.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/608dd590-855c-4f9e-2b3e-b3ea9bcca38f.png)

## 参考
https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-cloudformation-stack.html

https://docs.aws.amazon.com/ja_jp/AWSCloudFormation/latest/UserGuide/using-cfn-nested-stacks.html

https://dev.classmethod.jp/articles/apply-basic-authentication-password-with-cloudfront-functions/
