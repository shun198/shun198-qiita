---
title: DjangoとPythonのsecretsを使ってパスワードの自動生成・ハッシュ化をしよう
tags:
  - Python
  - Django
private: false
updated_at: '2023-11-29T09:55:05+09:00'
id: b54b741553d0ee905c08
organization_url_name: null
slide: false
---
## 概要
Djangoにはmake_random_password()というメソッドがあるのですが非推奨なので今回は公式で推奨されているsecretsを使ったパスワード生成方法を使用します
また、ハッシュ化はDjangoにある機能を使って行います

https://github.com/django/django/commit/00e187961059a0e77403151d2bb38c217101d5af#diff-7f8222e3ea4582896fd11abf2064580181e771c652e4e469b4a101fb3380a2c5

https://docs.djangoproject.com/en/4.2/releases/4.2/#id1

https://docs.python.org/3/library/secrets.html#recipes-and-best-practices

今回はDjangoのshellを使って自動生成します
secretsとstringをimportし、メソッドを実行します

```
poetry run python manage.py debugsqlshell
Python 3.11.2 (main, Mar 23 2023, 14:09:52) [GCC 10.2.1 20210110] on linux
Type "help", "copyright", "credits" or "license" for more information.
(InteractiveConsole)
>>> import string
>>> import secrets
>>> alphabet = string.ascii_letters + string.digits + string.punctuation
>>> password = ''.join(secrets.choice(alphabet) for i in range(16))
>>> password
'i,Id1DtX$y5dNLo('
```

- ascii_letters
- digits
- punctuation

の中身は以下の通りです
```
>>> string.ascii_letters
'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ'
>>> string.digits
'0123456789'
>>> string.punctuation
'!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~'
```

また、range内の数字でパスワードの長さを調整できます

## パスワードのハッシュ化
fixtureを使う際にパスワードをハッシュ化する際はDjangoのmake_passwordメソッドを使います
make_passwordメソッドの中に先ほど自動生成したパスワードを入れます
```
>>> from django.contrib.auth.hashers import make_password
>>> make_password('!"#$%&\'()*+,-./:;<=>?@[\\]^_`{|}~')
'pbkdf2_sha256$600000$QcH0cm6kihyD7LCU3vL0XG$bcnfLwTFLzewYJj14xIhErzDY82qK57KRLLu0I7p6Ew='
```

以上です

## 参考
https://stackoverflow.com/questions/9480641/django-password-generator

https://www.idiotinside.com/2017/06/04/django-make-random-passwords/

https://docs.python.org/3/library/secrets.html#recipes-and-best-practices

https://pgstudio.oji-cloud.net/2021/03/17/post-2607/
