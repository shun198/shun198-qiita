---
title: aws-vaultを使ってAWSのシークレットキーおよびアクセスキーを暗号化した状態で使用しよう！
tags:
  - AWS
  - aws-cli
  - aws-vault
private: false
updated_at: '2023-07-31T11:32:20+09:00'
id: 9af6911457ad43a6c237
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## aws-vaultとは
AWSのシークレットキーとアクセスキーを暗号化して保存できるツールです
aws configure コマンドでこれらの秘匿情報が平文でローカルマシンの ~/.aws/credentials に保存されてしまいます
セキュリティリスクが大きいため、aws-vaultを使うことを推奨します

GitHubのリンクは以下の通りです

https://github.com/99designs/aws-vault

## aws-vaultのインストール
brewでインストールします
```
brew install --cask aws-vault
```

下記のようにバージョンが表示されたら成功です
```
aws-vault --version
v6.6.1
```

## aws-vaultの設定を行おう!
### シークレットキーとアクセスキーの設定
まず、`aws-vault add` ユーザ名でユーザを追加します
```
aws-vault add shun198
```

以下のようなポップアップが表示されますが`開く`を押します

![スクリーンショット 2023-07-31 11.27.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ee1c7b80-e234-2a1f-1c15-d5ae671019f2.png)


AWSのIAMユーザの
- アクセスキー
- シークレットキー

を入力していきます
```
Enter Access Key ID:
Enter Secret Access Key:
```

aws-vault用のパスワードを作成します

![スクリーンショット 2023-07-31 11.24.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/435e7a35-d0d5-93ac-eec3-ef1dda29dbed.png)

以下のように表示されたら登録成功です
```
Added credentials to profile "shun198" in vault
```

以下のコマンドでキー一覧を確認できます
```
aws-vault ls
Profile                  Credentials              Sessions                 
=======                  ===========              ========                 
shun198                  shun198                  -          
```

### 追加の設定
`~/.aws/config`を開いて
- リージョン
- MFA認証

の設定を追加します
```
code ~/.aws/config
```

```~/.aws/config
[profile shun198]
region=ap-northeast-1
mfa_serial=<多段階認証のarnを記載>
```

arnに関しましてはIAMのユーザから該当するユーザを選択した後に多要素認証(MFA)を開くとシリアル番号として表示されるのでこちらをコピーして貼り付けます

![スクリーンショット 2023-01-13 18.09.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6f46cafa-1f7f-a4bd-77bf-896f09c48a43.png)


上記の設定が完了したらMFA認証を以下のコマンドで行います
デフォルトだと1時間ですが、最大12時間まで有効化できます

```
aws-vault exec shun198 --duration=12h
```

MFAコードを入力します
```
Enter MFA code for arn:aws:iam::xxxxxxxxxxxx:user/shun198:
```

![スクリーンショット 2023-07-31 11.28.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/194e1c75-0c10-da50-8911-4f779b91271a.png)

aws-vaultのパスワードを入力した後にエラーなどが表示されていなかったら成功です

## aws-vault経由でaws cli関連のコマンドを実行しよう！
今回はS3バケットの一覧を表示させます
aws cliと違ってaws-vault経由で使用するときは
```
aws-vault exec <ユーザ名> --
```
と指定します
```
aws-vault exec shun198 -- aws s3 ls
2023-01-08 08:10:15 terraform-playground-for-cicd
```

AWSリソースにアクセスできたことが確認できました

## トラブルシューティング
### aws-vault: error: exec: aws-vault sessions should be nested with care, unset AWS_VAULT to force
このエラーが出たときは以下のコマンドを実行してください
```
unset AWS_VAULT
```

## IAMロールを使って運用する時
スイッチロールなどを使ってロールに応じてcliを利用する際は以下の手順の通りに設定する必要があります

### configファイルの設定
configファイルに使用するロールの設定を行います
```
code ~/.aws/config
```

以下のように
- bastion用
- default
- スイッチロール用

のprofileを設定します
今回bastion用のprofileをcommonにしています
common内に下記の設定を記載します

| 項目 | 内容 |
| -------- | -------- | 
| source_profile     | IAMユーザのユーザ名を記載します     |
| region | ap-northeast-1をリージョンとして設定します |
| output | JSON |
| mfa_serial | MFAのarnを記載します |
| role_session_name | ロール元(bastion)のユーザ名を記載します |

また、使用するロール内に
- include_profile
- role_session_name

を記載します
include_profileには先ほど指定したロール元のprofile(common)、role_arnに使用するロールのarnを指定します

```~/.aws/config   
[profile common]
source_profile=shun198
region=ap-northeast-1
output=json
mfa_serial=arn:aws:iam::XXXXXXXXXXXX:mfa/shun198
role_session_name=shun198

[default]
region=ap-northeast-1
output=json

[profile shun198-poweruser]
include_profile=common
role_arn=arn:aws:iam::YYYYYYYYYYYY:role/shun198-PowerUser
```

### なんでdefaultを記載するの？
defaultがないと以下のエラーが出力され、指定したロールで実行することができなくなってしまいます
```
aws-vault: error: exec: Failed to get credentials for child
```

詳細は以下のissueを参照してください

https://github.com/99designs/aws-vault/issues/978

## 参考
https://blog.microcms.io/aws-vault-introduction/
