---
name: shun198-qiita-article-filename-convention
description: Qiita記事作成時にUUIDではなく直感的なファイル名で管理する。記事タイトルからslugを作成し、命名ルールチェックと重複確認をしてから `qiita new` を実行する依頼で使う。
---

# Qiita Article Filename Convention

## Goal

記事作成時に、どの記事か直感的に分かるMarkdownファイル名で運用する。

## Naming Rules

1. ファイル名は `kebab-case` を使う
2. 英小文字・数字・ハイフンのみを許可する
3. 先頭と末尾にハイフンを置かない
4. 連続ハイフンを使わない
5. 目安は 60 文字以内に収める
6. 拡張子は `.md`（`qiita new` 実行時は拡張子なしベース名）

## Recommended Patterns

- `<topic>-<purpose>`
- `<tool>-<how-to>`
- `<yyyymmdd>-<topic>`

Examples:

- `github-actions-service-container`
- `terraform-oidc-deploy`
- `20260705-fastapi-jwt-auth`

## Workflow

1. 記事タイトルと対象読者を確認する
2. タイトルから候補slugを3案作る
3. 既存の `public/*.md` と重複しないか確認する
4. ルール違反がない候補を1つ選ぶ
5. `npx qiita new <slug>` または `pnpm exec qiita new <slug>` を実行する
6. 生成ファイルを開いてFront Matterを更新する

## Guardrails

- UUID形式のファイル名を新規作成に使わない
- 日本語やスペースをファイル名に含めない
- 既存記事のファイル名を安易に変更しない（Qiita連携切れ防止）

## Checklist

- [ ] ファイル名が `kebab-case`
- [ ] slugが記事内容を表している
- [ ] `public` 配下で重複していない
- [ ] `qiita new` で作成できる文字種になっている
- [ ] Front Matter の `title` と内容が一致している
