#!/bin/bash
# Playwright environment
SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
export PLAYWRIGHT_BROWSERS_PATH="${PLAYWRIGHT_BROWSERS_PATH:-/home/user_aioc/workspace/tools/browser-temp/browsers}"
export LD_LIBRARY_PATH="/home/user_aioc/workspace/tools/browser-temp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
