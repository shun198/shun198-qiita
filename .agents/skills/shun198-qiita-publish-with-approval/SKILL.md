---
name: shun198-qiita-publish-with-approval
description: Qiitaへのpublish、push、または投稿につながるワークフローを安全に実行する。対象記事、公開範囲、コマンドを提示し、ユーザーの明示承認を得て投稿するときに使う。
---

# Qiita Publish With Approval

## Mandatory Approval

投稿コマンドの実行直前に、次の情報を提示してユーザーの明示承認を得る。

- 対象記事または`--all`の対象範囲
- 公開または限定共有の公開範囲
- 実行する完全なコマンド

承認が曖昧な場合は実行しない。

## Workflow

1. 対象記事の`title`、`tags`、`private`、`id`を確認する
2. previewで記事を最終確認する
3. 対象、公開範囲、コマンドを提示して承認を得る
4. 承認後にだけpublishまたはpushを実行する
5. 実行結果と反映対象を報告する

## Guardrails

- ユーザー承認前に投稿系コマンドを実行しない
- 対象が不明なまま`--all`を使わない
- Front Matterにある`id`を変更しない
