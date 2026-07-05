---
title: CORSとは？Djangoでの設定方法についても解説
tags:
  - Django
  - CORS
private: false
updated_at: '2024-02-20T10:05:41+09:00'
id: 9ebf19d8fd2c412396dd
organization_url_name: null
slide: false
---
## CORSって何？
オリジン間リソース共有(Cross-Origin Resource Sharing)の略で
自身のオリジンから見た別のオリジン(Cross-Origin)からのリクエストを共有するかどうか決定できる仕組みのことです

## そもそもオリジンって何？
オリジンは
- スキーム
    - サイトによってはプロトコルと書かれていたりするが厳密には違う。しかし、Web開発においては基本httpかhttpsを使うのでプロトコルでも問題ない
- FQDN
    - サイトによってはホストやドメインと書かれていたりするが厳密にはFQDNつまり完全修飾ドメイン名のこと
- ポート

を全て組み合わせたものです

![CORS_origin.drawio.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8e144bfb-4e57-d9ed-fa12-204dad8b596d.png)

通常はあるWebサイトが持つ情報が別の悪意あるWebサイトに悪用される(後述)のを防ぐために同一オリジンポジシーが適用されます

## 同一オリジンポリシーって何？
あるオリジンで読み込まれたリソース（HTML, スクリプト, Cookie など）が、異なるオリジン（クロスオリジンとも呼ばれる）のリソースとの通信・アクセスを制限する、Web ブラウザが持つセキュリティ機能です。
異なるオリジンからロードされたリソースへのアクセスをブロックすることにより、元オリジンで読み込まれたリソースに対して悪い影響を及ぼさないようにすることを目的としています。
2つのオリジン(Origin)の
- スキーム(プロトコル)
- FQDN(ホスト、ドメイン)
- ポート

がすべて一致した場合のみ同一オリジンだと言えます

### 同一オリジンの例

:::note 
```
http://example.com:8000/api/customers/1
```
```
http://example.com:8000/api/customers/2
```
:::

パスは異なるものの、スキーム、FQDN、ポートは同じなので同一オリジンです

### 同一オリジンではない例(1)

:::note alert
```
http://example.com:8000/api/customers/1
```
```
https://example.com:8000/api/customers/1
```
:::

スキームが違う(`http`と`https`)ため、同一オリジンではありません

### 同一オリジンではない例(2)

:::note alert
```
http://example.com:8000/api/customers/1
```
```
http://example.com:8080/api/customers/1
```
:::

ポートが違う(8000と8080)ため、同一オリジンではありません

## 同一オリジンポリシーがないとどうなるの？
ユーザがWebサイトにログインした状態で別の悪意のあるサイト(別オリジン)から本人が意図しない情報やリクエストを勝手に送信されてしまうCSRF(Cross-Site Request Forgeries)や外部の不正なスクリプトを実行させるXSS(Cross Site Scripting)を受けてしまいます

## CORSが必要なのはなぜ？
フロントエンドとバックエンドに分けて開発する際はそれぞれ別々のオリジンに配置するのが一般的です
そこでCORSの設定をすることで同一オリジンポリシーを守りつつ別のオリジン(Cross-Origin)からのリクエストを共有できます

## 必要なパッケージのインストール
下記をインストールします
```
pip install django-cors-headers
```

## 必要な設定を記載
Djangoのsettings.pyに記載していきます
```settings.py
import os


# corsheadersを追加
INSTALLED_APPS = [
    'corsheaders',
]

# corsheaders.middleware.CorsMiddlewareを追加
MIDDLEWARE = [
    # 一番上に記載
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]


# 自身以外のオリジンのHTTPリクエスト内にクッキーを含めることを許可する
CORS_ALLOW_CREDENTIALS = True
# アクセスを許可したいURL（アクセス元）を追加
CORS_ALLOWED_ORIGINS = os.environ.get("TRUSTED_ORIGINS").split(" ")
# プリフライト(事前リクエスト)の設定
# 30分だけ許可
CORS_PREFLIGHT_MAX_AGE = 60 * 30
```

envファイルに許可するoriginを記載します
```.env
TRUSTED_ORIGINS="http://localhost:3000"
```

以上です

## 参考
https://developer.mozilla.org/ja/docs/Web/HTTP/CORS

https://qiita.com/att55/items/2154a8aad8bf1409db2b

https://coliss.com/articles/build-websites/operation/work/cs-visualized-cors.html

https://zenn.dev/syo_yamamoto/articles/445ce152f05b02

https://kikuichige.com/11885/

https://yamory.io/blog/about-cors/

https://livra.geolocation.co.jp/iplearning/250/
