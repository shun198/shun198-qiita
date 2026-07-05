---
title: AWS Secrets ManagerとLambdaを使ってローテーションする際に「シークレットをローテーションできませんでした」とエラーが出た時の対象法
tags:
  - AWS
  - lambda
  - SecretsManager
private: false
updated_at: '2023-09-13T15:43:03+09:00'
id: 078771acfa959d138b12
organization_url_name: null
slide: false
---
## 概要
AWS Secrets Manager内でキーローテーションの設定をしてうまくいかなかった際に下記画像のように
`シークレットをローテーションできませんでした`
としか表示されずに困ったのでその原因と対処法について解説します

![スクリーンショット 2023-09-13 14.14.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dac7b8c9-abd6-b85b-a218-26262ce69bc4.png)

## 原因
結論から言うとリソースベース(今回だとSecerts Manager)のポリシーステートメントが足りてなくてローテーションができませんでした

リソースベースのポリシーステートメントについては下記の通りです
> 関数は、その実行ロールから AWS リソースに対する許可を受け取ります。AWS SDK を使用して AWS のサービスを呼び出すには、そのサービスの API オペレーションへのアクセスを許可するポリシーをロールに追加します。
Lambda コンソールが作成するデフォルトの実行ロールには、Amazon CloudWatch ログにログを保存するアクセス許可しかありません。X-Ray トレースなどの一部の機能では、追加のアクセス許可が必要です。コンソールで関数を設定すると、コンソールは必要なアクセス許可を追加しようとします。

要するに何かしらのマネージドサービスをトリガーにLambdaを実行するにはトリガーとなるマネージドサービスのアクセスを許可する必要がある、ということです

## 対処法
### ポリシーステートメントの設定
Lambdaの設定タブを選択し、アクセス権限を追加をクリックします
![スクリーンショット 2023-09-13 15.38.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d4cfc8ca-2e7a-d03c-3fb6-a980ba8e2ae8.png)

AWSのサービスを選択し、今回はSecrets Managerを選択します
ローテーションで設定した時間に実行させたいのでアクションはlambda:invokefunctionにします
![スクリーンショット 2023-09-13 14.13.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fffd5dfb-4bcd-aba5-6538-6fd6665a0b3d.png)

以下のようにポリシーステートメントが追加されたら成功です
![スクリーンショット 2023-09-13 15.42.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4f92e541-839d-9720-e2b2-ba118f6a5480.png)

### Secrets Managerの設定
Secrets Managerにローテーションの設定を行います
![スクリーンショット 2023-09-13 14.14.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/45e355a4-50ce-796b-3b7b-84b0114f2bf0.png)
![スクリーンショット 2023-09-13 14.14.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3f155b6d-0341-c6e3-782d-0e7712a8f23d.png)

以下のように正常にローテーションの設定ができていたら成功です
![スクリーンショット 2023-09-13 14.16.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a198814d-e1d3-cb00-efa9-b8cd18330cd1.png)

![スクリーンショット 2023-09-13 14.16.50.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/05db17a8-8dfc-9ed7-8271-041b9281f1ab.png)

## 参考
https://docs.aws.amazon.com/secretsmanager/latest/userguide/troubleshoot_rotation.html

https://stackoverflow.com/questions/58899204/secrets-manage-fail-to-rotate-the-secret-cannot-invoke-the-specified-lambda-fu
