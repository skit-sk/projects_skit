# Skills Directory

Директория `/skills` содержит инструкции для AI-агентов по использованию инструментов.

## Доступные скиллы

| Скилл | Путь | Описание |
|-------|------|----------|
| **agent-browser** | [agent-browser/](agent-browser/) | Browser automation для AI-агентов |
| **graphifyy** | [graphifyy/](graphifyy/) | Knowledge graph из кода/документов |
| **awesome-design-md** | [awesome-design-md/](awesome-design-md/) | Коллекция DESIGN.md файлов брендов |
| **ui-ux-design-pro** | [ui-ux-design-pro/](ui-ux-design-pro/) | Генерация кастомных дизайн-систем |

---

## agent-browser

AI-агент использует **agent-browser** для автономного управления браузером.

### Основные команды

| Команда | Назначение |
|---------|------------|
| `agent-browser open <url>` | Открыть страницу |
| `agent-browser snapshot -i` | Получить элементы с референсами |
| `agent-browser click @eN` | Клик по референсу |
| `agent-browser fill @eN "text"` | Заполнить поле |
| `agent-browser find role button click --name "X"` | Семантический локатор |

### Workflow для AI-агента

```
1. agent-browser open <url>
2. agent-browser snapshot -i → получить [ref=e1], [ref=e2], etc.
3. agent-browser click @eN → клик без селекторов
4. agent-browser fill @eN "text" → заполнить
```

### Файлы скилла

| Файл | Назначение |
|------|------------|
| `skill.md` | Основной скилл (для agent config) |
| `instructions.md` | Подробные инструкции |
| `examples.md` | Примеры использования |

### Быстрая ссылка

- Инструмент: [../../tools/agent-browser/](../../tools/agent-browser/)
- GitHub: https://github.com/vercel-labs/agent-browser