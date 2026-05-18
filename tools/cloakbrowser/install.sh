#!/bin/bash
set -e

echo "=== CloakBrowser installer ==="

source "$(dirname "$0")/config/env.sh"

echo "Installing/updating cloakbrowser pip package..."
pip install -U cloakbrowser 2>&1 | tail -1

echo "Downloading stealth Chromium binary..."
python3 -m cloakbrowser install 2>&1 | tail -3

CB_DIR="$CLOAKBROWSER_CACHE_DIR"
if [ -z "$CB_DIR" ]; then
    CB_DIR="/tmp/cloakbrowser"
fi
BIN_DIR="$CB_DIR/chromium-"*""
CHROME=$(ls -d $BIN_DIR 2>/dev/null | head -1)

if [ -z "$CHROME" ] || [ ! -f "$CHROME/chrome" ]; then
    echo "ERROR: Chromium binary not found in $CB_DIR"
    exit 1
fi

echo "Setting up crashpad wrapper..."
mkdir -p /tmp/crashpad_db
if [ -f "$CHROME/chrome_crashpad_handler.real" ]; then
    echo "  crashpad wrapper already exists, skipping"
else
    mv "$CHROME/chrome_crashpad_handler" "$CHROME/chrome_crashpad_handler.real"
    cat > "$CHROME/chrome_crashpad_handler" << 'WRAPPER'
#!/bin/bash
exec "$(dirname "$0")/chrome_crashpad_handler.real" --database=/tmp/crashpad_db "$@"
WRAPPER
    chmod +x "$CHROME/chrome_crashpad_handler"
    echo "  crashpad wrapper created"
fi

echo ""
echo "=== Done ==="
echo "Quick test:  ./tools/cloakbrowser/bin/test.sh"
echo "TV screenshot: python3 tools/cloakbrowser/workflows/tv_screenshot.py BITGET:DOTUSDT 1D"
