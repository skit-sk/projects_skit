# Apply: Build mode only super + screenshot check

## Step 1 — Edit commands.py

**File:** `projects/07_tg_bot_aiforguest/bot/commands.py`
**Target:** function `cmd_build(uid)` around line 537

Add `is_super` check after `_check_user`:

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

## Step 2 — Verify handler.py

**File:** `projects/07_tg_bot_aiforguest/bot/handler.py`

Check that `/build` is in the handlers dict (around line 83):

```python
"/build": lambda: cmd_build(uid),
```

If missing — add it.

## Step 3 — Update skill docs

**File:** `skills/instructions/tg_bot.md`

Update section 9:
- `/build` only for super users
- Normal users always in `plan` mode

## Step 4 — Restart bot

```bash
cd /home/user_aioc/workspace && ./scripts/tg_bot.sh restart
```

## Step 5 — Test

```bash
# Test normal user cannot access build
# Test super user: /build сделай скриншот TradingView DOTUSDT 1D
# Verify auto-revert to plan after response
```
