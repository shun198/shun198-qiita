---
name: shun198-qiita-cli-login-preview
description: Qiita CLIで記事執筆に必要なログインとpreview運用を進める。初期設定、認証、preview起動、トラブルシュート、pull/publish前の確認依頼で使う。
---

# Qiita CLI Login And Preview

## Instructions

1. Node.js 20.0.0以上であることを確認する
2. `@qiita/qiita-cli` をインストールし、`qiita.config.json` があるか確認する
3. トークン権限は `read_qiita` と `write_qiita` を前提にする
4. `qiita login` を実行し、認証状態を確認する
5. `qiita preview` を起動し、`host` / `port` 設定に従って画面表示を確認する
6. preview起動時に同期される記事の差分を確認し、ローカル編集と競合しないようにする

## Standard Commands

```bash
npx qiita init
npx qiita login
npx qiita preview
npx qiita pull
```

## Safety Rules

- 公開操作は自動実行しない（`publish` / `push` はユーザー確認後のみ）
- API操作時は下書き運用を優先し、公開可否を明示する
- 認証情報ファイル（`credentials.json`）はコミット対象から除外する

## Config And Options

- `--credential <dir>`: 認証情報ディレクトリを明示
- `--config <dir>`: `qiita.config.json` の配置先を明示
- `--root <dir>`: 記事ルート（`public` を含む）を明示
- `--verbose`: トラブル時に詳細ログを出力

## Failure Playbook

1. `qiita` コマンドが見つからない: `@qiita/qiita-cli` の導入方法を確認する
2. `pull` できない: `qiita.config.json` の存在と `qiita login` 実施有無を確認する
3. previewが見えない: `host` / `port` の衝突とファイアウォールを確認する
4. 同期差分が不自然: `qiita pull --force` の実行可否を確認してから実施する

## Checklist

- [ ] Node.jsのバージョン要件を満たしている
- [ ] `qiita init` 済みで `qiita.config.json` がある
- [ ] `qiita login` 済みで認証できている
- [ ] `qiita preview` でブラウザ表示できる
- [ ] `public/` 配下の同期結果を確認した
- [ ] 公開操作はユーザー承認後に限定している
