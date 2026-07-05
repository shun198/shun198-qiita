---
name: shun198-qiita-publish-with-approval
description: Qiitaへの投稿・反映を実行する。publish/push実行前に必ずユーザー承認を取得し、対象記事・公開範囲・実行コマンドを明示してから進める依頼で使う。
---

# Qiita Publish With Approval

## Mandatory Approval Rule

1. `qiita publish` / `qiita push` / GitHub Actions経由の反映を実行する前に、必ずユーザー承認を取る
2. 承認取得時は以下を明示する
   - 対象記事（ファイル名 or `--all`）
   - 公開範囲（公開 / 限定共有）
   - 実行コマンド（例: `npx qiita publish xxx`）
3. ユーザーが明示的に「実行してよい」と回答するまで、投稿系コマンドは実行しない
4. 承認が曖昧な場合は再確認する（推測で実行しない）

## Safe Workflow

1. 対象記事のFront Matterを確認する（`title`, `tags`, `private`, `id`）
2. `qiita preview` で最終確認する
3. 投稿対象とコマンドを提示して承認を取得する
4. 承認後にのみ `qiita publish` または `qiita push` を実行する
5. 実行結果（成功 / 失敗、反映対象）を報告する

## Preflight Checklist

- [ ] 記事内容の最終確認が完了している
- [ ] `private` の意図（公開 or 限定共有）が明確
- [ ] 誤って `--all` を使わないことを確認
- [ ] 実行前にユーザー承認を取得した

## Postflight Checklist

- [ ] 実行コマンドを記録した
- [ ] 反映結果を共有した
- [ ] 想定外の記事が反映されていないことを確認した

## Prohibited Behavior

- ユーザー承認前に投稿系コマンドを実行しない
- 「たぶんOK」などの推測で公開しない
- 対象が不明なまま `--all` を使わない
