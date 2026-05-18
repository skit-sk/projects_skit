#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
RUNNER="$SCRIPT_DIR/runner.py"
cd /home/user_aioc/workspace
exec python3 "$RUNNER" "$@"
