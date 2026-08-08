# SQLite Migration Plan: замена state.json на SQLite

## Мотивация

- **Параллелизм** — SQLite WAL-mode позволяет одновременное чтение + конкурентную запись
- **Атомарность mixed ops** — транзакции решают проблему create_session (пишет и system, и per-user)
- **Масштабирование** — не читаем весь файл при каждой операции
- **Нет flock** — SQLite сам управляет блокировками

---

## Этап 1: Схема БД

### Таблицы

```sql
-- SYSTEM
CREATE TABLE meta (
    key   TEXT PRIMARY KEY,
    value TEXT NOT NULL
);
-- ключи: super, default_model, session_seq

CREATE TABLE session_stats (
    stat  TEXT PRIMARY KEY,  -- total_created, total_deleted, active
    value INTEGER NOT NULL
);

-- USERS
CREATE TABLE users (
    uid          TEXT PRIMARY KEY,
    name         TEXT NOT NULL,
    role         TEXT NOT NULL DEFAULT 'normal',
    model        TEXT,
    limits_msg   INTEGER DEFAULT 50,
    limits_token INTEGER DEFAULT 1000000,
    limits_storage_mb INTEGER DEFAULT 500,
    limits_file_count INTEGER DEFAULT 1000,
    cwd          TEXT,
    last_task_text    TEXT,
    last_task_session TEXT,
    last_task_ts      INTEGER,
    created_at   INTEGER NOT NULL DEFAULT (unixepoch())
);

CREATE TABLE platform_links (
    uid         TEXT NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    platform    TEXT NOT NULL,
    platform_id INTEGER NOT NULL,
    PRIMARY KEY (uid, platform, platform_id)
);
CREATE INDEX idx_platform_links_platform ON platform_links(platform, platform_id);

-- SESSIONS
CREATE TABLE sessions (
    session_key  TEXT PRIMARY KEY,
    uid          TEXT NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    status       TEXT NOT NULL DEFAULT 'ACT',
    name         TEXT,
    created      INTEGER NOT NULL,
    messages     INTEGER NOT NULL DEFAULT 0,
    model        TEXT,
    opencode_id  TEXT,
    agent        TEXT,
    tokens       INTEGER NOT NULL DEFAULT 0,
    seq          INTEGER,
    cost         REAL NOT NULL DEFAULT 0.0,
    usage_input  INTEGER NOT NULL DEFAULT 0,
    usage_output INTEGER NOT NULL DEFAULT 0,
    last_msg_input  INTEGER NOT NULL DEFAULT 0,
    last_msg_output INTEGER NOT NULL DEFAULT 0,
    build_mode   INTEGER NOT NULL DEFAULT 0,
    is_current   INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX idx_sessions_uid ON sessions(uid);
CREATE INDEX idx_sessions_status ON sessions(status);

-- MODEL HISTORY (capped at 50/user)
CREATE TABLE model_history (
    uid   TEXT NOT NULL REFERENCES users(uid) ON DELETE CASCADE,
    ts    REAL NOT NULL,
    model TEXT NOT NULL,
    setter_by INTEGER,
    id    INTEGER PRIMARY KEY AUTOINCREMENT
);
CREATE INDEX idx_model_history_uid ON model_history(uid, id);
```

### Миграция existing state.json

Скрипт migrate_to_sqlite.py:
- Читает state.json целиком
- Вставляет meta, session_stats
- Для каждого user: users, platform_links, model_history, sessions
- Одноразовый, idempotent (INSERT OR IGNORE)

---

## Этап 2: Database Access Layer (db.py)

Новый файл `projects/07_tg_bot_aiforguest/bot/db.py`.

- `transaction()` — context manager с BEGIN IMMEDIATE
- `read_transaction()` — context manager для reads
- WAL mode + busy_timeout=5000

Методы (дублируют все функции session.py):

| session.py | db.py |
|------------|-------|
| _load / _save | transaction() context manager |
| resolve_uid(any_id) → str | resolve_uid(platform, platform_id) → uid |
| get_user(uid) → dict | get_user(uid) → dict (та же структура) |
| add_user(...) | INSERT INTO users |
| ensure_super() | INSERT OR IGNORE super user |
| create_session(uid) | INSERT INTO sessions + UPDATE stats |
| link_platforms(...) | INSERT INTO platform_links |
| set_user_model(uid, model) | UPDATE users SET model=? |
| set_limit(...) | UPDATE users SET limits_*=? |
| increment_msg(uid) | UPDATE sessions SET messages=messages+1 |
| update_session_tokens(...) | UPDATE sessions SET tokens=?, usage_*=?, cost=? |
| set_build_mode(...) | UPDATE sessions SET build_mode=? |
| save_last_task(...) | UPDATE users SET last_task_*=? |
| append_model_history(...) | INSERT INTO model_history (capped at 50) |
| set_default_model(model) | INSERT OR REPLACE INTO meta |
| get_session_full(uid) | SELECT user + sessions + stats |
| list_users() | SELECT * FROM users |
| get_all_pending_tasks() | SELECT uid, last_task_* FROM users WHERE last_task_text IS NOT NULL |
| rebuild_ranks(uid) | SELECT + window functions / ORDER BY |

---

## Этап 3: Подключение

### Вариант A: session.py → тонкая обёртка

```python
# session.py
from db import (
    get_user, add_user, create_session, resolve_uid,
    link_platforms, set_user_model, ...
)
# ничего своего — все функции живут в db.py
```

Все импорты `from session import ...` продолжают работать без изменений.

### Вариант B: Dual-backend (для отката)

```python
# config.py
DB_BACKEND = "sqlite"  # или "json"

# session.py
if DB_BACKEND == "sqlite":
    from db import get_user
else:
    # старый JSON-код
```

---

## Этап 4: План деплоя

1. Создать db.py + migrate_to_sqlite.py в bot/
2. Остановить ботов: `./scripts/tg_bot.sh stop && ./scripts/max_bot.sh stop`
3. Запустить миграцию: `python3 migrate_to_sqlite.py` → создаст bot_state.db
4. Переключить session.py на импорт из db.py
5. Запустить ботов: `./scripts/tg_bot.sh start && ./scripts/max_bot.sh start`
6. В мониторинге проверить, что state.json больше не пишется (только читается для совместимости)
7. Через неделю — удалить state.json + JSON-код из session.py

---

## Оценка

| Файл | Строк | Сложность |
|------|-------|-----------|
| db.py | ~500 | Средняя |
| migrate_to_sqlite.py | ~100 | Низкая |
| session.py (переделка) | ~50 | Низкая |
| **Итого** | **~650** | |

### Выигрыш

- ✅ Нет race condition (транзакции)
- ✅ Нет блокировки между юзерами (row-level locking)
- ✅ resolve_uid за O(1) вместо O(N)
- ✅ session_stats.active вычисляется в SQL, а не перебором
- ✅ Меньше данных грузится в память
- ✅ Одна БД вместо `state.json` + надо будет `task_state.json` можно туда же

### Риски

- ⚠️ Код импорта из session.py размазан по 8 файлам — нужно проверить, что все имена остались
- ⚠️ sqlite3 должен быть доступен (built-in в Python, ок)
- ⚠️ Два бота могут открывать одну БД — busy_timeout + WAL спасают
