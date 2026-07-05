---
title: BigQuery内のDatasetから最新の日付のPrefix/Suffixのテーブル名を取得するには？
tags:
  - SQL
  - BigQuery
  - GoogleCloud
  - information_schema
private: false
updated_at: '2025-04-13T08:39:36+09:00'
id: b4c44ac564799fc08a7c
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Dataset内の履歴テーブルから最新のPreffixもしくはSuffixのテーブル名(例えば、history_20250202)を取得したいニーズがあるかと思います
INFORMATION_SCHEMAを使えば実現できるのでその方法について解説します

## INFORMATION_SCHEMAとは？
BigQueryに関するメタデータ情報を提供するシステム定義の読み取り専用のViewです
BigQueryに限らず、MySQLやPostgresにも存在します
INFORMATION_SCHEMA.TABLESのViewからデータセット内の各テーブルまたはViewが表示されます
今回はINFORMATION_SCHEMA.TABLESを使ってテーブルの一覧を取得し、MAX関数とREGEXP_CONTAINS関数を使って該当するREGEXと日付の形式(YYYYMMDD)のテーブルから最新の日付のテーブル名を取得するクエリを作成します

https://cloud.google.com/bigquery/docs/information-schema-tables?hl=ja#schema

## 最新の日付のPrefix/Suffixのテーブル名を取得できるクエリ
最新の日付のPrefixのテーブル名は以下のように取得できます
```
SELECT MAX(table_name) FROM project.dataset.INFORMATION_SCHEMA.TABLES
WHERE REGEXP_CONTAINS(table_name,"[0-9]{8}_history")
```

また、最新の日付のSuffixのテーブル名は以下のように取得できます

```
SELECT MAX(table_name) FROM project.dataset.INFORMATION_SCHEMA.TABLES
WHERE REGEXP_CONTAINS(table_name,"history_[0-9]{8}")
```

## 実際に実行してみよう！
今回はSuffixに日付をつけた履歴テーブルを作成してみました

![スクリーンショット 2025-04-13 8.35.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dfeb022c-b9b0-40d3-9f99-287d2fab412c.png)

クエリを実行し、最新の日付のテーブル名を取得できれば成功です

![スクリーンショット 2025-04-13 8.37.11.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b04ec496-8607-4f38-a878-0c4849c3a08e.png)

また、MIN関数を使って一番古い日付のテーブル名も取得できます

![スクリーンショット 2025-04-13 8.38.45.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cb80ddf1-97dc-4e43-9ee1-c9d5801de81c.png)

## 参考
https://cloud.google.com/bigquery/docs/information-schema-intro?hl=ja
