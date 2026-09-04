---
name: shun198-qiita-article-filename-convention
description: Qiita記事の新規作成時に、タイトルから内容が分かるkebab-caseのslugを作り、重複確認後にqiita newを実行する。UUID風のファイル名を避けたいときに使う。
---

# Qiita Article Filename Convention

## Naming Rules

1. 英小文字・数字・ハイフンによる`kebab-case`を使う
2. 先頭末尾や連続したハイフンを避ける
3. おおむね60文字以内に収める
4. `public/*.md`と重複しない名前を選ぶ

## Workflow

1. 記事タイトルからslug候補を3案作る
2. 既存記事との重複と命名ルールを確認する
3. 最適な候補を選び、次を実行する

   ```bash
   pnpm exec qiita new <slug>
   ```

4. 生成ファイルのFront Matterにある`title`、`tags`、`private`を確認する

## Guardrails

- 新規記事でUUID風、日本語、空白を含むファイル名を使わない
- 公開済みの記事ファイル名を安易に変更しない
- 既存記事のFront Matterにある`id`を変更しない
