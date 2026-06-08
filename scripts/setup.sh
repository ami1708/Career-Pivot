#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

cd "$ROOT_DIR"

if [ ! -f .env ]; then
  cp .env.example .env
fi

python3 -m venv backend/.venv
source backend/.venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e "backend[test]"
python -m playwright install chromium

cd "$ROOT_DIR/frontend"
npm install

echo "Setup complete. Run: docker compose up --build"

