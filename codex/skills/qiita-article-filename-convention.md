# qiita-article-filename-convention

## 目的

Qiita記事をUUID風ではなく、内容が分かるファイル名で作成する。

## 命名ルール

1. `kebab-case` を使う
2. 英小文字・数字・ハイフンのみを使う
3. 先頭末尾にハイフンを置かない
4. ハイフンの連続を避ける
5. 長さはおおむね60文字以内に収める

## 実行手順

1. 記事タイトルからslug候補を3案作る
2. `public/*.md` の重複を確認する
3. 命名ルールを満たす候補を選ぶ
4. `pnpm exec qiita new <slug>` を実行する
5. Front Matter（`title`, `tags`, `private`）を更新する

## ガードレール

- 新規記事でUUID風ファイル名を使わない
- 日本語やスペースをファイル名に含めない
- 既存公開記事のファイル名は安易に変更しない
- 既存記事のFront Matterにある `id` は絶対に更新しない
