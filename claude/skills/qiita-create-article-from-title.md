# qiita-create-article-from-title

## 目的

ユーザーが入力した記事タイトルから、タイトル連動の Markdown ファイル名、Front Matter の `title`、テンプレート本文、自動推定タグ付きの Qiita 下書きを作成する。

## 実行コマンド

```bash
python3 scripts/create_qiita_article.py --title "<記事タイトル>"
```

## 手順

1. ユーザーから記事タイトルを受け取る
2. リポジトリルートで補助スクリプトを実行する
3. 生成されたファイルパスと推定タグを確認する
4. 生成時の初期値 `private: false`、`ignorePublish: true`、`id: null` を維持する
5. 生成したファイルに対して対象限定の lint を実行する

## 生成内容

- ファイル配置先: `public/<タイトル由来のファイル名>.md`
- Front Matter の `title`: ユーザー入力タイトルをそのまま反映
- Front Matter の `tags`: タイトル中のキーワードから自動推定
- 本文テンプレート:
  - `## 概要`
  - `## 前提`
  - `## 構成`
  - `## 実装`
  - `## 実際に検証してみよう`
  - `## まとめ`
  - `## 参考`

## 作成後チェック

生成した `<file>.md` に対して次を実行する。

```bash
CI=true pnpm exec markdownlint-cli2 "public/<file>.md"
CI=true pnpm exec textlint "public/<file>.md"
```

## ガードレール

- 既存記事ファイルを上書きしない
- 既存記事の `id` は変更しない
- 記事作成時に Qiita への publish / push は行わない
- 推定タグの修正は、タイトル文脈から明らかに不適切な場合だけに留める
