# Fix: Concurrent access to state.json

## Проблема

TG Bot и MAX Bot разделяют один `state.json`. Оба бота делают `_load()` → модифицируют → `_save()`. Между чтением и записью второй процесс может перезаписать файл, теряя изменения первого.

## Решение

Добавить cross-process блокировку через `fcntl.flock` на отдельный lock-файл `state.json.lock`.

## Изменения в `session.py`

### 1. Добавить imports и `_LOCK_FILE` / `_transaction()`

```python
import contextlib
import fcntl
import os

_LOCK_FILE = STATE_FILE.parent / (STATE_FILE.name + ".lock")


@contextlib.contextmanager
def _transaction():
    """Атомарная read-modify-write транзакция с cross-process блокировкой."""
    _LOCK_FILE.parent.mkdir(parents=True, exist_ok=True)
    fd = os.open(str(_LOCK_FILE), os.O_CREAT | os.O_RDWR)
    try:
        fcntl.flock(fd, fcntl.LOCK_EX)
        yield
    finally:
        fcntl.flock(fd, fcntl.LOCK_UN)
        os.close(fd)
```

### 2. Обернуть `_load() → _save()` паттерн в `with _transaction():`

Для каждой функции, которая делает `state = _load()` + `_save(state)`:

| Функция | Строки | Тип обёртки |
|---------|--------|-------------|
| `link_platforms` | 162-192 | Весь блок |
| `add_platform_link` | 195-208 | Весь блок |
| `add_user` | 244-263 | Весь блок |
| `remove_user` | 266-269 | Весь блок |
| `ensure_super` | 277-291 | Весь блок |
| `set_session_opencode_id` | 294-301 | Весь блок |
| `reset_opencode_id` | 305-313 | Весь блок |
| `set_session_tokens` | 317-325 | Весь блок |
| `create_session` | 346-377 | Весь блок |
| `switch_session` | 380-386 | Весь блок |
| `rename_session` | 390-397 | Весь блок |
| `drop_session` | 401-416 | Весь блок |
| `dropsession_by_key` | 420-434 | Весь блок |
| `save_last_task` | 632-641 | Весь блок |
| `clear_last_task` | 644-649 | Весь блок |
| `reset_session_counters` | 662-671 | Весь блок |
| `update_session_tokens` | 727-736 | Только `_load/_save` |
| `increment_msg` | 745-754 | Весь блок |
| `set_user_model` | 757-763 | Весь блок |
| `set_default_model` | 767-770 | Весь блок |
| `append_model_history` | 773-782 | Весь блок |
| `set_limit` | 785-796 | Весь блок |
| `set_build_mode` | 831-842 | Весь блок |

**Паттерн для каждой функции** — "было" → "стало":

```python
# Было
def add_user(uid, name, ...):
    state = _load()
    ...
    _save(state)

# Стало
def add_user(uid, name, ...):
    with _transaction():
        state = _load()
        ...
        _save(state)
```

Исключение: `update_session_tokens` (строки 674-742). Там есть `time.sleep(2)`, subprocess вызовы. Обернуть только `_load/_save`:

```python
    with _transaction():
        state = _load()
        sid = _sid(uid)
        u = state["users"].get(sid)
        if u and key in u["sessions"]["list"]:
            sess = u["sessions"]["list"][key]
            ...
            _save(state)
```

### 3. Read-only функции (не трогаем)

Эти функции только читают `_load()` без записи. Stale read допустим:

- `resolve_uid`, `get_user`, `user_exists`, `is_super`, `get_current_session`
- `get_session_full`, `list_users`, `get_session_opencode_id`
- `get_session_agent`, `resolve_session`, `rebuild_ranks`
- `user_dir`, `get_quota`, `list_unauthorized`, `_context_limit`
- `_recalc_stats`, `log_unauthorized`

## Изменения в `commands.py`

Импорты `from session import _load, _save` (строки 390, 440, 1023, 1045) — обернуть в `with _transaction():`:

```python
from session import _load, _save, _transaction
with _transaction():
    state = _load()
    ...
    _save(state)
```

## Порядок применения

1. `session.py`: добавить imports + `_LOCK_FILE` + `_transaction()`
2. `session.py`: обернуть 23 функции
3. `commands.py`: обернуть 4 места
