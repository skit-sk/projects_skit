# Task: kb-search.sh — поиск по KB

## Идея

Скрипт для полнотекстового поиска по всем .md файлам KB.

## Функционал

```bash
./kb-search.sh -q "bitget fetchOHLCV"         # Поиск по содержимому
./kb-search.sh -q "таблица" -c tools           # Поиск в категории
./kb-search.sh -q "margin" -f md               # Вывод в markdown
./kb-search.sh --list                          # Список всех файлов
./kb-search.sh --stats                         # Статистика KB
```

## Технологии

- grep/rg (ripgrep) для поиска
- SQLite FTS (opencode.db) для индексации
- tabulate для форматирования результатов

## Статус

⏳ Отложено. Сначала завершить наполнение KB.
