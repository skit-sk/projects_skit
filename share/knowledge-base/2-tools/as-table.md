# Форматирование таблиц в CLI

## as-table (JavaScript)

```bash
npm install as-table
```

```javascript
const asTable = require('as-table')
console.log(asTable([
  { foo: true,  string: 'abcde',  num: 42 },
  { foo: false, string: 'qwerty', num: 43 },
]))
// foo    string   num
// ------------   -----
// true   abcde    42
// false  qwerty   43
```

## Альтернативы для Python

### 1. tabulate ⭐ (рекомендуется)

```bash
pip install tabulate
```

```python
from tabulate import tabulate
data = [["BTC", 50000, 0.5], ["ETH", 3000, 10]]

# simple (как as-table)
print(tabulate(data, headers=["Symbol", "Price", "Volume"]))

# grid
print(tabulate(data, tablefmt="grid"))

# fancy_grid (unicode)
print(tabulate(data, tablefmt="fancy_grid"))

# github markdown
print(tabulate(data, tablefmt="github"))

# 30+ форматов
```

**Особенности:** 30+ форматов, 0 зависимостей, автоопределение числовых колонок, выравнивание по десятичной точке.

**Форматы:** plain, simple, github, grid, fancy_grid, simple_grid, rounded_grid, heavy_grid, mixed_grid, double_grid, pipe, orgtbl, asciidoc, jira, presto, pretty, psql, rst, mediawiki, html, latex, tsv и др.

### 2. rich — цветной CLI

```bash
pip install rich
```

```python
from rich.console import Console
from rich.table import Table
from rich import box

c = Console()

# Таблица с цветом и ASCII-рамкой
table = Table(
    title="[bold]Portfolio[/]",
    box=box.ASCII,       # ASCII-рамка (совместимость)
    header_style="bold cyan"
)
table.add_column("Symbol", style="green")
table.add_column("Price", justify="right", style="yellow")
table.add_column("Volume", justify="right", style="blue")
table.add_row("BTC/USDT", "50000.00", "0.5000")
table.add_row("ETH/USDT", "3000.00",  "10.000")
table.add_row("SOL/USDT", "150.00",   "100.00")
c.print(table)
```

Вывод (цветной в терминале):
```
┌──────────┬─────────┬─────────┐
│ Symbol   │   Price │  Volume │
├──────────┼─────────┼─────────┤
│ BTC/USDT │ 50000.0 │   0.500 │
│ ETH/USDT │  3000.0 │  10.000 │
│ SOL/USDT │   150.0 │ 100.000 │
└──────────┴─────────┴─────────┘
```

**rich умеет:**
- Цветные таблицы с разными стилями рамок (ASCII, SQUARE, ROUNDED, DOUBLE)
- Markdown-рендеринг
- Progress bar, индикаторы
- Syntax highlighting
- Panel, Tree, Columns
- Эмодзи и Unicode

**Стили рамок (box):**
```python
box.ASCII      # +--+--+
box.SQUARE     # ┌──┬──┐
box.ROUNDED    # ╭──╤──╮
box.DOUBLE     # ╔══╦══╗
box.MINIMAL    # ┌──┬──┐ (без нижней)
box.HEAVY      # ┏━━┳━━┓
```

### 3. prettytable — классика

```bash
pip install prettytable
```

```python
from prettytable import PrettyTable

t = PrettyTable(["Symbol", "Price", "Volume"])
t.add_row(["BTC", 50000, 0.5])
t.add_row(["ETH", 3000, 10])
t.align["Price"] = "r"
t.float_format = ".2"
print(t)
# +--------+-------+--------+
# | Symbol | Price | Volume |
# +--------+-------+--------+
# |  BTC   | 50000 |  0.5   |
# |  ETH   |  3000 |   10   |
# +--------+-------+--------+
```

### Сравнение

| Библиотека | Платформа | Форматы | Цвет | Emoji | Вес |
|------------|-----------|---------|------|-------|-----|
| as-table | JS | 1-2 | ❌ | ✅ | лёгкая |
| **tabulate** | **Python** | **30+** | **❌** | **✅** | **0 зависимостей** |
| rich | Python | 10+ | ✅ | ✅ | средняя (зависимости) |
| prettytable | Python | 1-2 | ❌ | ❌ | лёгкая |

### Когда что использовать

| Ситуация | Инструмент |
|----------|------------|
| README.md / документация | tabulate (github, rst, mediawiki) |
| CLI-утилита, быстрый вывод | tabulate (simple, grid) |
| Красивый цветной терминал | rich |
| JSON/API-ответы | tabulate (html, latex) |
| Логи, отладка | prettytable |
