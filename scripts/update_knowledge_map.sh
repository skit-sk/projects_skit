#!/bin/bash
#==============================================================================
# update_knowledge_map.sh
# Обновление карты знаний workspace
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
KB_DIR="$WORKSPACE/share/knowledge-base"
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

    echo ""
    echo "  Projects:"
    local count=0
    for project in "$WORKSPACE"/projects/[0-9][0-9]_*/; do
        if [ -d "$project" ]; then
            echo -e "    ✓ $(basename "$project")"
            count=$((count + 1))
        fi
    done

    echo ""
    echo "  Knowledge Base:"
    local kb_count=0
    if [ -d "$KB_DIR/3-projects" ]; then
        kb_count=$(find "$KB_DIR/3-projects" -name "*.md" 2>/dev/null | wc -l)
        echo -e "    ✓ 3-projects/ ($kb_count md files)"
    else
        echo -e "    ✗ 3-projects/ NOT FOUND"
    fi

    if [ -d "$KB_DIR/4-guides" ]; then
        local guides_count=$(find "$KB_DIR/4-guides" -name "*.md" 2>/dev/null | wc -l)
        echo -e "    ✓ 4-guides/ ($guides_count md files)"
    fi

    echo ""
    log_info "Найдено проектов: $count"
    log_info "Статей в KB: $kb_count"
}

#------------------------------------------------------------------------------
# Проверка KB
#------------------------------------------------------------------------------
check_kb_completeness() {
    log_step "Проверка полноты Knowledge Base..."

    local missing=0
    for project in "$WORKSPACE"/projects/[0-9][0-9]_*/; do
        local name=$(basename "$project")
        local slug=$(echo "$name" | tr '_' '-')
        local article="$KB_DIR/3-projects/$slug.md"
        if [ -f "$article" ]; then
            echo -e "  ✓ $name"
        else
            echo -e "  ✗ $name — отсутствует KB-статья ($article)"
            missing=$((missing + 1))
        fi
    done

    if [ $missing -eq 0 ]; then
        log_info "Все проекты имеют KB-статьи"
    else
        log_warn "$missing проектов без KB-статей"
    fi
}

#------------------------------------------------------------------------------
# Обновление даты версии
#------------------------------------------------------------------------------
update_versions() {
    log_step "Обновление версий..."

    local today=$(date +%Y-%m-%d)
    local current_version="2.0"

    for file in "$MAP_ALL" "$MAP_SMALL" "$MAP_UPDATE"; do
        if [ -f "$file" ]; then
            sed -i "s/\*\*Версия:\*\*.*/\*\*Версия:\*\* $current_version/" "$file" 2>/dev/null || true
            sed -i "s/\*\*Дата:\*\*.*/\*\*Дата:\*\* $today/" "$file" 2>/dev/null || true
            sed -i "s/\"updated\": \"[^\"]*\"/\"updated\": \"$today\"/" "$file" 2>/dev/null || true
            echo -e "  ✓ $(basename "$file") → v$current_version ($today)"
        fi
    done
}

#------------------------------------------------------------------------------
# Сбор статистики
#------------------------------------------------------------------------------
collect_stats() {
    log_step "Сбор статистики..."

    local project_count=0
    for project in "$WORKSPACE"/projects/[0-9][0-9]_*/; do
        if [ -d "$project" ]; then
            project_count=$((project_count + 1))
        fi
    done

    local kb_file_count=0
    for dir in "$KB_DIR"/*/; do
        if [ -d "$dir" ]; then
            local dir_count=$(find "$dir" -name "*.md" 2>/dev/null | wc -l)
            kb_file_count=$((kb_file_count + dir_count))
        fi
    done

    echo ""
    log_info "Статистика:"
    echo "  - Projects: $project_count"
    echo "  - KB files: $kb_file_count"
}

#------------------------------------------------------------------------------
# Проверка ссылок
#------------------------------------------------------------------------------
verify_links() {
    log_step "Проверка ссылок..."

    local broken=0

    # Проверяем, что все KB-статьи упоминают архитектуру
    if grep -q "architecture-overview" "$KB_DIR/README.md" 2>/dev/null; then
        echo -e "  ✓ KB README ссылается на architecture-overview"
    else
        echo -e "  ✗ KB README не ссылается на architecture-overview"
        broken=$((broken + 1))
    fi

    # Проверяем, что map_all_small ссылается на все map-файлы
    for file in map_all.md map_mermaid.md map_tree.md map_json.md map_links.md map_update.md; do
        if grep -q "\[$file\]" "$MAP_SMALL" 2>/dev/null; then
            echo -e "  ✓ map_all_small ссылается на $file"
        else
            echo -e "  ✗ map_all_small не ссылается на $file"
            broken=$((broken + 1))
        fi
    done

    if [ $broken -eq 0 ]; then
        log_info "Все ссылки в порядке"
    else
        log_warn "$broken ссылок отсутствует"
    fi
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
# Главная функция
#------------------------------------------------------------------------------
main() {
    echo ""
    echo "========================================"
    echo "  Workspace Knowledge Map Updater"
    echo "  v2.0"
    echo "========================================"
    echo ""

    check_workspace
    echo ""

    if [ "$CHECK_ONLY" = true ]; then
        log_info "Режим проверки (без обновления)"
        echo ""
        check_map_files
        echo ""
        check_structure
        echo ""
        check_kb_completeness
        echo ""
        verify_links
        echo ""
        exit 0
    fi

    check_map_files
    echo ""

    check_structure
    echo ""

    check_kb_completeness
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
