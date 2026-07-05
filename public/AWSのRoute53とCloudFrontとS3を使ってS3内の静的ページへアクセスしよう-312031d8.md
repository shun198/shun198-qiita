---
title: AWSのRoute53とCloudFrontとS3を使ってS3内の静的ページへアクセスしよう！
tags:
  - AWS
  - S3
  - route53
  - CloudFront
private: false
updated_at: '2024-01-12T13:20:52+09:00'
id: 312031d80455418d1e8d
organization_url_name: null
slide: false
---
## 概要
AWSのCloudFrontのディストリビューションまたはRoute53のドメインからアクセスする際にS3バケット内の静的ファイルが表示されるようにする設定方法について解説します

## 前提
- Route53に自身のドメインを設定済み
- ACMを発行済み(ただし、CloudFrontに設定する際はACMをバージニア北部(us-east-1)に発行する必要があります)

ドメインの設定については以下の記事がわかりやすかったのでまだ設定できていない方は以下の記事を参考にしてください

https://dev.classmethod.jp/articles/route53-domain-onamae/

## S3バケットの作成
静的ファイルを格納する用のS3バケットを作成します
今回はS3に直接アクセスしないのでバケットのブロックパブリックアクセス設定はブロックしても大丈夫です
パブリックアクセス以外の設定も今回はデフォルトのままで大丈夫です

![スクリーンショット 2024-01-12 10.43.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/721e9b01-2237-ae68-db78-1ac334df0d3c.png)

![スクリーンショット 2024-01-12 10.44.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5df83028-7128-7612-7deb-30440190858a.png)

バケット作成後に静的ファイルをアップロードします
今回はCloudFrontにデフォルトルートオブジェクトをindex.htmlを設定するのでindex.htmlを忘れずにアップロードします

![スクリーンショット 2024-01-12 10.42.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f0592dd3-4ac7-8668-cc6f-4636624c78b6.png)

## CloudFrontののディストリビューションの作成
CloudFrontを使用してコンテンツ配信する際はディストリビューションを作成します
ディストリビューションの作成方法について順番に説明します

### オリジンの設定
CloudFrontがエッジロケーションを通じて配信するコンテンツのリクエストを送信するロケーションのことをオリジンといいます
今回はS3をオリジンに設定するので下記の画像のようにオリジンドメインを先ほど作成したS3バケットに設定します
次にOrigin Acccess Control(OAC)の設定を行います
OACを設定することで指定したCloudFrontのディストリビューションのみ対象のS3へのアクセスを許可することができるようになります
今回は新規でS3を作成したのでOACも新規で作成します

![make_distribution.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5a9566e7-1802-dd8a-81f4-6ce171c8f12c.png)

S3バケットの名前が入ったOAC名で作成します
オリジンタイプはS3に設定します

![create_controll_settings.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9ebca29e-c095-5d54-0ae1-2eb7d21e010d.png)

### デフォルトのキャッシュビヘイビア
CloudFrontがリクエストをオリジンに対してどう扱うか(ビヘイビア)の設定を行います
今回は以下の画像のように設定します

![スクリーンショット 2024-01-12 10.48.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/89364119-fe47-b09e-5ca8-5deae54a57af.png)

### キャッシュキーとオリジンリクエスト
キャッシュポリシーはCachingOpitmizedに設定します
CloudFront がキャッシュキーに含める値を最小限に抑えることで、キャッシュ効率を最適化するように設計されているオプションです

![スクリーンショット 2024-01-12 10.49.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3bbc624b-e0c6-3665-fa7e-9d5ec5b5e681.png)

### WAF
今回はWAFを作成していないので有効にしない、に設定しますが本番環境で使用する際は設定するようにしましょう

![スクリーンショット 2024-01-12 10.51.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/240b4223-5499-bab2-fd4c-c8b516134acf.png)

### SSLの設定
カスタムSSL証明書にバージニア北部リージョン(us-east-1)内に作成したSSL証明書を指定します

![ssl.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e0aac4d4-775d-d70f-5782-5e4c33c10f2a.png)


### デフォルトルートオプション
デフォルトルートオプションにindex.htmlを指定します
![スクリーンショット 2024-01-12 11.03.16.png](
https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/743766b4-d37c-524c-7604-a2f9aadd3199.png)

### ディストリビューションの作成完了

以下のようにディストリビューションが作成されたら成功です

![distribution_complete.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e0d80177-f2ff-f01e-7b84-4b82faf23611.png)

また、S3バケットにCloudWatchへのアクセスを許可するためにバケットポリシーを付与する必要があります
```json
{
    "Version": "2008-10-17",
    "Id": "PolicyForCloudFrontPrivateContent",
    "Statement": [
        {
            "Sid": "AllowCloudFrontServicePrincipal",
            "Effect": "Allow",
            "Principal": {
                "Service": "cloudfront.amazonaws.com"
            },
            "Action": "s3:GetObject",
            "Resource": "arn:aws:s3:::{バケット名}/*",
            "Condition": {
                "StringEquals": {
                    "AWS:SourceArn": "arn:aws:cloudfront::{アカウントID}:distribution/{ディストリビューション名}"
                }
            }
        }
    ]
}
```

## Route53の設定
Route53のAレコードのトラフィックのルーティング先に先ほど作成したCloudFrontのディストリビューションを指定します

![route53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/26e91ab1-9069-8e56-e5d4-01e6992734f5.png)

## 実際にディストリビューションとドメインからアクセスしてみよう！
以下のようにディストリビューションとドメインからアクセスした際にindex.htmlが表示されたら成功です

![スクリーンショット 2024-01-12 11.02.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3734a8e2-b1bd-470e-91d9-63042bfc09ab.png)


## 参考
https://dev.classmethod.jp/articles/s3-cloudfront-static-site-design-patterns-2022/

https://docs.aws.amazon.com/ja_jp/AmazonCloudFront/latest/DeveloperGuide/distribution-overview.html

https://docs.aws.amazon.com/ja_jp/whitepapers/latest/best-practices-wordpress/origins-and-behaviors.html

https://aws.amazon.com/jp/blogs/news/amazon-cloudfront-introduces-origin-access-control-oac/

https://docs.aws.amazon.com/ja_jp/AmazonCloudFront/latest/DeveloperGuide/using-managed-cache-policies.html#managed-cache-caching-optimized

https://jnsato.hateblo.jp/entry/2020/03/26/110255

https://qiita.com/sakuraya/items/add2cb7ced954215fb03
