---
title: AWS SESの初期設定の方法についてコンソール画面を交えながら解説
tags:
  - AWS
  - ses
  - DMARC
  - DKIM
private: false
updated_at: '2026-07-05T20:53:20+09:00'
id: 3f3b8d40f550059bea25
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: 16baee61b1d8bd4aac5a
agreed_posting_campaign_term: true
---
## 概要
AWS SESの初期設定の方法について説明していきます

## SESのコンソール画面
コンソール画面からSESのアカウントダッシュボードを開きます
SESの設定が完了していない場合は以下のように最初はサンドボックスとして利用出来ます
本番運用でSESを使用する場合はサンドボックス外へ移動する必要があります
![スクリーンショット 2024-06-12 10.18.41.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e4a9ec53-9de7-26fe-ec8b-d5cee3d41249.png)

## IDの設定
SESでメール送信するためにIDを作成します
![スクリーンショット 2024-06-12 10.19.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ad36fc0f-0381-80f5-6506-59592f563025.png)

今回はID作成時にメール送信で使用するドメインを登録します
![スクリーンショット 2024-06-12 10.19.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d3be541b-5917-b75f-1649-6c939c83b07d.png)

DKIMを有効化します
DKIM (DomainKeys Identified Mail)は、 電子メールにおける送信ドメイン認証技術の一つで、メールを送信する際に送信元が電子署名を行い、 受信者がそれを検証することで、 送信者のなりすましやメールの改ざんを検知できます
![スクリーンショット 2024-06-12 10.19.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4476f2bc-f43d-ba19-d2c5-58d82a3a26c3.png)

以下のようにIDが作成されたら成功です
![スクリーンショット 2024-06-12 10.20.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4b3aa507-cb01-d4e5-b725-630c4fc3d0f4.png)

## DMACRの設定
DMARCは送信ドメイン認証技術の一つで、送信元ドメインの認証を行い、不正な送信元からのメールをブロックすることで、メール詐欺やなりすましを防ぐことができます
IDの下の方にDomain-based Message Authentication, Reporting, and Conformance (DMARC)
`DNSレコードのRoute53への発行`を押します

![スクリーンショット 2024-06-12 10.21.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3546297b-a00a-8195-f145-238897ab1bd4.png)

以下のようにDMARCとDKIMが表示されたら成功です
![スクリーンショット 2024-06-12 10.21.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e8ec9dd5-5a75-b122-7b92-0e223fcb8a47.png)

## 本稼働アクセスのリクエスト
本稼働アクセスのリクエストを押します
![スクリーンショット 2024-06-12 10.21.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f2a27b45-860c-d2d1-e2d4-690bffb0d10c.png)

メールタイプはマーケティング、ウェブURLにメール送信機能を使用するウェブサイトのURLを指定します
ユースケースの説明にメール送信を使用する用途を記載します
その他の連絡先に自身のメールアドレスを記載します
![スクリーンショット 2024-06-12 10.22.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/affaf2e1-ff29-0126-4462-5910703801e7.png)

リクエストが完了したら以下のように`リクエストを確認中`と表示されます
![スクリーンショット 2024-06-12 10.22.35.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/114bc9e7-d1a2-aa56-6402-29b32bd8aff0.png)

ケースIDのリンクを開くとケースの詳細が表示されます
![スクリーンショット 2024-06-12 10.22.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/95472f08-3e42-6b1a-c170-7efc0a0e9345.png)


## リクエスト申請後
以下のメールを受信します
申請が完了するまでおよそ1日かかるので気長に待ちます
![スクリーンショット 2024-06-12 10.23.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/122ade71-9dac-3b10-f981-21ec7b28115b.png)
![スクリーンショット 2024-06-12 10.23.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/da69a1a9-8367-b733-559e-c6cf4b7415fa.png)

以下のメールを受信し、メール送信できるようになれば成功です
![スクリーンショット 2024-06-12 10.23.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/34183d4e-f746-ba4e-1618-6c64e29d0de8.png)

![スクリーンショット 2024-06-12 10.24.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/141847f9-0b6a-ccf0-033a-71d9f33b1e3b.png)

## 参考
https://docs.aws.amazon.com/ja_jp/ses/latest/dg/setting-up.html

https://qiita.com/y-okuhira/items/e0a393dc3b6cec653c76

https://www.nic.ad.jp/ja/basics/terms/dkim.html

https://www.value-domain.com/media/dmarc-about/

