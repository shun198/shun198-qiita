---
title: pre-commitを使ってgit pushする前にBlack、Isortでコードを事前にチェックしよう
tags:
  - Python
  - Git
  - pre-commit
private: false
updated_at: '2023-01-23T21:24:46+09:00'
id: 7352a5c67bb3284583d1
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## pre-commitとは？
Git hookを使ってコミット時にPylint等のlinterやBlack等のformatterを実行するツールです
コミット時にlinterやformatterを実行させることで事前にコード規約に沿ったコードかどうか確認できます
今回は
- Black
- Isort

を使ってコードをチェックします

## pre-commitのインストール

```
brew install pre-commit
```

バージョンが表示されたらインストール成功です
```
pre-commit --version
pre-commit 2.21.0
```

## .pre-commit-config.yamlの作成
コミット時にコードのチェックを行うために.pre-commit-config.yamlファイルをルートディレクトリ直下に作成します

下記の記事を参考にしました

https://developer.lsst.io/python/formatting.html

```.pre-commit-config.yaml
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
        args:
          - "--unsafe"
      - id: end-of-file-fixer
      - id: trailing-whitespace
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3.10
  - repo: https://github.com/pycqa/isort
    rev: 5.11.4
    hooks:
      - id: isort
        name: isort (python)
```

順番に説明していきます

### check-yaml
```.pre-commit-config.yaml
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: check-yaml
        args:
          - "--unsafe"
      - id: end-of-file-fixer
      - id: trailing-whitespace
```
repoにpre-commit-hooksのリポジトリのurlを指定します

|設定|説明|
|----|----|
|repo|GitHubのリポジトリのurl|
|rev|使用するパッケージのバージョン|
|hooks|オプション|

hooks内に
- id
- args
 
を指定しました
idに使用するhooksを指定できます
今回は以下の通りです
|hook|説明|
|----|----|
|check-yaml|yamlファイルの構文を解析|
|end-of-file-fixer|ファイル内の最後の行を改行|
|trailing-whitespace|末尾の空白を削除|

また、argsには構文解析のみを行う`--unsafe`を使用しています

hooksの一覧と詳細は全て公式ドキュメントとGitHubに記載されています

https://pre-commit.com/hooks.html

https://github.com/pre-commit/pre-commit-hooks

### BlackとIsort
```.pre-commit-config.yaml
  - repo: https://github.com/psf/black
    rev: 22.10.0
    hooks:
      - id: black
        language_version: python3.10
  - repo: https://github.com/pycqa/isort
    rev: 5.11.4
    hooks:
      - id: isort
        name: isort (python)
```

BlackとIsortの設定を行います
どちらも公式ドキュメントに従って記載していきます

https://black.readthedocs.io/en/stable/integrations/source_version_control.html

https://pycqa.github.io/isort/docs/configuration/pre-commit.html

## .pre-commit-config.yamlに記載した内容をコミットに反映させよう
下記のコマンドを実行してコミットするたびに.pre-commit-config.yamlの内容を反映させます
```
pre-commit install
```

以下のログが出たら成功です
```
pre-commit installed at .git/hooks/pre-commit
```

## 実際にコミットしてみよう！
初回のコミットをします
```
git commit
```

初回コミットを行うと以下のようにpre-commmitの設定を行います
2回目以降はpre-commmitの設定を行わずにコードのチェックが行われます
```
[INFO] Initializing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Initializing environment for https://github.com/psf/black.
[INFO] Initializing environment for https://github.com/pycqa/isort.
[INFO] Installing environment for https://github.com/pre-commit/pre-commit-hooks.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/psf/black.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
[INFO] Installing environment for https://github.com/pycqa/isort.
[INFO] Once installed this environment will be reused.
[INFO] This may take a few minutes...
```

コードのチェックが行われるときは以下のようにどの処理がうまくいってうまくいかなかったのかが表示されます
```
Check Yaml...........................................(no files to check)Skipped
Fix End of Files.........................................................Passed
Trim Trailing Whitespace.................................................Passed
black....................................................................Failed
isort (python)...........................................................Failed
```

以下のようにcommit時に全てパスすると成功です
```
Check Yaml...............................................................Passed
Fix End of Files.........................................................Passed
Trim Trailing Whitespace.................................................Passed
black....................................................................Passed
isort (python)...........................................................Passed
```

## 参考
https://developer.lsst.io/python/formatting.html

https://pylint.pycqa.org/en/latest/user_guide/installation/pre-commit-integration.html

https://pre-commit.com/#plugins

https://pre-commit.com/hooks.html
