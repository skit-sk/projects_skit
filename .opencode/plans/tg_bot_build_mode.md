# План: Build mode только super + screenshot

## 1. `bot/commands.py:cmd_build()` — добавить is_super

```python
def cmd_build(uid):
    err = _check_user(uid)
    if err:
        return err
    if not is_super(uid):
        return "❌ Только super."
    if set_build_mode(uid, True):
        return "✅ Build mode включён для следующего сообщения. После ответа — автоматически вернусь в plan."
    return "❌ Не удалось включить build mode."
```

## 2. `bot/handler.py` — `/build` уже добавлен, изменений не требует

## 3. `skills/instructions/tg_bot.md` — обновить правило

Строка 61: `/build` только super.

## 4. Перезапуск

```bash
./scripts/tg_bot.sh restart
```
