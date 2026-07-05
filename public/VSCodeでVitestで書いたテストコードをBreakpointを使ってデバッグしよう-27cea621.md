---
title: VSCodeでVitestで書いたテストコードをBreakpointを使ってデバッグしよう！
tags:
  - VSCode
  - Vitest
private: false
updated_at: '2023-11-26T08:59:46+09:00'
id: 27cea621e023b43d7547
organization_url_name: null
slide: false
---
## 概要
Vitestでフロントエンドのテストをデバッグする際にブレークポイントを使用する方法について解説します

## 前提
- すでにVitestやReactの環境構築が完了済みであること

## 手順
VSCodeのターミナル上で`Javascript デバッグ　ターミナル`を開きます

![スクリーンショット 2023-11-26 8.46.20.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/269ef7fb-84ae-0c7f-ebc8-1b9a6bdeb115.png)

続いて
```
npm run test
```
を実行します

実行すると以下のようにデバッガーが起動します
```
Debugger attached.

> project@0.0.0 test
> vitest --watch

Debugger attached.
```

すると、以下のようにブレークポイントによるデバッグができます
![スクリーンショット 2023-11-26 8.33.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/d14a2bb6-af92-716d-6272-1b07731dbeca.png)

変数の中身もこのように確認できます
![スクリーンショット 2023-11-26 8.54.01.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/39ad7926-c3b0-c451-8235-f0a7955b5dd7.png)

デバッグコンソール上でも変数の中身も確認できます
![スクリーンショット 2023-11-26 8.54.44.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/0bb3139a-143c-4666-81e2-ca25dec0d8fb.png)

デバッグコンソールから変数を直接参照したり変数の中身を変更することもできます
![スクリーンショット 2023-11-26 8.55.33.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/46b0e6f3-2467-4f38-451c-0bc84c077a51.png)

## まとめ
テストを実行するたびに毎回console.logを記載したりするのはめんどくさいので便利な機能は積極的に使いましょう

## 参考
https://vitest.dev/guide/debugging

https://ics.media/entry/11356/
