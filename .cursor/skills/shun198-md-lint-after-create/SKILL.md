---
name: shun198-md-lint-after-create
description: Markdownファイル作成・更新後に必ずlint checkを実行する。Qiita記事やREADME編集後に markdownlint と textlint を対象ファイル単位で実行し、失敗時に修正して再実行する依頼で使う。
disable-model-invocation: true
---

# Markdown Lint After Create

## Rule

Markdownファイルを新規作成または更新した直後に、必ずlint checkを実行する。

## Required Commands

対象ファイルが `<file>.md` の場合、次の順で実行する。

```bash
CI=true pnpm exec markdownlint-cli2 "<file>.md"
CI=true pnpm exec textlint "<file>.md"
```

## Workflow

1. 変更したMarkdownファイルのパスを特定する
2. `markdownlint-cli2` を対象ファイルに対して実行する
3. `textlint` を対象ファイルに対して実行する
4. エラーがあれば修正する
5. 修正後に同じ2コマンドを再実行して成功を確認する

## Guardrails

- 対象ファイルを限定して実行する（不要な全量lintを避ける）
- lint失敗を無視して作業完了にしない
- 既存記事の Front Matter `id` は絶対に更新しない

## Checklist

- [ ] 変更したMarkdownファイルを特定した
- [ ] `markdownlint-cli2` が成功した
- [ ] `textlint` が成功した
- [ ] 失敗時の修正と再実行を完了した
