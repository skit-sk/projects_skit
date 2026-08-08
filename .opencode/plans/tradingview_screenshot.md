# Задача: доработка Telegram бота — скриншоты TradingView

## Контекст

Telegram бот-proxy к opencode (`projects/07_tg_bot_aiforguest/`).
Пользователь отправляет сообщение → бот передаёт в `opencode run` (AI-агент) → 
AI может использовать `agent-browser` для скриншотов → файл сохраняется,
но бот возвращает только **текст**, картинка не отправляется в Telegram.

## Цель

Модифицировать бота, чтобы после ответа opencode бот **детектил новые
изображения** в рабочей директории пользователя и отправлял их как
`reply_photo` в Telegram.

## План реализации (2 файла)

### 1. `bot/commands.py` — `cmd_message()`

Добавить снэпшот изображений ДО и ПОСЛЕ `run_opencode`,
возвращать 3-кортеж `(resp, err, new_images)`.

**Изменения:**

A) Все ранние `return None, err` → `return None, err, []` (4 места)

B) Перед вызовом `run_opencode` добавить:
```python
before = set(wd.rglob("*.[pj][np]g"))
```

C) После успешного выполнения (после `update_session_tokens`), перед return:
```python
after = set(wd.rglob("*.[pj][np]g"))
new_images = [str(p) for p in (after - before)]
```

D) Финальный return:
```python
return resp, None, new_images
```

**Полный дифф:** см. вложение `commands.py.diff`

### 2. `bot/handler.py` — `_handle_message()`

Изменить распаковку ответа и отправлять изображения.

**Было:**
```python
resp, err = await asyncio.to_thread(cmd_message, uid, text)
if err:
    await _reply(update, err, uid)
elif resp:
    await _reply(update, resp, uid)
```

**Стало:**
```python
resp, err, new_images = await asyncio.to_thread(cmd_message, uid, text)
if err:
    await _reply(update, err, uid)
elif resp:
    await _reply(update, resp, uid)
for img_path in new_images:
    with open(img_path, 'rb') as f:
        await update.message.reply_photo(photo=f)
```

### 3. Проверка работоспособности

После правок:

```bash
./scripts/tg_bot.sh restart
```

Отправить боту:
```
сделай скриншот TradingView DOTUSDT 1D, прими куки, скрой левую панель, отправь мне
```

Если AI-агент не может выполнить (ограничение `--agent plan`) — 
попробовать снять `agent = None` для super user или для запросов со словом "скриншот".

## Ожидаемый результат

1. Бот отправляет текст ответа opencode
2. Если opencode/AI создал PNG/JPG в `TG_ALL/TG_{uid}/` — бот отправляет
   каждое новое изображение как `reply_photo`
3. Скриншот TradingView DOTUSDT 1D приходит пользователю в чат

## Архитектурные заметки

- `TG_ALL_DIR` — `pathlib.Path`, работает `.rglob()`
- Рабочая директория пользователя `wd = TG_ALL_DIR / f"TG_{uid}"`
- `agent-browser` сохраняет скриншоты в `./screenshots/` (относительно wd)
  или в корень wd (зависит от команды AI)
- `.rglob("*.[pj][np]g")` ловит как `*.png` так и `*.jpg` во всех поддиректориях
- Лимит: отправлять макс 3 изображения за один ответ (защита от спама)
