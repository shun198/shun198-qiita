---
title: Djangoでマイグレーションのロールバックを行う方法について解説
tags:
  - Django
private: false
updated_at: '2024-05-07T10:25:14+09:00'
id: f4ba99bd4e546b8f165a
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
間違えてマイグレーションした際のロールバック方法について解説します

## マイグレーションの履歴の確認
マイグレーションを行う際に`django_migrations`というDjango独自のテーブルに今までのマイグレーションの履歴が以下のように表示されます

```
select * from django_migrations;
+----+--------------+-----------------------------------------------------------+----------------------------+
| id | app          | name                                                      | applied                    |
+----+--------------+-----------------------------------------------------------+----------------------------+
|  1 | contenttypes | 0001_initial                                              | 2024-01-09 00:27:23.126549 |
|  2 | contenttypes | 0002_remove_content_type_name                             | 2024-01-09 00:27:23.195867 |
|  3 | auth         | 0001_initial                                              | 2024-01-09 00:27:23.471762 |
|  4 | auth         | 0002_alter_permission_name_max_length                     | 2024-01-09 00:27:23.532722 |
|  5 | auth         | 0003_alter_user_email_max_length                          | 2024-01-09 00:27:23.546001 |
|  6 | auth         | 0004_alter_user_username_opts                             | 2024-01-09 00:27:23.557053 |
|  7 | auth         | 0005_alter_user_last_login_null                           | 2024-01-09 00:27:23.568794 |
|  8 | auth         | 0006_require_contenttypes_0002                            | 2024-01-09 00:27:23.574990 |
|  9 | auth         | 0007_alter_validators_add_error_messages                  | 2024-01-09 00:27:23.586035 |
| 10 | auth         | 0008_alter_user_username_max_length                       | 2024-01-09 00:27:23.603642 |
| 11 | auth         | 0009_alter_user_last_name_max_length                      | 2024-01-09 00:27:23.612873 |
| 12 | auth         | 0010_alter_group_name_max_length                          | 2024-01-09 00:27:23.633020 |
| 13 | auth         | 0011_update_proxy_permissions                             | 2024-01-09 00:27:23.642737 |
| 14 | auth         | 0012_alter_user_first_name_max_length                     | 2024-01-09 00:27:23.653120 |
| 15 | XXXXXXXXXXXX | 0001_initial                                              | 2024-01-09 00:27:25.111524 |
| 16 | sessions     | 0001_initial                                              | 2024-01-09 00:27:25.186248 |
| 17 | XXXXXXXXXXXX | 0002_AAAAAAAAAA                                           | 2024-01-15 02:48:40.977177 |
| 18 | XXXXXXXXXXXX | 0003_BBBBBBBBBB                                           | 2024-01-16 01:07:38.831112 |
| 19 | XXXXXXXXXXXX | 0004_CCCCCCCCCC                                           | 2024-01-16 04:33:55.459254 |
| 20 | XXXXXXXXXXXX | 0005_DDDDDDDDDD                                           | 2024-03-03 23:13:13.811010 |
| 21 | XXXXXXXXXXXX | 0006_EEEEEEEEEE                                           | 2024-04-16 01:22:34.708066 |
+----+--------------+-----------------------------------------------------------+----------------------------+
```

## どうやってロールバックするの？
ロールバックする際は
```
python manage.py migrate <アプリケーション名> <マイグレーションファイルの番号>
```

の形式でコマンドを実行する必要があります
今回は`XXXXXXXXXXXX`のアプリケーションの0005のファイルまでロールバックを行いたいので以下のようにコマンドを実行します

```
python manage.py migrate XXXXXXXXXXXX 0005
Operations to perform:
  Target specific migration: 0005_DDDDDDDDDD, from XXXXXXXXXXXX
Running migrations:
  Rendering model states... DONE
  Unapplying XXXXXXXXXXXX.0006_EEEEEEEEEE... OK
```

以下のように0006_EEEEEEEEEEのマイグレーションが履歴から削除されていることを確認したら成功です
```
select * from django_migrations;
+----+--------------+-----------------------------------------------------------+----------------------------+
| id | app          | name                                                      | applied                    |
+----+--------------+-----------------------------------------------------------+----------------------------+
|  1 | contenttypes | 0001_initial                                              | 2024-01-09 00:27:23.126549 |
|  2 | contenttypes | 0002_remove_content_type_name                             | 2024-01-09 00:27:23.195867 |
|  3 | auth         | 0001_initial                                              | 2024-01-09 00:27:23.471762 |
|  4 | auth         | 0002_alter_permission_name_max_length                     | 2024-01-09 00:27:23.532722 |
|  5 | auth         | 0003_alter_user_email_max_length                          | 2024-01-09 00:27:23.546001 |
|  6 | auth         | 0004_alter_user_username_opts                             | 2024-01-09 00:27:23.557053 |
|  7 | auth         | 0005_alter_user_last_login_null                           | 2024-01-09 00:27:23.568794 |
|  8 | auth         | 0006_require_contenttypes_0002                            | 2024-01-09 00:27:23.574990 |
|  9 | auth         | 0007_alter_validators_add_error_messages                  | 2024-01-09 00:27:23.586035 |
| 10 | auth         | 0008_alter_user_username_max_length                       | 2024-01-09 00:27:23.603642 |
| 11 | auth         | 0009_alter_user_last_name_max_length                      | 2024-01-09 00:27:23.612873 |
| 12 | auth         | 0010_alter_group_name_max_length                          | 2024-01-09 00:27:23.633020 |
| 13 | auth         | 0011_update_proxy_permissions                             | 2024-01-09 00:27:23.642737 |
| 14 | auth         | 0012_alter_user_first_name_max_length                     | 2024-01-09 00:27:23.653120 |
| 15 | XXXXXXXXXXXX | 0001_initial                                              | 2024-01-09 00:27:25.111524 |
| 16 | sessions     | 0001_initial                                              | 2024-01-09 00:27:25.186248 |
| 17 | XXXXXXXXXXXX | 0002_AAAAAAAAAA                                           | 2024-01-15 02:48:40.977177 |
| 18 | XXXXXXXXXXXX | 0003_BBBBBBBBBB                                           | 2024-01-16 01:07:38.831112 |
| 19 | XXXXXXXXXXXX | 0004_CCCCCCCCCC                                           | 2024-01-16 04:33:55.459254 |
| 20 | XXXXXXXXXXXX | 0005_DDDDDDDDDD                                           | 2024-03-03 23:13:13.811010 |
+----+--------------+-----------------------------------------------------------+----------------------------+
```

## 参考
https://docs.djangoproject.com/en/5.0/topics/migrations/#reversing-migrations
