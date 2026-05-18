#!/bin/bash
# source_env.sh — загружает .env из корня workspace
# Использование: source scripts/source_env.sh

set -a
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "${SCRIPT_DIR}/../.env" 2>/dev/null || {
    echo "Warning: .env not found at ${SCRIPT_DIR}/../.env" >&2
    return 1
}
set +a

echo "Environment loaded from .env"
