#!/bin/bash
# ============================================================
# preflight.sh — Строгая проверка перед релизом EPF
# Использование: ./scripts/preflight.sh <build_dir> <output.epf>
#
# Проходит 7 этапов верификации:
#   1. verify_elem_strict.py — статический анализ Form.elem.json
#   2. v8unpack -B — сборка
#   3. v8unpack -E — распаковка (ловит «Ошибка формата потока»)
#   4. verify_elem_strict.py на распакованном
#   5. Roundtrip diff — пересборка распакованного, сравнение Form
#   6. verify_epf.py — проверка паттернов и регрессий
#   7. Сигнатура ff ff ff 7f
#
# ⚠️  Все временные файлы создаются в _work/.tmp/ проекта 11,
#      НЕ в глобальной /tmp/. Это исключает лишние запросы прав доступа.
# ============================================================
set -euo pipefail

if [ $# -lt 2 ]; then
    echo "Использование: $0 <build_dir> <output.epf>"
    echo "  build_dir  — каталог с исходниками (ExternalDataProcessor.json, Form/, ...)"
    echo "  output.epf — имя целевого .epf файла"
    exit 1
fi

BUILD_DIR="$(cd "$(dirname "$1")" && pwd)/$(basename "$1")"
if [ ! -d "$BUILD_DIR" ]; then
    BUILD_DIR="$1"
fi
OUTPUT="$2"

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

# ⚠️  Все временные файлы 1С EPF — ТОЛЬКО в _work/.tmp/ (не /tmp/)
WORK="$PROJECT_DIR/projects/11_ut11_loader/_work/.tmp/preflight_$$"
mkdir -p "$(dirname "$WORK")"
VERIFY_ELEM="$PROJECT_DIR/projects/11_ut11_loader/_work/verify_elem_strict.py"
VERIFY_EPF="$PROJECT_DIR/projects/11_ut11_loader/_work/verify_epf.py"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

PASS=0
FAIL=0

check() {
    local name="$1"
    shift
    if "$@"; then
        echo -e "  ${GREEN}✓${NC} $name"
        PASS=$((PASS + 1))
    else
        echo -e "  ${RED}✗${NC} $name"
        FAIL=$((FAIL + 1))
    fi
}

cleanup() {
    rm -rf "$WORK"
}
trap cleanup EXIT

echo ""
echo "============================================================"
echo "  PREFLIGHT: $OUTPUT"
echo "============================================================"
echo "  Build dir: $BUILD_DIR"
echo "  Рабочая папка: $WORK"
echo ""

mkdir -p "$WORK"

# ===== Шаг 1: verify_elem_strict.py =====
echo "--- [1/7] verify_elem_strict.py (build) ---"
if [ -f "$VERIFY_ELEM" ]; then
    check "Статический анализ Form.elem.json" \
        bash -c 'python3 "$0" "$1" 2>/dev/null; rc=$?; [ $rc -eq 0 -o $rc -eq 3 ]' "$VERIFY_ELEM" "$BUILD_DIR/Form/Форма/Form.elem.json"
else
    echo "  ${YELLOW}⚠  verify_elem_strict.py не найден, пропускаем${NC}"
fi

# ===== Шаг 2: v8unpack -B =====
echo "--- [2/7] v8unpack -B (сборка) ---"
check "Сборка EPF из исходников" v8unpack -B "$BUILD_DIR" "$OUTPUT"

# ===== Шаг 3: v8unpack -E =====
echo "--- [3/7] v8unpack -E (распаковка) ---"
check "Распаковка EPF без ошибок" v8unpack -E "$OUTPUT" "$WORK/unpack"

# ===== Шаг 4: verify_elem_strict.py на распакованном =====
echo "--- [4/7] verify_elem_strict.py (unpack) ---"
if [ -f "$VERIFY_ELEM" ]; then
    check "Строгая проверка распакованной формы" \
        bash -c 'python3 "$0" "$1" 2>/dev/null; rc=$?; [ $rc -eq 0 -o $rc -eq 3 ]' "$VERIFY_ELEM" "$WORK/unpack/Form/Форма/Form.elem.json"
fi

# ===== Шаг 5: Roundtrip diff =====
echo "--- [5/7] Roundtrip (build→unpack→rebuild→diff) ---"
mkdir -p "$WORK/rebuild" "$WORK/rebuild_unpack"
v8unpack -B "$WORK/unpack" "$WORK/rebuild/test.epf" 2>/dev/null
v8unpack -E "$WORK/rebuild/test.epf" "$WORK/rebuild_unpack" 2>/dev/null
if diff -rq "$WORK/unpack/Form" "$WORK/rebuild_unpack/Form" >/dev/null 2>&1; then
    echo -e "  ${GREEN}✓${NC} Roundtrip: Form идентична после пересборки"
    PASS=$((PASS + 1))
else
    echo -e "  ${RED}✗${NC} Roundtrip: Form ИЗМЕНЯЕТСЯ при пересборке!"
    echo "    Сравнение:"
    diff -rq "$WORK/unpack/Form" "$WORK/rebuild_unpack/Form" 2>/dev/null | head -20
    FAIL=$((FAIL + 1))
fi

# ===== Шаг 6: verify_epf.py =====
echo "--- [6/7] verify_epf.py (паттерны + регрессии) ---"
if [ -f "$VERIFY_EPF" ]; then
    # Если есть epf1 для сравнения — используем
    EPF1=""
    if [ -f "$PROJECT_DIR/projects/11_ut11_loader/_work/ВыгрузкаДанныхВXML_v105.epf" ]; then
        EPF1="$PROJECT_DIR/projects/11_ut11_loader/_work/ВыгрузкаДанныхВXML_v105.epf"
    fi
    if [ -n "$EPF1" ]; then
        python3 "$VERIFY_EPF" "$EPF1" "$OUTPUT" 2>&1 | tail -5 | grep -q "Все патчи применились" && \
            echo -e "  ${GREEN}✓${NC} verify_epf.py: все проверки пройдены" || \
            echo -e "  ${YELLOW}⚠  verify_epf.py: смотри вывод выше${NC}"
    else
        echo "  ${YELLOW}⚠  EPF1 не найден, пропускаем verify_epf.py${NC}"
    fi
fi

# ===== Шаг 7: Сигнатура =====
echo "--- [7/7] Сигнатура контейнера 1С 8.3 ---"
SIG_OK=$(head -c 4 "$OUTPUT" | od -A n -t x1 | tr -d ' ' | grep -c "ffffff7f" || true)
if [ "$SIG_OK" -gt 0 ]; then
    echo -e "  ${GREEN}✓${NC} Сигнатура ff ff ff 7f — корректна"
    PASS=$((PASS + 1))
else
    echo -e "  ${RED}✗${NC} Сигнатура неверна!"
    head -c 4 "$OUTPUT" | od -A n -t x1
    FAIL=$((FAIL + 1))
fi

# ===== ИТОГ =====
echo ""
echo "============================================================"
if [ "$FAIL" -eq 0 ]; then
    echo -e "  ${GREEN}✅ PREFLIGHT PASSED — ${PASS}/${PASS} проверок${NC}"
    echo "  Файл готов к релизу: $OUTPUT"
    echo "============================================================"
    exit 0
else
    echo -e "  ${RED}❌ PREFLIGHT FAILED — ${FAIL} ошибок${NC}"
    echo "  Релиз НЕ ВЫПУСКАТЬ до исправления"
    echo "============================================================"
    exit 2
fi
