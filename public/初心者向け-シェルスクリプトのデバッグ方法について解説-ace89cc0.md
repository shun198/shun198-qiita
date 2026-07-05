---
title: '[初心者向け] シェルスクリプトのデバッグ方法について解説'
tags:
  - ShellScript
  - Linux
  - Linuxコマンド
private: false
updated_at: '2024-05-24T08:28:16+09:00'
id: ace89cc09c877e8290f4
organization_url_name: null
slide: false
---
## 概要
シェルスクリプトのデバッグ方法について知っていると効率よくトラブルシューティングできます
今回はデバッグする際に知っておくべき
- オプション
- ブレークポイント

の設定方法について解説します

## set
Bash には便利なオプションが多数用意されおり、以下のようにスクリプトの先頭に set コマンドで記述するとオプションを実行できます
一般的に`set -eu`を使用します(eとuの説明は後述)
```
#!/bin/bash
set -eu
```

### -e
シェルスクリプトが1度実行されてしまうと途中でエラーがある、ないに関わらず最後まで処理が実行されてしまいます
 -e オプションを定義することでシェルスクリプト内で エラーが発生した時点で、それ以降の処理を中断する ことができます

### -u
-u オプションを定義することで、未定義の変数に対して読み込み等を行おうとした際に、エラーとして扱うようになります

## ブレークポイント
VSCode上でブレークポイントを使用することができます
まずはlaunch.jsonを作成します
![スクリーンショット 2022-11-20 15.35.58.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c3b42891-a5f2-a069-fc7c-744fd36963f6.png)

bashを選択します
![スクリーンショット 2022-11-20 15.36.37.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/6ecf52d6-efaf-d14f-97f7-054b4cccf60d.png)

launch.jsonが以下の通りになっていれば大丈夫です
今回はnameを`Bash-Debug`にします
```launch.json
{
    "version": "0.2.0",
    "configurations": [
        {
            "type": "bashdb",
            "request": "launch",
            "name": "Bash-Debug (simplest configuration)",
            "program": "${file}"
        }
    ]
}
```

緑色の三角のボタンを押します
![スクリーンショット 2023-11-26 9.05.15.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/2c9a3590-704b-c9a5-23b0-c65dda8a79ab.png)


以下のようにデバッグモードになったら成功です
ブレークポイントによるステップイン・ステップオーバーをはじめ
ウォッチ、デバッグコンソールなども使用できます

![スクリーンショット 2023-11-26 9.05.31.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/08b2a1f1-e827-58e0-9778-a51606b09d2b.png)


## 参考
https://qiita.com/m-yamashita/items/889c116b92dc0bf4ea7d

https://qiita.com/3364git/items/51ee3f18fb81fcaca5f4
