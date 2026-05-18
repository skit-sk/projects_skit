#!/bin/bash
#==============================================================================
# update_knowledge_map.sh
# Обновление карты знаний workspace (модульная версия)
#==============================================================================
# Использование:
#   ./update_knowledge_map.sh
#   ./update_knowledge_map.sh --check    # только проверка
#   ./update_knowledge_map.sh --force    # принудительное обновление
#
# Алиас команды:
#   /update_map
#==============================================================================

set -e

WORKSPACE="/home/user_aioc/workspace"
MAP_DIR="$WORKSPACE/share/opencode"
SCRIPT_DIR="$WORKSPACE/scripts"

# Файлы карты
MAP_SMALL="$MAP_DIR/map_all_small.md"
MAP_MERMAID="$MAP_DIR/map_mermaid.md"
MAP_TREE="$MAP_DIR/map_tree.md"
MAP_JSON="$MAP_DIR/map_json.md"
MAP_LINKS="$MAP_DIR/map_links.md"
MAP_UPDATE="$MAP_DIR/map_update.md"
MAP_ALL="$MAP_DIR/map_all.md"

# Цвета
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

#------------------------------------------------------------------------------
# Функции логирования
#------------------------------------------------------------------------------
log_info() { echo -e "${GREEN}[INFO]${NC} $1"; }
log_warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
log_error() { echo -e "${RED}[ERROR]${NC} $1"; }
log_step() { echo -e "${BLUE}[STEP]${NC} $1"; }

#------------------------------------------------------------------------------
# Проверка аргументов
#------------------------------------------------------------------------------
CHECK_ONLY=false
FORCE_UPDATE=false

while [[ $# -gt 0 ]]; do
    case $1 in
        --check)
            CHECK_ONLY=true
            shift
            ;;
        --force)
            FORCE_UPDATE=true
            shift
            ;;
        *)
            shift
            ;;
    esac
done

#------------------------------------------------------------------------------
# Проверка существования файлов
#------------------------------------------------------------------------------
check_map_files() {
    log_step "Проверка файлов карты..."

    local all_exist=true
    for file in "$MAP_SMALL" "$MAP_MERMAID" "$MAP_TREE" "$MAP_JSON" "$MAP_LINKS" "$MAP_UPDATE" "$MAP_ALL"; do
        if [ -f "$file" ]; then
            echo -e "  ✓ $(basename "$file")"
        else
            echo -e "  ✗ $(basename "$file") NOT FOUND"
            all_exist=false
        fi
    done

    if [ "$all_exist" = false ]; then
        log_error "Не все файлы карты существуют!"
        return 1
    fi
}

#------------------------------------------------------------------------------
# Проверка workspace
#------------------------------------------------------------------------------
check_workspace() {
    log_step "Проверка workspace..."

    if [ ! -d "$WORKSPACE" ]; then
        log_error "Workspace не найден: $WORKSPACE"
        exit 1
    fi
    log_info "  Workspace: $WORKSPACE"
}

#------------------------------------------------------------------------------
# Проверка структуры
#------------------------------------------------------------------------------
check_structure() {
    log_step "Проверка структуры workspace..."

    local projects=("projects/01_fundament_rf" "projects/02_graphs_candle" "projects/04_tradingview-demos" "projects/05_transcript")
    local kb_dirs=("tradingview" "tv")

    echo ""

    echo "  Projects:"
    for project in "${projects[@]}"; do
        if [ -d "$WORKSPACE/$project" ]; then
            echo -e "    ✓ $project"
        else
            echo -e "    ✗ $project NOT FOUND"
        fi
    done

    echo ""
    echo "  Knowledge Bases:"
    for kb in "${kb_dirs[@]}"; do
        kb_path="$WORKSPACE/share/knowledge-base/$kb"
        if [ -d "$kb_path" ]; then
            local md_count=$(find "$kb_path" -name "*.md" 2>/dev/null | wc -l)
            echo -e "    ✓ $kb ($md_count md files)"
        else
            echo -e "    ✗ $kb NOT FOUND"
        fi
    done
}

#------------------------------------------------------------------------------
# Обновление даты версии
#------------------------------------------------------------------------------
update_versions() {
    log_step "Обновление версий..."

    local today=$(date +%Y-%m-%d)
    local current_version="1.0"

    # Обновляем дату во всех файлах
    for file in "$MAP_ALL" "$MAP_SMALL" "$MAP_UPDATE"; do
        if [ -f "$file" ]; then
            # Заменяем дату
            sed -i "s/\*\*Дата:\*\*.*/\*\*Дата:\*\* $today/" "$file" 2>/dev/null || true
            # Заменяем updated в JSON
            sed -i "s/\"updated\": \"[^\"]*\"/\"updated\": \"$today\"/" "$file" 2>/dev/null || true
            echo -e "  ✓ $(basename "$file") → $today"
        fi
    done

    log_info "Версия обновлена: $current_version ($today)"
}

#------------------------------------------------------------------------------
# Сбор статистики
#------------------------------------------------------------------------------
collect_stats() {
    log_step "Сбор статистики..."

    # Проекты
    local project_count=0
    for dir in "$WORKSPACE"/*/; do
        basename_dir=$(basename "$dir")
        case "$basename_dir" in
            01_fundament_rf|02_graphs_candle|04_tradingview-demos|05_transcript)
                ((project_count++))
                ;;
        esac
    done

    # KB файлы
    local kb_file_count=0
    for kb in "$WORKSPACE/share/knowledge-base"/*/; do
        if [ -d "$kb" ]; then
            ((kb_file_count+=$(find "$kb" -name "*.md" 2>/dev/null | wc -l)))
        fi
    done

    # JSON файлы данных
    local json_count=0
    if [ -d "$WORKSPACE/projects/01_fundament_rf/data" ]; then
        json_count=$(find "$WORKSPACE/projects/01_fundament_rf/data" -name "*.json" 2>/dev/null | wc -l)
    fi

    echo ""
    log_info "Статистика:"
    echo "  - Projects: $project_count"
    echo "  - KB files: $kb_file_count"
    echo "  - JSON data files: $json_count"
}

#------------------------------------------------------------------------------
# Генерация отчёта
#------------------------------------------------------------------------------
generate_report() {
    log_step "Генерация отчёта..."

    local today=$(date +%Y-%m-%d)
    local report="
================================================================================
  Workspace Knowledge Map - Update Report
================================================================================

  Date:    $today
  Status:  OK

  Files:
    - $MAP_ALL
    - $MAP_SMALL
    - $MAP_MERMAID
    - $MAP_TREE
    - $MAP_JSON
    - $MAP_LINKS
    - $MAP_UPDATE

================================================================================
"

    echo "$report"
}

#------------------------------------------------------------------------------
# Проверка ссылок
#------------------------------------------------------------------------------
verify_links() {
    log_step "Проверка ссылок..."

    local broken=0

    # Проверяем project → KB ссылки
    if grep -q "fundament_rf.*tradingview" "$MAP_LINKS" 2>/dev/null; then
        echo -e "  ✓ fundament_rf → tradingview link exists"
    else
        echo -e "  ✗ fundament_rf → tradingview link MISSING"
        ((broken++))
    fi

    if grep -q "graphs_candle.*tradingview" "$MAP_LINKS" 2>/dev/null; then
        echo -e "  ✓ graphs_candle → tradingview link exists"
    else
        echo -e "  ✗ graphs_candle → tradingview link MISSING"
        ((broken++))
    fi

    if [ $broken -eq 0 ]; then
        log_info "Все ссылки в порядке"
    else
        log_warn "$broken ссылок отсутствует"
    fi
}

#------------------------------------------------------------------------------
# Главная функция
#------------------------------------------------------------------------------
main() {
    echo ""
    echo "========================================"
    echo "  Workspace Knowledge Map Updater"
    echo "  (modular version)"
    echo "========================================"
    echo ""

    # Проверки
    check_workspace
    echo ""

    if [ "$CHECK_ONLY" = true ]; then
        log_info "Режим проверки (без обновления)"
        echo ""
        check_map_files
        echo ""
        check_structure
        echo ""
        verify_links
        echo ""
        exit 0
    fi

    # Полное обновление
    check_map_files
    echo ""

    check_structure
    echo ""

    update_versions
    echo ""

    collect_stats
    echo ""

    verify_links
    echo ""

    generate_report

    echo "========================================"
    log_info "Обновление завершено!"
    echo "========================================"
    echo ""
    log_info "Для проверки запустите:"
    echo "  $0 --check"
    echo ""
}

#------------------------------------------------------------------------------
# Запуск
#------------------------------------------------------------------------------
main "$@"
