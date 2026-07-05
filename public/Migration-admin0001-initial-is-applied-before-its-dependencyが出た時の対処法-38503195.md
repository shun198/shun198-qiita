---
title: Migration admin.0001_initial is applied before its dependencyが出た時の対処法
tags:
  - Django
  - Docker
  - docker-compose
  - django-admin
private: false
updated_at: '2022-10-29T11:40:33+09:00'
id: 38503195637b2c33fde3
organization_url_name: null
slide: false
---
## 前提
- Dockerおよびdocker-composeを使用
- カスタムユーザModelを作成済み

## エラーが発生するまでの流れ
カスタムユーザを作成後、makemigrationsでmigrationファイルを作成し、migrateします
```terminal:terminal
docker-compose exec app python manage.py makemigrations
Migrations for '<アプリケーション名>':
  <アプリケーション名>/migrations/0001_initial.py
    - Create model User
python manage.py migrate
```

すると、以下のエラーが出ることがあると思います

```terminal:terminal
django.db.migrations.exceptions.InconsistentMigrationHistory: Migration admin.0001_initial is applied before its dependency <アプリケーション名>.0001_initial on database 'default'
```

## エラーが表示される理由
カスタムユーザを作成する前にmigrateすると下記のようにすでにあるDjangoのデフォルトのadminユーザのModelとカスタムユーザのModelが衝突してしまうために起こるエラーです
```
auth_group
auth_group_permissions
auth_permission
authtoken_token
django_admin_log
django_content_type
django_migrations
django_session 
```

`INSTALLED_APPS`内の`django.contrib.admin`と`AUTH_USER_MODEL`をコメントアウトしてからもう一度migrationファイルを作成してmigrateする記事もありましたが、docker-composeを使っているのであれば永続volumeを削除する方法の方が手取り早くて簡単なので今回はそちらの方法を紹介します

## 永続volumeを削除しよう
まずはコンテナをdownします
```terminal:terminal
docker-compose down
```

下記のコマンドでvolume名を調べます
```terminal:terminal
docker volume ls
```

以下のコマンドで該当するvolume名を指定し、削除します
削除できない場合はrm -f で無理やり削除することもできます
```terminal:terminal
docker volume rm <ボリューム名>
```

コンテナを再起動します
```terminal:terminal
docker-compose up -d
```

すでにmigratationファイルがあるのでmigrateするとカスタムユーザのmigrationがうまく反映されます
以下のような出力結果が表示されたら成功です
```yaml:terminal
docker-compose exec app python manage.py migrate
Operations to perform:
  Apply all migrations: admin, auth, contenttypes, <アプリケーション名>, sessions
Running migrations:
  Applying contenttypes.0001_initial... OK
  Applying contenttypes.0002_remove_content_type_name... OK
  Applying auth.0001_initial... OK
  Applying auth.0002_alter_permission_name_max_length... OK
  Applying auth.0003_alter_user_email_max_length... OK
  Applying auth.0004_alter_user_username_opts... OK
  Applying auth.0005_alter_user_last_login_null... OK
  Applying auth.0006_require_contenttypes_0002... OK
  Applying auth.0007_alter_validators_add_error_messages... OK
  Applying auth.0008_alter_user_username_max_length... OK
  Applying auth.0009_alter_user_last_name_max_length... OK
  Applying auth.0010_alter_group_name_max_length... OK
  Applying auth.0011_update_proxy_permissions... OK
  Applying auth.0012_alter_user_first_name_max_length... OK
  Applying <アプリケーション名>.0001_initial... OK
  Applying admin.0001_initial... OK
  Applying admin.0002_logentry_remove_auto_add... OK
  Applying admin.0003_logentry_add_action_flag_choices... OK
  Applying sessions.0001_initial... OK
```

## まとめ
はじめてこのエラーに遭遇した時はかなり混乱しました。実際の開発ではデフォルトのadminのModelではなく、自分達でカスタムユーザを作るのが一般的なので今後同じエラーに遭遇される方の少しでもお役に立てたらと思い、書きました

## 記事の紹介
以下の記事も作成しましたので見ていただけると幸いです

https://qiita.com/shun198/items/f6864ef381ed658b5aba

https://qiita.com/shun198/items/9e4fcb4479385217c323

## 参考
https://note.com/mihami383/n/nb58eec166df6
