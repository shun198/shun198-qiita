---
title: '[初心者向け] MySQL8.0の権限の確認および付与・削除する方法について解説'
tags:
  - MySQL8.0
private: false
updated_at: '2024-08-15T07:30:09+09:00'
id: b7f86bd7b998d3676c55
organization_url_name: null
slide: false
---
## 概要
DBを特定のユーザで直接操作したり、フレームワークのマイグレーション機能経由で操作する際にはDBの権限設定について理解する必要があるので

- 権限の種類
- 権限の確認方法
- 権限の付与方法
- 権限の削除方法

について解説していきたいと思います

## 前提
- 今回はMySQL8.0系を例に説明します

## 権限の種類
MySQLに限らず、DBにはさまざまな権限が存在します
よく見かける権限だけ列挙していきます
他の権限を見たい場合は以下の記事を参照してください

https://dev.mysql.com/doc/refman/8.0/ja/privileges-provided.html

### SELECT
- DBのテーブルから行を選択できる権限

### INSERT
- DBのテーブルに行を挿入できる権限

### UPDATE
- データベース内のテーブルで行を更新できる権限

### DELETE
- データベース内のテーブルから行を削除できる権限

### CREATE
- 新しいデータベースおよびテーブルを作成できる権限

### REFERENCES
- 外部キー制約を作成できる権限

### DROP
- 既存のDB、テーブル、ビューを削除できる権限

### ALL, ALL PRIVILEGES
- 全ての権限が付与される

## 権限の確認
権限を確認する際は以下のようにユーザ名を指定して確認します

```
show grants for 'dev_user'@'%';
+------------------------------------------------------------------------------------------------------------------+
| Grants for dev_user@%                                                                                            |
+------------------------------------------------------------------------------------------------------------------+
| GRANT USAGE ON *.* TO `dev_user`@`%`                                                                             |
| GRANT SELECT, INSERT, UPDATE, DELETE, CREATE, REFERENCES, ALTER, INDEX ON `dev_database`.* TO `dev_user`@`%` |
+------------------------------------------------------------------------------------------------------------------+
```
## 権限の付与
GRANTを使って権限を付与できます
付与する権限はGRANTの後ろに記載します
今回はdev_databaseの全てのテーブルにREFERENCEの権限を付与しています

```
GRANT REFERENCE ON dev_database.* TO 'dev_user'@'%';
```

## 権限の削除
REVOKEを使って権限を付与できます
削除する権限はREVOKEの後ろに記載します
今回はdev_databaseの全てのテーブルからREFERENCEの権限を削除しています

```
REVOKE REFERENCE ON dev_database.* FROM 'dev_user'@'%';
```

## 参考
https://dev.mysql.com/doc/refman/8.0/ja/grant.html

https://dev.mysql.com/doc/refman/8.0/ja/revoke.html

https://dev.mysql.com/doc/refman/8.0/ja/privileges-provided.html

https://qiita.com/shuntaro_tamura/items/2fb114b8c5d1384648aa
