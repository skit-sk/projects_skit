# 01 — Fundament RF

**ID:** 01
**Расположение:** `projects/01_fundament_rf/`
**Тип:** Flask-монолит (хаб)
**Порт:** 5000
**Запуск:** `./scripts/flask.sh start 01`

## Назначение

Главный хаб workspace. Трекер торговых сделок Bitget с визуализацией, аналитикой, dashboard'ами и песочницей (Sandbox) для интеграции всех проектов.

## Стек

- Flask
- Jinja2
- ccxt / requests
- Plotly / SVG / Canvas
- JSON-файлы (хранение карточек сделок)

## Архитектура

```
projects/01_fundament_rf/
├── app.py                  # Flask factory, регистрация blueprint'ов
├── models.py               # FundObj dataclass
├── storage.py              # JSONStorage
├── flask_runner.py         # Watchdog автоперезапуск
├── account/                # Bitget private API (HMAC-SHA256)
├── api/                    # WebSocket / CCXT загрузчики
├── infographics/           # Движки визуализации
├── routes/                 # Blueprint'ы
│   ├── api.py
│   ├── web.py
│   ├── graphics.py
│   ├── graphics_v2.py
│   ├── processor_1d.py
│   ├── dashboard.py
│   ├── trade_analytics.py
│   ├── ma_analytics.py
│   ├── ccxt_api.py
│   ├── account_api.py
│   ├── ai_models.py         # 09 Model Catalog
│   ├── viz_lab.py           # Visualization Lab
│   ├── med_life.py          # 11 Med Life
│   ├── sandbox.py           # Sandbox UI
│   ├── proxy.py             # Proxy к satellite-проектам
│   ├── med_life.py          # Med Life Atlas
│   └── ofd_api.py           # 08 OFD API
├── templates/
├── static/
└── data/card/               # Карточки сделок
```

## Entry points

- Главная: `/`
- Dashboard: `/dashboard/`
- Sandbox: `/sandbox/`
- Knowledge Base: `/kb/`
- Viz Lab: `/viz-lab/`
- Med Life: `/med-life/`
- OFD API: `/ofd-api/`
- AI Models: `/ai-models/`
- CCXT API: `/ccxt-api/`

## Зависимости

| Тип | Зависимость | Описание |
|---|---|---|
| Внутренняя | `projects/08_ofd_api/` | Импортируется как blueprint |
| Внутренняя | `projects/09_model_catalog/models_catalog.json` | Данные каталога моделей |
| Внутренняя | `projects/11_med_life/` | Med Life Atlas |
| Внешняя | Bitget API | REST + WebSocket |

## Связи с другими проектами

| Проект | Тип связи | Детали |
|---|---|---|
| 02 Graphs Candle | proxy | `/proxy/02/` |
| 03 Demo Charts ASCII | proxy | `/proxy/03/` |
| 04 TradingView Demos | static mount | `/static/sandbox/04/` |
| 06 Screenshots Catalog | static mount | `/static/sandbox/06/` |
| 07 TG Bot AIForGuest | HTTP | Бот вызывает `localhost:5000` |
| 08 OFD API | blueprint | Импорт `ofd_api` в `app.py` |
| 09 Model Catalog | blueprint/data | `/ai-models/` + JSON |
| 10 MAX Bot | HTTP | Бот вызывает `localhost:5000` |
| 11 Med Life | blueprint | `/med-life/` |

> **Примечание:** Viz Lab (`/viz-lab/`) — это blueprint внутри `01_fundament_rf`, не отдельный проект.

## Запуск

```bash
./scripts/flask.sh start 01
```

## Связанные KB

- [Архитектура workspace](../4-guides/architecture-overview.md)
- [URL/Port карта](../4-guides/url-port-map.md)
