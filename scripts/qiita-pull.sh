#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

QIITA_CMD=""
if command -v qiita >/dev/null 2>&1; then
  QIITA_CMD="qiita"
elif command -v pnpm >/dev/null 2>&1; then
  QIITA_CMD="pnpm exec qiita"
else
  echo "Error: qiita command is not found."
  echo "Install @qiita/qiita-cli or use pnpm in this repository."
  exit 1
fi

if [ ! -f "qiita.config.json" ]; then
  echo "Error: qiita.config.json is not found."
  echo "Run 'qiita init' first, then retry."
  exit 1
fi

echo "Pulling articles from Qiita..."
${QIITA_CMD} pull
echo "Done. Articles are synced to this repository."
