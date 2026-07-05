---
title: '[Django] DBのテーブルやカラムにコメントを追加する方法について解説'
tags:
  - Django
private: false
updated_at: '2024-07-10T07:58:44+09:00'
id: 15d9f3ac280ef2f044bf
organization_url_name: null
slide: false
---
## 概要
Django4.2からDB内のテーブルやカラムにコメントを追加できるようになリました
保守性の観点からコメントはほしいので本記事で追加する方法について解説していきます

## 前提
- DBはMySQLを使用
- Django4.2以上を使用
- Django内でMySQLの接続設定を完了済み

## ファイル構成
```
application
   ├── __init__.py
   ├── admin.py
   ├── apps.py
   ├── migrations
   └── models.py
```

## Modelにコメントを追加しよう
今回は例として
- お客様
- 住所

のModelを2つ作成しました
カラムにコメントを追加する際は該当するField内に
```
db_comment="コメント",
```
を記載していきます
また、テーブルにコメントを追加する際はMetaクラス内に
```
db_table_comment = "コメント"
```
を記載していきます

```models.py
import uuid

from django.core.validators import RegexValidator
from django.db import models


class Customer(models.Model):
    """お客様"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="お客様ID",
    )
    kana = models.CharField(
        max_length=255,
        db_comment="カナ氏名",
    )
    name = models.CharField(
        max_length=255,
        db_comment="氏名",
    )
    birthday = models.DateField(
        db_comment="誕生日",
    )
    phone_no = models.CharField(
        max_length=11,
        validators=[RegexValidator(r"^[0-9]{11}$", "11桁の数字を入力してください。")],
        blank=True,
        db_comment="電話番号",
    )
    address = models.ForeignKey(
        "Address",
        on_delete=models.CASCADE,
        related_name="address",
        db_comment="住所ID",
    )

    class Meta:
        db_table = "Customer"
        db_table_comment = "お客様"


class Address(models.Model):
    """住所"""

    id = models.UUIDField(
        primary_key=True,
        default=uuid.uuid4,
        editable=False,
        db_comment="住所ID",
    )
    prefecture = models.CharField(
        max_length=255,
        db_comment="都道府県",
    )
    municipalities = models.CharField(
        max_length=255,
        db_comment="市区町村",
    )
    house_no = models.CharField(
        max_length=255,
        db_comment="丁・番地",
    )
    other = models.CharField(
        max_length=255,
        blank=True,
        db_comment="その他(マンション名など)",
    )
    post_no = models.CharField(
        max_length=7,
        validators=[RegexValidator(r"^[0-9]{7}$", "7桁の数字を入力してください。")],
        null=True,
        db_comment="郵便番号",
    )

    class Meta:
        db_table = "Address"
        db_table_comment = "住所"
```

## コメントが追加されているか確認しよう！
DBの内容を適用させるためにマイグレーションを実行しましょう
```
python manage.py makemigrations
python manage.py migrate
```

実際にMySQLに接続して確認してみましょう

### テーブル名とテーブルのコメント
該当するテーブルのテーブル名とテーブルのコメントが記載されているかどうか確認するには以下のコマンドを実行します
```
mysql> select table_name, table_comment from information_schema.tables where TABLE_NAME = "テーブル名";
```

- お客様
- 住所

のテーブル名とテーブルのコメントを取得していきます

```
mysql> select table_name, table_comment from information_schema.tables where TABLE_NAME = "Customer";
+------------+---------------+
| TABLE_NAME | TABLE_COMMENT |
+------------+---------------+
| Customer   | お客様        |
+------------+---------------+
1 row in set (0.00 sec)
```

```
mysql> select table_name, table_comment from information_schema.tables where TABLE_NAME = "Address";
+------------+---------------+
| TABLE_NAME | TABLE_COMMENT |
+------------+---------------+
| Address    | 住所          |
+------------+---------------+
1 row in set (0.00 sec)
```

テーブル名とテーブルのコメントを確認できました

### カラムのコメント
続いてカラムのコメントが記載されているかどうか確認するには以下のコマンドを実行します

```
mysql> show full columns from テーブル名;
```

- お客様
- 住所

のカラムのコメントを取得していきます

```
mysql> show full columns from Customer;
+------------+--------------+-------------+------+-----+---------+-------+---------------------------------+--------------+
| Field      | Type         | Collation   | Null | Key | Default | Extra | Privileges                      | Comment      |
+------------+--------------+-------------+------+-----+---------+-------+---------------------------------+--------------+
| id         | char(32)     | utf8mb4_bin | NO   | PRI | NULL    |       | select,insert,update,references | お客様ID     |
| kana       | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | カナ氏名     |
| name       | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | 氏名         |
| birthday   | date         | NULL        | NO   |     | NULL    |       | select,insert,update,references | 誕生日       |
| phone_no   | varchar(11)  | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | 電話番号     |
| address_id | char(32)     | utf8mb4_bin | NO   | MUL | NULL    |       | select,insert,update,references | 住所ID       |
+------------+--------------+-------------+------+-----+---------+-------+---------------------------------+--------------+
6 rows in set (0.01 sec)
```

```
mysql> show full columns from Address;
+----------------+--------------+-------------+------+-----+---------+-------+---------------------------------+-------------------------------------+
| Field          | Type         | Collation   | Null | Key | Default | Extra | Privileges                      | Comment                             |
+----------------+--------------+-------------+------+-----+---------+-------+---------------------------------+-------------------------------------+
| id             | char(32)     | utf8mb4_bin | NO   | PRI | NULL    |       | select,insert,update,references | 住所ID                              |
| prefecture     | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | 都道府県                            |
| municipalities | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | 市区町村                            |
| house_no       | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | 丁・番地                            |
| other          | varchar(255) | utf8mb4_bin | NO   |     | NULL    |       | select,insert,update,references | その他(マンション名など)            |
| post_no        | varchar(7)   | utf8mb4_bin | YES  |     | NULL    |       | select,insert,update,references | 郵便番号                            |
+----------------+--------------+-------------+------+-----+---------+-------+---------------------------------+-------------------------------------+
6 rows in set (0.00 sec)
```

カラムのコメントを確認できました

## 参考
https://docs.djangoproject.com/en/4.2/ref/models/fields/

https://blog.pyq.jp/entry/python_news_230406

https://qiita.com/snaka/items/28c636214099f3b99c18
