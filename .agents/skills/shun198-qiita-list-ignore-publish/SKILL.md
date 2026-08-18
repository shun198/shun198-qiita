---
name: shun198-qiita-list-ignore-publish
description: Front MatterにignorePublish trueを持つQiita記事を抽出し、ファイル名、タイトル、公開範囲、更新日、タグをMarkdown表で一覧表示する依頼で使う。
---

# Qiita List Ignore Publish

## Workflow

1. リポジトリルートで次を実行する

   ```bash
   python3 scripts/list_ignore_publish_articles.py
   ```

2. `public/*.md`から`ignorePublish: true`の記事だけが抽出されたことを確認する
3. ファイル名、タイトル、private、更新日、タグをMarkdown表で返す

## Guardrails

- 読み取り専用タスクとして扱い、記事を変更しない
- 該当記事がない場合は、その旨を明確に返す
