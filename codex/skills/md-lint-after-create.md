# md-lint-after-create

## 目的

Markdownファイルを作成・更新した直後に、必ずlint checkを実行する。

## 実行コマンド

変更対象が `<file>.md` の場合は次を実行する。

```bash
CI=true pnpm exec markdownlint-cli2 "<file>.md"
CI=true pnpm exec textlint "<file>.md"
```

## 手順

1. 変更したMarkdownファイルを特定する
2. `markdownlint-cli2` を対象ファイルへ実行する
3. `textlint` を対象ファイルへ実行する
4. エラーを修正する
5. 両方成功するまで再実行する

## ガードレール

- 原則は対象ファイル単位でlintする
- lint失敗を無視して完了扱いにしない
- 既存記事の Front Matter `id` は更新しない
