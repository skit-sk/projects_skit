# flask — управление Flask-проектами

Центральный инструмент для запуска/остановки Flask-проектов.

## Быстрый справочник

Полная инструкция: `skills/instructions/flask.md`

## Расположение

```
scripts/
├── flask.sh             ← bash-управление
├── flask_manager.py     ← продвинутое управление (+ watchdog)
├── flask-runner.sh      ← точка входа (watchdog)
└── runner.py            ← ядро watchdog
```

## Использование

```bash
# По номеру (рекомендуется)
./scripts/flask.sh start 01      # = fundament_rf
./scripts/flask.sh start 02      # = graphs_candle

# Управление
./scripts/flask.sh stop 01
./scripts/flask.sh status
```

## Проекты

Любая директория в `projects/` с `app.py`:
`01_fundament_rf`, `02_graphs_candle`, `03_demo_charts_ascii`

## Связанное

- [fundament_rf](../3-projects/fundament-rf.md)
- [graphs_candle](../3-projects/graphs-candle.md)
