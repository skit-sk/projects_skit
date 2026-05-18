#!/bin/bash
# Flask manager script — СТРОГОЕ ПРАВИЛО:
# Все Flask-проекты перезапускать ТОЛЬКО через этот скрипт.
# НИКОГДА не запускать python app.py напрямую.
#
# Usage: ./flask.sh start|stop|status|restart <project> [port]

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
WORKDIR="/home/user_aioc/workspace"
ACTION="${1:-help}"
PROJECT_INPUT="${2:-}"
PORT="${3:-}"

# ─── Маппинг проектов ─────────────────────────────────────
declare -A PROJECT_MAP=(
    ["01"]="01_fundament_rf"
    ["1"]="01_fundament_rf"
    ["fundament_rf"]="01_fundament_rf"
    ["02"]="02_graphs_candle"
    ["2"]="02_graphs_candle"
    ["graphs_candle"]="02_graphs_candle"
    ["03"]="03_demo_charts_ascii"
    ["3"]="03_demo_charts_ascii"
    ["demo_charts_ascii"]="03_demo_charts_ascii"
    ["04"]="04_tradingview-demos"
    ["4"]="04_tradingview-demos"
    ["tradingview-demos"]="04_tradingview-demos"
    ["05"]="05_transcript"
    ["5"]="05_transcript"
    ["transcript"]="05_transcript"
    ["06"]="06_screenshots_project"
    ["6"]="06_screenshots_project"
    ["screenshots_project"]="06_screenshots_project"
)

# ─── Определить директорию проекта ───────────────────────
resolve_project() {
    local input="${1:-}"
    if [ -z "$input" ]; then
        echo "Error: project name or number required"
        exit 1
    fi

    local proj_name="${PROJECT_MAP[$input]:-}"
    if [ -z "$proj_name" ]; then
        # Попробовать как есть (если передали полное имя директории)
        if [ -d "${WORKDIR}/${input}" ]; then
            proj_name="$input"
        elif [ -d "${WORKDIR}/projects/${input}" ]; then
            proj_name="$input"
        else
            echo "Error: unknown project '${input}'"
            echo "Known: 01/fundament_rf, 02/graphs_candle, 03/demo_charts_ascii"
            exit 1
        fi
    fi

    # Проверить путь
    if [ -d "${WORKDIR}/projects/${proj_name}" ]; then
        echo "${WORKDIR}/projects/${proj_name}"
    elif [ -d "${WORKDIR}/${proj_name}" ]; then
        echo "${WORKDIR}/${proj_name}"
    else
        echo "Error: project directory not found: ${proj_name}"
        exit 1
    fi
}

# ─── Определить точку входа ──────────────────────────────
resolve_entrypoint() {
    local proj_dir="$1"
    if [ -f "${proj_dir}/app.py" ]; then
        echo "app.py"
    elif [ -f "${proj_dir}/main.py" ]; then
        echo "main.py"
    else
        echo "Error: no app.py or main.py found in ${proj_dir}"
        exit 1
    fi
}

# ─── Определить venv ─────────────────────────────────────
resolve_venv() {
    local proj_dir="$1"
    # Приоритет: venv_uv (новый uv venv) > venv (старый) > .venv
    if [ -f "${proj_dir}/venv_uv/bin/python3" ]; then
        echo "${proj_dir}/venv_uv/bin/python3"
    elif [ -f "${proj_dir}/venv/bin/python3" ]; then
        echo "${proj_dir}/venv/bin/python3"
    elif [ -f "${proj_dir}/.venv/bin/python3" ]; then
        echo "${proj_dir}/.venv/bin/python3"
    else
        echo "python3"
    fi
}

# ─── Определить порт по умолчанию ────────────────────────
# Порт по умолчанию 5000 для ВСЕХ проектов.
# Переопределить можно 3-м аргументом.
resolve_port() {
    echo "${1:-5000}"
}

# ─── Команды ─────────────────────────────────────────────
cmd_start() {
    local proj_dir="$1"
    local entrypoint="$2"
    local python_bin="$3"
    local port="$4"
    local proj_name="$(basename "$proj_dir")"
    local pidfile="/tmp/flask_${proj_name}.pid"
    local logfile="/tmp/flask_${proj_name}.log"

    # Проверить, не запущен ли уже
    if [ -f "$pidfile" ] && kill -0 "$(cat "$pidfile")" 2>/dev/null; then
        echo "${proj_name} already running (PID: $(cat $pidfile))"
        return
    fi

    cd "$proj_dir"
    rm -f "$logfile"

    # Загрузить .env перед запуском
    set -a
    source "${SCRIPT_DIR}/../.env" 2>/dev/null || true
    set +a

    # Запуск через setsid для detach от терминала
    setsid "$python_bin" "$entrypoint" "$port" > "$logfile" 2>&1 &
    local pid=$!

    sleep 3
    if curl -s "http://127.0.0.1:${port}/" > /dev/null 2>&1; then
        echo "$pid" > "$pidfile"
        echo "✅ Started ${proj_name} on :${port} (PID: $pid)"
    else
        echo "❌ Error: ${proj_name} failed to start on :${port}"
        [ -f "$logfile" ] && tail -10 "$logfile"
        exit 1
    fi
}

cmd_stop() {
    local proj_dir="$1"
    local port="$2"
    local proj_name="$(basename "$proj_dir")"
    local pidfile="/tmp/flask_${proj_name}.pid"

    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            kill "$pid" 2>/dev/null && rm "$pidfile"
            echo "✅ Stopped ${proj_name} (PID: $pid)"
            return
        fi
        rm "$pidfile"
    fi

    # Fallback: kill by port pattern
    if pkill -f "python.*${proj_name}.*:${port}" 2>/dev/null || \
       pkill -f "python.*${port}" 2>/dev/null; then
        echo "✅ Stopped ${proj_name} by pattern"
    else
        echo "⚠️ ${proj_name} not running"
    fi
}

cmd_status() {
    local proj_dir="$1"
    local port="$2"
    local proj_name="$(basename "$proj_dir")"
    local pidfile="/tmp/flask_${proj_name}.pid"

    if [ -f "$pidfile" ]; then
        local pid
        pid=$(cat "$pidfile")
        if kill -0 "$pid" 2>/dev/null; then
            echo "🟢 ${proj_name}: running on :${port} (PID: $pid)"
            return
        fi
        rm -f "$pidfile"
    fi

    # Check by port
    if curl -s "http://127.0.0.1:${port}/" > /dev/null 2>&1; then
        echo "🟡 ${proj_name}: running on :${port} (PID unknown)"
    else
        echo "🔴 ${proj_name}: not running"
    fi
}

cmd_restart() {
    local proj_dir="$1"
    local entrypoint="$2"
    local python_bin="$3"
    local port="$4"

    cmd_stop "$proj_dir" "$port"
    sleep 1
    cmd_start "$proj_dir" "$entrypoint" "$python_bin" "$port"
}

# ─── Main ────────────────────────────────────────────────
PROJ_DIR=$(resolve_project "$PROJECT_INPUT")
PROJ_NAME=$(basename "$PROJ_DIR")
ENTRYPOINT=$(resolve_entrypoint "$PROJ_DIR")
PYTHON_BIN=$(resolve_venv "$PROJ_DIR")
PORT=${PORT:-$(resolve_port "${3:-}")}

case "$ACTION" in
    start)   cmd_start   "$PROJ_DIR" "$ENTRYPOINT" "$PYTHON_BIN" "$PORT" ;;
    stop)    cmd_stop    "$PROJ_DIR" "$PORT" ;;
    status)  cmd_status  "$PROJ_DIR" "$PORT" ;;
    restart) cmd_restart "$PROJ_DIR" "$ENTRYPOINT" "$PYTHON_BIN" "$PORT" ;;
    *)
        echo "Flask Project Manager — СТРОГОЕ ПРАВИЛО:"
        echo "  Все Flask-проекты запускать ТОЛЬКО через этот скрипт."
        echo ""
        echo "Usage: $0 start|stop|status|restart <project> [port]"
        echo ""
        echo "Projects:"
        echo "  01 / fundament_rf       → projects/01_fundament_rf/"
        echo "  02 / graphs_candle      → projects/02_graphs_candle/"
        echo "  03 / demo_charts_ascii  → projects/03_demo_charts_ascii/"
        echo ""
        echo "Port: default 5000 for all projects, override with 3rd argument"
        echo ""
        echo "Examples:"
        echo "  $0 start 01                  # port 5000"
        echo "  $0 start fundament_rf        # port 5000"
        echo "  $0 restart 02 5002           # custom port"
        echo "  $0 stop 03"
        echo "  $0 status graphs_candle"
        ;;
esac
