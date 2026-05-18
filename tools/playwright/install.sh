#!/bin/bash
set -e

echo "=== Playwright installer ==="
echo "Installing playwright Python package..."

source "$(dirname "$0")/config/env.sh" 2>/dev/null || true

pip install playwright 2>/dev/null | tail -1

echo "Downloading Chromium browser..."
python3 -m playwright install chromium 2>&1 | tail -3

echo ""
echo "=== Done ==="
echo "Run test:  python3 tools/playwright/workflows/basic.py"
