#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "${ROOT_DIR}"

if ! command -v qiita >/dev/null 2>&1; then
  echo "Error: qiita command is not found."
  echo "Install it with: npm install -g @qiita/qiita-cli"
  exit 1
fi

if [ ! -f "qiita.config.json" ]; then
  echo "Error: qiita.config.json is not found."
  echo "Run 'qiita init' first, then retry."
  exit 1
fi

echo "Pulling articles from Qiita..."
qiita pull
echo "Done. Articles are synced to this repository."
