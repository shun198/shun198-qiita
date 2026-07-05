---
title: 【Python】AtCoderのワークフローを標準入力から提出までVSCode内で完結させよう！
tags:
  - Python
  - Mac
  - AtCoder
  - Linuxコマンド
private: false
updated_at: '2022-10-29T11:44:34+09:00'
id: 6dffbb119a3a133b8e3c
organization_url_name: null
slide: false
---
## 概要
エディタ内で書いたコードをAtCoderにコピぺしたり、コピペしたコードをマウス使って手動でテストするのめんどくさいですよね？
今回はなんと
- コード記述用のテンプレートファイル作成
- 入力例の自動入力
- コードのテスト
- コードの提出

まで全てVSCode内で完結させる手順について１から解説していきたいと思います

## 前提
- AtCoderで使用する言語がPythonの場合の設定方法です。別の言語を使う際は使用する言語にコマンドを置き換えてください
- 問題文の取り込みまでは自動化できないです。ご了承ください
- 開発環境はMac
- Linuxのコマンドはある程度理解している
- pip、Node.js、pythonはインストール済み
- AtCoderのアカウント作成済み

## 1.atcoder-cli, online-judge-toolsをインストール
atcoder-cli, online-judge-toolsをインストールします
```terminal
pip install online-judge-tools
npm -g install atcoder-cli
```
インストールしたあとにバージョンが確認できたら成功です
```terminal
acc -v
2.2.0
oj --version
online-judge-tools 11.5.1 (+ online-judge-api-client 10.10.0)
```

## 2.ログイン
- コンテストのリアルタイム参加
- ローカル環境から問題の提出

の際はログインが必須です
```terminal
acc login
oj login https://atcoder.jp
```

## 3.テンプレートファイルの作成および設定
テンプレートファイル作成の設定をすることで後述の問題とテストのダウンロードの際に提出するファイルの作成を自動化できます
作成するテンプレートは
- template.json
- main.py

です。main.pyは提出する用のファイルなので.pyの拡張子がついていたら名前はなんでもいいです

```terminal
# atcoderのconfigのディレクトリへ移動
cd $(acc config-dir)
mkdir atcoder_template && cd atcoder_template
touch template.json 
touch main.py
```
では、template.jsonに必要な情報を記載しましょう

### template.json
template.jsonにはプログラムを実行するファイルと提出するファイルを指定します
実行するファイルと提出するファイルは同じにしたいので下の例ではどちらもmain.pyを指定しています
```json:template.json
{
    "task": {
        "program": [
            "main.py"
        ],
        "submit": "main.py"
    }
}
```

### main.pyの編集
以下の様に記載します

```python:main.py
# コードを記載
import io
import sys

# 下記に標準入力を記載
_INPUT = """\

"""
sys.stdin = io.StringIO(_INPUT)
```

```
_INPUT = """\

"""
```
内に入力例を記載することでインタプリンタを実行するたびに手動で入力例を記載せずに済みます
下記の問題を例にやってみましょう

https://atcoder.jp/contests/abc269/tasks/abc269_a

1 2 5 3の入力例を記載し、実行します
```python:入力例1
import io
import sys

# 下記に標準入力を記載
_INPUT = """\
1 2 5 3

"""
sys.stdin = io.StringIO(_INPUT)
# ここからコードを記載
a,b,c,d = map(int,input().split())
print((a+b)*(c-d))
print("Takahashi")
```

```python:出力例1
6
Takahashi
```
ちなみに入力例の後に改行があっても正しく実行されます

### main.pyのアクセス権変更
テストを実行する際にアクセス権がなくて拒否されてしまうのでchmodコマンドで権限を変更します
```terminal
ls -l
total 16
-rw-r--r--  1 shun  staff   21  8 11 19:26 main.py
-rw-r--r--  1 shun  staff  105  8 11 19:25 template.json
# 権限を変更
# main.pyの権限がrw-からrwxに変更される(実行ができる)
chmod 755 main.py
ls -l
# main.pyを実行する権限が付与されたことを確認
total 16
-rwxr-xr-x  1 shun  staff   21  8 11 19:26 main.py
-rw-r--r--  1 shun  staff  105  8 11 19:25 template.json
```

### テンプレートの設定
作成したテンプレートフォルダをテンプレートとして設定します
```terminal
acc config default-template atcoder_template
```

## 4.問題文およびテストケースのダウンロード
`acc new`の後に作成する問題を指定します。今回はabc262を指定します

問題を作成したいディレクトリでコマンドを実行すると以下のように表示されます
選択する問題はmacの矢印キーで操作できます
```terminal
acc new abc262
abc262/contest.acc.json created.
create project of AtCoder Beginner Contest 262
? select tasks (Press <space> to select, <a> to toggle all, <i> to invert selection)
❯◉ A World Cup
 ◯ B Triangle (Easier)
 ◯ C Min Max Pair
 ◯ D I Hate Non-integer Number
 ◯ E Red and Blue Graph
 ◯ F Erase and Rotate
 ◯ G LIS with Stack
```

キーの操作は以下の通りです
| キー | 説明文 |
|:-----------:|:------------:|
|  enter  | 選択された問題とそのテストケースを作成 |
|  space  | ❯で指している問題を選択/解除 |
|  a  | 全選択/全解除 |
|  i  | 選択箇所を反転 |

### ダウンロードした問題のディレクトリ構成
問題とテストケース(今回はabc262のa問題のみ)のダウンロードが完了したあとのディレクトリ構成は以下の通りです
ダウンロードする問題のフォルダ名の中にtemplates.jsonで設定したmain.pyとテストケースが格納されたtestsフォルダおよびテストケースとcontest.acc.jsonが作成されます

```terminal
❯ tree
.
└── abc262
    ├── a
    │   ├── main.py
    │   └── tests
    │       ├── sample-1.in
    │       ├── sample-1.out
    │       ├── sample-2.in
    │       ├── sample-2.out
    │       ├── sample-3.in
    │       └── sample-3.out
    └── contest.acc.json
```

:::note warn
後から問題を追加したいときは？
:::

例えば以下のようにA問題とテストケースをダウンロードしたけどB問題も追加でダウンロードしたいケースもあるかと思います
```terminal
❯ tree
.
└── abc262
    ├── a
    │   ├── main.py
    │   └── tests
    │       ├── sample-1.in
    │       ├── sample-1.out
    │       ├── sample-2.in
    │       ├── sample-2.out
    │       ├── sample-3.in
    │       └── sample-3.out
    └── contest.acc.json
```

問題とテストケースを追加でダウンロードするときは問題が格納されているディレクトリまで移動した後に`acc add`を実行します
```terminal
cd abc262
acc add
? select tasks (Press <space> to select, <a> to toggle all, <i> to invert selection)
 - A World Cup (already installed)
❯◉ B Triangle (Easier)
 ◯ C Min Max Pair
 ◯ D I Hate Non-integer Number
 ◯ E Red and Blue Graph
 ◯ F Erase and Rotate
 ◯ G LIS with Stack
(Move up and down to reveal more choices)
```

すでにダウンロードされている問題は`-`と表示されます。追加でダウンロードしたい問題を選択し、Enterを押します

:::note warn 
問題を削除するには？
:::

問題を削除する際は問題が格納されているディレクトリごと削除することで問題とテストケースを削除できます
```terminal
rm -rf abc262
```

:::note warn  
すでに削除してしまった問題をもう一度追加したいときは？
:::

例えば、すでにある問題を削除した後に削除した問題をもう一度追加しようとします。ターミナル上では一度削除した問題は選択できないようになってしまっています
```terminal
cd abc262
# B問題を削除
rm -rf b
acc add
? select tasks (Press <space> to select, <a> to toggle all, <i> to invert selection)
 - A World Cup (already installed)
 - B Triangle (Easier) (already installed)
❯◉ C Min Max Pair
 ◯ D I Hate Non-integer Number
 ◯ E Red and Blue Graph
 ◯ F Erase and Rotate
 ◯ G LIS with Stack
```

一度削除した問題をもう一度追加する際は`--force`を使って追加できます。

:::note warn
ただし、すでにある問題を選択してしまうと今まで書いたコードが全て上書きされるので注意が必要です
:::

```terminal
acc add --force
? select tasks (Press <space> to select, <a> to toggle all, <i> to invert selection)
❯◯ A World Cup
 ◯ B Triangle (Easier)
 ◯ C Min Max Pair
 ◉ D I Hate Non-integer Number
 ◯ E Red and Blue Graph
 ◯ F Erase and Rotate
 ◯ G LIS with Stack
```

## 5.テストケースの実行
問題をダウンロードし、main.pyにコードを記述できた後はテストを実行できます。
pythonのソースコードをテストする際はファイル名の前にpythonもしくはpython3を指定する必要があります
また、gnu-timeをインストールするとメモリの消費量まで表示することができます
```terminal
brew install gnu-time
```
以下のコードを実行するとテスト結果が表示されます
```terminal
oj test -c  "python3 main.py" -d tests
[INFO] online-judge-tools 11.5.1 (+ online-judge-api-client 10.10.0)
[INFO] 3 cases found

[INFO] sample-1
[INFO] time: 0.016689 sec
[SUCCESS] AC

[INFO] sample-2
[INFO] time: 0.016522 sec
[SUCCESS] AC

[INFO] sample-3
[INFO] time: 0.019020 sec
[SUCCESS] AC

[INFO] slowest: 0.019020 sec  (for sample-3)
[INFO] max memory: 7.840000 MB  (for sample-1)
[SUCCESS] test success: 3 cases
```

## 6.コードの提出
書いたコードを提出します
```terminal
acc submit
```

途中で

:::note warn

```
the problem "https://atcoder.jp/contests/abc262/tasks/abc262_a" is specified to submit, but no samples were downloaded in this directory. this may be mis-operation
Are you sure? Please type "abca"
```

:::

と表示されますが無視して入力します
その後、atcoderのページが開き、コードが自動的に実行されます

:::note

```
[NETWORK] 200 OK
[INFO] You are logged in.
[NETWORK] GET: https://atcoder.jp/contests/abc262/tasks/abc262_a
[NETWORK] 200 OK
[INFO] PyPy is available for Python interpreter
[INFO] chosen language: 4006 (Python (3.8.2))
[WARNING] the problem "https://atcoder.jp/contests/abc262/tasks/abc262_a" is specified to submit, but no samples were downloaded in this directory. this may be mis-operation
Are you sure? Please type "abca" abca
[NETWORK] GET: https://atcoder.jp/contests/abc262/tasks/abc262_a
[NETWORK] 200 OK
[NETWORK] GET: https://atcoder.jp/contests/abc262/submit
[NETWORK] 200 OK
[NETWORK] POST: https://atcoder.jp/contests/abc262/submit
[NETWORK] redirected to: https://atcoder.jp/contests/abc262/submissions/me
[NETWORK] 200 OK
[SUCCESS] result: https://atcoder.jp/contests/abc262/submissions/33953955
[INFO] open the submission page with browser: <webbrowser.MacOSXOSAScript object at 0x1064888b0>
```
:::

下記画像のように実行結果が表示されたら成功です

:::note

![スクリーンショット 2022-08-12 12.46.36.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/8d4d71f4-1606-0596-0ee1-338a81a27891.png)

:::

## 問題文を確認したいときは？
問題文をVSCodeから直接見ることはできませんがurlは問題のディレクトリ内の`contest.acc.json`から確認できます
urlをクリックすると問題文まで直接飛ぶことができます

```json:contest.acc.json
{
  "contest": {
    "id": "abc240",
    "title": "AtCoder Beginner Contest 240",
    "url": "https://atcoder.jp/contests/abc240"
  },
  "tasks": [
    {
      "id": "abc240_a",
      "label": "A",
      "title": "Edge Checker",
      "url": "https://atcoder.jp/contests/abc240/tasks/abc240_a",
      "directory": {
        "path": "a",
        "testdir": "tests",
        "submit": "main.py"
      }
    },
    {
      "id": "abc240_b",
      "label": "B",
      "title": "Count Distinct Integers",
      "url": "https://atcoder.jp/contests/abc240/tasks/abc240_b",
      "directory": {
        "path": "b",
        "testdir": "tests",
        "submit": "main.py"
      }
    },
// [以下略]
```

## まとめ
1. atcoder-cli, online-judge-toolsをインストール
1. ログイン
1. テンプレートファイルの作成および設定
1. 問題文およびテストケースのダウンロード
1. テストケースの実行
1. コードの提出

の順で行うとAtCoderのワークフローを全てVSCode内で完結させることができます

## 記事の紹介
AtCoder始めたばかりで何を勉強したらいいいかわからない方向けの記事も作成したので見てくださると幸いです

https://qiita.com/shun198/items/e99a70147004814f15a6

## 参考文献
https://qiita.com/natsuozawa/items/c97f374900312fc4d8ca

https://github.com/Tatamo/atcoder-cli

https://github.com/online-judge-tools/oj
