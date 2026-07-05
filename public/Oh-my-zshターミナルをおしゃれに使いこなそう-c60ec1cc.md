---
title: 【Oh-my-zsh】ターミナルをおしゃれに使いこなそう!
tags:
  - Zsh
  - Terminal
  - zshrc
  - Linuxコマンド
private: false
updated_at: '2024-02-28T13:30:12+09:00'
id: c60ec1cce9c9bf1e8c26
organization_url_name: null
slide: false
---
## 概要
ターミナルをスタイリッシュにカスタマイズする方法について解説したいと思います

## 前提
- Macユーザ
- zshのカスタマイズです

## ターミナルをカスタマイズしようと思った背景
- コマンドど忘れしがち
- タイポ(タイプミス)を極力減らしたい
- エディタをおしゃれにできるならターミナルもできるのでは？と思った


## 何をインストールするの？
- `oh my zsh`
- `powerlevel10k`
- `zsh-autosuggestions`
- `zsh-syntax-highlighting`

の4つをインストールします

## oh my zsh
zshのフレームワーク

https://github.com/ohmyzsh/ohmyzsh

下記のコマンドを入力すると完了(詳しくは[公式HP](https://ohmyz.sh/)を参照)
```zsh
sh -c "$(curl -fsSL https://raw.githubusercontent.com/ohmyzsh/ohmyzsh/master/tools/install.sh)" "" --unattended
 ```

## powerlevel10k
zshのテーマを変更するプラグイン

https://github.com/romkatv/powerlevel10k

1.  `powerlevel10k`のGitリポジトリをホームディレクトリにクローン
```zsh
git clone --depth=1 https://github.com/romkatv/powerlevel10k.git ${ZSH_CUSTOM:-$HOME/.oh-my-zsh/custom}/themes/powerlevel10k
```
2. ~/.zshrcを開いてテーマを`ZSH_THEME="robbyrussell"`から　`ZSH_THEME="powerlevel10k/powerlevel10k"` に変更

3. 変更内容を保存後、exitしてからもう一度ターミナルを開くと以下のウィザード画面になるので選択肢に従って任意のデザインにカスタマイズ
![スクリーンショット 2024-02-28 13.28.29.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/76a51935-ca5b-c742-6c71-43dd0a5369dd.png)


人によって見た目は違いますが私はこんな感じになりました
![スクリーンショット 2024-02-28 13.28.48.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/69a973a0-b740-8bf2-6551-092749cfdb86.png)

### 再設定したい時は？
再設定したいときは以下の通りに入力するともう一度ウィザード画面が表示されます
```
p10k configure
```

### そもそもどうやってzshrcを編集するの？
#### Finderから
- .zshrcを開く
ホームディレクトリを指定して`shift+commad+ .`を押すと隠しファイルが表示されるので`.zshrc`を好きなエディタで開きます
![スクリーンショット 2022-08-13 16.25.03.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/c2fba943-311d-e130-97c6-b6bcb42f67db.png)

- .zshrcが開けたらZSH_THEMEを"powerlevel10k/powerlevel10k"に変更

![スクリーンショット 2022-08-13 16.36.21.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/f0145340-8f42-798d-cceb-20f7376d445d.png)

#### VSCodeから

`shift+commad+p`と押すとコマンドパレットが開くのでPATH内に'code'コマンドをインストールします、を選択する
これでターミナル上から`code`と入力するとファイルをVSCodeで開けるようになる

![スクリーンショット 2024-02-28 13.29.18.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/82aa8f3e-320b-b19e-2d4b-d66c23583a33.png)


ホームディレクトリに移動してターミナル上で以下の通りに入力
```zsh
cd ~
code .zshrc
```
.zshrcが開けたらZSH_THEMEを"powerlevel10k/powerlevel10k"に変更
```.zshrc
# Enable Powerlevel10k instant prompt. Should stay close to the top of ~/.zshrc.
# Initialization code that may require console input (password prompts, [y/n]
# confirmations, etc.) must go above this block; everything else may go below.
if [[ -r "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh" ]]; then
  source "${XDG_CACHE_HOME:-$HOME/.cache}/p10k-instant-prompt-${(%):-%n}.zsh"
fi

# If you come from bash you might have to change your $PATH.
# export PATH=$HOME/bin:/usr/local/bin:$PATH

# Path to your oh-my-zsh installation.
export ZSH="$HOME/.oh-my-zsh"

# Set name of the theme to load --- if set to "random", it will
# load a random theme each time oh-my-zsh is loaded, in which case,
# to know which specific one was loaded, run: echo $RANDOM_THEME
# See https://github.com/ohmyzsh/ohmyzsh/wiki/Themes
# ZSH_THEMEを"powerlevel10k/powerlevel10k"に変更
ZSH_THEME="powerlevel10k/powerlevel10k"
```

## zsh-autosuggestions
zshのターミナルのコマンド履歴に基づいてコマンド候補を表示、入力補完してくれるプラグイン

https://github.com/zsh-users/zsh-autosuggestions

1.  `zsh-autosuggestions`のGitリポジトリをホームディレクトリにクローン
```zsh
git clone https://github.com/zsh-users/zsh-autosuggestions ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-autosuggestions
```

2. ~/.zshrcを開いて`plugins`に`zsh-autosuggestions` を追加
```zsh
plugins=(git zsh-autosuggestions)
```

## zsh-syntax-highlighting
zshのターミナルのコマンドにハイライトが効く(色付けされる)プラグイン

https://github.com/zsh-users/zsh-syntax-highlighting

1.  `zsh-syntax-highlighting`のGitリポジトリをホームディレクトリにクローン
```zsh
git clone https://github.com/zsh-users/zsh-syntax-highlighting.git ${ZSH_CUSTOM:-~/.oh-my-zsh/custom}/plugins/zsh-syntax-highlighting
```
2. ~/.zshrcを開いて`plugins`に`zsh-syntax-highlighting` を追加
```zsh
plugins=(git zsh-autosuggestions zsh-syntax-highlighting)
```

### おまけ(さらにカラフルに)

下記を追記するとさらにカラフルにできる

![スクリーンショット 2024-02-28 13.30.00.png](https://qiita-image-store.s3.ap-northeast-1.amazonaws.com/0/625980/15956083-5a93-7aa4-547a-324eaa79f28c.png)

```.zshrc
# 下記を追記
ZSH_HIGHLIGHT_HIGHTLIGHTERS=(main brackets cursor root)
## 連想配列
typeset -A ZSH_HIGHLIGHT_STYLES
# ブラケット
# マッチしない括弧
ZSH_HIGHLIGHT_STYLES[bracket-error]='fg=red,bold'
# 括弧の階層
ZSH_HIGHLIGHT_STYLES[bracket-level-1]='fg=blue,bold'
ZSH_HIGHLIGHT_STYLES[bracket-level-2]='fg=green,bold'
ZSH_HIGHLIGHT_STYLES[bracket-level-3]='fg=magenta,bold'
ZSH_HIGHLIGHT_STYLES[bracket-level-4]='fg=yellow,bold'
ZSH_HIGHLIGHT_STYLES[bracket-level-5]='fg=cyan,bold'
# カーソルがある場所にマッチする括弧
ZSH_HIGHLIGHT_STYLES[cursor-matchingbracket]='standout'
# カーソル
ZSH_HIGHLIGHT_STYLES[cursor]='bg=blue'
# ルートユーザ
ZSH_HIGHLIGHT_STYLES[root]='bg=red'弧の色を変える
```
    
## まとめ
ターミナルは楽しく使いましょう

## 参考文献
https://ohmyz.sh/

https://github.com/romkatv/powerlevel10k

https://zenn.dev/luvmini511/articles/8d427e1faa089f

https://wonderwall.hatenablog.com/entry/2016/06/25/205033
