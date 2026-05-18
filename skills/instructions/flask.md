# FLASK Skill — Управление серверами

**Статус:** РАБОТАЕТ
**Обновлено:** 2026-05-06

## ⚠️ СТРОГОЕ ПРАВИЛО

**Все Flask-проекты запускать/перезапускать ТОЛЬКО через `scripts/flask.sh`.**

❌ **НИКОГДА** не запускать `python app.py` или `python main.py` напрямую —
процесс может зависнуть, не отвязаться от терминала и не перехватить сигналы.

## Расположение

`scripts/flask.sh`

## Использование

```bash
# По номеру проекта (рекомендуется)
./scripts/flask.sh start 01
./scripts/flask.sh start 02
./scripts/flask.sh start 03

# По имени проекта
./scripts/flask.sh start fundament_rf
./scripts/flask.sh start graphs_candle
./scripts/flask.sh start demo_charts_ascii

# Управление
./scripts/flask.sh stop 01
./scripts/flask.sh status 02
./scripts/flask.sh restart fundament_rf
```

## Маппинг номеров

| Номер | Проект | Путь |
|-------|--------|------|
| 01, 1 | fundament_rf | `projects/01_fundament_rf/` |
| 02, 2 | graphs_candle | `projects/02_graphs_candle/` |
| 03, 3 | demo_charts_ascii | `projects/03_demo_charts_ascii/` |
| 04, 4 | tradingview-demos | `projects/04_tradingview-demos/` |
| 05, 5 | transcript | `projects/05_transcript/` |
| 06, 6 | screenshots_project | `projects/06_screenshots_project/` |

## Порт

По умолчанию **5000** для ВСЕХ проектов. Переопределить 3-м аргументом:

```bash
./scripts/flask.sh start 01 8080
./scripts/flask.sh restart graphs_candle 5002
```

## Альтернативные скрипты

```bash
# Автоперезапуск (watchdog)
python scripts/flask_manager.py start 01 --watchdog

# Универсальный CLI
scripts/flask-runner.sh start 01
```
