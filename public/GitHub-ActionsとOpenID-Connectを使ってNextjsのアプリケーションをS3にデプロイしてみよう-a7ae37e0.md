---
title: GitHub ActionsとOpenID Connectを使ってNext.jsのアプリケーションをS3にデプロイしてみよう！
tags:
  - AWS
  - S3
  - Next.js
  - openidconnect
  - GitHubActions
private: false
updated_at: '2024-07-26T14:53:42+09:00'
id: a7ae37e0da3eba2c4387
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actionsを使ってNext.jsのアプリケーションをS3バケットにデプロイする方法について
- Next.jsのアプリケーションの作成と設定
- デプロイ先のS3バケットの作成と設定
- IAM Roleを使ったOpenID Connectの設定
- GitHub Actionsのワークフローの作成

の順で解説していきたいと思います
かなり分量がある上にある程度AWSの知識が必要ですが一緒に頑張りましょう

## 前提
- S3へデプロイする用のGitHubのリポジトリを作成済み
- AWSのアカウントとIAMユーザを作成済み
- AWSとGitHub Actionsの基礎的な知識を有していること
- 今回はCloud Frontを使用していません

## S3バケットにデプロイする理由
AWSへアプリケーションをデプロイする手段としてECS(コンテナ)もありますが
フロントエンドのソースコードをコンテナではなく、S3へデプロイする利点としては以下のとおりです

- 一般的にS3バケットは静的なファイルのホスティングに適している
- S3はCloud Frontと組み合わせることで静的なコンテンツを高速に配信できる
- オートスケーリングに対応してるなど、トラフィックの変動に柔軟
- サーバーレスなため、ECSと比べて管理・運用コストが低い

## Next.jsのアプリケーションの作成と設定
以下のコマンドでNext.jsのアプリケーションを作成します

```
❯ npx create-next-app@latest
✔ What is your project named? … frontend
✔ Would you like to use TypeScript? … No / Yes
✔ Would you like to use ESLint? … No / Yes
✔ Would you like to use Tailwind CSS? … No / Yes
✔ Would you like to use `src/` directory? … No / Yes
✔ Would you like to use App Router? (recommended) … No / Yes
? Would you like to customize the default import alias? › No / Yes
```

一度BuildしてからExportするため、next.config.jsに以下の記述を記載します
```next.config.js
/** @type {import('next').NextConfig} */
const nextConfig = {
  // next buildすると自動的にexportするので記載
  output: 'export',
  // 画像の最適化を無効化し、元の画像ファイルをそのまま使用
  images: {
    unoptimized: true,
  },
};

module.exports = nextConfig;
```

## S3バケットの作成と設定
### S3バケットの作成
S3バケットを作成します
今回はfrontend-deploy-demoという名前のバケットを作成します

![スクリーンショット 2023-07-12 20.08.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8e64e1e2-d3ef-c17a-c988-49e384ee384b.png)

S3内のファイルにアクセスしたいのでパブリックアクセスを許可します
![スクリーンショット 2023-07-12 20.09.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/482c9da9-a136-765e-3183-c78dee021fc3.png)
![スクリーンショット 2023-07-12 20.09.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/629fdd5e-aba9-d7cc-04dc-4fe354386848.png)

以下のとおりバケットを作成できたら成功です
![スクリーンショット 2023-07-12 20.10.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/24b72499-bc78-fd7e-9c7c-6680219cfb75.png)

プロパティ内の静的ウェブホスティングを編集します
![スクリーンショット 2023-07-12 20.12.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/86a29de2-ce81-65de-6664-b0262f00f381.png)

静的ウェブホスティングを編集します

![スクリーンショット 2023-07-12 20.12.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e42e2b31-2187-e559-3a3b-5770b6d177e2.png)

以下の画像のように設定していきます

![スクリーンショット 2023-07-12 20.13.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/66deab99-39a0-cffa-5d47-db3a1a3a7803.png)

### バケットポリシーの設定
続いてS3バケットに付与するバケットポリシーを設定していきます

![スクリーンショット 2023-07-12 20.14.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9022baeb-2faa-3a12-74ae-96190955bcad.png)

以下のようにバケットポリシーを作成します
Resourceの箇所にご自身が作成したバケット名を記載してください

```json:S3バケットポリシー
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Sid": "PublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::frontend-deploy-demo/*"
        }
    ]
}
```

## OpenID Connect
OpenID Connectを使用することでAWSの
- シークレットキー
- アクセスキー

を使わずにIAMロールを使ってよりセキュアにGitHub Actionsを実行できますので設定していきます

### OpenID Connectとは
簡単にいうと認証を行うための仕組みです
GitHub Actions内でOpenID Connectを使うメリットは以下の通りです

- GitHub Secretsでアクセスキーとシークレットキーを管理する必要がないため、AWS関連の秘匿情報を管理するコストがなくなる
- IAMロールを使った運用になるため、ロールに応じた細かい権限別のワークフローを実行できる
- OpenID Connectを使う際に生成されるJWTトークンが1つのジョブに対してのみ有効であり、自動的に失効する有効期間が短いトークンを使用できるためセキュリティリスクが低い

### OpenID Connectの仕組み
仕組みをざっと説明すると
- AWSなどのクラウドプロバイダにOpenID Connect(OIDC Trust)を設定
- GitHub Actionsのワークフロー内のjobを実行するたびにGitHubがJWTトークンを生成し、クラウドプロバイダへ渡す
- クラウドプロバイダが受け取ったJWTトークンを使って認証が成功したらGitHubのOpenID Connectのプロバイダがクラウドプロバイダからアクセストークンを受け取る
- 受け取ったアクセストークンを使用してaws cliコマンドをIAMロールを使って実行する

という流れになっています

詳細は以下の公式ドキュメントを参照してください

https://docs.github.com/ja/actions/deployment/security-hardening-your-deployments/configuring-openid-connect-in-amazon-web-services

### OpenID Connectの設定
AWS上でOpenID Connectの設定をしていきます
IAMのID プロバイダを開き、プロバイダの追加を押します
![スクリーンショット 2023-07-13 6.41.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/244ee90f-c15d-b03a-5d16-a2e3df87e81d.png)

OpenID Connectを選択し、画像のとおり
- プロバイダのURL:　https://token.actions.githubusercontent.com
- 対象者：　sts.amazonaws.com

を入力します

![スクリーンショット 2023-07-13 6.43.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ccee9dc6-6b8d-e168-4e77-c56c5054b7af.png)

以下のようにプロバイダが作成されたら成功です
![スクリーンショット 2023-07-13 7.05.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3171e724-4839-dad4-6a02-f886f2e9aafc.png)

## IAMロールの作成と割り当て
GitHub Actionsを使ってS3へデプロイできるIAMロールを作成していきます
IAMロールを作成する際に
- S3バケット用のIAMポリシー
- OpenID Connect用の信頼されたエンティティ

の設定を行います

今回はS3バケットとバケット内ののオブジェクトへの
- 追加
- 取得
- 表示
- 削除

の4つの権限をActionで許可します

また、指定した
- S3バケット自体
- S3バケット内のオブジェクト

を対象に前述の権限を付与することをResourceに記載します

```json:IAM ポリシー
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Action": [
                "s3:PutObject",
                "s3:GetObject",
                "s3:ListBucket",
                "s3:DeleteObject"
            ],
            "Resource": [
                "arn:aws:s3:::frontend-deploy-demo",
                "arn:aws:s3:::frontend-deploy-demo/*"
            ]
        }
    ]
}
```

### ロールに付与するエンティティの設定を行います
Principal内のFederatedに作成したOpenID ConnectのプロバイダのARNを記載します
Condition内のStringLikeにロールを使用するリポジトリを記載します
今回はmainブランチでのみ実行したいので
```
{GitHubのリポジトリ名}:ref:refs/heads/main
```
と指定していますが全てのブランチで実行したいのであれば
```
{GitHubのリポジトリ名}:*
```
という風にワイルドカードを設定します

```json:信頼されたエンティティ
{
    "Version": "2012-10-17",
    "Statement": [
        {
            "Effect": "Allow",
            "Principal": {
                "Federated": "arn:aws:iam::XXXXXXXXXXXX:oidc-provider/token.actions.githubusercontent.com"
            },
            "Action": "sts:AssumeRoleWithWebIdentity",
            "Condition": {
                "StringLike": {
                    "token.actions.githubusercontent.com:sub": "repo:shun198/github-actions-playground:ref:refs/heads/main"
                },
                "StringEquals": {
                    "token.actions.githubusercontent.com:aud": "sts.amazonaws.com"
                }
            }
        }
    ]
}
```

## GitHub Actionsのワークフローの作成
- S3バケット
- IAM

関連の設定が終わったのでワークフローを作成していきます

```.github/workflows/deploy-frontend.yml
name: Deploy Frontend Project to S3

on:
  push:
    branches:
      - main

env:
  BUCKET_NAME: frontend-deploy-demo
  REGION_NAME: ap-northeast-1

jobs:
  deploy:
    runs-on: ubuntu-latest
    permissions:
      id-token: write # This is required for requesting the JWT
      contents: read # This is required for actions/checkout
    defaults:
      run:
        working-directory: frontend
    steps:
      - name: Checkout
        uses: actions/checkout@v3
      - name: configure aws credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::XXXXXXXXXXXX:role/github-actions-deploy-s3-bucket
          role-session-name: samplerolesession
          aws-region: ${{ env.REGION_NAME }}
      - name: Setup NodeJS
        uses: actions/setup-node@v3
        with:
          node-version: '16'
      - name: Cache NodeJS
        uses: actions/cache@v3
        with:
          path: '**/node_modules'
          key: node-modules-${{ hashFiles('**/package-lock.json') }}
      - name: Install dependencies
        run: npm ci --omit=dev
      - name: Build and Export
        run: npm run build
      - name: Deploy To S3 Bucket
        run: aws s3 sync --region ${{ env.REGION_NAME }} ./out s3://${{ env.BUCKET_NAME }} --delete
```

### 権限の設定
JWTトークンを使って認証を行いますがGitHub Actionsのid-tokenのデフォルトのpermissionがNoneなのでid-tokenのpermissionsはwriteに変更します
また、GitHub Actionsの仕様上、1つのpermissionsを変更するとその他のpermissionがNoneになってしまうので、checkoutを実行できるよう追加でcontentsのpermissionsをreadに変更します

```yml
    permissions:
      id-token: write # This is required for requesting the JWT
      contents: read # This is required for actions/checkout
```

### OpenID Connectの設定
OpenID Connectを使用する際はAWSが出している公式のActionを使用します

https://github.com/aws-actions/configure-aws-credentials

role-to-assumeに自身で作成されたIAM Roleを記載します
今回は東京リージョンを使用するのでaws-regionはap-northeast-1に設定します
デフォルトのrole-session-nameはGitHubActionsですが、任意の名前に設定しても大丈夫です
また、ワークフロー内で複数回`aws-actions/configure-aws-credentials@v2`を使用する際は一意の名前にする必要があります

```yml
      - name: configure aws credentials
        uses: aws-actions/configure-aws-credentials@v2
        with:
          role-to-assume: arn:aws:iam::XXXXXXXXXXXX:role/github-actions-deploy-s3-bucket
          role-session-name: samplerolesession
          aws-region: ${{ env.REGION_NAME }}
```

### 必要なパッケージのインストール
今回は本番環境にdeployすることを想定しているので
package.jsonのdependenciesのみインストールしますので
--omit=devを入れた上でnpm ciを実行します
```yml
      - name: Install dependencies
        run: npm ci --omit=dev
```

### デプロイ
S3バケットへ静的ファイルをデプロイします
ファイルやディレクトリをS3バケットと同期させるコマンドです
```
npm run build
```
コマンドを実行すると`./out`へビルドしたファイルやディレクトリを出力し、指定したS3バケットと同期させます
また、`--delete`を入れることで同期先のS3バケットに存在しないファイルやディレクトリを削除します

```yml
      - name: Deploy To S3 Bucket
        run: aws s3 sync --region ${{ env.REGION_NAME }} ./out s3://${{ env.BUCKET_NAME }} --delete
```


## デプロイしてみよう
先ほど作成したワークフローの内容をmainブランチへpushし、以下のようにワークフローが正常に実行できたら成功です

![スクリーンショット 2023-07-13 21.50.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/59a6176a-2e9f-57a7-683f-4827de4f88a6.png)

デプロイ完了後、作成したS3バケット内のindex.htmlにアクセスするとオブジェクトURLが記載されています
![スクリーンショット 2023-07-13 21.56.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1573b0c1-6ae6-c72c-96c2-fcb332136ba6.png)

オブジェクトURLに遷移し、以下のNext.jsの画面が表示されたら成功です
![スクリーンショット 2023-07-14 12.55.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c54fbae4-7bde-0a0b-f16d-26ac5882a918.png)

## CloudFormationを使ってS3とIAMロールを作成するには
冒頭で作成したS3とIAMロールをIaCで作成することができます
今回は
- S3
- IAMロール

に分けてテンプレートを作成しています

```s3-bucket.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "S3 Bucket For Deployment"

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
      - prd
    ConstraintDescription: "Environment name must be selected."

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  # -------------------------------------
  # S3
  # -------------------------------------
  # For CloudFormation Templates
  S3DeployBucket:
    DeletionPolicy: Retain
    UpdateReplacePolicy: Retain
    Type: AWS::S3::Bucket
    Properties:
      BucketEncryption:
        ServerSideEncryptionConfiguration:
          - ServerSideEncryptionByDefault:
              SSEAlgorithm: AES256
      BucketName: !Sub s3-deploy-${ProjectName}-${Environment}-${AWS::Region}

  # S3 Bucket Policy
  S3DeployBucketPolicy:
    Type: AWS::S3::BucketPolicy
    Properties:
      Bucket: !Ref S3DeployBucket
      PolicyDocument:
        Version: '2012-10-17'
        Statement:
          - Sid: PublicRead
            Effect: Allow
            Principal: '*'
            Action: 's3:GetObject'
            Resource: !Sub 'arn:aws:s3:::${S3DeployBucket}/*'

# -------------------------------------
# Outputs
# -------------------------------------
Outputs:
  S3DeployBucket:
    Value: !Ref S3DeployBucket
  S3DeployBucketArn:
    Value: !GetAtt S3DeployBucket.Arn

```

```deploy-role.yml
AWSTemplateFormatVersion: 2010-09-09
Description: "IAM Role For Deployment"

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
          default: "IAM Configuration"
        Parameters:
          - S3DeployBucketName
          - RepositoryName
          - OIDCArn

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
      - prd
    ConstraintDescription: "Environment name must be selected."
  S3DeployBucketName:
    Description: "Enter the S3 bucket name."
    Type: String
    MinLength: 1
    ConstraintDescription: "S3 bucket name must be entered."
  RepositoryName:
    Description: "Enter the repository name. (ex: shun198/github-actions-tutorial)"
    Type: String
    MinLength: 1
    ConstraintDescription: "Repository name must be entered."
  OIDCArn:
    Description: "Enter the OIDC Arn. (ex: arn:aws:iam::XXXXXXXXXXXX:oidc-provider/token.actions.githubusercontent.com)"
    Type: String
    MinLength: 1
    ConstraintDescription: "OIDC Arn must be entered."

# -------------------------------------
# Resources
# -------------------------------------
Resources:
  S3DeployIAMRole:
    Type: AWS::IAM::Role
    Properties:
      RoleName: !Sub s3-deploy-${ProjectName}-${Environment}
      AssumeRolePolicyDocument:
        Version: 2012-10-17
        Statement:
          - Effect: Allow
            Principal:
              Federated: !Ref OIDCArn
            Action: 'sts:AssumeRoleWithWebIdentity'
            Condition:
              StringLike:
                token.actions.githubusercontent.com:sub: !Sub repo:${RepositoryName}:ref:refs/heads/main
              StringEquals:
                token.actions.githubusercontent.com:aud: sts.amazonaws.com
      Policies:
        - PolicyName: !Sub S3DeployAccessPolicy-${ProjectName}-${Environment}
          PolicyDocument:
            Version: '2012-10-17'
            Statement:
              - Effect: Allow
                Action:
                  - s3:PutObject
                  - s3:GetObject
                  - s3:ListBucket
                  - s3:DeleteObject
                Resource:
                  - !Sub arn:aws:s3:::${S3DeployBucketName}
                  - !Sub arn:aws:s3:::${S3DeployBucketName}/*

```

## まとめ
今回はCloudFrontを使っていなかったりbuildの効率が悪かったりと、まだ実務で使える構成とは程遠いですがS3への基本的なデプロイの流れを理解いただければ幸いです
今後CloudFrontを使ったり効率よくbuildできる構成にするなど、より実践的な記事を書いていきたいと思います

## 参考
https://zenn.dev/harasho/articles/e972a51e6fa52b1b160c

https://docs.github.com/en/actions/deployment/security-hardening-your-deployments/about-security-hardening-with-openid-connect

https://github.com/aws-actions/configure-aws-credentials

