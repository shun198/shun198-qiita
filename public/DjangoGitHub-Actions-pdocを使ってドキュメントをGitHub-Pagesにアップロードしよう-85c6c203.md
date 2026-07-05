---
title: '[Django+GitHub Actions] pdocを使ってドキュメントをGitHub Pagesにアップロードしよう！'
tags:
  - Django
  - GithubPages
  - GitHubActions
  - Poetry
  - pdoc
private: false
updated_at: '2024-06-02T10:53:07+09:00'
id: 85c6c203f4b40abba344
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
pdocを使えばPythonで書いたソースコードをドキュメント化できます
また、GitHub ActionsとGitHub Pagesを使ってWebサイトとしてとリポジトリ内でドキュメントを公開することができます
今回はDjangoのプロジェクト内のテストコードを単体テスト仕様書としてpdocで出力する方法からGitHub Actionsを使って仕様書を公開する方法まで解説していきます
量が多い上に内容が少し難しいかと思いますが一緒に頑張っていきましょう

## 前提
- 今回のプロジェクトではPoetryとPostgresを使用
- Pythonのバージョンは3.11を使用
- テストフレームワークはPytestを使用
- テストコードを作成済みおよびdocstringを記載済み
- Djangoのプロジェクトを作成済み

## ファイル構成
ファイル構成は以下のとおりです
今回はapplicationフォルダ内にDjangoのプロジェクトを格納します
Djangoのプロジェクト名はproject、アプリケーション名はapplicationとします
```
tree
・
├── .github
│   └── workflows
│       └── docs.yml
├── .gitignore
└── application
    ├── application
    │   ├── __init__.py
    │   ├── admin.py
    │   ├── apps.py
    │   ├── migrations
    │   ├── models.py
    │   ├── tests
    │   ├── urls.py
    │   └── views.py
    ├── manage.py
    ├── poetry.lock
    ├── project
    │   ├── __init__.py
    │   ├── asgi.py
    │   ├── settings.py
    │   ├── urls
    │   └── wsgi.py
    └── pyproject.toml
```

## 今回作成するファイル
今回作成するファイルは以下の通りです
- `application/pyproject.toml`
- `application/application/__init__.py`
- `.gitignore`
- `.github/workflow/docs.yml`

## application/pyproject.toml
pyproject.tomlを作成します
今回は
- Python
- Django
- Postgres
- Pytest
- Pdoc

のパッケージをインストールします

```pyproject.toml
[tool.poetry]
name = "api"
version = "0.1.0"
description = "api"
authors = ["shun198"]
readme = "README.md"

[tool.poetry.dependencies]
python = "^3.11"
Django = "^4.1.2"
psycopg2 = "^2.9.6"

[tool.poetry.group.dev.dependencies]
pytest = "^7.1.3"
pytest-django = "^4.5.2"
pdoc = "^13.0.0"
```

Poetryの使い方について詳細に知りたい方は以下の記事を参照してください

https://qiita.com/shun198/items/97483a227f288ad58112

## Djangoでpdocを実行できないのはなぜ？
Pdocでドキュメントを生成する際は以下のコマンドを実行するかと思います
```
poetry run pdoc -o docs application/tests
```

本来はこのコマンドを実行すればdocsフォルダ内にapplication/tests内のソースコードが全てhtmlとして出力されますが以下のエラーが出力されるかと思います

```
  File "/root/.cache/pypoetry/virtualenvs/api-MATOk_fk-py3.11/lib/python3.11/site-packages/django/apps/registry.py", line 260, in get_containing_app_config
    self.check_apps_ready()
  File "/root/.cache/pypoetry/virtualenvs/api-MATOk_fk-py3.11/lib/python3.11/site-packages/django/apps/registry.py", line 138, in check_apps_ready
    raise AppRegistryNotReady("Apps aren't loaded yet.")
django.core.exceptions.AppRegistryNotReady: Apps aren't loaded yet.
```

pdocを実行する際は内部でDjangoを起動させた状態で出力をするものの、今回はtestsフォルダ内のソースコードを出力する際にDjangoを起動させていないため、
```
Apps aren't loaded yet
```
が表示されていると思われます

### Apps aren't loaded yetについてもう少し詳しく知りたい方へ
Djangoを起動させる際はasgi.py(もしくはwsgi.py)内が実行されます

```application/project/asgi.py
"""
ASGI config for project project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/4.1/howto/deployment/asgi/
"""

import os

from django.core.asgi import get_asgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")

application = get_asgi_application()
```

その後にget_asgi_application()が呼ばれます

```django/core/asgi.py
import django
from django.core.handlers.asgi import ASGIHandler


def get_asgi_application():
    """
    The public interface to Django's ASGI support. Return an ASGI 3 callable.

    Avoids making django.core.handlers.ASGIHandler a public API, in case the
    internal implementation changes or moves in the future.
    """
    django.setup(set_prefix=False)
    return ASGIHandler()
```

その後、setup()が呼ばれ、Djangoの
- apps
- settings

などDjangoに必要なパッケージがimportされていきます
setup()メソッドがないとappsやsettingsがimportされず、
```
Apps aren't loaded yet
```
というエラーが表示されるのはこのためです

```django/__init__.py
from django.utils.version import get_version

VERSION = (4, 0, 6, "final", 0)

__version__ = get_version(VERSION)


def setup(set_prefix=True):
    """
    Configure the settings (this happens as a side effect of accessing the
    first setting), configure logging and populate the app registry.
    Set the thread-local urlresolvers script prefix if `set_prefix` is True.
    """
    from django.apps import apps
    from django.conf import settings
    from django.urls import set_script_prefix
    from django.utils.log import configure_logging

    configure_logging(settings.LOGGING_CONFIG, settings.LOGGING)
    if set_prefix:
        set_script_prefix(
            "/" if settings.FORCE_SCRIPT_NAME is None else settings.FORCE_SCRIPT_NAME
        )
    apps.populate(settings.INSTALLED_APPS)
```

つまり、pdocを実行する際はsetupメソッドを実行しないといけません

## 対処法
django.setup()を実行させた上でpdocを使って出力させるには出力したいフォルダ(今回だとapplication/tests)配下の`__init__.py`　内にdjango.setup()を記載します
django.setup()はproject内でも実行されるので仮にDjangoを起動させようとするとdjango.setup()が競合して起動できなくなる恐れがあります
そこで、CI_MAKING_DOCSという環境変数があるかないかで判断して競合を防ぎます

```application/application/tests/__init__.py
import os

if os.environ.get("CI_MAKING_DOCS") is not None:
    """テスト仕様書をpdocで出力するためにdjango.setupを実施する"""
    import django

    django.setup()
```

### pdocを実行するコマンド
Poetry実行時にCI_MAKING_DOCSという環境変数に値を渡すことでdjango.setup()が実行されます
```
CI_MAKING_DOCS=1 poetry run pdoc -o docs application/tests/
```

docker-composeを使用される方は下記のコマンドを実行してください
```
docker-compose exec app env CI_MAKING_DOCS=1 poetry run pdoc -o docs application/tests/
```

下記のようにdocsフォルダができたら成功です

![スクリーンショット 2023-06-10 11.49.13.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/963be675-75e5-b772-3733-8f8258125716.png)

## .gitignore
docsフォルダはバージョン管理しないので.gitignoreに追加します

```.gitignore
docs/
```

## GitHub Pagesの設定
ワークフローを作成する前にGitHub Pagesの設定を行います
settings>pagesを開いた後に
SourceをGitHub Actionsにします

![スクリーンショット 2023-06-10 14.42.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/22a40eff-faa6-df3a-98d0-9b63201cb591.png)


## ワークフローの作成
続いてpdocで出力したドキュメントをGitHub Pagesにアップロードするワークフローの作成方法について解説します
こちらはpdocが公式で出しているワークフローに基づいて作成しておりますがPoetryを使っているなど若干違う箇所があるので解説します

https://github.com/mitmproxy/pdoc/blob/main/.github/workflows/docs.yml

```.github/workflows/docs.yml
name: GitHub Pages
on:
  push:
    branches:
      - develop

# security: restrict permissions for CI jobs.
permissions:
  contents: read

env:
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings
  ALLOWED_HOSTS: 127.0.0.1
  POSTGRES_NAME: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_HOST: 127.0.0.1
  POSTGRES_PORT: 5432
  CI_MAKING_DOCS: 1

jobs:
  # Build the documentation and upload the static HTML files as an artifact.
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: application
    steps:
      - name: Chekcout code
        uses: actions/checkout@v4
      - name: Install poetry
        run: pipx install poetry
      - name: Use cache dependencies
        uses: actions/setup-python@v5
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      - name: Install Packages
        run: poetry install
      - name: Create documentation
        run: poetry run pdoc -o docs application/tests/
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v3
        with:
          # 絶対パスを指定
          path: application/docs/

  # Deploy the artifact to GitHub pages.
  # This is a separate job so that only actions/deploy-pages has the necessary permissions.
  deploy:
    needs: build
    runs-on: ubuntu-latest
    permissions:
      pages: write
      id-token: write
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

### 実行する際のブランチの指定
今回はdevelopブランチにfeatureブランチがmergeされた、もしくはdevelopにpushした際に
ワークフローが実行されるようにします
```.github/workflows/docs.yml
name: GitHub Pages
on:
  push:
    branches:
      - develop
```

### 環境変数
今回私はPostgresを使用しているので
DBを使用している際はDBの環境変数を指定してください
SECRET_KEYをはじめとするDjangoを起動する際に必要な環境変数も指定してください
pdocを使う際はCI_MAKING_DOCSも必要です
```github/workflows/docs.yml
env:
  SECRET_KEY: test
  DJANGO_SETTINGS_MODULE: project.settings
  ALLOWED_HOSTS: 127.0.0.1
  POSTGRES_NAME: test
  POSTGRES_USER: test
  POSTGRES_PASSWORD: test
  POSTGRES_HOST: 127.0.0.1
  POSTGRES_PORT: 5432
  CI_MAKING_DOCS: 1
```

### Poetryを使ったpdocの実行
今回はPoetryを使用しているのでPoetryのセットアップとCacheを使って2回目以降のインストールを高速化させています
PoetryのCacheの使い方などについて詳細に知りたい方は以下の記事を参考にしてください

https://qiita.com/shun198/items/65025b5cc5729b4217e1

また、actions/upload-pages-artifact@v3を使用する際のdocsフォルダのパスは絶対パスにしてください
公式が出しているこのアクションを使うことでdocsフォルダ内のファイル群はartifactとしてGitHub Actions内で保存され、GitHub Pagesにアップロードできるようになります

```github/workflows/docs.yml
jobs:
  # Build the documentation and upload the static HTML files as an artifact.
  build:
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: application
    steps:
      - name: Chekcout code
        uses: actions/checkout@v4
      - name: Install poetry
        run: pipx install poetry
      - name: Use cache dependencies
        uses: actions/setup-python@v5
        with:
          # pyproject.tomlからPythonのversionを指定(絶対パス)
          python-version-file: "${{ env.WORKING_DIRECTORY }}/pyproject.toml"
          cache: 'poetry'
      - name: Install Packages
        run: poetry install
      - name: Create documentation
        run: poetry run pdoc -o docs application/tests/
      - name: Upload Documents
        uses: actions/upload-pages-artifact@v3
        with:
          # 絶対パスを指定
          path: application/docs/
```

## ワークフローを実行してみよう！
developに直接pushするかPRをdevelopにmergeするとワークフローが実行されます

以下のようにgithub-pagesというartifactが作成され、公開用にリンクに遷移して閲覧できたら成功です

![スクリーンショット 2023-06-10 12.13.06.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/98a67030-e086-7eb9-4296-db125189508a.png)

![スクリーンショット 2023-06-10 12.14.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4053e16c-0571-a886-de1e-0a6e2277e0c2.png)

## まとめ
Djangoを使ってpdocでドキュメントをGitHub Pagesにアップロードする記事がない上に見たことないエラー文が出て最初はどうしたらいいかわからなかったので記事にしてみました
理屈がわかれば簡単に作成できたのでぜひ実践してほしいです

## 参考
https://github.com/pdoc3/pdoc/issues/314

https://pdoc3.github.io/pdoc/doc/pdoc/

https://pdoc.dev/docs/pdoc.html

https://github.com/actions/deploy-pages

https://github.com/actions/upload-pages-artifact
