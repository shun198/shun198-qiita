---
title: '[初心者向け] SlackとChatbotとLambdaを使ってChatOpsを実現しよう！'
tags:
  - AWS
  - lambda
  - Slack
  - ChatOps
  - chatbot
private: false
updated_at: '2024-07-04T09:25:52+09:00'
id: 4f3d120c2f3445cd5c1c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
Slack（Chatbot）経由でLambdaを使ってChatOpsを実現できるのでその方法について解説します

## 前提
- SlackのワークスペースとChatbotとの連携が完了していること

## ChatOpsとは
Chatツール(Slack、Teamsなど)を通じてシステム開発・運用から一般業務などさまざまな業務の効率化を行う手法のことです
ChatOpsでできることは色々あり、Slackにメッセージを送ることで

- SSOユーザの発行
- SGへIPアドレスを登録
- デプロイ

などさまざまなことを行うことができます
また、Slackのワークフローを組み合わせることでより汎用性が高くなります

## Chatbotの設定
Chatbotの設定を行います
設定名とチャネルIDを設定します

![スクリーンショット 2024-06-29 17.47.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d07ae4f1-c4d9-eb1a-6bcb-c117a7b6eef7.png)

アクセスロールは下記の通りに行います

![スクリーンショット 2024-07-04 9.05.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2fbf9c2b-04e8-3070-138b-53024f0852f8.png)

Lambda経由で処理を実行するので今回はガードレールポリシーにAWSLambda_FullAccessを追加します

![スクリーンショット 2024-07-04 9.06.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/baf50b26-0927-516e-d23a-5a4628cd3f5f.png)


設定が終わったら保存を押します
以下のように設定できれば成功です

![スクリーンショット 2024-06-29 17.53.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8fb982f6-4416-ccaa-be37-446c47a2cf49.png)

## Lambdaの作成
以下の通りにLambdaを作成します

![スクリーンショット 2024-06-29 18.02.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a01b9793-0ef0-1ac3-69c9-1203fa4e76e1.png)

今回は以下のレスポンスを返す簡単なLambdaを使ってChatOpsを実現します
![スクリーンショット 2024-06-29 18.05.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/87a638b7-a102-dccb-eef1-a8507893cc47.png)

## Slack内でChatbotの設定を行うには
以下のコマンドを実行するとAWSが招待されます
```
/invite @aws
```

![スクリーンショット 2024-06-29 17.50.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/79f91a00-f16f-d172-cbfa-53b9b4f3aade.png)

また、以下のコマンドを実行するとChatbotの色々な使い方が表示されます
```
@aws --help
```

![スクリーンショット 2024-06-29 17.53.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b599424d-2c33-a426-f780-5f373a5deabd.png)

## 実際に実行してみよう！
以下のようにawsのアプリケーションにメンションした上でaws cliを使ってLambdaを実行します
```
@aws lambda invoke --function-name TestChatOps --region ap-northeast-1
```

以下のようにコマンドが実行されてLambdaからレスポンスが返ってきたら成功です

![スクリーンショット 2024-07-04 9.02.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d4377276-c09a-0a69-7f40-51c12fcbd29e.png)

## 参考
https://fu3ak1.hatenablog.com/entry/2020/11/10/235659

https://www.rapid7.com/ja/fundamentals/chatops/#:~:text=%E3%83%80%E3%82%A6%E3%83%B3%E3%83%AD%E3%83%BC%E3%83%89-,ChatOps%E3%81%A8%E3%81%AF%EF%BC%9F,%E5%AF%BE%E5%BF%9C%E3%82%92%E5%8A%B9%E7%8E%87%E5%8C%96%E3%81%97%E3%81%BE%E3%81%99%E3%80%82

https://qiita.com/m_mizutani/items/f7fa7b1d1c077b139f98

https://tech.systems-inc.com/col-tool-cops-02/
