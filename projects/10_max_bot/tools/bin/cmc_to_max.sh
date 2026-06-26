#!/bin/bash
# cmc_to_max.sh — full pipeline: CoinMarketCap screenshot → MAX bot
#
# Usage:
#   ./bin/cmc_to_max.sh                     # screenshot + send (auto-name)
#   ./bin/cmc_to_max.sh /path/out.png      # explicit output path
#   ./bin/cmc_to_max.sh --no-send /path    # screenshot only
#   ./bin/cmc_to_max.sh --keep            # don't delete after send

set -e

SCRIPT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/../../../.." && pwd)"

source "$WORKSPACE/tools/cloakbrowser/config/env.sh"

KEEP=0
NO_SEND=0
EXPLICIT_PATH=""

for arg in "$@"; do
    case "$arg" in
        --keep)   KEEP=1 ;;
        --no-send) NO_SEND=1 ;;
        *)        EXPLICIT_PATH="$arg" ;;
    esac
done

# Step 1: screenshot
if [ -n "$EXPLICIT_PATH" ]; then
    python3 "$SCRIPT_DIR/cmc_screenshot.py" "$EXPLICIT_PATH"
    LATEST="$EXPLICIT_PATH"
else
    python3 "$SCRIPT_DIR/cmc_screenshot.py"
    LATEST=$(ls -t "$SCRIPT_DIR/tmp/"cmc_*.png 2>/dev/null | head -1)
fi

if [ -z "$LATEST" ] || [ ! -f "$LATEST" ]; then
    echo "ERROR: no screenshot produced"
    exit 1
fi

if [ "$NO_SEND" = "1" ]; then
    echo "Screenshot saved: $LATEST"
    exit 0
fi

# Step 2: send to MAX
source "$WORKSPACE/scripts/source_env.sh" 2>/dev/null || true
python3 "$WORKSPACE/tools/scripts/send_to_max.py" "$LATEST" "" \
    "📊 CoinMarketCap — $(basename "$LATEST")"

# Step 3: cleanup (optional)
if [ "$KEEP" = "0" ] && [ -z "$EXPLICIT_PATH" ]; then
    rm -f "$LATEST"
    echo "Cleaned up: $LATEST"
fi

echo "Done."
