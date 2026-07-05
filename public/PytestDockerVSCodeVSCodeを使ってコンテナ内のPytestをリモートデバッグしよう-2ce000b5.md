---
title: 【Pytest+Docker+VSCode】VSCodeを使ってコンテナ内のPytestをリモートデバッグしよう！
tags:
  - Python
  - Docker
  - pytest
  - VSCode
  - Remote-Containers
private: false
updated_at: '2025-07-21T12:25:51+09:00'
id: 2ce000b5b9f1818a16d5
organization_url_name: null
slide: false
---
## はじめに
VSCodeでコンテナ内のPytestをリモートデバッグをするには
- PythonもしくはPython関連のFrameworkのDockerfileの作成
- リモートデバッグの設定
- **Python Test Explorer for Visual Studio Code**(VSCodeの拡張機能)のインストール

をする必要があります
今回はDjango Rest Framework内でPytestのデバッグを行います
Dockerでの環境構築したことないよ！という方は下記の記事を参考にしてください

https://qiita.com/shun198/items/f6864ef381ed658b5aba

## Poetry を使用する場合は？
リモートデバッグの設定の記事の後半に記載されていますPoetryのPythonのパスの指定方法を参照してください

https://qiita.com/shun198/items/9e4fcb4479385217c323

## 使用する拡張機能について
今回はテストをGUIで確認・実行できる拡張機能である
 `Python Test Explorer for Visual Studio Code`を使用します
ボタンひとつで全てのテストを実行できたり任意のテストを実行できるだけでなく、
ブレークポイントも使えるので非常に便利です

![スクリーンショット 2023-11-26 9.09.27.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/4d717f85-9108-bbe4-deb0-b1188fea3cb6.png)

## 使用するテストのフレームワーク設定方法
`command+shift+p`を押した後`Python:テストを構成する`を選択します
![スクリーンショット 2023-11-26 9.09.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a185dbd4-1ab2-7b87-c607-3948b6145d5d.png)

使用するテストフレームワークを選択します
今回はPytestを選択しますがUnittestも選択できます
後からテストフレームワークを変更される場合はもう一度上記の`Python:テストを構成する`からはじめてください
![スクリーンショット 2023-11-26 9.10.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/fc005122-4055-49db-7811-22f8d54919cc.png)

テストファイルが置かれているディレクトリを選択します
![スクリーンショット 2023-11-26 9.10.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1ee6906c-784d-8421-60d9-9b7a6f5e79c7.png)

以下のようなファイルが作成されたら成功です
```settings.json
{
    "python.testing.pytestArgs": [
        "."
    ],
    "python.testing.unittestEnabled": false,
    "python.testing.pytestEnabled": true
}
```

## 実際に使用してみよう！
### テストエクスプローラの概要
サイドバーにあるテストエクスプローラのアイコンを選択するとテストの一覧が表示されます
![スクリーンショット 2023-11-26 9.10.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d8cb47f5-f664-4a18-7404-cd0cf3c498b6.png)

テストエクスプローラの文字の右側に4つのアイコンがあります。左から順に
- 再読み込み
- テストを一斉に実行
- テストを一斉にデバッグ(ブレークポイント)
- ターミナルの起動

となっております
![スクリーンショット 2023-11-26 9.11.12.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e0e780a9-37a2-93b4-5e41-3b5a9fbfd4e2.png)

また、個別のメソッドの
- 実行
- デバッグ
- メソッドのあるファイルへ飛ぶ

こともできます
![スクリーンショット 2023-11-26 9.11.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/62ea70ae-ece2-c125-72be-f9cb73c3863c.png)

### デバッグしてみよう！
該当する箇所へブレークポイントを設定し、ブレークポイントのマークを押すとデバッガーが起動します
![スクリーンショット 2023-11-26 9.11.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ab2eb17a-a8ad-32fe-a71f-e32127fcf021.png)

通常のVSCodeのデバッガ同様変数の中をみたりウォッチの設定、デバッグコンソールも使用できます
![スクリーンショット 2023-11-26 9.12.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/84176948-b7d0-2efe-5157-3165715db6c3.png)
![スクリーンショット 2023-11-26 9.12.16.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/500131af-009e-97c1-7d18-eb1d319c8273.png)

また、APIのテストを行う際は該当するメソッドにブレークポイントを設定するとテストコード同様ブレークポイントが使えるので大変便利です
![スクリーンショット 2023-11-26 9.12.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c78c8efb-866c-edb7-4b48-e032ed54d440.png)

## Pytest用の設定を1つのファイルにまとめたい時
例えば1つのリポジトリに複数のプロジェクトでPytestの設定をしたい時、今の方法だとPythonのパスがプロジェクトごとに分かれているとプロジェクトごとにsettings.jsonを生成する必要があるので不便です
そこで、launch.jsonにPytestの設定をまとめて記載することができます

```launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "name": "Pytest Project1",
            "type": "debugpy",
            "request": "launch",
            "cwd": "${workspaceFolder}/projects/project1/",
            "module": "pytest",
            "args": [
                "--log-cli-level=INFO"
            ],
            "python": "${workspaceFolder}/projects/project1/.venv/bin/python",
        },
        {
            "name": "Pytest Project2",
            "type": "debugpy",
            "request": "launch",
            "cwd": "${workspaceFolder}/projects/project2/",
            "module": "pytest",
            "args": [
                "--log-cli-level=INFO"
            ],
            "python": "${workspaceFolder}/projects/project2/.venv/bin/python",
        }
    ]
}
```

## 注意
pytest.iniのaddoptsにcoverageを入れるとブレークポイントが使えない不具合があるようです
リモートデバッグの設定をしたにも関わらずブレークポイントが機能しない場合はpytest.iniを確認してください

https://github.com/microsoft/vscode-python/issues/693

## 記事の紹介
以下の記事も書きましたので良かったら読んでみてください

https://qiita.com/shun198/items/fff4ddc0d7ae53665c2c

https://qiita.com/shun198/items/35c97c95079ecbe80e9d

https://qiita.com/shun198/items/318847d7e0be59108f22

## 参考
https://learn.microsoft.com/en-us/visualstudio/test/run-unit-tests-with-test-explorer?view=vs-2022
