#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PID_FILE="/tmp/max_bot.pid"
LOG_FILE="$PROJECT_DIR/bot.log"
METRICS_PY="$SCRIPT_DIR/../../tools/scripts/metrics_logger.py"

_kill_all() {
  for pid in $(pgrep -f "python3.*main.py" 2>/dev/null); do
    kill "$pid" 2>/dev/null || true
  done
  sleep 1
  for pid in $(pgrep -f "python3.*main.py" 2>/dev/null); do
    kill -9 "$pid" 2>/dev/null || true
  done
}

case "${1:-}" in
  start)
    _kill_all
    rm -f "$PID_FILE"
    python3 "$METRICS_PY" start 2>/dev/null || true
    echo "🚀 Запуск MAX бота (Long Polling)..."
    cd "$PROJECT_DIR"
    source "$SCRIPT_DIR/../../scripts/source_env.sh" 2>/dev/null || true
    source "$PROJECT_DIR/../../venv/bin/activate" 2>/dev/null || true
    PYTHONUNBUFFERED=1 nohup python3 main.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ MAX бот запущен (PID: $(cat "$PID_FILE"))"
    else
      echo "❌ Ошибка запуска. Лог: $LOG_FILE"
      tail -5 "$LOG_FILE"
      rm -f "$PID_FILE"
    fi
    ;;
  stop)
    _kill_all
    rm -f "$PID_FILE"
    echo "✅ MAX бот остановлен"
    ;;
  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ MAX бот запущен (PID: $(cat "$PID_FILE"))"
    else
      echo "❌ MAX бот не запущен"
    fi
    ;;
  logs)
    tail -f "$LOG_FILE"
    ;;
  webhook)
    if [ -z "${2:-}" ]; then
      echo "Использование: $0 webhook <url>"
      exit 1
    fi
    url="$2"
    echo "🔄 Установка webhook: $url"
    cd "$PROJECT_DIR"
    source "$PROJECT_DIR/../../venv/bin/activate" 2>/dev/null || true
    "$PROJECT_DIR/../../venv/bin/python3" -c "
import sys; sys.path.insert(0, '.'); sys.path.insert(0, 'bot')
from max_client import MAXClient
import asyncio
async def main():
    c = MAXClient()
    r = await c.setup_webhook('$url', update_types=['message_created', 'message_callback', 'bot_started', 'bot_added', 'bot_stopped'])
    print(r)
    await c.close()
asyncio.run(main())
"
    ;;
  test)
    echo "🧪 Тестовый запуск (foreground)..."
    cd "$PROJECT_DIR"
    source "$PROJECT_DIR/../../venv/bin/activate" 2>/dev/null || true
    "$PROJECT_DIR/../../venv/bin/python3" main.py
    ;;
  *)
    echo "Использование: $0 {start|stop|status|restart|logs|webhook|test}"
    exit 1
    ;;
esac
