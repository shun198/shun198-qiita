---
name: shun198-md-lint-after-create
description: Markdownファイル作成・更新後に、このリポジトリのmarkdownlintとtextlintを対象ファイル単位で実行する。Qiita記事やREADMEを編集し、lintエラーの修正と再検証が必要なときに使う。
---

# Markdown Lint After Create

## Workflow

1. 変更したMarkdownファイルを特定する
2. 対象ファイルごとに次のコマンドを実行する

   ```bash
   CI=true pnpm exec markdownlint-cli2 "<file>.md"
   CI=true pnpm exec textlint "<file>.md"
   ```

3. エラーがあれば修正する
4. 同じコマンドを再実行し、両方の成功を確認する

## Guardrails

- 対象ファイルを限定し、不要な全量lintを避ける
- lint失敗を無視して完了扱いにしない
- 既存記事のFront Matterにある`id`を変更しない
