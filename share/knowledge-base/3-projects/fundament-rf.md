# fundament_rf — Трекер сделок Bitget

**Расположение:** `projects/01_fundament_rf/`

## Назначение

Учёт торговых сделок с биржи Bitget, визуализация отклонений цены.

## Стек

- **Flask** (веб-фреймворк)
- **ccxt** (Bitget API через прямые HTTP-запросы)
- **requests** (HTTP-клиент)
- JSON-файлы (хранение данных)

## Архитектура

```
projects/01_fundament_rf/
├── app.py                          # Входная точка Flask
├── flask_runner.py                 # Watchdog для автоперезапуска
├── routes/
│   ├── api.py                      # API-эндпоинты
│   ├── web.py                      # Веб-маршруты
│   ├── graphics.py                 # Графики и визуализация
│   └── processor_1d.py             # Обработчик дневных данных (bitget REST)
├── data/                           # JSON-файлы сделок
└── templates/                      # HTML-шаблоны
```

## Ключевые особенности

- **Bitget API v2** — прямые запросы к `api.bitget.com` (без ccxt)
- **Данные:** JSON-файлы, не БД
- **Обработка:** processor_1d.py парсит свечи `1d` для анализа отклонений

## Запуск

```bash
cd projects/01_fundament_rf
source venv/bin/activate
python app.py
# или
./scripts/flask.sh start 01
```

## Связанные KB

- [ccxt Bitget API](../1-exchanges/ccxt-bitget.md) — справочник по Bitget
