---
title: GitHub Actionsを使ってリリースのたびにリリースノートとリリースタグを自動作成しよう！
tags:
  - Git
  - git-flow
  - release-note
  - GitHubActions
private: false
updated_at: '2023-11-22T16:46:18+09:00'
id: 176037432f7efc8fde26
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## はじめに
何かしらのプロダクトをリリースする際に
- リリースノート
- リリースタグ
 
を作成するのが一般的です
GitHub Actionsを使って
- 変更箇所
- 作業者

などを記載したリリースノートを下記のように自動作成できます
![スクリーンショット 2023-11-22 16.42.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/31df1d41-7253-5f80-ad2a-7cd440e1c5ae.png)


また、プロジェクトのバージョンが記載されたリリースタグを下記のように自動生成できます
![スクリーンショット 2023-11-22 16.43.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e6996f95-06cd-ad0c-166b-feb127b88d64.png)


今回はリリース用ワークフローの設定からreleaseブランチをmainブランチへマージ後にリリースノートが作成されるところまで解説します

## GitHub Actionsの設定
以下のようなリポジトリ構成で設定ファイルを作成します
```
tree
.
└── .github
    ├── release-drafter.yml
    └── workflows
        └── release-drafter.yml
```

### リリースノートのテンプレート作成
下記のように該当するラベルとブランチ名(autolabeler)に応じてカテゴリ化します
```yml:.github/release-drafter.yml
name-template: 'v$RESOLVED_VERSION 🌈'
tag-template: 'v$RESOLVED_VERSION'

categories:
  - title: '🚀 Features'
    labels:
      - 'enhancement'
  - title: '🐛 Bug Fixes'
    labels:
      - 'bug'
      - 'emergency'
  - title: '🔧 Refactoring'
    label: 'refactor'
  - title: '📖 Documentation'
    label: 'documentation'
  - title: '✅ Tests'
    label: 'test'

change-template: '- $TITLE @$AUTHOR (#$NUMBER)'

change-title-escapes: '\<*_&' # You can add # and @ to disable mentions, and add ` to disable code blocks.

version-resolver:
  major:
    labels:
      - 'major'
  minor:
    labels:
      - 'minor'
  patch:
    labels:
      - 'patch'
  default: patch

template: |
  ## Changes
  $CHANGES
  
autolabeler:
  - label: enhancement
    branch:
      - '/^feat(ure)?[/-].+/'
  - label: bug
    branch:
      - '/^fix[/-].+/'
  - label: emergency
    branch:
      - '/^hotfix[/-].+/'
  - label: test
    branch:
      - '/^test[/-].+/'
  - label: refactor
    branch:
      - '/^refactor[/-].+/'
  - label: documentation
    branch:
      - '/^doc[/-].+/'
```

### リリースノート作成用ワークフロー
下記のように作成します
今回はmainブランチにリリースブランチがマージされたときに実行するよう設定します

```yml:.github/workflows/release-drafter.yml
name: Create Release Note

on:
  pull_request:
    # PRが閉じたタイミングで実行
    types:
      - closed
    # mainブランチのみを対象とする
    branches:
      - main

permissions:
  contents: read

jobs:
  release:
    permissions:
      # write permission is required to create a github release
      contents: write
      # リリースノートを書くためwrite用のpermissionを付与
      pull-requests: write
    if: github.event.pull_request.merged == true && startsWith(github.head_ref, 'release')
    runs-on: ubuntu-latest
    steps:
      - name: Create Release Tag And Note
        env:
          # このトークンは自動生成されるのでsecretsを登録する必要ない
          GITHUB_TOKEN: ${{ secrets.GITHUB_TOKEN }}
          # PRのタイトルと内容をRelease内容に追加する
          RELEASE_TAG: ${{ github.event.pull_request.title }}
        uses: release-drafter/release-drafter@v7
        with:
          tag: ${{ env.RELEASE_TAG }}
          name: Release ${{ env.RELEASE_TAG }}
          version: ${{ env.RELEASE_TAG }}
          publish: true
```


## mainブランチへマージ
releaseブランチをmainへマージします
今回のリリースは1.0.0とします
![スクリーンショット 2023-11-22 16.43.49.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/45cf4213-a29f-41b4-de5c-8e37b1d28f55.png)

![スクリーンショット 2023-11-22 16.43.54.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/39d6361d-24b0-1db9-0dfb-acfe4ce8afd1.png)


下記のようにワークフローが正常に実行されたら成功です
![スクリーンショット 2023-11-22 16.44.24.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c1873496-cb3e-e1ac-d39a-150b4da2a67e.png)

## マージ後
mainブランチへmerge後、下記のようにリリース用のリンクが作成されます
![スクリーンショット 2023-11-22 16.45.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/deb97cc2-6607-17ab-b065-5d9645fde4ca.png)

下記のようにリリースノートが作成されました
このように
- PRの作成者
- ラベルに応じたカテゴリーの割り振り

が記載されているリリースノートとリリースタグが作成されていることを確認できれば成功です
![スクリーンショット 2023-11-22 16.42.30.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/31df1d41-7253-5f80-ad2a-7cd440e1c5ae.png)

![スクリーンショット 2023-11-22 16.43.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e6996f95-06cd-ad0c-166b-feb127b88d64.png)

## 参考
https://github.com/release-drafter/release-drafter

https://zenn.dev/kshida/articles/auto-generate-release-note-with-calver

