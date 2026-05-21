#!/bin/bash
set -e

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
PROJECT_DIR="$(cd "$SCRIPT_DIR/../projects/07_tg_bot_aiforguest" && pwd)"
METRICS_PY="$SCRIPT_DIR/../tools/scripts/metrics_logger.py"
PID_FILE="/tmp/tg_bot_aiforguest.pid"
LOG_FILE="$PROJECT_DIR/bot.log"

case "${1:-}" in
  start)
    # убить все zombie-процессы перед стартом
    for pid in $(pgrep -f "python3.*bot/main.py" 2>/dev/null); do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
    for pid in $(pgrep -f "python3.*bot/main.py" 2>/dev/null); do
      kill -9 "$pid" 2>/dev/null || true
    done
    rm -f "$PID_FILE"
    # стартуем логгер метрик, если ещё не запущен
    python3 "$METRICS_PY" start 2>/dev/null || true
    echo "🚀 Запуск бота..."
    cd "$PROJECT_DIR"
    source "$(dirname "$0")/source_env.sh" 2>/dev/null || true
    source "$(dirname "$0")/../venv/bin/activate" 2>/dev/null || true
    PYTHONUNBUFFERED=1 nohup python3 bot/main.py >> "$LOG_FILE" 2>&1 &
    echo $! > "$PID_FILE"
    sleep 2
    if kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ Бот запущен (PID: $(cat "$PID_FILE"))"
    else
      echo "❌ Ошибка запуска. Лог: $LOG_FILE"
      tail -5 "$LOG_FILE"
      rm -f "$PID_FILE"
    fi
    ;;
  stop)
    # убиваем все zombie-процессы бота
    for pid in $(pgrep -f "python3.*bot/main.py" 2>/dev/null); do
      kill "$pid" 2>/dev/null || true
    done
    sleep 1
    for pid in $(pgrep -f "python3.*bot/main.py" 2>/dev/null); do
      kill -9 "$pid" 2>/dev/null || true
    done
    rm -f "$PID_FILE"
    echo "✅ Бот остановлен"
    ;;
  status)
    if [ -f "$PID_FILE" ] && kill -0 "$(cat "$PID_FILE")" 2>/dev/null; then
      echo "✅ Бот запущен (PID: $(cat "$PID_FILE"))"
    else
      echo "❌ Бот не запущен"
    fi
    ;;
  restart)
    "$0" stop
    sleep 1
    "$0" start
    ;;
  logs)
    tail -f "$LOG_FILE"
    ;;
  watch)
    echo "🔄 Watch mode — автоперезапуск при падении..."
    while true; do
      "$0" start
      BOT_PID=$(cat "$PID_FILE" 2>/dev/null || echo 0)
      if [ "$BOT_PID" -gt 0 ]; then
        tail --pid="$BOT_PID" -f "$LOG_FILE" 2>/dev/null &
        TAIL_PID=$!
        wait "$BOT_PID" 2>/dev/null
        kill "$TAIL_PID" 2>/dev/null || true
      fi
      echo "⚠️ Бот упал. Перезапуск через 2с..."
      sleep 2
    done
    ;;
  logger)
    case "${2:-}" in
      start)
        python3 "$METRICS_PY" start
        ;;
      stop)
        python3 "$METRICS_PY" stop
        ;;
      status)
        python3 "$METRICS_PY" status
        ;;
      restart)
        python3 "$METRICS_PY" stop
        sleep 1
        python3 "$METRICS_PY" start
        ;;
      *)
        echo "Использование: $0 logger {start|stop|status|restart}"
        exit 1
        ;;
    esac
    ;;
  *)
    echo "Использование: $0 {start|stop|status|restart|logs|watch|logger}"
    exit 1
    ;;
esac
