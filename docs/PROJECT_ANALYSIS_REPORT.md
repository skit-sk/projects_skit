# Глубокий анализ проектов workspace

**Дата:** 2026-06-21  
**Область:** `/home/user_aioc/workspace/projects/`  
**Методология:** статический анализ, карта зависимостей, аудит безопасности, UI/UX-аудит, архитектурное проектирование.  
**Цель:** подготовить полный анализ, план рефакторинга и концепцию единой визуальной песочницы на базе `01_fundament_rf`.

---

## 1. Executive Summary

В workspace находится **11 проектов** (10 из `AGENTS.md` + `11_med_life`).

`01_fundament_rf` уже является **неофициальным хабом**: в него импортированы blueprints из `08_ofd_api`, каталог `09_model_catalog` потребляется через `viz_lab`, a боты `07_tg_bot_aiforguest` и `10_max_bot` обращаются к `localhost:5000/account-api`. Остальные проекты физически изолированы, но имеют высокий потенциал для интеграции в единую песочницу.

### Ключевые выводы

| Аспект | Оценка | Главные проблемы |
|---|---|---|
| Архитектура | Средняя | Дублирование, хрупкие `sys.path.insert`, отсутствие shared-библиотек |
| Качество кода | Низкая-средняя | Огромные модули, нет тестов, широкие `except`, много хардкода |
| Безопасность | **Критическая** | Утечка секретов, path traversal, CSRF, webhook без секрета |
| UI/UX | Средняя | Разрозненные дизайны, inline-стили, слабая accessibility |
| Визуализация | Высокая | Богатый набор инструментов, но без унификации |
| Готовность к интеграции | Высокая | 03 и 08/09 уже связаны с 01; 02/04/06 легко встроить |

### Три главных риска

1. **Повреждение состояния**: `state.json`, `task_state.json`, `JSONStorage`, `Viz Lab SessionStore` — read-modify-write без блокировок.
2. **Уязвимости безопасности**: endpoint `/ccxt-api/api/env-keys` отдаёт секреты, path traversal в Viz Lab, CSRF на `/delete`, MAX-webhook без секрета.
3. **Массовое дублирование**: Bitget-клиенты, Telegram/MAX-боты, визуализация — ни одного shared-пакета.

---

## 2. Методология анализа

Для объективного сравнения проектов, технологий и вариантов интеграции использовались следующие методы:

| Метод | Применение | Форма |
|---|---|---|
| **Feature Matrix** | Наличие функций по проектам | Таблица |
| **Integration Readiness Matrix** | Готовность к встраиванию в 01 | Приоритет / сложность |
| **Risk / Effort Matrix** | Приоритизация проблем | 2×2 квадрант |
| **Technology Radar** | Визуализационные библиотеки | Adopt / Trial / Assess / Hold |
| **Pros/Cons Comparison** | Варианты интеграции | Таблица |
| **Dependency Mapping** | Связи между проектами | Граф/таблица |
| **Static Code Review** | Качество кода и безопасность | Примеры с путями |

---

## 3. Инвентаризация проектов

| # | Проект | Entry point | Тип | Зрелость | Примечание |
|---|---|---|---|---|---|
| 01 | `fundament_rf` | `app.py` | Flask-монолит | High | Хаб, 9+ blueprints |
| 02 | `graphs_candle` | `main.py` | Flask demo | Medium | Plotly + SVG |
| 03 | `demo_charts_ascii` | `app.py` | Flask demo | Medium | ASCII + Plotly + Chart.js |
| 04 | `tradingview-demos` | `update_widgets.py` | Static/Vercel | Low | TradingView widgets |
| 05 | `transcript` | `transcript_pipeline.py` | CLI pipeline | Medium | yt-dlp + Whisper |
| 06 | `screenshots_project` | `catalog.html` | Static/Vercel | Low | Каталог скриншотов |
| 07 | `tg_bot_aiforguest` | `bot/main.py` | Telegram bot | High | ~2454 строк в `handler.py` |
| 08 | `ofd_api` | `routes.py` | Flask Blueprint | Medium-High | Уже интегрирован в 01 |
| 09 | `model_catalog` | `models_catalog.json` | JSON catalog | Low | Уже используется в 01 |
| 10 | `max_bot` | `main.py` | MAX bot | Medium | Сателлит 07 |
| 11 | `med_life` | `scripts/generate_combined_analysis.py` | Data/Atlas | Medium | Медицинские данные, PDF-отчёты |

### Технологический стек

| Проект | Язык/фреймворк | Ключевые библиотеки |
|---|---|---|
| 01 | Python 3.12, Flask | plotly, ccxt, requests, numpy |
| 02 | Python, Flask | plotly, pandas, numpy, ccxt |
| 03 | Python, Flask | asciichart, plotext, termgraph, chart.js |
| 04 | HTML/JS | TradingView widgets |
| 05 | Python | yt-dlp, openai, requests |
| 06 | HTML/CSS | — |
| 07 | Python | python-telegram-bot, httpx, numpy |
| 08 | Python, Flask | — |
| 09 | Python (JSON) | — |
| 10 | Python 3.12 | httpx, python-dotenv |
| 11 | Python | fpdf, markdown |

---

## 4. Архитектура и связи

### 4.1. Карта связей

| От проекта | Куда смотрит | Механизм |
|---|---|---|
| `01_fundament_rf` | `08_ofd_api` | `importlib` + blueprint |
| `01_fundament_rf` | `09_model_catalog` | чтение JSON через `Path` |
| `03_demo_charts_ascii` | `01_fundament_rf` | fallback `data/card` |
| `05_transcript` | `09_model_catalog` | чтение `models_catalog.json` |
| `05_transcript` | `07_tg_bot_aiforguest` | запись в `TG_ALL/` |
| `07_tg_bot_aiforguest` | `08_ofd_api/bot_ofd` | `sys.path.insert` |
| `07_tg_bot_aiforguest` | `tools/scripts` | `sys.path.insert` |
| `07_tg_bot_aiforguest` | `01_fundament_rf` | HTTP `localhost:5000/account-api` |
| `10_max_bot` | `08_ofd_api/bot_ofd` | `sys.path.insert` |
| `10_max_bot` | `tools/scripts` | `sys.path.insert` |
| `10_max_bot` | `01_fundament_rf` | HTTP `localhost:5000/account-api` |
| `11_med_life` | `10_max_bot` | `sys.path.insert` + `MAXClient.send_file()` |

### 4.2. Общие ресурсы

| Ресурс | Пользователи | Проблема |
|---|---|---|
| Root `.env` | 01, 05, 07, 08, 10 | Права 644 |
| Root venv | 03, 04, 05, 06, 08, 10 | Нет изоляции |
| `tools/scripts` | 07, 10 | Неизвестное содержимое |

---

## 5. Дублирование кода

### 5.1. Bitget / биржевая логика

| Компонент | Файл |
|---|---|
| REST API цены | `01/routes/graphics.py` |
| REST API свечи 1D | `01/routes/processor_1d.py` |
| Account client (HMAC) | `01/account/api_client.py` |
| CLI checker | `01/bitget_checker.py` |
| CCXT proxy | `01/routes/ccxt_api.py` |
| TG/MAX symbol prefix | `07/bot/handler.py`, `10/handler.py` |

**Рекомендация:** создать `shared/bitget_client.py` с HMAC, REST и WebSocket-обёртками.

### 5.2. Telegram / MAX bot логика

| Модуль | 07 | 10 |
|---|---|---|
| Handler | `bot/handler.py` (2454 строки) | `handler.py` (889 строк) |
| Config | `bot/config.py` | `config.py` |
| Session | `bot/session.py` | `bot/session.py` |
| Screenshot | `bot/screenshot_*.py` | импорты/копии |
| Sync exchange | `bot/sync.py` | `bot/sync.py` |

**Рекомендация:** вынести общее в `shared/bot_core/`.

### 5.3. Визуализация

| Функция | Где дублируется |
|---|---|
| OHLC / candlestick | `01/infographics/charts.py`, `02/charts/candlestick.py`, `03/indicators.py` |
| PnL chart | `01/infographics/charts.py`, `02/charts/pnl.py` |
| Индикаторы (SMA, RSI, MACD, BB) | `01/calculator/indicators.py`, `03/indicators.py` |
| SVG charts | `01/infographics/svg.py`, `02/charts/svg_charts.py` |

### 5.4. Внутри `05_transcript`

Функции `fetch_playlist_entries`, `process_single_video`, `process_playlist` продублированы **трижды** в `transcript_pipeline.py`.

---

## 6. Качество кода и технический долг

### 6.1. Race conditions и потокобезопасность

| Проблема | Локация | Уровень |
|---|---|---|
| `JSONStorage` singleton без блокировок | `01/storage.py` | High |
| `sync-all` пишет в общие JSON без синхронизации | `01/routes/processor.py` | High |
| `SessionStore` Viz Lab не потокобезопасен | `01/viz_lab/storage/session.py` | High |
| `task_state.json` read-modify-write без блокировок | `07/bot/task_state.py` | High |
| Блокировка `state.json` удерживается во время сна/subprocess | `07/bot/session.py` | High |
| Кэш провайдеров OFD без синхронизации | `08/routes.py` | Medium |

### 6.2. Обработка ошибок

- **281** широких блока `except Exception` или `except:`.
- Подавление ошибок без логирования в `01/routes/processor.py`.
- `except:` без типа в `07/bot/commands.py`.
- Отсутствие exponential backoff в retry-логике.

### 6.3. Хардкод и магические числа

| Что | Где | Пример |
|---|---|---|
| Плечо по умолчанию `10` | 01, 07, 10 | `data.get("leverage", 10)` |
| `localhost:5000` | 07, 10 | base URL HTTP-клиента |
| `BITGET:` prefix | 07, 10 | `f"BITGET:{raw}"` |
| Модели по умолчанию | 07, 10 | `opencode/deepseek-v4-flash-free` |
| Цены токенов | 07 | `0.27 / 1_000_000` |

### 6.4. Размер модулей / нарушение SRP

| Модуль | Строк | Проблема |
|---|---|---|
| `07/bot/handler.py` | 2454 | Команды, скриншоты, HTTP, whois, голос, перезапуск |
| `07/bot/commands.py` | 1074 | Пользователи, сессии, модели, токены |
| `07/bot/session.py` | 896 | Хранение, миграции, квоты, subprocess |
| `01/routes/account_api.py` | 834 | Баланс, позиции, ордера, сделки, live-данные |

### 6.5. Явные баги

| Баг | Локация |
|---|---|
| Неопределённая переменная `out_path` | `05/transcript_pipeline.py` |
| Утечка файлового дескриптора | `05/transcript_pipeline.py` |
| `os._exit(0)` без graceful shutdown | `10/handler.py` |
| Суммирование всех активов как USDT | `01/account/api_client.py` |
| `abs(fee_amount)` теряет знак комиссии | `01/account/api_client.py` |

### 6.6. Тестируемость

- **Нет ни одного теста** во всех проектах.
- Нет mock-объектов.
- Все внешние API вызываются напрямую.
- Активно используется `subprocess`, что усложняет тестирование.

---

## 7. Аудит безопасности

### 7.1. Критические находки

| # | Проблема | Локация | Риск |
|---|---|---|---|
| 1 | Endpoint отдаёт Bitget-секреты | `01/routes/ccxt_api.py` `/api/env-keys` | Утечка ключей |
| 2 | Path traversal + удаление файлов | `01/routes/viz_lab.py` `delete_file_by_path` | Удаление `.env`, `/etc/passwd` |
| 3 | Path traversal в чтении | `01/routes/viz_lab.py` чтение файлов | Чтение произвольных файлов |
| 4 | Раскрытие дерева workspace | `01/routes/viz_lab.py` `/api/project-tree` | Информационная утечка |
| 5 | CSRF GET `/delete/<obj_id>` | `01/routes/web.py` | Несанкционированное удаление |
| 6 | MAX webhook без секрета | `10/main.py`, `max_bot.sh` | Фейковые обновления |
| 7 | Захардкоженные Bitget-ключи | `01/bitget_checker.py` | Попадание в git |
| 8 | Токены OFD в `.env` проекта | `08/ofd_storage/__init__.py` | Утечка токенов |
| 9 | OFD-токен в `localStorage` | `08/static/js/ofd_api.js` | XSS → утечка |
| 10 | Поля токенов plain text | `08/templates/ofd_api.html` | Shoulder surfing |

### 7.2. Отсутствующие защиты

- Нет `app.secret_key` в 01, 02, 03.
- Нет rate limiting ни в одном Flask-проекте.
- Нет CSRF-токенов.
- Нет авторизации на `/ofd-api/*`, `/viz-lab/*`, `/ccxt-api/*`.
- `03_demo_charts_ascii` запущен с `debug=True` и CORS `*`.

### 7.3. Права доступа

| Файл | Права | Рекомендуемые |
|---|---|---|
| Root `.env` | 644 | 600 |
| `07/.env` | 644 | 600 |
| `10/.env` | 644 | 600 |
| `08/data/ofd/.../.env` | 644 | 600 |
| `07/bot/state.json` | 644 | 600 |
| `10/bot/state.json` | 644 | 600 |

---

## 8. UI/UX и визуализация

### 8.1. Технологии визуализации

| Технология | Проекты | Плюсы | Минусы | Применение |
|---|---|---|---|---|
| **Plotly** | 01, 02, 03, 08 | Интерактивность, OHLC, subplots | Тяжёлый JS, CDN | Аналитика, финансовые графики |
| **SVG custom** | 01, 02 | Лёгкий, вектор, контроль | Ручной код | KPI, donut, sparklines |
| **ASCII/plotext** | 01, 03 | CLI-friendly | Плохая читаемость в веб | Логи, Telegram, демо |
| **TradingView Widget** | 04 | Профессиональный UI | Внешняя зависимость | Публичные виджеты |
| **Chart.js** | 03 | Простой | Меньше возможностей | Комбо-дашборды |
| **Canvas 2D** | 01, 03 | Быстрый | Нет интерактивности | Генеративная графика |

### 8.2. Общие проблемы UI/UX

- **Inline-стили** — главный техдолг (`card.html`, `index.html`, `account/index.html`).
- **Дублирование версий**: `graphics/all.html` vs `graphics_v2/all.html`.
- **Слабая accessibility**: почти нет `aria-label`, `label`, `focus-visible`.
- **Непоследовательный responsive**: есть media queries, но много фиксированных размеров.
- **CDN в production**: Tailwind CDN в 02, TradingView iframe без fallback.
- **Разрозненные палитры**: 5+ разных цветовых схем.

### 8.3. Сильные стороны

- Единый `base.html` в 01 с темной/светлой темой.
- CSS-переменные в `01/static/css/style.css`.
- `trade_analytics.html` — хороший responsive layout.
- `graphics_v2/all.html` — Bento-like grid.
- `viz_lab/lab.html` — уже задуман как песочница.

---

## 9. Архитектура песочницы

### 9.1. Варианты интеграции

| Критерий | Монолит | Микрофронтенды | Портал-навигатор (рекомендуем) |
|---|---|---|---|
| Сложность | Высокая | Средняя | Низкая |
| Изоляция отказов | Плохая | Хорошая | Хорошая |
| Конфликты зависимостей | Высокий риск | Низкий | Низкий |
| Скорость внедрения | Медленно | Средне | Быстро |
| Единый UI | Да | Частично | Да (iframe) |
| Health-check | Встроенный | Свой | Централизованный |

**Выбор:** использовать **портал-навигатор** как основной паттерн. Для повторно используемых виджетов допускается лёгкий микрофронтенд через `postMessage`.

### 9.2. Целевая маршрутизация

| Путь | Назначение |
|---|---|
| `/sandbox/` | Главная: карточки всех проектов |
| `/sandbox/project/<id>/` | Страница проекта |
| `/sandbox/project/<id>/<section>/` | Подраздел |
| `/sandbox/health` | Дашборд статусов |
| `/sandbox/api/health` | JSON статусов |
| `/sandbox/api/registry` | JSON реестра |
| `/sandbox/logs/<id>` | Безопасное чтение логов |
| `/proxy/<id>/<path>` | Flask-прокси к внутренним портам 02/03 |
| `/static/sandbox/<id>/<path>` | Статический mount для 04/06 |

### 9.3. Матрица встраивания

| # | Проект | Тип | Встраивание | Примечание |
|---|---|---|---|---|
| 01 | fundament_rf | Flask-хост | Нативно | Уже хаб |
| 02 | graphs_candle | Flask | `/proxy/02/*` → localhost:5002 | iframe |
| 03 | demo_charts_ascii | Flask | `/proxy/03/*` → localhost:5003 | iframe |
| 04 | tradingview-demos | Static | `/static/sandbox/04/*` | mount |
| 05 | transcript | CLI | статус + лог | Нет UI |
| 06 | screenshots_project | Static | `/static/sandbox/06/*` | mount |
| 07 | tg_bot_aiforguest | Bot | статус + лог | Нет UI |
| 08 | ofd_api | Blueprint | iframe `/ofd-api` | Уже в 01 |
| 09 | model_catalog | JSON | `/ai-models` | Уже в 01 |
| 10 | max_bot | Bot | статус + лог | Нет UI |
| 11 | med_life | Atlas | `/med-life/*` | Blueprint в 01 |

---

## 10. Project 11: Med Life / Atlas of Human

### 10.1. Структура данных

```
11_med_life/
├── data/objects/<patient_id>/
│   ├── meta.json
│   └── entries/
│       ├── YYYY-MM-DD_001_examination.json
│       ├── YYYY-MM-DD_002_event.json
│       └── YYYY-MM-DD_003_lab.json
├── data/drug_reference/<drug_id>/
│   ├── meta.json
│   └── analysis/*.md
├── data/price_tracker/<drug_id>.json
└── scripts/
    ├── generate_combined_analysis.py
    └── generate_prescriptions_pdf.py
```

### 10.2. Домены записей

| Домен | Описание |
|---|---|
| `examination` | Осмотр специалиста |
| `lab` | Лабораторные анализы |
| `medication` | Приём препарата |
| `event` | Медицинские события |
| `subjective` | Самочувствие (шкалы 0–10) |
| `lifestyle` | Сон, питание, активность |

### 10.3. Подключение к Flask

Создаётся Blueprint `med_life` в `01_fundament_rf`:

```python
bp = Blueprint('med_life', __name__, url_prefix='/med-life')
```

### 10.4. Концепция «Атласа человека»

Левая панель с SVG-иконками **12 жизненных систем**:

1. Сердечно-сосудистая
2. Дыхательная
3. Нервная
4. Эндокринная
5. Опорно-двигательная
6. Пищеварительная
7. Мочевыделительная
8. Иммунная / аллергическая
9. Репродуктивная
10. Сенсорная
11. Психоэмоциональная
12. Общий обзор (радар)

### 10.5. Паспорт состояния

| Слой | Данные |
|---|---|
| Идентификация | ФИО, пол, ДР, группа крови |
| Диагнозы | основной, вторичный |
| Аллергии | `meta.allergies` |
| Терапия | активные препараты + цены |
| Измерения | lab + subjective + lifestyle |
| События | timeline |
| Документы | PDF/MD отчёты |

---

## 11. Roadmap

### Этап 0. Безопасность и стабильность (P0)
- [ ] Удалить/защитить `/ccxt-api/api/env-keys`.
- [ ] Исправить path traversal в Viz Lab.
- [ ] Перевести `/delete/<obj_id>` на POST + CSRF.
- [ ] Установить `MAX_WEBHOOK_SECRET`.
- [ ] Удалить захардкоженные ключи из `bitget_checker.py`.
- [ ] Права 600 на `.env`, `state.json`, логи.
- [ ] Ввести атомарную работу с JSON (`filelock`, tmp+rename).
- [ ] `app.secret_key` для Flask-проектов.

### Этап 1. Shared библиотеки
- [ ] `shared/bitget_client.py` — REST + HMAC.
- [ ] `shared/bot_core/` — session, task, screenshot, sync.
- [ ] `shared/storage.py` — потокобезопасное JSON-хранилище.

### Этап 2. Sandbox в 01
- [ ] `config/sandbox_registry.yaml`.
- [ ] `services/health_aggregator.py`.
- [ ] Blueprint `routes/sandbox.py`.
- [ ] Flask-прокси `routes/proxy.py`.
- [ ] Шаблоны `templates/sandbox/*.html`.
- [ ] Статический mount для 04/06.

### Этап 3. Med Life Atlas
- [ ] `routes/med_life.py`.
- [ ] `services/med_life_loader.py`.
- [ ] `templates/med_life/*.html`.
- [ ] `static/med_life/icons/*.svg`.

### Этап 4. Единая дизайн-система
- [ ] CSS-токены и компоненты.
- [ ] Удаление inline-стилей.
- [ ] Accessibility.

### Этап 5. Тесты и документация
- [ ] `pytest` + `tests/`.
- [ ] Retry с exponential backoff.
- [ ] Документация UI-kit и API.

---

## 12. Рекомендации

1. **Не мержить проекты в монолит** — риск дестабилизировать `01_fundament_rf`.
2. **Использовать портал-навигатор** с iframe/proxy и health-агрегатором.
3. **Сначала закрыть критические security-риски**, затем строить песочницу.
4. **Вынести shared-компоненты** в отдельные пакеты до масштабного рефакторинга.
5. **Добавить тесты** для критичных путей.
6. **Централизовать конфигурацию**: URL, порты, биржи, модели — в `.env` или YAML.
7. **Развивать `/viz-lab/`** и `/med-life/` как единые лаборатории.

---

## Appendix A: Критические файлы для аудита

- `/home/user_aioc/workspace/projects/01_fundament_rf/storage.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/app.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/routes/viz_lab.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/routes/web.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/routes/ccxt_api.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/account/api_client.py`
- `/home/user_aioc/workspace/projects/01_fundament_rf/bitget_checker.py`
- `/home/user_aioc/workspace/projects/07_tg_bot_aiforguest/bot/handler.py`
- `/home/user_aioc/workspace/projects/07_tg_bot_aiforguest/bot/session.py`
- `/home/user_aioc/workspace/projects/07_tg_bot_aiforguest/bot/task_state.py`
- `/home/user_aioc/workspace/projects/10_max_bot/handler.py`
- `/home/user_aioc/workspace/projects/10_max_bot/main.py`
- `/home/user_aioc/workspace/projects/05_transcript/transcript_pipeline.py`
- `/home/user_aioc/workspace/projects/08_ofd_api/routes.py`
- `/home/user_aioc/workspace/projects/08_ofd_api/ofd_storage/__init__.py`
- `/home/user_aioc/workspace/projects/11_med_life/scripts/generate_combined_analysis.py`

## Appendix B: Security Checklist

- [ ] Нет захардкоженных секретов в коде.
- [ ] `.env` и `state.json` имеют права 600.
- [ ] Endpoint'ы не отдают секреты.
- [ ] Path traversal устранён.
- [ ] CSRF-токены на изменяющих операциях.
- [ ] Webhook'и проверяют подпись/секрет.
- [ ] Rate limiting включён.
- [ ] `debug=True` отключён в production.
- [ ] CORS ограничен.
- [ ] XSS-векторы экранированы.
