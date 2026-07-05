---
title: Django Rest FrameworkでToken認証を実装する方法について
tags:
  - swagger
  - django-rest-framework
  - token
private: false
updated_at: '2022-12-24T16:20:20+09:00'
id: 9a7fa7ba9e834767081b
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

今回はToken認証について具体例を交えながら解説していきます

## Token認証
認証方式の一つで、HTTPヘッダにある一意のトークンを使用して認証します
作成されたトークンはデータベース内に保存されます

### Django Rest Frameworkで再現してみよう！
Django Rest FrameworkでToken認証を設定するには以下のファイルを編集します

- settings.py

#### settings.py
settings.pyに以下を追加します
```settings.py
INSTALLED_APPS = [
"rest_framework.authtoken",
]


REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.TokenAuthentication',
    ],
}
```

settings.pyの設定を終えた後にマイグレーションを行うとauthtoken_tokenというテーブルが作成されます
```
mysql> desc authtoken_token;
+---------+-------------+------+-----+---------+-------+
| Field   | Type        | Null | Key | Default | Extra |
+---------+-------------+------+-----+---------+-------+
| key     | varchar(40) | NO   | PRI | NULL    |       |
| created | datetime(6) | NO   |     | NULL    |       |
| user_id | char(32)    | NO   | UNI | NULL    |       |
+---------+-------------+------+-----+---------+-------+
3 rows in set (0.00 sec)
```

### Tokenを発行してみよう！
本来はToken発行用のエンドポイントを作成しますが、今回はDjangoのShellを使ってTokenを発行します
```
python manage.py shell
Python 3.10.9 (main, Dec  8 2022, 01:35:40) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> from rest_framework.authtoken.models import Token
>>> from application.models import User
>>> user = User.objects.get(employee_number="00000001")
>>> token = Token.objects.create(user=user)
>>> print(token.key)
cf4f9aa310f933333331082744c5dab67e29a5b9
```

authtoken_tokenテーブル内に
- 該当するUser
- トークン
- 作成時間

が記録されていることが確認されます
```
mysql> select * from authtoken_token;
+------------------------------------------+----------------------------+----------------------------------+
| key                                      | created                    | user_id                          |
+------------------------------------------+----------------------------+----------------------------------+
| cf4f9aa310f933333331082744c5dab67e29a5b9 | 2022-12-18 11:29:36.033368 | 00000000000000000000000000000001 |
+------------------------------------------+----------------------------+----------------------------------+
1 row in set (0.00 sec)
```

右にある`Authorize`ボタンを押します
![スクリーンショット 2022-12-18 20.48.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/29c64bfa-f9fc-e2ac-ad7f-cf51064e6a75.png)

`Token <トークン>`を入力し、`Authorize`ボタンを押すと認証完了です
![スクリーンショット 2022-12-24 15.43.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d4a86feb-25b9-5b3a-afaa-8c4598f87663.png)


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

