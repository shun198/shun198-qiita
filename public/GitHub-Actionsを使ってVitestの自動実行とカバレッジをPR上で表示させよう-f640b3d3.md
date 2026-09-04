---
title: GitHub Actionsを使ってVitestの自動実行とカバレッジをPR上で表示させよう！
tags:
  - GitHubActions
  - vite
  - Vitest
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: f640b3d3bf73d2cc3510
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
GitHub Actions内でVitestを使って単体テストを実行し、PRにカバレッジを表示させることができれば便利なのでその方法について解説していきたいと思います

## 前提
- Vite、Vitestをインストール済み
- 以下のactionを使ってカバレッジを表示させる
    - https://github.com/davelosert/vitest-coverage-report-action

## ディレクトリ構成
```
├── .github
│   └── workflows
│       └── test.yml
└── application
    ├── package-lock.json
    ├── package.json
    ├── src
    └── vite.config.ts
```

## vite.config.ts
カバレッジを表示するactionを使用するには以下の設定をvite.config.tsファイルに記載する必要があります

> To use this action, you need to configure vitest to create a coverage report with the following reporters:
json-summary (required): This reporter generates a high-level summary of your overall coverage.
json (optional): If provided, this reporter generates file-specific coverage reports for each file in your project.

```vite.config.ts
import { defineConfig } from 'vitest/config';

export default defineConfig({
  test: {
    coverage: {
      // you can include other reporters, but 'json-summary' is required, json is recommended
      reporter: ['text', 'json-summary', 'json'],
    },
  },
});

```

## ワークフローの作成
Vitestを実行する用のワークフローを作成します
今回はapplication配下にソースコードがあるので`working-directory`を指定します

```test.yml
name: Vitest

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
        uses: actions/setup-node@v7
        with:
          node-version-file: ${{ env.WORKING_DIRECTORY }}/package.json
          cache: 'npm'
          cache-dependency-path: '**/package-lock.json'
      - name: Install dependencies
        run: npm ci
      - name: Run Vitest
        run: npx vitest --coverage.enabled true
      - name: Show coverage
        uses: davelosert/vitest-coverage-report-action@v2
        with:
          working-directory: ${{ env.WORKING_DIRECTORY }}

```

## ワークフローを実行してみよう！
以下のようにテストが正常に実行され、カバレッジがPR上に表示されたら成功です
![スクリーンショット 2024-05-22 15.03.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d968bed1-2006-1f36-5b8c-e92535b4a64b.png)

![スクリーンショット 2024-05-22 15.10.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/071cbee3-353a-d073-f9d4-4d4b99b3e9b6.png)

## 参考
https://github.com/davelosert/vitest-coverage-report-action

https://stackoverflow.com/questions/72146352/vitest-defineconfig-test-does-not-exist-in-type-userconfigexport

