---
title: パッケージを自動で更新してくれるRenovateとその導入方法について徹底解説！
tags:
  - Docker
  - docker-compose
  - Renovate
  - Poetry
private: false
updated_at: '2024-03-23T08:07:46+09:00'
id: 0b24bb3f1660fb726ddb
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
今回はRenovateの概要、導入方法、renovate.jsonの書き方について解説していきます

## 前提
- 今回はpyproject.toml、Docker、GitHub Actions内のパッケージの自動更新の方法をメインに説明していますが別のFWや言語でも使用できます

## Renovateとは
プロジェクト内のライブラリを自動で更新してくれるツールです
運用・保守フェーズになると定期的にライブラリを更新しないとセキュリティホールが生まれてしまう場合があります
Renovateを使うと自動でPRをあげてますし、GitHub Actions内でテストが成功したらそのままmerge、失敗したら原因を調査する、などの運用ができるのでとても便利です

## 導入
MarketPlaceからRenovateを選択します
![スクリーンショット 2024-01-22 16.12.40.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a43e2709-40f6-db74-5ac5-26749d00bfab.png)

アカウント名を入力して無料でインストールします
![スクリーンショット 2024-01-22 16.12.59.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2e5d0311-8081-946d-84eb-788096ee9b13.png)

今回は全てのリポジトリを選択します
![スクリーンショット 2024-01-22 16.16.22.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/7a37d818-c0fe-4dea-7e1d-6717fa9e30af.png)

許可します
![スクリーンショット 2024-01-22 16.16.47.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8510ad8e-5b00-2a95-8192-cab4493ebd75.png)

https://developer.mend.io/

にアクセスします
以下のように更新する対象となるパッケージの一覧が表示されたら成功です
![スクリーンショット 2024-01-22 16.23.14.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/10f65d7d-5bf1-beec-d945-a4651e94599a.png)

![スクリーンショット 2024-01-22 17.52.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/aa69ac93-ecb9-03b5-6e7a-7960ae9360ef.png)

![スクリーンショット 2024-01-22 16.25.26.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/1ecaee02-8c66-3f01-30fd-42ca3c31521f.png)

![スクリーンショット 2024-01-22 16.33.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/b6ff8379-8b1a-2797-108e-6162bc7bd129.png)

## Renovateを設定しよう！
Renovateが自動にPRを作成し、以下のように対象のパッケージを表示します
![スクリーンショット 2024-01-22 16.41.09.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/e347b02b-448f-3538-bfdd-7bf6cbbb7d2a.png)

![スクリーンショット 2024-01-22 16.41.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ffabae50-891c-9bbb-09d0-446b131e8142.png)

以下が初期設定の時のrenovate.jsonです
```renovate.json
{
    "$schema": "https://docs.renovatebot.com/renovate-schema.json",
    "extends": [
        "config:recommended"
    ]
}
```

![スクリーンショット 2024-01-23 11.03.39.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0151c284-db24-c63c-fa04-e311982a05df.png)

今回はDockerfile、docker-compose.yml、GitHub Actions内の
- Python
- Postgres

を自動で更新したくないのでpackageRulesで定義します
各項目の詳細は公式ドキュメントを参照してください

https://docs.renovatebot.com/

```renovate.json
{
    "$schema": "https://docs.renovatebot.com/renovate-schema.json",
    "extends": [
        "config:recommended"
    ],
    "baseBranches": [
        "develop"
    ],
    "reviewers": [
        "@shun198"
    ],
    "timezone": "Asia/Tokyo",
    "schedule": [
        "after 8am every weekday"
    ],
    "prHourlyLimit": 0,
    "prConcurrentLimit": 0,
    "automerge": false,
    "platformAutomerge": false,
    "labels": [
        "renovate"
    ],
    "docker-compose": {
        "enabled": false
    },
    "dockerfile": {
        "enabled": false
    },
    "lockFileMaintenance": {
        "enabled": true
    },
    "packageRules": [
        {
            "matchDatasources": [
                "docker"
            ],
            "matchPackagePatterns": [
                "postgres"
            ],
            "enabled": false
        },
        {
            "matchDepTypes": [
                "dev"
            ],
            "matchUpdateTypes": [
                "minor",
                "patch",
                "pin",
                "digest"
            ],
            "automerge": true
        }
    ]
}
```

以下のようにPRが自動で生成されたら成功です

![スクリーンショット 2024-03-21 8.18.05.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/ac847363-a400-8269-bca2-e54f5accc79e.png)

## PRが自動生成されないときは？
ブランチプロテクションルールを適用しているときはrenovateがPRを作成する権限を付与していない可能性があります
以下のように`Allow specified actors to bypass required pull requests`にチェックを入れ、renovateを追加してみてください

![スクリーンショット 2024-03-22 9.15.52.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c790711f-db14-6781-1fbf-f377d00c2994.png)

Rulesetsを適用している場合はAdd bypassにrenovateを追加してください
![スクリーンショット 2024-03-22 9.19.32.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/dc521189-85e8-4886-fb48-dcc47f5148d3.png)

## 参考
https://github.com/marketplace/renovate

https://docs.renovatebot.com/modules/platform/github/

https://docs.renovatebot.com/modules/versioning/#poetry-versioning

https://zenn.dev/sunadoi/articles/889219ab865583

https://note.com/takahiroanno/n/n053723a676dd
