---
title: '[初心者向け] [GitHub Actions] Cacheを使ったNode.jsのパッケージのインストールの方法と仕組みについて徹底解説'
tags:
  - Node.js
  - npm
  - GitHubActions
private: false
updated_at: '2026-07-05T22:24:13+09:00'
id: d976c4c442ddcabdadfb
organization_url_name: null
slide: false
ignorePublish: false
posting_campaign_uuid: null
agreed_posting_campaign_term: false
---
## 概要
Node.jsの必要なパッケージをインストールする際はワークフローを実行するたびに新しいrunnerを使用する関係でパッケージを1からインストールします
パッケージが少ないうちはいいものの、プロジェクトが大きくなるにつれてパッケージが多くなるとパッケージのインストール時間分ワークフローの実行時間が長くなってしまいます
そこでパッケージをインストールする際はCacheを使うとパッケージがどんなに多くてもインストール作業を数秒以内に終わらせることができます
今回はGitHubの公式で公開されている
- actions/cache
- actions/setup-node

について解説していきます

## actions/cache
公式が出しているActionで今回使用するNode.js以外の言語やDockerのCacheも扱うことができます
詳細は以下の公式ドキュメントに記載されています

https://github.com/actions/cache

以下を例に説明します
```yml
      - name: Cache dependencies
        uses: actions/cache@v6
        with:
          path: '**/node_modules'
          key: node-modules-${{ hashFiles('**/package-lock.json') }}
      - name: Install dependencies
        run: npm ci
```

### path
今回Cacheするのはnode_modulesで`**`をつけるとソースコード内にある全てのnode_modulesのCacheを作成します
`**`をつけることでnode_modulesのパスが変更したとしてもCacheを作成してくれるので便利です

### key
Cacheを参照する際に一意のkeyが必要です
```
key: node-modules-${{ hashFiles('**/package-lock.json') }}
```
`node-modules`の箇所はどんなCacheか判別できさえすれば任意の値で大丈夫なのですが
```
${{ hashFiles('**/package-lock.json') }}
```
で一意のkeyを作成します
package-lock.jsonを指定しているので必ずGit管理下に置く必要があります

### hashFiles関数
ワークフロー内で使用できるGitHub Actions独自のメソッドです

>path パターンに一致するファイル群から単一のハッシュを返します。

>この関数はマッチしたそれぞれのファイルに対するSHA-256ハッシュを計算し、それらのハッシュを使ってファイルの集合に対する最終的なSHA-256ハッシュを計算します。

簡単に説明するとpackage-lock.jsonの内容をもとに一意のハッシュ値を作成しています
以下のように`node-modules-<package-lock.jsonのハッシュ値>`がCacheを参照する際のkeyとして使用されます
2回目以降のパッケージのインストールはkeyをもとに該当するCacheを探します
該当するCacheがあればそれを使用するのでパッケージのインストールが高速化されます

![スクリーンショット 2023-07-05 8.19.04.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/a978e9dd-527a-525f-a51c-3e2e69e3994f.png)

新たなパッケージがインストールされるとpackage-lock.jsonが変更、つまりkeyの値が変わるのでインストール作業を1から行い、新たなkeyをもとにCacheを生成します
そのため、package-lock.jsonなど頻繁に変更されないファイルを使ってCacheを生成するのが一般的です

詳細は以下の公式ドキュメントに記載されています

https://docs.github.com/ja/actions/learn-github-actions/expressions#hashfiles

## npm ci
CI/CDではパッケージをインストールする際はnpm installではなく、npm ciを使用します
npm ciを使用するとパッケージの依存関係の解消は行わずに常に package-lock.json を見てnode_modulesを削除してからパッケージのインストールを行います
仮に依存関係が間違っている場合はnpm installのように依存関係を解決せずに実行するのでエラーを出してくれます
そのため、actions/cacheの公式ドキュメントでもnpm installではなく、npm ciを推奨しています

https://docs.npmjs.com/cli/v8/commands/npm-ci

## actions/setup-node
setup-nodeでも同様のことができます
```yml
    - name: Cache Dependencies
      uses: actions/setup-node@v7
      with:
        node-version: '16'
        cache: 'npm'
      - name: Install dependencies
        run: npm ci
```
actions/cacheと比べて記述が楽な上にNode.jsのセットアップも同時にできます
しかし、複数ワークフローで使用するとワークフローの数だけCacheが生成されてしまうのでactions/cacheの使用を推奨しています

https://github.com/actions/setup-node/issues/409

setup-nodeの詳細は以下の公式ドキュメントに記載されています

https://github.com/actions/setup-node

## 参考
https://github.com/actions/cache

https://github.com/actions/setup-node

https://docs.github.com/ja/actions/learn-github-actions/expressions#hashfiles

https://qiita.com/mstssk/items/8759c71f328cab802670

