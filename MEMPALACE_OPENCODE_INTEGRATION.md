# MemPalace + OpenCode: Интеграция локальной памяти AI

## Исследование

### Цель

Подключить MemPalace (локальная система памяти AI) к OpenCode через MCP протокол для накопления контекста между сессиями.

### Источники

- [MemPalace SKILL.md](https://github.com/milla-jovovich/mempalace-Aya-fork/blob/develop/integrations/openclaw/SKILL.md)
- [OpenCode MCP Docs](https://opencode.ai/docs/mcp-servers)

### Компоненты

- **MemPalace** v3.3.0 — Python, локальная ChromaDB, MCP server
- **OpenCode MCP** — нативная поддержка локальных и удалённых MCP серверов
- **Конфиг**: `~/.config/opencode/opencode.json`

---

## Решение: Интеграция

### Архитектура

```
OpenCode <--MCP--> mempalace.mcp_server <---> ChromaDB (local)
```

### План выполнения

#### 1. Проверка окружения

```bash
python3 --version  # >= 3.10
pip3 --version
```

#### 2. Установка и инициализация

```bash
pip3 install mempalace
mempalace init ~/my-palace
```

#### 3. Конфигурация MCP в opencode.json

```json
{
  "mcp": {
    "mempalace": {
      "type": "local",
      "command": ["python3", "-m", "mempalace.mcp_server"],
      "enabled": true
    }
  }
}
```

#### 4. Верификация

```bash
opencode mcp list  # должен показать mempalace
```

---

## Автоматическое логирование сессий

### Проблема

`mempalace_diary_write` требует ручного вызова — не происходит автоматически.

### Решение: customInstructions

В `opencode.json` добавить:

```json
{
  "customInstructions": {
    "system": "После каждой сессии, перед завершением диалога, САМОСТОЯТЕЛЬНО предложи записать итог: 'Хотите сохранить итог сессии в память?' — и если пользователь согласится, вызови mempalace_diary_write с кратким содержанием."
  }
}
```

### Триггеры для предложения записи

- Ключевые слова: "пока", "bye", "закончили", "завершили"
- После принятия важных решений
- После обсуждения фактов о людях/проектах

---

## Протокол использования

### При каждом старте сессии

OpenCode автоматически вызывает `mempalace_status` → загружает контекст palace.

### При запросах о прошлых решениях

```
Вы: "Что решили в прошлый раз про БД?"
→ mempalace_search("база данных проект")
→ Ответ на основе palace
```

### После сессии

```
Вы: "Пока"
→ OpenCode: "Сохранить итог?"
→ Вы: "Да"
→ mempalace_diary_write(...)
```

---

## Структура palace

| Уровень | Назначение       | Пример                    |
|---------|------------------|---------------------------|
| Wing    | Проект/человек   | `wing_work`, `wing_ai-project` |
| Hall    | Категория        | facts, events, preferences |
| Room    | Тема             | `database-choice`, `api-design` |
| Drawer  | Чанк памяти      | verbatim text              |

---

## Итог

- **Установка**: ~5 минут
- **Наполнение**: постепенное через diary_write
- **Поиск**: автоматический при запросах о прошлых сессиях
- **Данные**: локально в `~/my-palace`, без облака, без API ключей