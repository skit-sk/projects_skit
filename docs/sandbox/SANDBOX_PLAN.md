# План песочницы на базе 01_fundament_rf

**Цель:** создать в `01_fundament_rf` единый визуальный контроль-центр для всех проектов workspace.

## 1. Принципы

1. `01_fundament_rf` — хост, но не поглощает код других проектов.
2. Проекты запускаются изолированно (свои порты / процессы).
3. Веб-проекты встраиваются через iframe.
4. Во внешку открыт только порт 5000 — всё остальное проксируется через 01.
5. CLI/боты показываются как карточки статуса + логи.
6. Единая навигация в `base.html`.
7. Централизованный health-check.

## 2. Маршруты

| Путь | Назначение |
|---|---|
| `/sandbox/` | Главная страница: сетка карточек проектов |
| `/sandbox/project/<id>/` | Страница проекта: описание + iframe/ссылки |
| `/sandbox/project/<id>/<section>/` | Подраздел проекта |
| `/sandbox/health` | HTML-дашборд статусов |
| `/sandbox/api/health` | JSON статусов всех сервисов |
| `/sandbox/api/registry` | JSON реестра проектов |
| `/sandbox/logs/<id>?n=50` | Последние N строк лога |
| `/proxy/<int:id>/<path:path>` | Flask-прокси к внутренним портам 02/03 |
| `/static/sandbox/<id>/<path>` | Статический mount для 04/06 |

## 3. Проксирование через порт 5000

Поскольку во внешку открыт только порт 5000, все внешние Flask-проекты доступны через прокси внутри 01:

| Внешний URL | Цель |
|---|---|
| `/proxy/02/<path>` | `localhost:5002/<path>` |
| `/proxy/03/<path>` | `localhost:5003/<path>` |

HTML проектов 02/03 патчится на лету: абсолютные ссылки `href="/..."`, `src="/..."`, `url(/...)` заменяются на `/proxy/NN/...`.

## 4. Статические проекты 04 и 06

Для полностью статичных проектов используется **static mount** в `static/sandbox/`:

| Внешний URL | Цель |
|---|---|
| `/static/sandbox/04/<path>` | файлы `projects/04_tradingview-demos/<path>` |
| `/static/sandbox/06/<path>` | файлы `projects/06_screenshots_project/<path>` |

Преимущества: не нужен отдельный процесс, нет HTML-патчинга, меньше нагрузки на Flask.  
Недостатки: требуется синхронизация при изменении исходных файлов.

## 5. Новые файлы в 01

```
projects/01_fundament_rf/
├── routes/
│   ├── sandbox.py              # Blueprint 'sandbox'
│   ├── proxy.py                # Flask-прокси /proxy/<id>/<path>
│   └── med_life.py             # Blueprint 'med_life' (см. docs/med_life)
├── services/
│   ├── health_aggregator.py    # опрос HTTP / процессов / логов
│   └── med_life_loader.py      # загрузка данных Med Life
├── config/
│   └── sandbox_registry.yaml   # метаданные проектов
└── templates/
    ├── sandbox/
    │   ├── index.html          # сетка карточек
    │   ├── project.html        # iframe + описание
    │   └── health.html         # таблица статусов
    └── med_life/
        └── ...                 # см. docs/med_life/FLASK_INTEGRATION_PLAN.md
```

## 6. Health Aggregator

Проверяет проекты по типу:

| Тип | Метод |
|---|---|
| `flask` | `GET health_url`, ожидаем 200, меряем `response_ms` |
| `static` | `GET entry_url`, ожидаем 200 |
| `bot` | `kill -0 $(cat pidfile)` или `pgrep -f` |
| `data` | существование директории и `mtime` последнего файла |
| `atlas` | как `flask` (Blueprint в 01) |

Результат:

```json
{
  "projects": {
    "02_graphs_candle": {"status": "up", "response_ms": 42},
    "07_tg_bot_aiforguest": {"status": "up", "pid": 1234}
  }
}
```

## 7. Безопасность логов

Endpoint `/sandbox/logs/<id>`:
- путь берётся только из реестра;
- запрещены `..`, `/etc`, `/root`;
- возвращает только последние N строк через `tail`;
- ограничение на размер файла.

## 8. UI

- Расширяет `base.html`.
- Карточки проектов с иконками, статусом, кнопками.
- Цвета статуса: `up` зелёный, `down` красный, `unknown` серый.
- Автообновление health каждые 30 секунд.

## 9. Этапы реализации

### Этап 1. Реестр и health
- Создать `config/sandbox_registry.yaml`.
- Реализовать `services/health_aggregator.py`.
- Добавить `/sandbox/api/health` и `/sandbox/api/registry`.

### Этап 2. Flask-прокси
- Создать `routes/proxy.py`.
- Патчинг HTML для 02/03.
- Проксирование headers, cookies, query string.

### Этап 3. Статический mount
- Скопировать `projects/04_tradingview-demos/*` → `static/sandbox/04/`.
- Скопировать `projects/06_screenshots_project/*` → `static/sandbox/06/`.

### Этап 4. Sandbox UI
- Создать Blueprint `routes/sandbox.py`.
- Шаблоны `templates/sandbox/index.html`, `project.html`, `health.html`.
- Добавить пункт `[Sandbox]` в `templates/base.html`.

### Этап 5. Med Life Atlas
- Создать `routes/med_life.py` и `services/med_life_loader.py`.
- Шаблоны `templates/med_life/*.html`.
- Иконки `static/med_life/icons/*.svg`.

### Этап 6. CLI/боты/данные
- Карточки для 05, 07, 09, 10, 11.
- PID, последняя строка лога, ссылка на лог.

### Этап 7. Оптимизации
- Reverse proxy: `localhost:5000/projects/<id>/` → upstream порты.
- Уведомления в Telegram/MAX при падении сервиса.

## 10. Запуск

```bash
./scripts/flask.sh start 01 5000   # хост + sandbox + proxy + med_life
./scripts/flask.sh start 02 5002   # graphs_candle
./scripts/flask.sh start 03 5003   # demo_charts_ascii

# static проекты не требуют запуска — они смонтированы в static/sandbox/

# боты
./scripts/tg_bot.sh start
./scripts/max_bot.sh start
```
