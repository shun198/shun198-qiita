---
title: Symbolic Linkを使ってTerraformをDRYに管理しよう！
tags:
  - Linux
  - Terraform
private: false
updated_at: '2025-04-22T08:16:25+09:00'
id: 654a2441380f11d3033f
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Terraformを使ってインフラ構築する際にdev、stg、prdと環境を分けるかと思います
今回はSymbolic Linkを使って共通で使用するコードをDryに管理する方法について解説していきたいと思います

## Symbolic Linkとは
Wikipediaからの引用ですが
> In computing, a symbolic link (also symlink or soft link) is a file whose purpose is to point to a file or directory (called the "target") by specifying a path thereto.

ファイルまたはディレクトリ（「ターゲット」と呼ばれる）へのパスを指定することによって、そのファイルまたはディレクトリを指すことを目的としたファイル

とのことです
ざっくりと説明するとシンボリックリンクを貼ることで、そのディレクトリやファイルを参照するショートカットを作成する仕組みだと思っていただけたらいいと思います

## 今回検証するディレクトリ構成
```
├── dev
├── prd
├── README.md
├── shared
│   └── query
│       └── insert_coupon_usage.sql
└── stg
```

## Symbolic Linkを貼ってみよう！
以下のコマンドでSymbolic Linkを貼ることができます
```
ln -s {参照元ファイル/フォルダ}　{リンク名}
```

今回だとinsert_coupon_usage.sqlが参照元でdevフォルダ配下がリンク名です

```
ln -s shared/query/insert_coupon_usage.sql dev
```

以下のようにdev配下にSymbolic Linkを貼ることができれば成功です

```
├── dev
│   └── insert_coupon_usage.sql
├── prd
├── README.md
├── shared
│   └── query
│       └── insert_coupon_usage.sql
└── stg
```

## 実際に実行してみよう！
試しに以下のファイルにコメントを記載してみます
```insert_coupon_usage.sql
MERGE INTO ${dataset}.used_coupons AS target
USING (
    SELECT user_id, coupon_code, used_at
    FROM ${dataset}.coupon_usage
    WHERE is_used = TRUE
)
AS source ON target.user_id = source.user_id
AND target.coupon_code = source.coupon_code
-- 条件に一致しなければInsertする
WHEN NOT MATCHED THEN
    INSERT (user_id, coupon_code, used_at, migrated_at)
    VALUES (source.user_id, source.coupon_code, source.used_at, CURRENT_TIMESTAMP());
```

以下のように差分を検知することができれば成功です

```
Terraform will perform the following actions:

  # google_bigquery_data_transfer_config.insert_coupon_usage_query will be updated in-place
  ~ resource "google_bigquery_data_transfer_config" "insert_coupon_usage_query" {
        id                        = "projects/XXXXXXXXXXXXX/locations/us/transferConfigs/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXXX"
        name                      = "projects/XXXXXXXXXXXXX/locations/us/transferConfigs/XXXXXXXX-XXXX-XXXX-XXXX-XXXXXXXXXXXXX"
      ~ params                    = {
          ~ "query" = <<-EOT
                MERGE INTO practice_dataset.used_coupons AS target
                USING (
                    SELECT user_id, coupon_code, used_at
                    FROM practice_dataset.coupon_usage
                    WHERE is_used = TRUE
                )
                AS source ON target.user_id = source.user_id
                AND target.coupon_code = source.coupon_code
              + -- 条件に一致しなければInsertする
                WHEN NOT MATCHED THEN
                    INSERT (user_id, coupon_code, used_at, migrated_at)
                    VALUES (source.user_id, source.coupon_code, source.used_at, CURRENT_TIMESTAMP());
            EOT
        }
        # (10 unchanged attributes hidden)
    }

Plan: 0 to add, 1 to change, 0 to destroy.
```


## 参考
https://zenn.dev/pageo/articles/d90d89e2168061

https://atmarkit.itmedia.co.jp/ait/articles/1605/30/news022.html

https://qiita.com/att55/items/ab7781dae0bcd4d31395
