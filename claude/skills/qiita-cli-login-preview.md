# qiita-cli-login-preview

## 目的

Qiita CLIで記事執筆に必要なログインとプレビュー環境を安定して運用する。

## 基本フロー

1. Node.js 20.0.0以上を確認する
2. `@qiita/qiita-cli` を導入する
3. `npx qiita init` で設定ファイルを生成する
4. `npx qiita login` でトークン認証する（`read_qiita` / `write_qiita`）
5. `npx qiita preview` でプレビューを起動する
6. 必要に応じて `npx qiita pull` で記事を同期する

## 運用ルール

- ユーザー確認なしで公開操作をしない
- 認証情報はGit管理に含めない
- 公開前は下書きベースで確認を進める
- 記事Front Matterの `id` は絶対に更新しない

## 主要オプション

- `--credential <dir>`: 認証情報の配置先
- `--config <dir>`: 設定ファイルの配置先
- `--root <dir>`: 記事ルートの指定
- `--verbose`: 詳細ログ出力

## トラブルシュート

1. コマンド未検出: パッケージ導入とPATHを確認する
2. pull失敗: `qiita.config.json` とログイン状態を確認する
3. preview未表示: `host` / `port` 競合を確認する
4. 同期差分が不正: 意図を確認して `npx qiita pull --force` を検討する
