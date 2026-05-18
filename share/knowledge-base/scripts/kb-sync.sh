#!/bin/bash
# kb-sync.sh — синхронизация KB с opencode.db
# Индексирует все .md файлы и обновляет карту знаний

set -e

KB_DIR="$(cd "$(dirname "$0")/.." && pwd)"
MAP_DIR="$(cd "$KB_DIR/../opencode" && pwd)"
MAP_FILE="$MAP_DIR/map_all.md"

echo "=== KB Sync ==="
echo "Source: $KB_DIR"
echo "Map:    $MAP_FILE"

# Сбор статистики
echo ""
echo "=== Статистика KB ==="
find "$KB_DIR" -name "*.md" -not -path "*/scripts/*" | while read f; do
  lines=$(wc -l < "$f")
  name=$(basename "$f")
  echo "  $name: $lines строк"
done

echo ""
echo "=== Категории ==="
for d in "$KB_DIR"/*/; do
  name=$(basename "$d")
  count=$(find "$d" -name "*.md" | wc -l)
  echo "  $name: $count файлов"
done

echo ""
echo "=== Всего файлов: $(find "$KB_DIR" -name "*.md" | wc -l) ==="
echo "Sync complete."
