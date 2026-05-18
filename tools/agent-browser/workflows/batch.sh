#!/bin/bash
# batch.sh - Batch execution для сложных сценариев
# Пакетное выполнение команд (избегает overhead на каждый запрос)

URL="${1:-https://example.com}"
shift
COMMANDS=("$@")

echo "=== agent-browser Batch Workflow ==="
echo "URL: $URL"
echo "Commands: ${COMMANDS[*]:-snapshot -i}"
echo ""

# Формируем команду
if [ ${#COMMANDS[@]} -eq 0 ]; then
    agent-browser batch "open $URL" "snapshot -i"
else
    agent-browser batch "open $URL" "${COMMANDS[@]}"
fi

echo ""
echo "=== Batch Complete ==="