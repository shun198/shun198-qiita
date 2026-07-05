---
title: SQLServerがVisual Studio Code上でも使える!?拡張機能のインストール方法から使い方まで解説
tags:
  - SQLServer
  - VSCode
private: false
updated_at: '2022-08-12T08:38:14+09:00'
id: 0dea071628e320c5228b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
こんにちは。shun198です。
VSCodeでコード書いてるのにDBの実行結果をわざわざSQL Serverから閲覧するのはめんどくさい。。
VSCode内で完結できたらいいのになあって思うことがあると思います
今回はSQLServerの拡張機能のインストール方法とその使い方について一通り解説します。

## 前提
Visual Studio Codeをインストール済み
SQL Serverをインストール済み
SQL Server認証を使って接続

## 手順

### SQL Serverの拡張機能のインストール
まずは下記の画像のように拡張機能のメニューからMicrosoftの公式の拡張機能である<Strong>SQL Server (mssql) </Strong>をインストールします
![sqlserver_install.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/737a5612-4347-8345-1d69-1933054ffc13.png)

### SQL Serverのデータベースエンジンへ接続
SQL Serverのアイコンをクリックし、<Strong>Add Connection</Strong>を押します
![sqlserver_add connection.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2bc62b9a-3af0-93c0-9852-6bb5a79f6a57.png)

<Strong>Add Connection</Strong>をクリックしたあとにサーバー名を記入します
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/598139eb-df1e-4650-0d12-67314b4be8e1.png)

オプションでデータベースを選択することができます。今回はEnterを押して飛ばします
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/58665b8d-ff5d-c5a0-49ae-f58965657a6a.png)

認証方法を選択します。今回は前提にある通りSQL Server認証で接続するので<strong>SQL Login</strong>を選択します
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ff99cc5a-e7bd-1c2e-531d-f31fec0923f0.png)

ユーザ名とパスワードを入力します
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d4048a48-833e-6b4b-bc24-998c303840e2.png)
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/99302c21-ddfe-3be6-5556-f307d9bd91c1.png)

オプションで表示名を変えることができます。今回はDB_TESTにします
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/82ae0a2b-4f6b-67fc-e7cd-f2ade83de8e1.png)

無事データベースエンジンへ接続できました
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a8c6214f-e8ad-99b6-c8e6-a3713df4f144.png)

### SQL Serverの拡張機能でできること
Microsoftが出している拡張機能なだけあってできることは思ってた以上に使い勝手がいいです
おもな機能をざっとあげるとこんな感じです
- DB内のテーブルの閲覧
- テーブル内のカラムの閲覧
- クエリの実行
- クエリの履歴が左下から簡単に見れる上に再実行できる
- PDF,Excel,Jsonとして保存できる
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a4510c34-7595-c1d5-b328-6fb8283c361d.png)

また、SQLの拡張機能も一緒に入れるとクエリが見やすくなるのでデバッグがしやすくておすすめです
(SSMSだと見づらいので好きじゃないです。。)

コマンドパレットからも実行できるので使いやすいです
(shift+ctrl+pを押したあとにsqlと入力してください)
![image.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/547b8aca-644f-c104-b61a-684f736cdf45.png)

## まとめ
VSCode内で完結しているのと操作がわかりやすくて便利
ただ、テーブルをフィルターで絞ったりするなどの操作ができないので機能の充実度ではまだまだSSMSのほうが上だと感じました。
クエリを実行したりテーブルの中身を見るぶんには拡張機能のほうが使いやすいので入れておいて損はないかと思います






