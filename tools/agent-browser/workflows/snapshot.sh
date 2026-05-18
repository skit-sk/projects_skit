#!/bin/bash
# snapshot.sh - Snapshot с оптимизацией для AI
# Экономия токенов: только интерактивные элементы

URL="${1:-https://example.com}"
DEPTH="${2:-5}"
COMPACT="${3:--c}"

echo "=== agent-browser Snapshot Workflow ==="
echo "URL: $URL"
echo "Depth: $DEPTH"
echo ""

# Открыть страницу
echo "[1/2] Opening $URL..."
agent-browser open "$URL"

# Snapshot с оптимизацией для AI
echo "[2/2] Taking optimized snapshot..."
agent-browser snapshot -i $COMPACT -d $DEPTH --urls

echo ""
echo "=== Snapshot Complete ==="
echo "Flags used: -i (interactive) $COMPACT (compact) -d $DEPTH (depth)"