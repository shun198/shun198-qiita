---
title: django-axesを使ってアカウントのロック機能を実装しよう！
tags:
  - Django
  - django-rest-framework
  - axes
private: false
updated_at: '2024-01-23T18:06:26+09:00'
id: a6880feb82b7adaf68e5
organization_url_name: null
slide: false
---
## 概要
django-axesを使うとDjangoペースで不審なログインや不正なアクセスを防ぐライブラリを使ってアカウントのロック機能を気軽に実装できるので実装方法について解説します

## 前提
- Djangoのプロジェクトを作成済み
- ログインAPIを作成済み

## ディレクトリ構成
```
tree
・
├── .gitignore
├── README.md
├── application
│   ├── application
│   │   ├── __init__.py
│   │   ├── admin.py
│   │   ├── apps.py
│   │   ├── fixtures
│   │   │   └── fixture.json
│   │   ├── migrations
│   │   │   ├── __init__.py
│   │   │   └── 0001_initial.py
│   │   ├── models.py
│   │   ├── serializers.py
│   │   ├── utils
│   │   │   └── signals.py
│   │   ├── urls.py
│   │   └── views.py
│   ├── manage.py
│   ├── poetry.lock
│   ├── project
│   │   ├── __init__.py
│   │   ├── asgi.py
│   │   ├── settings.py
│   │   ├── urls.py
│   │   └── wsgi.py
│   └── pyproject.toml
└── docker-compose.yml
```

## 初期設定
django-axesをインストールします

```
pip install django-axes
```

settings.pyにaxesの設定を追加します
```settings.py
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # axesを追加
    'axes',
]


AUTHENTICATION_BACKENDS = [
    # AxesStandaloneBackendをAUTHENTICATION_BACKENDSのリストの先頭に記載する必要があります
    'axes.backends.AxesStandaloneBackend',
    # 今回はDjangoでデフォルトで設定されているModelBackendを認証で使用します
    'django.contrib.auth.backends.ModelBackend',
]

MIDDLEWARE = [
    # Djangoで使用されるデフォルトのミドルウェア
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    # AxesMiddlewareをMIDDLEWAREの配列の一番最後に記載する必要があります
    'axes.middleware.AxesMiddleware',
]

# ロックされるまでのログイン回数
AXES_FAILURE_LIMIT = 6
# 自動でロックが解除されるまでの時間
AXES_COOLOFF_TIME = 0.5
# ロック対象をusernameで判断する
AXES_LOCKOUT_PARAMETERS = ["username"]
# ログインに成功したら失敗回数をリセットされるようにする
AXES_RESET_ON_SUCCESS = True
# アクセスログをデータベースに書き込まないようにする
AXES_DISABLE_ACCESS_LOG = True
# ロックアウト中にログインに失敗した場合、クールオフ期間をリセットしないようにする
AXES_RESET_COOL_OFF_ON_FAILURE_DURING_LOCKOUT = False

```

以上の設定をDBに反映するために以下のコマンドでマイグレーションを実行します

```
python manage.py migrate
```

## 実装
以下のファイルを実装します
- signals.py
- apps.py

### シグナルの作成
以下のようにrecieverを使って6回ログインに失敗したら(user_locked_outのSignalを受け取ったら)403を返すよう設定します

```signals.py
from axes.signals import user_locked_out
from django.dispatch import receiver
from rest_framework.exceptions import PermissionDenied


@receiver(user_locked_out)
def user_locked(*args, **kwargs):
    raise PermissionDenied("ご利用のアカウントは凍結されています。しばらく経ってからログインしてください")

```

### apps.pyにシグナルを設定
先ほど作成したsignalを使用できるようAppConfigに設定します

```apps.py
from django.apps import AppConfig


class ApplicationConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "application"

    def ready(self):
        from application.utils import signals

```

django.apps.config.pyをオーバーライドすることでDjangoが起動した瞬間、signalsがimportされます

```django.apps.config.py
    def ready(self):
        """
        Override this method in subclasses to run code when Django starts.
        """
```

## 実際に操作してみよう！
間違ったパスワードを入力してログインAPIを実行します

![スクリーンショット 2024-01-23 17.29.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/3564c2dd-9b68-0057-2396-f041db273401.png)

```
django=# SELECT * FROM axes_accessattempt;
 id |                                                      user_agent                                                       |  ip_address  | username |   http_accept    | path_info  |         attempt_time  
        | get_data | post_data | failures_since_start 
----+-----------------------------------------------------------------------------------------------------------------------+--------------+----------+------------------+------------+-----------------------
--------+----------+-----------+----------------------
  1 | Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36 | 192.168.65.1 | 00000001 | application/json | /api/login | 2024-01-23 08:28:28.55
5871+00 |          |           |                    1
(1 row)
```

6回以上ログインに失敗して以下のようにエラーメッセージが出たら成功です
![スクリーンショット 2024-01-23 17.32.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ee3791c5-39c4-b915-2e7a-5b867d01aaaf.png)

また、ログインに失敗して5回目以内にログインに成功したら以下のようにaxes_accessattempt内に失敗した時のログがないことを確認できました

```

django=# SELECT * FROM axes_accessattempt;
 id | user_agent | ip_address | username | http_accept | path_info | attempt_time | get_data | post_data | failures_since_start 
----+------------+------------+----------+-------------+-----------+--------------+----------+-----------+----------------------
(0 rows)
```

## 参考
https://django-axes.readthedocs.io/en/latest/

https://github.com/jazzband/django-axes


https://qiita.com/startours777/items/5b1fc415e047a2044129

https://django-axes.readthedocs.io/en/latest/6_integration.html#integration-with-django-rest-framework
