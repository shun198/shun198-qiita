---
title: コンテナ内のDBをVSCodeからGUIで操作する方法
tags:
  - Docker
  - docker-compose
  - VSCode
  - MySQL8.0
private: false
updated_at: '2026-09-05T08:55:28+09:00'
id: cdc8eaa457c1dc202e1b
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
![スクリーンショット 2023-07-28 11.28.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a1eca4bf-246d-d098-de4a-b856ca99116c.png)
## 前提
- すでにコンテナを作成済み
- MySQLを例に操作説明します
- Dev Containersを設定済み
- launch.jsonを設定済み

上記の設定ができてない、方法がわからない方は下記の記事を参考にしてください

https://qiita.com/shun198/items/9e4fcb4479385217c323

## Dev Containersを使ってコンテナへリモート接続
![スクリーンショット 2023-07-28 11.28.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8f78758a-d47c-ec90-bd2a-1dd10df45921.png)

## SQLToolsをインストール
![スクリーンショット 2023-07-28 11.28.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d3619eb6-4852-0340-a1f3-4c89d801c874.png)

## SQLTools MySQL/MariaDBをインストール
今回はMySQLをインストールします
使用できるDBは以下の通りです
- AWS Redshift
- CockroachDB
- MariaDB
- Microsoft SQL Server/Azure
- MySQL
- PostgreSQL
- SQLite

![スクリーンショット 2023-07-28 11.29.08.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/52b512af-6e33-d7b0-492c-450e41fde038.png)

## Add New Connectionを選択
![スクリーンショット 2023-07-28 11.29.23.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f77b2a33-c569-710a-ad05-8ceb2dacadb8.png)


## MySQLを選択
![スクリーンショット 2023-07-28 11.29.38.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ad884260-d261-22fc-601d-d398a7bf930c.png)

## 設定を入力
接続する際の設定値を入力していきます
|  項目  |  入力値  | 
|-----|-----|
|  Connection name  | 任意の名前で大丈夫です  | 
| Server Address | DBのコンテナ名を指定します |
| Port | compose.yamlで指定したポート番号を入力します |
| Database | .envに記載しているDB名 |
| Username | .envに記載しているユーザ名 |
| Password | .envに記載しているパスワード |

![スクリーンショット 2023-07-28 11.29.57.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/efe98a23-86fc-daed-908f-a4a64ffb5fd3.png)

## 接続に成功
成功すると以下のようにDBとテーブル一覧が表示されます
![スクリーンショット 2023-07-28 11.30.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/aff2401b-e9c6-a4f2-4702-12e1154f96ee.png)

テーブルの詳細を見ることができます
![スクリーンショット 2023-07-28 11.30.28.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/29d9e1ac-b74d-157a-a549-0508f8b381c5.png)

🔍を押すとSelect文が実行され、データ一覧が表示されます
![スクリーンショット 2023-07-28 11.30.46.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e5db1a58-b645-6552-69ff-419134543dc6.png)

＋を押すと自動でInsert文を入力できます
![スクリーンショット 2023-07-28 11.31.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1146172d-526c-c9a5-8ef2-916a35ed2c84.png)

以上です。

## 記事の紹介
以下の記事も書いたのでよかったら読んでいただけると幸いです

https://qiita.com/shun198/items/a66d6214cdab5629029d

https://qiita.com/shun198/items/f6864ef381ed658b5aba

## 参考
https://qiita.com/Midoliy/items/0b254d91aa93763db11a

https://penpen-dev.com/blog/docker-compose-mysql-container-vscode/

