# CONTRIBUTING

## 目的

このリポジトリは、Qiita記事をGitHubで管理し、レビューを通して品質を担保したうえでQiitaへ反映するための運用基盤です。

## 初期セットアップ

1. Node.js 20系を用意する
1. 依存関係をインストールする

```bash
pnpm install
```

1. Qiita CLIをインストールする（未導入の場合）

```bash
npm install -g @qiita/qiita-cli
```

1. Qiitaアクセストークンを発行し、CLIを初期化する

```bash
qiita init
```

1. 投稿済み記事を取得する

```bash
qiita pull
```

## 日々の執筆フロー

1. ブランチを作成する
1. `public/`配下のMarkdownを編集する
1. ローカルで確認する

```bash
qiita preview
```

1. Lintを実行する

```bash
pnpm run lint
```

1. コミットしてPull Requestを作成する
1. レビュー完了後に`main`へマージする
1. Qiitaへ反映する

```bash
qiita push
```

## CIの内容

- `Lint Markdown`: `markdownlint` と `textlint` を実行
- `Check Links`: Markdown内リンクの有効性を検査（PR時 + 毎日1回の定期実行）

## 運用ルール

- 原則として直接`main`にpushしない
- 1記事1PRを基本とする
- タイトルとタグの表記ゆれを避ける
- 破壊的な一括置換は避け、小さな差分でレビューしやすくする
