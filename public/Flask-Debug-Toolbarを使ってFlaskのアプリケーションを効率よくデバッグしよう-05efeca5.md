---
title: Flask Debug Toolbarを使ってFlaskのアプリケーションを効率よくデバッグしよう！
tags:
  - Flask
  - flask-debug-toolbar
private: false
updated_at: '2025-01-15T15:40:14+09:00'
id: 05efeca5ba108ad6dcf6
organization_url_name: null
slide: false
---
## 概要
Flask Debug Toolbarを使うとローカル上のFlaskのアプリケーションを効率よくデバッグできます
今回はFlask Debug Toolbarの設定方法および利用方法について解説します

## 実装
以下のようにDebugToolbarExtensionを初期化します
app.debugをTrueにすればDebug Toolbarを使用できます

```main.py
import os

from flask_debugtoolbar import DebugToolbarExtension

app = Flask(__name__)
app.debug = os.environ.get("DEBUG")

app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
toolbar = DebugToolbarExtension(app)
```

## 実際に触ってみよう！
以下のようにDebug　Toolbarのサイドバーが表示されたら成功です

![スクリーンショット 2025-01-15 15.35.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d2047bac-5b14-cc3a-f761-7508e7883ec4.png)

各パッケージの詳細、HTTPヘッダ、環境変数、APIのルートなどを確認できるので便利ですね

![スクリーンショット 2025-01-15 15.38.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d66362e5-f8c1-c6cf-0a0e-88f82f6b0db6.png)

![スクリーンショット 2025-01-15 15.38.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/37093d45-4ac2-214b-9edc-33b92aca5515.png)

![スクリーンショット 2025-01-15 15.39.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/5a02b8f1-913d-cdb4-ea50-208667b415ba.png)

![スクリーンショット 2025-01-15 15.39.42.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0cdbf286-7c6a-acef-1539-cc5349c8a73e.png)

## 参考
https://flask-debugtoolbar.readthedocs.io/en/latest/

https://github.com/pallets-eco/flask-debugtoolbar?tab=readme-ov-file
