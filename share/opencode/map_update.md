# Update Instructions

**Файл:** map_update.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Обзор

Карта знаний состоит из модульных файлов:

```
share/opencode/
├── map_all_small.md    # Главный файл (mindmap + навигация)
├── map_mermaid.md     # Mermaid диаграммы
├── map_tree.md        # Tree View
├── map_json.md        # JSON Structure
├── map_links.md       # Links Index
└── map_update.md      # Этот файл (инструкции)
```

---

## Автоматическое обновление

### Запуск скрипта

```bash
/home/user_aioc/workspace/scripts/update_knowledge_map.sh
```

### Алиас команды

```
/update_map
```

### Что делает скрипт

1. Проверяет структуру workspace
2. Собирает данные о проектах
3. Собирает данные о базах знаний
4. Проверяет ссылки
5. Генерирует JSON
6. Обновляет дату в map файлах

---

## Ручное обновление

### Добавление нового проекта

1. Создайте директорию проекта в `/home/user_aioc/workspace/`
2. Добавьте проект в `map_json.md` → `projects`
3. Определите домен и связи
4. Добавьте ссылки в `map_links.md`
5. Обновите `map_tree.md`
6. Обновите `map_mermaid.md` если нужно

### Добавление новой базы знаний

1. Создайте директорию в `/home/user_aioc/workspace/share/knowledge-base/`
2. Добавьте KB в `map_json.md` → `knowledge_bases`
3. Добавьте связь в `map_links.md`
4. Обновите `map_tree.md`

### Добавление новой связи

Отредактируйте `map_links.md`:

```markdown
| От | К | Тип | Описание |
|----|---|-----|----------|
| новый_проект | существующий | `related_to` | причина |
```

---

## Типы связей

### Связь project → project

```markdown
| `fundament_rf` | `graphs_candle` | `related_to` | trading domain |
```

### Связь project → technology

```markdown
| `fundament_rf` | `ccxt/Bitget` | `uses` | API |
```

### Связь project → KB

```markdown
| `fundament_rf` | `share/knowledge-base/tradingview/` | `related_to` | charts |
```

### Связь KB → project

```markdown
| `share/knowledge-base/tradingview/` | `tradingview-demos` | `documents` | examples |
```

---

## Форматы данных

### Типы узлов в JSON

| Тип | Описание | Пример |
|-----|----------|--------|
| `project` | Проект | `fundament_rf` |
| `knowledge_base` | База знаний | `tradingview` |
| `technology` | Технология | `ccxt`, `Plotly` |
| `domain` | Домен | `trading`, `visualization` |

### Типы связей в JSON

```json
{
  "type": "related_to | uses | documents | documented_by | belongs_to | depends_on",
  "direction": "bidirectional | unidirectional"
}
```

---

## Структура файлов карты

### map_all_small.md
- Mindmap (основной вид)
- Quick Navigation
- Ссылки на другие файлы

### map_mermaid.md
- Flowchart
- Hierarchical
- Sequence
- Pie Chart

### map_tree.md
- Полная структура workspace
- Краткая структура (только директории)

### map_json.md
- Полная JSON структура
- Упрощённый JSON для навигации
- Links JSON

### map_links.md
- Project → KB
- KB → Project
- Cross-Project
- Technology Links
- Domain Membership

### map_update.md
- Инструкции по обновлению
- Описание структуры файлов

---

## Проверка структуры

```bash
# Проверить все файлы карты
ls -la /home/user_aioc/workspace/share/opencode/

# Проверить проекты
ls -la /home/user_aioc/workspace/*/

# Проверить KB
ls -la /home/user_aioc/workspace/share/knowledge-base/*/

# Проверить скрипт
ls -la /home/user_aioc/workspace/scripts/update_knowledge_map.sh
```

---

## Версионирование

| Версия | Дата | Автор | Изменения |
|--------|------|-------|-----------|
| 1.0 | 2026-04-30 | opencode | Первая версия, модульная структура |

---

## Контакты для вопросов

При ошибках или вопросах по карте:
1. Проверьте структуру файлов
2. Запустите `update_knowledge_map.sh`
3. Проверьте JSON синтаксис в `map_json.md`
