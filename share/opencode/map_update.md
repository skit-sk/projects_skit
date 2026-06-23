# Update Instructions

**Файл:** map_update.md
**Родительский:** [map_all_small.md](./map_all_small.md)

---

## Автоматическое обновление

```bash
/home/user_aioc/workspace/scripts/update_knowledge_map.sh
```

### Режим проверки

```bash
/home/user_aioc/workspace/scripts/update_knowledge_map.sh --check
```

## Что обновляет скрипт

1. Проверяет структуру workspace.
2. Проверяет наличие KB-статей для всех 11 проектов.
3. Обновляет дату/версию в map-файлах.
4. Собирает статистику по проектам и KB.
5. Проверяет cross-links между KB-статьями.

## Ручное обновление

Если скрипт недоступен, отредактируйте файлы в `share/opencode/` вручную и обновите поля:

```markdown
**Версия:** 2.0
**Дата:** 2026-06-22
```
