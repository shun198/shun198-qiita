---
title: BigQueryのMerge関数の使用方法について
tags:
  - SQL
  - BigQuery
  - GoogleCloud
private: false
updated_at: '2025-03-09T12:11:23+09:00'
id: 51eb079068511309243c
organization_url_name: null
slide: false
---
## 概要
BigQueryのMerge関数の使用方法について解説します

## 前提
- データセットを作成済み
    - [データセットを作成する](https://cloud.google.com/bigquery/docs/datasets?hl=ja)

## 実装
今回はわかりやすい例として
- クーポンの使用履歴テーブル
- クーポン使用済み履歴テーブル

の2テーブルを例にMerge関数を使います
クーポンの使用済み履歴テーブルと使用履歴テーブルを比較してすでに使用しているデータがあれば使用済み履歴テーブルにInsertする処理を書きます

### 必要なテーブルとデータの作成
以下がクーポンの使用履歴テーブルです

```sql
CREATE OR REPLACE TABLE practice_dataset.coupon_usage (
    user_id INT64,
    coupon_code INT64,
    is_used BOOL,
    used_at TIMESTAMP
);
```

以下がクーポンの使用済み履歴テーブルです
```sql
CREATE OR REPLACE TABLE practice_dataset.used_coupons (
    user_id INT64,
    coupon_code INT64,
    used_at TIMESTAMP,
    migrated_at TIMESTAMP
);
```

それぞれのテーブルにデータをInsertしていきます
```sql
INSERT INTO practice_dataset.coupon_usage (user_id, coupon_code, is_used, used_at)
VALUES
    (1, 1, true, TIMESTAMP '2025-03-08 10:00:00'),
    (2, 2, true, TIMESTAMP '2025-03-08 11:00:00'),
    (3, 3, false, NULL),
    (1, 2, false, NULL);
```

```sql
INSERT INTO practice_dataset.used_coupons (user_id, coupon_code, used_at, migrated_at)
VALUES
    (1, 1, TIMESTAMP '2025-03-08 10:00:00', TIMESTAMP '2025-03-08 10:00:00')
```

クーポン使用履歴テーブルの中身は以下のとおりです

![スクリーンショット 2025-03-08 14.17.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f29f5511-a5fd-4668-bb5d-ac703cf1db69.png)

クーポン使用済み履歴テーブルの中身は以下のとおりです

![スクリーンショット 2025-03-08 14.18.02.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/230ee9ec-72a8-4f27-9b80-59541a96b199.png)

### Mergeクエリの作成
coupon_usage内で使用済みのもの(is_used)のみ抽出し、used_couponsにmatchしなければInsertします
その際にWHEN NOT MACHED THENを使います

```sql
MERGE INTO practice_dataset.used_coupons AS target
USING (
    SELECT user_id, coupon_code, used_at
    FROM practice_dataset.coupon_usage
    WHERE is_used = TRUE
) AS source
ON target.user_id = source.user_id AND target.coupon_code = source.coupon_code
WHEN NOT MATCHED THEN
    INSERT (user_id, coupon_code, used_at, migrated_at)
    VALUES (source.user_id, source.coupon_code, source.used_at, CURRENT_TIMESTAMP());

```

### 実行結果
以下のように使用済みの履歴がused_couponsにInsertされていたら成功です

![スクリーンショット 2025-03-08 14.31.51.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/efaeef01-e3bc-4165-894f-bc05e820e872.png)



## トラブルシューティング
```
Not found: Dataset practice_dataset.user_01 was not found in location US 
```

データセット名が間違っているので確認しましょう

## 参考
https://cloud.google.com/bigquery/docs/reference/standard-sql/dml-syntax#merge_statement

https://cloud.google.com/bigquery/docs/tables?hl=ja

https://sql.info/d/bigquery-error-not-found-dataset-xyz-was-not-found-in-location-us
