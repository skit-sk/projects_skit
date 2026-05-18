#!/bin/bash
# Playwright environment
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-$SCRIPT_DIR/browsers}"
export LD_LIBRARY_PATH="$SCRIPT_DIR/lib:$LD_LIBRARY_PATH"
