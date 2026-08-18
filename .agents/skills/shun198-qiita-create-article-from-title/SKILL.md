---
name: shun198-qiita-create-article-from-title
description: ユーザーが指定したタイトルから、ファイル名、Front Matter、推定タグ、本文テンプレートを備えたQiita下書きを生成する。新しい記事ファイルの作成依頼で使う。
---

# Qiita Create Article From Title

## Workflow

1. ユーザーから記事タイトルを受け取る
2. リポジトリルートで次を実行する

   ```bash
   python3 scripts/create_qiita_article.py --title "<記事タイトル>"
   ```

3. 生成されたファイルパス、タイトル、推定タグを確認する
4. `private: false`、`ignorePublish: true`、`id: null`の初期値を維持する
5. `shun198-md-lint-after-create`に従って生成ファイルを検証する

## Guardrails

- 既存記事ファイルを上書きしない
- 既存記事のFront Matterにある`id`を変更しない
- 記事作成時にQiitaへのpublishやpushを実行しない
