#!/bin/bash
# quick-snapshot.sh - Быстрый snapshot с фильтрами
# Использует текущую открытую сессию или открывает URL

URL="${1:-}"
OUTPUT="${2:--}"

if [ -z "$URL" ]; then
    echo "Taking snapshot of current page..."
    if [ "$OUTPUT" = "-" ]; then
        agent-browser snapshot -i -c -d 5 --urls
    else
        agent-browser snapshot -i -c -d 5 --urls > "$OUTPUT"
        echo "Snapshot saved to: $OUTPUT"
    fi
else
    echo "Opening $URL and taking snapshot..."
    if [ "$OUTPUT" = "-" ]; then
        agent-browser batch "open $URL" "snapshot -i -c -d 5 --urls"
    else
        agent-browser batch "open $URL" "snapshot -i -c -d 5 --urls" > "$OUTPUT"
        echo "Snapshot saved to: $OUTPUT"
    fi
fi