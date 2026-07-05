---
title: Cookieとは？Cacheとは？2つの違いも含めて徹底解説
tags:
  - Web
  - cookie
  - ブラウザ
  - Cache
private: false
updated_at: '2023-10-22T21:32:38+09:00'
id: 59f2d59263930b30d1bd
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## Cookieとは？

Cookie（クッキー）とはWebサイト(Webサーバー)にアクセスしたクライアント(ユーザー)の情報を一定期間保持するファイルまたは仕組みのことです

Cookieにはアクセスしたクライアントの
- セッションID(IDやパスワードなどの個人情報を直接保存することは一般的に避けられいるため)
- IPアドレス
- 訪れた日時
- 訪問回数

など様々なデータが保存されており、アクセスしたWEBサイトから自身のブラウザに送られ、保存されます。

### Cookieの仕組み
![cookie.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3b0f5afa-9dac-e3b5-a676-0bc06368de47.png)

上の図のようにサイトを利用する際に一度IDとパスワードでログインすると、しばらくの間ログイン情報を入力することなく、自分のアカウントにアクセスできるのはCookie内にログイン情報が入っているからです
Cookieがあることでクライアント(ユーザ)は２回目以降訪れたサイトを毎回情報を再入力せずに利用できるため、便利です

## Cacheとは？
訪れたWEBページの
- HTML
- 画像
- アイコン

などの情報をブラウザが一時的に保存する仕組みです
ブラウザの中に保存したキャッシュを読み込むことで、次に同じWebページを訪問したときにブラウザに保存されたデータを参照するため、表示するスピードが早くなり、閲覧しやすくなります

### Cacheの仕組み
![cache.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a70078fc-40a2-c957-29d7-f3170894cf1f.png)


上の図のようにサイトを利用する際に一度サイトにアクセスすると、ブラウザからキャッシュを参照するので表示が高速になります。
ただし、一時的に保存された古いキャッシュが原因で、古いままページの情報が表示されたり、正しく表示されなかったりすることがあります
キャッシュを削除することで更新された最新のページが表示されるので例えばWebページを更新したのになんで反映されないんだ、と思った時はキャッシュを消してみるのも手です

## CookieとCacheの違い
どちらも情報をブラウザに一時保存する仕組みですが保存する情報が違います
CookieにセッションIDなどサイトの閲覧情報が保存されるのに対して
CacheにサイトのHTMLや画像が保存されます
Cookieを削除すると閲覧情報が消えるため、例えばサイトにログインする際はもう一度ログインする必要があります
Cacheを削除するとサイトを表示するHTMLデータや画像が消えるため、ブラウザではなくサイトから直接取得するので表示が遅くなります

## 参考
https://gmotech.jp/semlabo/seo/blog/cookie/

https://www.geekly.co.jp/column/cat-webgame/1910_001/

https://myajo.net/tips/7527

https://www.orixbank.co.jp/aboutus/policy/guide/cache.html

https://pcdr-chiebukuro.com/cache-sakujo-dounaru/

https://www.engilaboo.com/definitely-understand-cookie-session/

