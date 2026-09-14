#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "Creating .env from .env.example..."
  cp .env.example .env
fi

echo "Installing frontend dependencies..."
(cd frontend && npm install)

if [[ -f backend/pyproject.toml ]]; then
  echo "Installing backend dependencies with uv..."
  if ! command -v uv >/dev/null 2>&1; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="${HOME}/.local/bin:${PATH}"
  fi
  (cd backend && uv sync --group dev)
elif [[ -f backend/requirements.txt ]]; then
  echo "Installing backend dependencies from requirements.txt..."
  pip install -r backend/requirements.txt
else
  echo "No backend dependency file yet; skipping Python install."
fi

echo "DevContainer setup complete."
