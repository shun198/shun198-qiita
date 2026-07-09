# qiita-list-ignore-publish

## 目的

Front Matter に `ignorePublish: true` を持つ Qiita 記事を抽出し、Markdown の表で一覧表示する。

## 実行コマンド

```bash
python3 scripts/list_ignore_publish_articles.py
```

## 手順

1. リポジトリルートで補助スクリプトを実行する
2. `public/*.md` を読み取る
3. `ignorePublish: true` の記事だけを抽出する
4. ファイル名、タイトル、private、更新日、タグを Markdown 表で返す

## 出力形式

```markdown
| File | Title | Private | Updated | Tags |
| --- | --- | --- | --- | --- |
| ... | ... | ... | ... | ... |
```

## ガードレール

- 一覧化は読み取り専用タスクとして扱う
- 一覧表示のために記事内容を変更しない
- 該当記事がない場合は失敗ではなく、その旨を明確に返す
