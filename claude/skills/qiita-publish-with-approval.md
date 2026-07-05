# qiita-publish-with-approval

## 目的

Qiita投稿を安全に実行し、投稿系コマンドの実行前に必ずユーザー承認を取得する。

## 承認必須ルール

1. 投稿系コマンド実行前に、必ず明示的な承認を取る
2. 承認確認時は次を必ず提示する
   - 対象記事
   - 公開範囲（公開 / 限定共有）
   - 実行コマンド
3. 承認が明確になるまで実行しない
4. あいまいな返答の場合は再確認する

## 対象コマンド

- `npx qiita publish <article>`
- `npx qiita publish --all`
- `npx qiita push`
- 投稿につながるワークフロー実行

## 安全な実行手順

1. Front Matter（`title`, `tags`, `private`, `id`）を確認
2. previewで最終確認
3. 対象/公開範囲/コマンドを提示して承認取得
4. 承認後に実行
5. 実行結果と反映対象を報告
