#!/usr/bin/env bash
set -euo pipefail

VENV=".venv"

if ! command -v python3 >/dev/null 2>&1; then
  echo "Python3 is required but was not found in PATH."
  exit 1
fi

if [ -d "$VENV" ]; then
  echo "Activating existing virtualenv: $VENV"
  source "$VENV/bin/activate"
else
  echo "Creating virtualenv: $VENV"
  python3 -m venv "$VENV"
  source "$VENV/bin/activate"
fi

if [ -f requirements.txt ]; then
  echo "Installing dependencies from requirements.txt..."
  pip install -r requirements.txt
else
  echo "No requirements.txt found. Skipping dependency installation."
fi

echo "Environment prepared. Virtualenv located at $VENV."
