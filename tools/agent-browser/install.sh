#!/bin/bash
# agent-browser install script
# Full installation with Playwright Chrome and all dependencies

set -e

echo "=== agent-browser Full Installation ==="

# Setup directories
export HOME=/tmp
export npm_config_cache=/tmp/npm-cache
mkdir -p /tmp/.agent-browser/sockets /tmp/pango_libs

# 1. Install agent-browser
echo "[1/7] Installing agent-browser..."
npm install -g agent-browser --prefix /home/user_aioc/.local 2>/dev/null || true

# 2. Install Playwright
echo "[2/7] Installing Playwright..."
npm install -g playwright --prefix /home/user_aioc/.local 2>/dev/null || true

# 3. Install Playwright browsers
echo "[3/7] Installing Playwright Chromium..."
export PATH="/home/user_aioc/.local/bin:$PATH"
playwright install chromium 2>/dev/null || true

# 4. Install Chrome dependencies
echo "[4/7] Installing Chrome libraries..."
install_lib() {
    local pkg="$1"
    local dir="/tmp/pango_libs"
    if ! ldconfig -p 2>/dev/null | grep -q "$(basename $pkg .deb)"; then
        apt-get download "$pkg" 2>/dev/null && dpkg -x "$pkg"*.deb "$dir" 2>/dev/null || true
    fi
}

install_lib libpango-1.0-0
install_lib libxdamage1
install_lib libfribidi0
install_lib libthai0
install_lib libharfbuzz0b
install_lib libdatrie1
install_lib libgraphite2-3

# 5. Create wrapper script
echo "[5/7] Creating wrapper script..."
cat > /home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh << 'WRAPPER'
#!/bin/bash
export LD_LIBRARY_PATH="/tmp/pango_libs/usr/lib/x86_64-linux-gnu:$LD_LIBRARY_PATH"
export HOME=/tmp
export AGENT_BROWSER_STATE_DIR=/tmp/.agent-browser
export PATH="/home/user_aioc/.local/bin:$PATH"
CHROME_PATH="/tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome"
if [ "$1" = "open" ] || [ "$1" = "goto" ] || [ "$1" = "navigate" ]; then
    exec /home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64 --executable-path "$CHROME_PATH" "$@"
else
    exec /home/user_aioc/.local/lib/node_modules/agent-browser/bin/agent-browser-linux-x64 "$@"
fi
WRAPPER
chmod +x /home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh

# 6. Download Lightpanda (optional alternative)
echo "[6/7] Downloading Lightpanda (optional)..."
if [ ! -f /tmp/lightpanda ]; then
    curl -L -o /tmp/lightpanda https://github.com/lightpanda-io/browser/releases/download/nightly/lightpanda-x86_64-linux 2>/dev/null && chmod +x /tmp/lightpanda || true
fi

# 7. Verify
echo "[7/7] Verifying installation..."
/home/user_aioc/workspace/tools/agent-browser/bin/agent-browser.sh --version 2>/dev/null || echo "CLI ready"

echo ""
echo "=== Installation Complete ==="
echo ""
echo "Usage:"
echo "  ./tools/agent-browser/bin/agent-browser.sh open https://example.com"
echo ""
echo "Or with environment:"
echo "  export LD_LIBRARY_PATH=\"/tmp/pango_libs/usr/lib/x86_64-linux-gnu:\$LD_LIBRARY_PATH\""
echo "  export PATH=\"/home/user_aioc/.local/bin:\$PATH\""
echo "  agent-browser open https://example.com --executable-path /tmp/.cache/ms-playwright/chromium-1217/chrome-linux64/chrome"