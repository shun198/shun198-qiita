---
title: Django+Docker+VSCodeでDjangoのコンテナへリモートデバッグしよう！
tags:
  - Django
  - Docker
  - VSCode
  - ブレークポイント
  - Remote-Containers
private: false
updated_at: '2025-07-21T12:17:59+09:00'
id: 9e4fcb4479385217c323
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
【Django+Docker】の開発環境をVSCodeでリモートデバッグする方法について解説します
リモードデバッグする際は拡張機能のRemote Containersを使用します
VSCodeのブレークポイントやウォッチが使えるとかなり開発効率が上がるのでぜひ設定してみてください
記事の後半ではPoetryを使ってリモートデバッグする方法についても解説します

## 前提
- すでにDjangoのプロジェクトを`git clone`している
- VSCodeをインストール済み
- Dockerをインストール済み
- Remote Containersを使用します
- Dockerfileおよびcompose.yamlはある程度読める方が望ましい
- ブレークポイント、ウォッチの解説はしません

## コンテナイメージを作成しよう
Remote Containersを使うには該当コンテナのイメージをbuildする必要があります

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
- compose.yaml

が作成されます。`devcontainer.json`に必要な情報を入力していきます

```yml:devcontainer.json
{
    # 任意の名前を設定
    "name": "django container",

    # compose.yamlのパスを指定
    # 今回は.devcontainersフォルダと同じディレクトリ階層に作成したので以下のように記載しています
    "dockerComposeFile": ["../compose.yaml"],

    # compose.yamlに記載されているコンテナのサービス名を記入
    "service": "app",

    # compose.yamlに記載されているWORKDIRを指定
    "workspaceFolder": "/workspace"

    // Use 'forwardPorts' to make a list of ports inside the container available locally.
    // "forwardPorts": [],

    // Uncomment the next line if you want start specific services in your Docker Compose config.
    // "runServices": [],

    // Uncomment the next line if you want to keep your containers running after VS Code shuts down.
    // "shutdownAction": "none",

    // Uncomment the next line to run commands after the container is created - for example installing curl.
    // "postCreateCommand": "apt-get update && apt-get install -y curl",

    // Uncomment to connect as a non-root user if you've added one. See https://aka.ms/vscode-remote/containers/non-root.
    // "remoteUser": "vscode"
}
```

`Open Folder in Container`から該当するプロジェクトのディレクトリを開きます
![スクリーンショット 2022-08-21 21.36.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cb63d518-04c8-86d7-b801-8db3909d250d.png)

2回目以降は`Attach to Running Container`から開くこともできます
![スクリーンショット 2022-11-20 20.13.53.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ab3e087e-a414-b02d-82ca-de1bdb83aa48.png)

該当するプロジェクトのディレクトリを開くとコンテナにリモート接続できます
![スクリーンショット 2022-08-21 21.29.20（2）.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/9e93f4ff-b93b-85d8-a178-2a8521f2eb45.png)

DjangoのデバッグをするにはPythonの拡張機能をインストールする必要があります
![スクリーンショット 2022-08-21 21.38.07.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2c6661c8-c0ce-ee7b-a175-de1d49718071.png)

VSCodeのブレークポイントやウォッチが使えるよう設定します
実行とデバッグを選択し、`launch.jsonファイルを作成します`を押します
![スクリーンショット 2022-08-21 21.37.17.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/64058dbb-48d5-6c51-7aea-bea6c4336731.png)

デバッガーはPythonを選択します
![スクリーンショット 2022-08-21 21.40.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/375e5ab4-5668-fb18-7ce3-3bc36f8a2466.png)

フレームワークはDjangoを選択します
![スクリーンショット 2022-08-21 21.40.43.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a0bc69ec-81a6-f0f9-1fd6-d09ff968655a.png)

launch.jsonに必要な情報を入力します
記事によってはtypeの箇所をpythonにしているものもありますが2024年1月から非推奨になっているのでdebugpyにしましょう

```yml:launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            # 任意の名前でOK
            "name": "django container",
            "type": "debugpy",
            "request": "launch",
            # Djangoのmanage.pyを起動するよう設定します
            "program": "${workspaceFolder}/manage.py",
            # args(arguments)にrunserverコマンドを記載
            "args": [
                "runserver",
                "0.0.0.0:8080"
            ],
            "django": true,
            # falseにすることで自分が書いたコード以外の箇所をデバッグできます(後述)
            "justMyCode": false
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
![スクリーンショット 2022-08-21 21.42.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/16127502-574d-2e7d-47f0-5fe159a78e13.png)

任意の箇所にブレークポイントを設定します
ブレークポイントが実行できれば成功です
![スクリーンショット 2022-08-21 21.42.55（2）.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/cf13b1f4-ffe0-a9fb-3eac-6f61dc2a3d6f.png)

### justMyCode: false
```
justMyCode: false
```
にすることで下記の様に自分が書いたコード以外の箇所でデバッグできます

![スクリーンショット 2022-11-05 14.53.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/320d64a6-ea40-5b6d-067b-c50f2d4eb429.png)

## ブラウザからデバッグするとき
ブラウザからアクセスしてブレークポイントで止める際は下記のように
`"--noreload"`オブションを付与すると止めることができます
@campbel2525さん、ありがとうございます

```launch.json
            "args": [
                "runserver",
                "--noreload",
                "0.0.0.0:8080"
            ],
```

## Poetryを使ってデバッグする時
Poetryを使用している場合はインタプリンタのパスをPoetryのVirtualenvのPythonのパスを指定する必要があります
```
poetry env info
```
を実行するとVirtualenvとSystemの情報が表示されます
```

Python:         3.10.7
Implementation: CPython
Path:           /root/.cache/pypoetry/virtualenvs/rest-framework-tutorial-MATOk_fk-py3.10
Executable:     /root/.cache/pypoetry/virtualenvs/rest-framework-tutorial-MATOk_fk-py3.10/bin/python
Valid:          True

System
Platform:   linux
OS:         posix
Python:     3.10.7
Path:       /usr/local
Executable: /usr/local/bin/python3.10
```

VirualenvのExecutableのパスをコピーし、VSCodeのコマンドパレットからインタプリンタをVirtualenvのExecutableのパスを設定します

![スクリーンショット 2023-05-31 17.07.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/72d06f72-012b-245a-a2ce-ceb5ccf2d0e4.png)

:::note alert
ImportError: Couldn't import Django. Are you sure it's installed and available on your PYTHONPATH environment variable? Did you forget to activate a virtual environment?
:::

実行するインタプリンタが間違っていることで生じるエラーです
コンテナ内のPython のPathを確認します
```
root@e9e17e517c4c:/workspace# which python
/usr/local/bin/python
```
コマンドパレットからインタプリンタを設定します
![スクリーンショット 2023-05-31 17.07.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6e64f339-e1ca-aecb-4a2f-be5b7ac169c8.png)

PythonのPathと一致するインタプリンタを選択またはPathを入力した後にデバッグするとエラーが解消されます
![スクリーンショット 2023-05-31 17.07.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/94f1b97f-5073-0186-01aa-e3382a6ad6e9.png)

## uv/venvを使ってデバッグする時
下記のようにpythonにvenvのパスを記載すればデバッグできます

```json:launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "django container",
            "type": "debugpy",
            "request": "launch",
            "program": "${workspaceFolder}/manage.py",
            "args": [
                "runserver",
                "0.0.0.0:8080"
            ],
            "python": "${workspaceFolder}/application/.venv/bin/python",
            "jinja": true,
            "justMyCode": false,
        }
    ]
}
```

## Remote Containersを使用するたびに拡張機能を入れるのはめんどくさい
Remote Containersを使用するときは拡張機能がインストールされていないのでextensionsの中に任意の拡張機能を記述します
```json:devcontainer.json
    "extensions": [
		"ms-python.python",
		"ms-python.vscode-pylance",
	]
}
```

## 記事の紹介
以下の記事も書いたので良かったら読んでいただけると幸いです

https://qiita.com/shun198/items/ee93c50eac2f7c77e443

https://qiita.com/shun198/items/f6864ef381ed658b5aba

## 参考文献
https://go.microsoft.com/fwlink/?linkid=830387

https://code.visualstudio.com/updates/v1_86#_python

https://qiita.com/thim/items/be2325deb65a30fac65e

https://qiita.com/nokonoko_1203/items/33a05c86f359027afb33

https://qiita.com/koshilife/items/3ed4b1c28de233f39ebb

https://blog.janjan.net/2021/02/01/python-django-uses-visual-studio-code-import-error-could-not-import-django-2/

https://python.plainenglish.io/debugging-django-with-vs-code-and-poetry-c41a7c517df0
