---
title: GitHub Actionsでメタデータファイル(action.yml)を作成してワークフローを共通化しよう！
tags:
  - Node.js
  - npm
  - GitHubActions
private: false
updated_at: '2026-09-05T08:55:27+09:00'
id: e7b7a3d9d3b86aec4813
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
複数以上のワークフローを実行する際に
- パッケージのインストール
- Cacheの設定

など、複数のワークフローで共通で使用できるものを1つのファイルにまとめる方法について解説していきたいと思います
今回はNode.js関連の設定を共通化してテストをビルドを実行します

作成するファイルの構成は以下の通りです
```
tree
└──.github
     ├── actions
     │   └── set-up-node
     |       └── action.yml
     └── workflows
       ├── build.yml
       └── jest.yml
```

## メタデータファイル
GitHub Actionsではメタデータファイルというファイルに共通の処理を記載することができます
その際はaction.ymlファイルを作成し、記載します

https://docs.github.com/ja/actions/creating-actions/metadata-syntax-for-github-actions

## Node.js用のメタデータファイルを作成しよう！
- Node.jsのインストール
- Cacheの作成
- npm ci

の実行までをaction.ymlに記載します
今回は今後別の処理を共通化したい時を想定してaction.ymlを
`.github/actions/set-up-node/`内に格納します

```yml:.github/actions/set-up-node/action.yml
name: 'Setup Node.js'

description: 'Setup Node.js by using cache and npm'

inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: true

runs:
  # compositeが必須
  using: 'composite'
  steps:
      - name: Setup NodeJS
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ inputs.working-directory }}/package.json
      - name: Install dependencies
        run: npm ci
        shell: bash
        working-directory: ${{ inputs.working-directory }}
```

メタデータファイルを作成する場合は以下の構文が必須です

| 構文 | 説明 | 
| -------- | -------- | 
| name     | アクションの名前   | 
| description | アクションの簡単な説明 |
| runs | 共通化したい処理を記載 |
| using |  compositeに設定する必要があります |

### action.yml内でrun句を使うとき
runを使用するときは使用するshellを必ず定義する必要があります

```yml
shell: bash
```

以下に使用できるshellが記載されていますが基本的にはbashで問題ないかと思います

https://docs.github.com/ja/actions/using-workflows/workflow-syntax-for-github-actions#jobsjob_idstepsshell

また、action.yml内で処理を行う際は参照先で
```yml
    defaults:
      run:
        working-directory: application
```
と定義したとしてもルートディレクトリで実行されてしまいます
そのため、action.yml内の処理にworking-directoryを使ってディレクトリを指定する必要があります

### inputs
そこでinputsを使って参照先のyml側で実行するディレクトリを指定するようにすれば
action.yml内でハードコーディングしなくてもよくなります
今回は必須入力にしています

```yml:.github/actions/set-up-node/action.yml
inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: true
```

また、任意入力にする場合はrequiredの値をfalseにし、defaultを定義することでデフォルト値を設定することもできます
```yml
inputs:
  working-directory:
    description: 'working-directory of package-lock.json'
    required: false
    default: 'application'
```

## 作成したaction.ymlの処理をワークフローで使おう！
- build.yml
- jest.yml

にaction.ymlの処理を参照するよう設定します
まずは、usesにaction.ymlのパスを指定します
パスを指定する際はaction.ymlまで記載しなくても大丈夫です
また、inputsを使用する際はwith内に値を指定します
working-directoryにapplicationを指定します

```yml
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
```

以上を踏まえると以下のようになります
```yml:.github/workflows/build.yml
# アクション名
name: Jest

# タイミングを指定
on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application

jobs:
  test:
    name: Run test codes
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Checkout
        uses: actions/checkout@v7
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Show coverage
        run: npm test -- --bail --maxWorkers=100% --watchAll=false --coverage
```

```yml:.github/workflows/build.yml
name: Build

on:
  pull_request:
    types: [opened, reopened, synchronize, ready_for_review]

env:
  WORKING_DIRECTORY: application

jobs:
  build:
    name: Build
    if: |
      github.event.pull_request.draft == false
      && !startsWith(github.head_ref, 'release')
      && !startsWith(github.head_ref, 'doc')
    runs-on: ubuntu-latest
    defaults:
      run:
        working-directory: ${{ env.WORKING_DIRECTORY }}
    steps:
      - name: Check out
        uses: actions/checkout@v7
      - name: Setup Node.js
        uses: ./.github/actions/set-up-node
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}
      - name: Run npm run build
        run: npm run build
```

## 参考
https://docs.github.com/ja/actions/creating-actions/metadata-syntax-for-github-actions


