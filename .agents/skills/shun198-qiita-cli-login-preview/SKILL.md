---
name: shun198-qiita-cli-login-preview
description: このリポジトリでQiita CLIの初期設定、ログイン、preview、pullを実行・トラブルシュートする。記事執筆環境の準備や表示確認が必要なときに使う。
---

# Qiita CLI Login And Preview

## Workflow

1. Node.js 20.0.0以上と依存関係の導入状況を確認する
2. `qiita.config.json`の存在を確認する
3. 必要に応じて次のコマンドを実行する

   ```bash
   pnpm exec qiita init
   pnpm exec qiita login
   pnpm exec qiita preview
   pnpm exec qiita pull
   ```

4. previewの表示と`public/`配下の同期差分を確認する

## Troubleshooting

1. コマンドが見つからない場合は依存関係とNode.jsのバージョンを確認する
2. pullに失敗する場合は設定ファイルとログイン状態を確認する
3. previewを表示できない場合はhost、port、競合プロセスを確認する
4. `pull --force`はローカル差分への影響を提示し、ユーザー承認後にだけ実行する

## Guardrails

- publishやpushはユーザー承認なしに実行しない
- 認証情報をGit管理へ追加しない
- 既存記事のFront Matterにある`id`を変更しない
