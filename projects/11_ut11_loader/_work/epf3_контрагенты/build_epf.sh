#!/usr/bin/env bash
# Сборка ВыгрузкаКонтрагентов_v1.epf из исходников через v8unpack.
# Зависимости: venv с v8unpack (workspace/venv).
set -euo pipefail

ROOT="/home/user_aioc/workspace/projects/11_ut11_loader/_work/epf3_контрагенты"
SRC="$ROOT/build"
DST_BASE="$ROOT/ВыгрузкаКонтрагентов_v1.epf"
DST_FINAL="/home/user_aioc/workspace/projects/11_ut11_loader/_work/ВыгрузкаКонтрагентов_v1.epf"

if [ ! -d "$SRC" ]; then
    echo "Нет каталога исходников: $SRC" >&2
    exit 1
fi

# shellcheck disable=SC1091
source /home/user_aioc/workspace/venv/bin/activate

v8unpack -B "$SRC" "$DST_BASE"
cp "$DST_BASE" "$DST_FINAL"

echo "OK -> $DST_FINAL ($(stat -c%s "$DST_FINAL") bytes)"
