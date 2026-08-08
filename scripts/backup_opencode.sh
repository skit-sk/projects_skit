#!/bin/bash
# backup_opencode.sh — экспорт всех сессий opencode в workspace/sessions/ (персистентно)
# Защита от потери сессий при пересоздании контейнера.
#
# Usage: ./scripts/backup_opencode.sh [--clean-old] [--quiet]
#   --clean-old  удалить старые session-ses_*.json (кроме тех, что экспортированы сейчас)
#   --quiet      без вывода списка

set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WORKSPACE="$(cd "$SCRIPT_DIR/.." && pwd)"
SESSIONS_DIR="$WORKSPACE/sessions"
OPENCODE_BIN="${OPENCODE_BIN:-$HOME/.opencode/bin/opencode}"
CLEAN_OLD=0
QUIET=0

for arg in "$@"; do
  case "$arg" in
    --clean-old) CLEAN_OLD=1 ;;
    --quiet) QUIET=1 ;;
  esac
done

if [ ! -x "$OPENCODE_BIN" ]; then
  echo "❌ opencode не найден: $OPENCODE_BIN (задайте OPENCODE_BIN)"
  exit 1
fi

mkdir -p "$SESSIONS_DIR"

exported=0
fail=0

while IFS= read -r sid; do
  [ -z "$sid" ] && continue
  out="$SESSIONS_DIR/session-$sid.json"
  if "$OPENCODE_BIN" export "$sid" > "$out" 2>/dev/null && [ -s "$out" ]; then
    exported=$((exported + 1))
    [ "$QUIET" -eq 0 ] && echo "✅ $sid → $out"
  else
    fail=$((fail + 1))
    echo "❌ Ошибка экспорта $sid"
  fi
done < <("$OPENCODE_BIN" session list --format json 2>/dev/null | grep -o '"id": "[^"]*"' | cut -d'"' -f4)

if [ "$CLEAN_OLD" -eq 1 ]; then
  find "$SESSIONS_DIR" -maxdepth 1 -name 'session-ses_*.json' -mmin +1 -print0 2>/dev/null | while IFS= read -r -d '' f; do
    sid="$(basename "$f" | sed 's/^session-//; s/\.json$//')"
    if ! grep -q "$sid" < <("$OPENCODE_BIN" session list --format json 2>/dev/null); then
      rm -f "$f"
      [ "$QUIET" -eq 0 ] && echo "🗑 Удалён устаревший: $f"
    fi
  done
fi

echo "📦 Бэкап завершён: экспортировано $exported, ошибок $fail. Каталог: $SESSIONS_DIR"
[ "$fail" -eq 0 ] && exit 0 || exit 1
