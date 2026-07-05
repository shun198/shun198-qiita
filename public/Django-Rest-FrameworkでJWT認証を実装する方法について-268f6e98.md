---
title: Django Rest FrameworkでJWT認証を実装する方法について
tags:
  - JWT
  - swagger
  - django-rest-framework
private: false
updated_at: '2022-12-24T16:26:11+09:00'
id: 268f6e98dbc11fac1831
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 前提
- カスタムユーザを作成済み
- テスト用データを作成済み

今回はカスタムユーザModelを作成して、employee_numberとpasswordでトークンを作成します
カスタムユーザを作成されたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/1e97889942f5da3bec1e

テスト用データを作成する際はfixtureを使うと効果的です
fixtureを作成されたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/29b5c253be6f802403cd

## 認証の種類
Webで使われている主な認証方法は以下の通りです

- Basic
- Token
- Json Web Token(JWT)
- Session

今回はJWT認証について具体例を交えながら解説していきます

## Json Web Token(JWT)認証
認証方法の一つでJSONベースのデータを暗号化してつくられる一意のトークンを使用して認証します
通常のToken認証との違ってクライアント側でTokenの正当性を確認できます
JWTから直接ユーザーを特定できるため、トークンをデータベースに保存しない(する必要がない)のが大きな特徴です
また、通常のToken認証のToken自体には意味を持たないのに対し、JWTはそれ自体が情報を持ちます
そのため、JWTの内部にパスワードなどの個人情報などを含めることは推奨されません

## JWTの構成
上から順に
- ヘッダ
- ペイロード
- キー(署名) 

の３つで構成されています

### ヘッダ
ヘッダには
- トークンの種類(JWT)
- 使用されている暗号方式(HMAC, SHA256, RSA)

の2つで構成されており、以下のような見た目になっています
```json
{
    "alg": "HS256",
    "typ": "JWT"
}
```
algは署名に使っているアルゴリズムを表しています
typはトークンの種別(Json Web Token)を表しています

### ペイロード
データ本体のことを指します
また、ペイロード内にはClaimというデータの属性情報も記載することができ、
- registered
- public
- private

の3種類あります

#### registered
必須ではないですがペイロード内に記載することが推奨されています
一般的によく使用されるものとして挙げられるのは
- iss（issuer,発行者）
- exp（expiration time,有効期限）
- sub（subject,対象者）
- aud（audience,視聴者）

などです

IANA(Internet Assigned Numbers Authority)のサイトから使用できるClaimの一覧を確認できます

https://www.iana.org/assignments/jwt/jwt.xhtml

#### public
IANAですでに定義されていないものであればJWTを使用する者が自由に定義することができます

#### private
当事者間でJWTを使って情報を共有するために作成される独自のClaimでregisterdでもpublicでもありません

### ペイロード例
よくある例としては以下のようにデータとsubというregistered claimを組み合わせたペイロードがあります
```json
{
  "sub": "1234567890",
  "name": "John Doe",
  "admin": true
}
```
前述の通りJWTの内部にパスワードなどの個人情報などを含めることは推奨されません
そのため、ペイロード内にパスワードなどの秘匿情報を入れることはありません

### キー(署名)
キー(署名)は
- エンコードされたヘッダー
- エンコードされたペイロード
- 秘密鍵
 
の3つを組み合わせて、ヘッダーで指定した暗号方式でエンコードします

例えば、HMACSHA256をヘッダに指定した場合、キー(署名)を以下のように作成します
```
HMACSHA256(
  # エンコードされたヘッダ
  base64UrlEncode(header) + "." +
  #　エンコードされたペイロード
  base64UrlEncode(payload),
  # 秘密鍵
  secret)
```
secretには主にDjangoのsecretkeyが利用されています

## Django Rest Frameworkで再現してみよう！
Django Rest FrameworkでJWT認証を設定するには以下のファイルを編集します
- settings.py
- プロジェクトのurls.py

### settings.py
今回は公式が推奨している`Simple JWT`を使用します

https://django-rest-framework-simplejwt.readthedocs.io/en/latest/index.html

まず、`Simple JWT`をインストールします
```
pip install djangorestframework-simplejwt
```

インストールが終わった後にsettings.pyに以下を追加します
```settings.py
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

### プロジェクトのurls.py
以下のコードを追加します
```プロジェクトのurls.py
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    ...
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ...
]
```

## tokenを発行してみよう！
以下に
- employee_number
- password

を入力してPOSTします
![スクリーンショット 2022-12-24 15.05.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/43a327ff-1e3c-0cca-7e96-fdfccd63881d.png)

すると、トークンが発行されます
![スクリーンショット 2022-12-24 15.05.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc90d1a9-324f-ab56-7135-35c7ce7f5bb6.png)

右にある`Authorize`ボタンを押します
![スクリーンショット 2022-12-18 20.48.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/29c64bfa-f9fc-e2ac-ad7f-cf51064e6a75.png)

先ほど作成したaccessトークンを入力し、`Authorize`ボタンを押すと認証完了です
![スクリーンショット 2022-12-24 15.15.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4548d7bf-91af-8e13-1e70-1f7915603bb3.png)

エンドポイントを操作できるようになりました
![スクリーンショット 2022-12-17 12.04.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6feac596-8281-ad09-deb4-6848806b3e98.png)
以上です

## 記事の紹介
以下の記事も書いたので良かったら読んでみてください

https://qiita.com/shun198/items/067e122bb291fed2c839

https://qiita.com/shun198/items/59f2d59263930b30d1bd

https://qiita.com/shun198/items/a79a17db571a461309ea

https://qiita.com/shun198/items/5cd0870ef95e0fc248bc

## 参考
https://www.django-rest-framework.org/api-guide/authentication/

