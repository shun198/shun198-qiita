# qiita-cli-login-preview

## Goal

Set up reliable Qiita article writing workflow with login and preview using Qiita CLI.

## Core Flow

1. Confirm Node.js 20.0.0+ is available
2. Install `@qiita/qiita-cli`
3. Initialize config with `npx qiita init`
4. Login with `npx qiita login` using a token with `read_qiita` and `write_qiita`
5. Start preview with `npx qiita preview`
6. Sync remote articles with `npx qiita pull` when needed

## Safety Rules

- Never auto-publish without user confirmation
- Keep credentials out of git history
- Prefer draft-first operation until final manual publish

## Useful Options

- `--credential <dir>`: custom credentials location
- `--config <dir>`: custom config directory
- `--root <dir>`: custom article root directory
- `--verbose`: detailed logs for troubleshooting

## Troubleshooting

1. Command not found: verify package installation path
2. Pull fails: verify `qiita.config.json` and login state
3. Preview unavailable: check host/port conflict
4. Drift from remote: review then use `npx qiita pull --force` only when intended
