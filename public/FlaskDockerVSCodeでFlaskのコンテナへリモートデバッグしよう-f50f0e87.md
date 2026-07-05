---
title: Flask+Docker+VSCodeでFlaskのコンテナへリモートデバッグしよう！
tags:
  - Flask
  - Docker
  - docker-compose
  - VSCode
private: false
updated_at: '2025-07-21T12:13:58+09:00'
id: f50f0e877dc3f35daa17
organization_url_name: null
slide: false
---
## 概要
【Flask+Docker】の開発環境をVSCodeでリモートデバッグする方法について解説します
リモードデバッグする際は拡張機能のRemote Containersを使用します
VSCodeのブレークポイントやウォッチが使えるとかなり開発効率が上がるのでぜひ設定してみてください
記事の後半ではPoetryを使ってリモートデバッグする方法についても解説します

## 前提
- すでにFlaskのプロジェクトを`git clone`している
- VSCodeをインストール済み
- Dockerをインストール済み
- Remote Containersを使用します
- Dockerfileおよびdocker-compose.ymlはある程度読める方が望ましい
- ブレークポイント、ウォッチの解説はしません

## コンテナイメージを作成しよう
Remote Containersを使うには該当コンテナのイメージをbuildする必要があります
docker-composeの構成は以下のように設定し、デバッグ用の8080番ポートを開放します

```yaml:docker-compose.yml
version: "3.9"

services:
  db:
    container_name: db
    build:
      context: .
      dockerfile: containers/postgres/Dockerfile
    volumes:
      - db_data:/var/lib/postgresql/data
    healthcheck:
      test: pg_isready -U "${POSTGRES_USER:-postgres}" || exit 1
      interval: 10s
      timeout: 5s
      retries: 5
    environment:
      - POSTGRES_NAME
      - POSTGRES_USER
      - POSTGRES_PASSWORD
    ports:
      - "5432:5432" # デバッグ用
  app:
    container_name: app
    build:
      context: .
      dockerfile: containers/flask/Dockerfile
    volumes:
      - ./application:/code
    ports:
      - 8000:8000
      # デバッグ用ポート
      - 8080:8080
    command: poetry run flask --app main run --debug -h 0.0.0.0 -p 8000
    env_file:
      - .env
    depends_on:
      db:
        condition: service_healthy
volumes:
  db_data:

```

## Remote Containersのインストール
まずは拡張機能のRemote Containersをインストールします
![スクリーンショット 2022-08-21 21.23.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/55b9de47-b8fa-1ac5-ccdd-7b3b8cfe3d17.png)

## 該当するコンテナへリモート接続しよう
Remotes Containerのインストールができたら左下の緑色のマークをクリックします
![スクリーンショット 2022-08-21 21.24.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ccfa9e5a-637a-a1c4-8a45-41a76c0d9263.png)

ボタンを押すとコマンドパレットが開くので`Add Development Container Configuration Files`を選択します
![スクリーンショット 2022-08-21 21.22.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/903984f8-de9f-ad37-ac68-f56998a2d83c.png)

リモート接続するコンテナイメージを作成するdocker-composeファイルを選択します
![スクリーンショット 2022-08-21 21.22.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/74bc2bf2-7231-eae9-4a8c-36f2082f89e6.png)

該当するコンテナ名を選択します
![スクリーンショット 2022-08-21 21.24.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e69c7595-8460-a101-331b-bc3288262636.png)

コンテナ名を選択すると`.devcontainer`フォルダが作成され、その中に
- devcontainer.json
- docker-compose.yml

が作成されます。`devcontainer.json`に必要な情報を入力していきます

```yml:devcontainer.json
// For format details, see https://aka.ms/devcontainer.json. For config options, see the
// README at: https://github.com/devcontainers/templates/tree/main/src/docker-existing-docker-compose
{
	"name": "flask container",
	"dockerComposeFile": [
		"../docker-compose.yml"
	],
    "service": "app",
	"workspaceFolder": "/code"
}

```

`Open Folder in Container`から該当するプロジェクトのディレクトリを開きます
![スクリーンショット 2022-08-21 21.36.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cb63d518-04c8-86d7-b801-8db3909d250d.png)

2回目以降は`Attach to Running Container`から開くこともできます
![スクリーンショット 2022-11-20 20.13.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ab3e087e-a414-b02d-82ca-de1bdb83aa48.png)

該当するプロジェクトのディレクトリを開くとコンテナにリモート接続できます
![スクリーンショット 2022-08-21 21.29.20（2）.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9e93f4ff-b93b-85d8-a178-2a8521f2eb45.png)

FlaskのデバッグをするにはPythonとPython Debuggerの拡張機能をインストールする必要があります
![スクリーンショット 2022-08-21 21.38.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2c6661c8-c0ce-ee7b-a175-de1d49718071.png)

![スクリーンショット 2024-09-12 14.33.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/23145d97-bb58-a83d-eeca-930ae953dfb6.png)

VSCodeのブレークポイントやウォッチが使えるよう設定します
実行とデバッグを選択し、`launch.jsonファイルを作成します`を押します
![スクリーンショット 2022-08-21 21.37.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/64058dbb-48d5-6c51-7aea-bea6c4336731.png)

デバッガーはPythonを選択します
![スクリーンショット 2022-08-21 21.40.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/375e5ab4-5668-fb18-7ce3-3bc36f8a2466.png)

フレームワークはFlaskを選択します
![スクリーンショット 2024-09-12 14.34.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/87922059-e16a-ecb9-1f15-ea38fabdd690.png)


launch.jsonに必要な情報を入力します
記事によってはtypeの箇所をpythonにしているものもありますが2024年1月から非推奨になっているのでdebugpyにしましょう

```json:launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask Debugger",
            "type": "debugpy",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "main.py",
                "FLASK_DEBUG": "1"
            },
            "args": [
                "run",
                "-h",
                "0.0.0.0",
                "-p",
                "8080",
            ],
            "justMyCode": false,
            "jinja": true,
            "autoStartBrowser": false
        }
    ]
}
```

debugpyを使うことでVSCodeのPythonの拡張機能のバージョンを落とさずに古いバージョンを使っているPythonのバージョンでリモートデバッグできるとのことです
詳細は以下の通りです

> The Python Debugger extension aims to separate the debugging functionality from the main Python extension to prevent compatibility issues. This ensures that even as the Python extension drops support for older Python versions (for example, Python 3.7), you can continue debugging projects with those versions without downgrading your Python extension. It also delivers platform-specific builds, ensuring you only receive the components relevant to your specific operating system, reducing download times and unnecessary overhead.

> To ensure you are using the new Python Debugger extension, replace "type": "python" with "type": "debugpy" from your launch.json configuration file. In the future, the Python extension will no longer offer debugging support, and we will transition all debugging support to the Python Debugger extension for all debugging functionality.

https://code.visualstudio.com/updates/v1_86#_python

緑の実行ボタンを押してデバッグを実行します
![スクリーンショット 2024-09-12 14.41.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1303de7d-38c6-e504-1e2f-89fb6fb1e476.png)


任意の箇所にブレークポイントを設定します
ブレークポイントが実行できれば成功です

![スクリーンショット 2024-12-13 19.00.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/bd0e5ea9-c521-5c18-e5fa-9ee9a01b3637.png)

### justMyCode: false
```
justMyCode: false
```
にすることで下記の様に自分が書いたコード以外の箇所でデバッグできます

![スクリーンショット 2024-12-13 19.00.55.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1556c60d-b648-b6d6-1556-8ab4e797a101.png)

## Poetryを使ってデバッグする時
Poetryを使用している場合はインタプリンタのパスをPoetryのVirtualenvのPythonのパスを指定する必要があります
```
poetry env info
```
を実行するとVirtualenvとSystemの情報が表示されます
```
Virtualenv
Python:         3.12.8
Implementation: CPython
Path:           /root/.cache/pypoetry/virtualenvs/flask-practice-MATOk_fk-py3.12
Executable:     /root/.cache/pypoetry/virtualenvs/flask-practice-MATOk_fk-py3.12/bin/python
Valid:          True

Base
Platform:   linux
OS:         posix
Python:     3.12.8
Path:       /usr/local
Executable: /usr/local/bin/python3.12
```

VirualenvのExecutableのパスをコピーし、VSCodeのコマンドパレットからインタプリンタをVirtualenvのExecutableのパスを設定します

![スクリーンショット 2024-12-13 18.58.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/71b00088-83d9-9def-9385-1a14f6823131.png)

## uv/venvを使ってデバッグする時
下記のようにpythonにvenvのパスを記載すればデバッグできます
cwdはオプションですがmain.pyが今回だとapplicationではなく、src配下だった場合に指定します

```json:launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Flask Debugger",
            "type": "debugpy",
            "request": "launch",
            "module": "flask",
            "env": {
                "FLASK_APP": "main.py",
                "FLASK_DEBUG": "1"
            },
            "args": [
                "run",
                "-h",
                "0.0.0.0",
                "-p",
                "8080",
            ],
            "python": "${workspaceFolder}/application/.venv/bin/python",
            "cwd": "${workspaceFolder}/application/src/",
            "justMyCode": false,
            "jinja": true,
            "autoStartBrowser": false
        }
    ]
}
```

## 参考文献
https://go.microsoft.com/fwlink/?linkid=830387

https://code.visualstudio.com/updates/v1_86#_python
