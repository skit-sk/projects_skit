#!/bin/bash
# basic.sh - Базовый AI-agent workflow
# Открыть URL → Snapshot → готов к взаимодействию

URL="${1:-https://example.com}"

echo "=== agent-browser Basic Workflow ==="
echo "URL: $URL"
echo ""

# Открыть страницу
echo "[1/2] Opening $URL..."
agent-browser open "$URL"

# Snapshot интерактивных элементов
echo "[2/2] Taking snapshot..."
agent-browser snapshot -i

echo ""
echo "=== Ready for interaction ==="
echo "Use: agent-browser click @eN, fill @eN \"text\", etc."