#!/bin/bash
# screenshot.sh - Screenshot с аннотациями
# Аннотированный скриншот с нумерованными метками элементов

URL="${1:-https://example.com}"
OUTPUT="${2:-screenshot.png}"
ANNOTATE="${3:---annotate}"

echo "=== agent-browser Screenshot Workflow ==="
echo "URL: $URL"
echo "Output: $OUTPUT"
echo ""

# Открыть страницу
echo "[1/2] Opening $URL..."
agent-browser open "$URL"

# Screenshot с аннотациями
echo "[2/2] Taking annotated screenshot..."
agent-browser screenshot $ANNOTATE "$OUTPUT"

echo ""
echo "=== Screenshot saved to: $OUTPUT ==="
echo "Use agent-browser click @eN to interact with labeled elements"