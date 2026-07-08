---
title: dbtとElementaryを使ってデータの品質向上およびテストをより快適に行おう！
tags:
  - PostgreSQL
  - Elementary
  - dbt
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: 7c769a0c2e0056954bd4
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Elementaryを使用することでdbtプロジェクトのデータの可視化、テスト実行、Slackによるアラート送信を行うことができます
今回はElementaryをdbtで使用する方法について解説していきます

## 前提
- パッケージの管理はuvを使って行います
- 今回はローカル上で検証しやすくするためにPostgresのコンテナを使っている前提で解説しています
- dbtに関する基礎知識を有していること
- 下記記事と派生した内容の記事になっていますのでdbtについて知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/4e26f776c67c06e55a95

## 実装
### 初期設定
以下のように
- pyproject.toml
- packages.yml

に必要なパッケージを記載していきます

```pyproject.toml
[project]
name = "application"
version = "0.1.0"
description = "Add your description here"
readme = "README.md"
requires-python = ">=3.14"
dependencies = [
    "dbt-core>=1.9.2",
    "dbt-postgres>=1.9.0",
    "elementary-data>=0.16.2",
    "setuptools>=75.8.0",
]
```


```packages.yml
# This is your packages.yml file. This is where you declare packages that your project depends on.
# For full documentation: https://docs.getdbt.com/docs/building-a-dbt-project/package-management

packages:

# The dbt_utils package is a package we recommend everyone installs. This package solves common questions of `How do I do this in SQL?`. 
# To learn more, check out the docs: https://hub.getdbt.com/dbt-labs/dbt_utils/latest/
  - package: dbt-labs/dbt_utils
    version: 1.3.0
## Docs: https://docs.elementary-data.com
  - package: elementary-data/elementary
    version: 0.16.2
```

elementaryのcliを使う際に必要な設定を
- profiles.yml
- dbt_project.yml

に記載します

```profiles.yml
dbt_practice:
  outputs:
    dev:
      dbname: postgres
      host: localhost
      pass: postgres
      port: 5432
      schema: dbt_dev
      threads: 1
      type: postgres
      user: postgres
  target: dev
## POSTGRES ##
## By default, edr expects the profile name 'elementary'.      ##
## Configure the database and schema of elementary models.     ##
## Check where 'elementary_test_results' is to find it.        ##

elementary:
  outputs:
    dev:
      type: postgres
      host: localhost
      user: postgres
      password: postgres
      port: 5432
      dbname: postgres
      schema: dbt_dev_elementary # elementary schema, usually [schema name]_elementary
      threads: 1 # 1 or more
      keepalives_idle: 0 # default 0 seconds
      connect_timeout: 10 # default 10 seconds
      # search_path: public # optional, not recommended
      # role: [optional, set the role dbt assumes when executing queries]
      # sslmode: [optional, set the sslmode used to connect to the database]
  target: dev
```

```dbt_project.yml
# https://docs.getdbt.com/reference/dbt_project.yml
# プロジェクト名
name: 'dbt_practice'
config-version: 2
version: '1.0.0'

# プロファイル、DWの接続設定名
profile: 'dbt_practice'

model-paths: ["models"]
analysis-paths: ["analysis"]
test-paths: ["tests"]
seed-paths: ["seeds"]
macro-paths: ["macros"]
snapshot-paths: ["snapshots"]

# dbt コマンドの出力先パス
target-path: "target"
# dbt clean コマンドを実行したときに削除対象のディレクトリ
clean-targets: [target, dbt_packages]

models:
  dbt_practice:
    schema: dbt_dev
# elementaryモデルのテーブルがelementaryスキーマに作成される
  elementary:
    +schema: elementary

# dbt1.8以降から必須
flags:
# https://docs.elementary-data.com/oss/general/troubleshooting#warning-installed-package-elementary-is-overriding-the-built-in-materialization-xxx
# Elementary以外のテストにレポート機能を追加するために必要。FalseにすることでElementaryなどのサードパーティーライブラリがdbtのmaterializationをoverrideできる
  require_explicit_package_overrides_for_builtin_materializations: False
# データが更新されているか監視する
  source_freshness_run_project_hooks: True
```

dbt depsコマンドで必要なパッケージをインストールします
```
dbt deps
```

以下のようにElementaryのバージョンが表示されたら成功です

```
edr --version
    ________                          __                  
   / ____/ /__  ____ ___  ___  ____  / /_____ ________  __
  / __/ / / _ \/ __ `__ \/ _ \/ __ \/ __/ __ `/ ___/ / / /
 / /___/ /  __/ / / / / /  __/ / / / /_/ /_/ / /  / /_/ / 
/_____/_/\___/_/ /_/ /_/\___/_/ /_/\__/\__,_/_/   \__, /  
                                                 /____/  

Elementary version 0.16.2.
```

## Elementaryを含めたschema、view、tableの作成
以下のコマンドを実行し、elementaryの
- schema
- view
- table
 
が作成されたら成功です

```
dbt run
```

```
postgres=# \dn
            List of schemas
        Name        |       Owner       
--------------------+-------------------
 dbt_dev            | postgres
 dbt_dev_dbt_dev    | postgres
 dbt_dev_elementary | postgres
 public             | pg_database_owner
(4 rows)

postgres=# \dv dbt_dev_elementary.*
                          List of relations
       Schema       |             Name              | Type |  Owner   
--------------------+-------------------------------+------+----------
 dbt_dev_elementary | alerts_anomaly_detection      | view | postgres
 dbt_dev_elementary | alerts_dbt_models             | view | postgres
 dbt_dev_elementary | alerts_dbt_source_freshness   | view | postgres
 dbt_dev_elementary | alerts_dbt_tests              | view | postgres
 dbt_dev_elementary | alerts_schema_changes         | view | postgres
 dbt_dev_elementary | anomaly_threshold_sensitivity | view | postgres
 dbt_dev_elementary | dbt_artifacts_hashes          | view | postgres
 dbt_dev_elementary | job_run_results               | view | postgres
 dbt_dev_elementary | metrics_anomaly_score         | view | postgres
 dbt_dev_elementary | model_run_results             | view | postgres
 dbt_dev_elementary | monitors_runs                 | view | postgres
 dbt_dev_elementary | seed_run_results              | view | postgres
 dbt_dev_elementary | snapshot_run_results          | view | postgres
(13 rows)

postgres=# \dt dbt_dev_elementary.*
                          List of relations
       Schema       |             Name             | Type  |  Owner   
--------------------+------------------------------+-------+----------
 dbt_dev_elementary | alerts_v2                    | table | postgres
 dbt_dev_elementary | data_monitoring_metrics      | table | postgres
 dbt_dev_elementary | dbt_columns                  | table | postgres
 dbt_dev_elementary | dbt_exposures                | table | postgres
 dbt_dev_elementary | dbt_invocations              | table | postgres
 dbt_dev_elementary | dbt_metrics                  | table | postgres
 dbt_dev_elementary | dbt_models                   | table | postgres
 dbt_dev_elementary | dbt_run_results              | table | postgres
 dbt_dev_elementary | dbt_seeds                    | table | postgres
 dbt_dev_elementary | dbt_snapshots                | table | postgres
 dbt_dev_elementary | dbt_source_freshness_results | table | postgres
 dbt_dev_elementary | dbt_sources                  | table | postgres
 dbt_dev_elementary | dbt_tests                    | table | postgres
 dbt_dev_elementary | elementary_test_results      | table | postgres
 dbt_dev_elementary | metadata                     | table | postgres
 dbt_dev_elementary | schema_columns_snapshot      | table | postgres
 dbt_dev_elementary | test_result_rows             | table | postgres
```

## テストレポートの作成
以下のコマンドでテストを実行します
```
dbt test
```

以下のコマンドを実行し、テストレポートが表示されたら成功です
```
edr report --profiles-dir .
```

![スクリーンショット 2025-02-22 10.24.10.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/56208117-8c00-4d22-b5a8-3c723cc16f74.png)

実行時に
```
Runtime Error
  Could not find profile named 'elementary'
```

と表示される場合はprofiles.ymlをElementaryが認識できてないので
```
--profiles-dir
```
のオプションを使って使用したいprofiles.ymlのパスを記載してください

## Slackを使ったモニタリングとテストレポートの送信
SlackのTokenやWebhookを使ってモニタリングおよびテストレポートの送信を実現できます
TokenやWebhookの設定方法は下記の公式ドキュメントを参考にしてください

https://docs.elementary-data.com/oss/guides/alerts/send-slack-alerts#create-slack-webhook

### モニタリング
以下のコマンドでテスト結果からwarningやerrorが出た時にSlackで通知することができます

```
edr monitor --slack-token "<トークン>"　--slack-channel-name "<チャンネル名>" --group-by alert --profiles-dir .
```

テストが失敗した際に以下のように通知が来たら成功です

![スクリーンショット 2025-02-22 14.10.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/65e72794-0682-4872-a5d3-dac977e819e4.png)


### テスト結果の送信
以下のコマンドでテスト結果とレポートをSlackで通知することができます

```
edr send-report --slack-token "<トークン>"　--slack-channel-name "<チャンネル名>" --profiles-dir .
```

以下のように通知が送信されたら成功です
![スクリーンショット 2025-02-22 13.41.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9498d378-9a9c-4260-93b7-665524ca2375.png)

### Database Error relation "elementary_test_results" does not exist が出た時の対処法

dbt runを実行するとelementaryのテーブルが作成されます
edrコマンドでSlack通知を送る際はElementaryがelementary_test_resultsのテーブルを参照して通知を送ります
`<スキーマ名>.<テーブル名>`とprofiles.ymlのelementaryのschemaの名前が一致してなくてelementary_test_resultsのテーブルを見つけられていない可能性があります
profiles.ymlのelementaryのschema名を一度確認してみてください

詳細はdbt-artifactsに記載されています

https://docs.elementary-data.com/data-tests/dbt/dbt-artifacts

## 参考
https://www.elementary-data.com/

https://zenn.dev/kyami/articles/f5ded861b6f56s

https://docs.elementary-data.com/oss/quickstart/quickstart-cli

https://stackoverflow.com/questions/7446187/no-module-named-pkg-resources

https://www.loom.com/share/5cf1aaa0708f43a993f8a2945473c7ac?sid=fdee9f79-8c85-4870-b40b-45c088e4b54d

https://github.com/elementary-data/elementary/issues/1702

https://docs.elementary-data.com/oss/quickstart/quickstart-cli-package#what-are-dbt-packages-and-packages-yml
