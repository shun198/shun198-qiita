# shun198-qiita

Qiita記事をGitHubで管理し、レビューとCIを通して安全に運用するためのリポジトリです。

## セットアップ

前提は次のとおりです。

- Node.js 20.0.0以上
- pnpm 11系

```bash
pnpm install
```

Qiita CLIの初期化とログインは次のコマンドで行います。

```bash
pnpm exec qiita init
pnpm exec qiita login
```

## よく使うコマンド

### Makefile経由（推奨）

```bash
make help
make setup
make init
make login
make preview
make pull
make lint
```

### pnpm経由

```bash
pnpm run lint
pnpm run qiita:pull
pnpm exec qiita preview
```

## 記事編集後の標準lint

Markdownを作成・更新した直後は、対象ファイルを指定して次を実行します。

```bash
CI=true pnpm exec markdownlint-cli2 "public/<file>.md"
CI=true pnpm exec textlint "public/<file>.md"
```

エラーが出た場合は修正後に同じコマンドを再実行し、両方が成功するまで繰り返します。

## 執筆から反映まで

1. `public/` 配下の記事を編集
2. `make preview` で表示確認
3. `make lint` で品質チェック
4. PRを作成してレビュー
5. `main` 反映後にQiitaへ投稿

## 投稿時の注意

- 投稿系コマンド（`qiita publish` / `qiita push`）は必ず事前承認を取る
- `--all` は対象を明確化できる場合だけ使う
- 認証情報ファイルはコミットしない
- 既存記事のFront Matterにある `id` は絶対に更新しない

## Agent Skills

このリポジトリで共通利用するAgent Skillは、`.agents/skills/`を正本として管理します。
Skillごとにディレクトリを作成し、frontmatter付きの`SKILL.md`を配置してください。
エージェント別のディレクトリへ同じSkillを複製しないでください。

## CI

- `lint.yml`: markdownlint + textlint
- `lint-check.yml`: lycheeによるリンクチェック
