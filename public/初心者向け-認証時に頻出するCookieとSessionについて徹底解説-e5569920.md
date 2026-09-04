---
title: '[初心者向け] 認証時に頻出するCookieとSessionについて徹底解説'
tags:
  - cookie
  - session
private: false
updated_at: '2023-10-22T21:33:18+09:00'
id: e5569920f73e213a63f6
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
ログイン認証時に頻出する
- Cookie
- Session

とその関係について解説していきます

## Cookieとは
WEBサイトを閲覧したときに、訪問者が訪れたサイトや入力したデータ、利用環境などの情報をWebブラウザに保存する仕組みのこと
CacheはHTMLなどの静的な情報を一時的に保存する仕組みに対してCookieは後述するSessionIDなどユーザの情報を保存する仕組みなので混同しないようにしましょう

https://qiita.com/shun198/items/59f2d59263930b30d1bd

通常RestAPIを使うとステートレスなやり取りになります
そのため、認証情報を格納してステートフルな状態にするには後述するSessionという概念について理解する必要があります

RestAPIとは何か？ステートレスとは何か？について知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/5cd0870ef95e0fc248bc

## Sessionとは
アクセスの開始から終了までの一連の通信のことです
もっと具体的な話をするとユーザが認証が必要なページにログイン(Sessionを開始)してからログアウト(Sessionを終了)するまでの期間のことを指します
ログイン認証でも説明しますがSessionが開始済み(ログイン済み)かどうかはSessionIDを使って管理するのが一般的です

## 一般的なログイン認証について
CookieとSessionについて説明したのでこの2つを使った一般的なログイン認証について説明します

![session.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7a821006-8d23-2d15-d6d1-61cd9de6f078.png)

まず、ログイン情報を入力した状態でリクエストします
その際、サーバ側はログイン情報を認証し、該当するユーザが存在するのであればSessionIDを作成し、DBに格納します
(図では便宜上sessionid1などと記載されていますが実際は推測されづらいランダムな値です)
その後、ログイン成功時のレスポンスにSessionIDを返します
SessionIDをブラウザ内のCookieに格納することで認証が必要なリクエストでもステートフルな通信を実現することができます
Cookie内は誰でも見ることができる都合上、ログイン情報はそのまま返さずに一意のSessionIDを使って行うのが一般的です
そのため、SessionIDは推測されないような値にする必要があります

## Cookieの中身を確認しよう
今回は簡単なログイン用のフォームを例に紹介します
ログイン用フォームに社員番号とパスワードを入力し、ログインするとログイン成功画面に遷移します
![スクリーンショット 2023-10-22 20.02.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1e44b2dd-615e-c0e7-732d-9d32a112bdd0.png)
![スクリーンショット 2023-10-22 15.38.25.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e98c7e72-621e-2594-e18b-7aaa993526ba.png)

Cookieの中身はChrome Developer ToolのアプリケーションのCookieから確認できます
ログイン前にCookieを開くと下記のように何も入ってない状態です
![スクリーンショット 2023-10-22 20.05.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/38ae7d17-54eb-e634-f9a0-2505b01ffd75.png)

ログインに成功すると以下のようにSessionIDがCookieに保存されます
![スクリーンショット 2023-10-22 21.15.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dd03349e-1cde-864b-d358-dc288153e4c6.png)

今回はフレームワークをDjango、DBをPostgresを例に説明していますが、DB上でもセッションIDが格納されていることを確認できます
```
postgres=# \d django_session
 session_key  | character varying(40)    |           | not null | 
 session_data | text                     |           | not null | 
 expire_date  | timestamp with time zone |           | not null | 
postgres=# select * from django_session;
 fjnp91385waomnbjeyrj9d5xv1yghwhu |.eJxtjEsOAiEQRO_CWgm_6UGX7j0DaWiQUQPJfFbGuzskLDSxFpVKql69mMNtzW5b4uwmYmcmuo5_rEuywzfmMTxiaSzdsdwqD7Ws8-R5m_DeLvxaKT4vfftzkHHJjSZAYEkDAqyQfuYRhIBtA0K9iohyFGBMkNKSRjac7RehkErTxI8e38AJ_E-gQ:1quXMh:m_UZbRXoULHFeFe6lyeb52dJw0Cpuq6VxCr8U8eOWCk | 2023-11-05 12:15:31.119386+00
```

## 参考
https://www.engilaboo.com/definitely-understand-cookie-session/

https://developer.mozilla.org/en-US/docs/Web/HTTP/Guides/Cookies

https://gmotech.jp/semlabo/webmarketing/blog/cookie/

https://gc-seo.jp/journal/session/
