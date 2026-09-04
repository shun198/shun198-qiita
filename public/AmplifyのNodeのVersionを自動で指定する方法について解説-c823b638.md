---
title: AmplifyのNodeのVersionを自動で指定する方法について解説
tags:
  - Node.js
  - AWS
  - amplify
private: false
updated_at: '2026-07-05T20:53:20+09:00'
id: c823b63868cfa4d4b8b5
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
AmplifyのNodeのVersionをコンソール画面から手動で変更するのは手間なので
- amplify.ymlにNodeのversionを直接記載する方法
- .nvmrcファイルを使って指定する方法
- voltaをAmplify内にインストールして指定する方法 <- オススメ

の3つについて解説したいと思います

## 前提
- 今回はバージョン20.10.0を例に解説します

## ディレクトリ構成
```
tree
├── .gitignore
├── Dockerfile
├── README.md
└── application
    ├── src
    ├── next-env.d.ts
    ├── next.config.js
    ├── package-lock.json
    └── package.json
```

## amplify.ymlに直接記載する方法
以下のようにnvmを使って使用したいNodeのバージョンを
```
nvm install 20.10.0
nvm use 20.10.0
```
の順で直接指定することができます

```amplify.yml
applications:
  - appRoot: application
    frontend:
      phases:
        preBuild:
          commands:
            - nvm install 20.10.0
            - nvm use 20.10.0
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

### 実際に実行してみよう
以下のようにnvmを使ってNodeのバージョン20.10.0がインストールおよび使用されていたら成功です

![スクリーンショット 2024-06-17 11.28.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/94d46e36-e85a-0db5-79cf-56c0f2bcf81a.png)


## .nvmrcファイルを使って指定する方法
.nvmrcファイルからNodeのバージョンを自動で指定することができます
package.jsonに以下のようにNodeのバージョンを記載します

```package.json
{
  "engines": {
    "node": "20.10.0"
  },
  "volta": {
    "node": "20.10.0"
  }
}
```

以下のコマンドを使うと.nvmrcファイルにNodeのバージョンが記載されます
```
node --version > .nvmrc
```

```.nvmrc
v20.10.0
```

以下のように
```
nvm install
nvm use
```
と記載したら.nvmrcファイルから自動でNodeのバージョンが指定されます

```amplify.yml
applications:
  - appRoot: application
    frontend:
      phases:
        preBuild:
          commands:
            - nvm install
            - nvm use
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

### 実際に実行してみよう
以下のように.nvmrcファイルに記載されているNodeのバージョン20.10.0がインストールおよび使用されていたら成功です

![スクリーンショット 2024-06-17 11.29.19.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3cf63dd3-3507-4e85-94a7-643ad65cb9bf.png)

## voltaをAmplify内にインストールして指定する方法
以下のようにVoltaを指定している場合、Amplifyのホステッドランナー内にVoltaをインストールしていればNodeのバージョンが自動で指定されます

```package.json
{
  "engines": {
    "node": "20.10.0"
  },
  "volta": {
    "node": "20.10.0"
  }
}
```

```
curl https://get.volta.sh | bash
```
を使ってVoltaをインストールします
```
source ~/.bash_profile
```
がないとVoltaがインストールされていると認識されないので忘れず記載します
```
volta install node
```
でpackage.jsonに記載されたNodeが自動でインストールされます

```amplify.yml
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
```

### 実際に実行してみよう
以下のようにpackage.jsonに記載されているNodeのバージョン20.10.0がインストールおよび使用されていたら成功です

![スクリーンショット 2024-06-17 14.59.56.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/df160aca-b6a4-0e7c-4e70-bbf08903c54a.png)

## まとめ
情報が少なくて調べるのが大変でしたが無事自動でNodeのversionを指定することに成功しました
個人的にvoltaをインストールして自動で指定するやり方だとフロント側が追加で設定しなくても済む上にNodeのversionが変わってもインフラ側で設定し直さなくてもよくなるからいいな、と思いました

## 参考
https://github.com/aws-amplify/amplify-hosting/issues/3785

https://stackoverflow.com/questions/56444337/how-to-change-node-version-in-provision-step-in-amplify-console

https://docs.aws.amazon.com/amplify/latest/userguide/node-version-support-ssr.html

https://stackoverflow.com/questions/57110542/how-to-write-a-nvmrc-file-which-automatically-change-node-version

https://github.com/nvm-sh/nvm

https://volta.sh/

https://github.com/volta-cli/volta/issues/1513

