# Rich — Rich Text and Beautiful Formatting in Terminal

**Rich** — Python-библиотека для форматирования rich text в терминале: цветной текст, таблицы, прогресс-бары, деревья, markdown, syntax highlighting.

**Репозиторий**: https://github.com/textualize/rich  
**PyPI**: `pip install rich`  
**Stars**: 56.2k  
**Python**: 3.7+

**Особенности**: Используется в termcharts для `rich=True` интеграции.

---

## Установка

```bash
pip install rich
```

---

## Console

```python
from rich.console import Console

console = Console()
console.print("Hello, World!")
console.print("[bold red]Warning![/bold red] This is important")
console.print("[link=https://example.com]Click here[/link]")
```

---

## Таблицы

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Portfolio")
table.add_column("Symbol", style="cyan")
table.add_column("Price", justify="right", style="green")
table.add_column("Change", justify="right", style="yellow")

table.add_row("BTC", "$45,000", "+2.5%")
table.add_row("ETH", "$3,000", "-1.2%")
table.add_row("SOL", "$100", "+5.8%")

console.print(table)
```

---

## Прогресс-бары

```python
from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn

with Progress(
    SpinnerColumn(),
    TextColumn("[progress.description]{task.description}"),
    BarColumn(),
    TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
) as progress:
    task = progress.add_task("Processing...", total=100)
    for i in range(100):
        progress.update(task, advance=1)
```

---

## Деревья

```python
from rich.tree import Tree
from rich.console import Console

console = Console()
tree = Tree("Root")
tree.add("Branch 1")
tree.add("Branch 2")
branch = tree.add("Branch 3")
branch.add("Leaf 3.1")
branch.add("Leaf 3.2")
console.print(tree)
```

---

## Панели

```python
from rich.panel import Panel
from rich.console import Console

console = Console()
console.print(Panel(
    "[bold]Welcome![/bold]\n\nSystem Status: OK",
    title="Dashboard",
    border_style="green"
))
```

---

## Markdown

```python
from rich.console import Console
from rich.markdown import Markdown

console = Console()
md = Markdown("# Hello\n\nThis is **bold** and *italic* text.")
console.print(md)
```

---

## Syntax Highlighting

```python
from rich.syntax import Syntax
from rich.console import Console

console = Console()
code = """
def hello():
    print("Hello, World!")
"""
syntax = Syntax(code, "python", theme="monokai", line_numbers=True)
console.print(syntax)
```

---

## Columns

```python
from rich.columns import Columns
from rich.console import Console

console = Console()
columns = Columns(["Item 1", "Item 2", "Item 3"], equal=True, column_first=True)
console.print(columns)
```

---

## Интеграция с termcharts

Rich используется в termcharts для `rich=True`:

```python
from termcharts import pie, doughnut, bar
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

console = Console()

charts = [
    doughnut({'a': 10, 'b': 20, 'c': 30}, rich=True),
    pie({'x': 10, 'y': 20, 'z': 30}, rich=True),
    bar({'p': 10, 'q': 20, 'r': 30}, rich=True)
]

user_renderables = [Panel(x, expand=True) for x in charts]
console.print(Columns(user_renderables))
```

---

## Все возможности

- **Color**: ANSI 16.7M colors (24-bit)
- **Styles**: bold, italic, underline, strikethrough, etc.
- **Tables**: с自動определением ширины
- **Progress**: tracks任务进度
- **Tree**: иерархические данные
- **Panel**: рамки с заголовками
- **Markdown**: рендеринг MD
- **Syntax**: подсветка синтаксиса
- **Emoji**: `:smile:` → 😄
- **Live Display**: обновление в реальном времени
- **Log**: форматированный вывод логов

---

## Ограничения

1. **Не графики**: это library for text formatting, not charting
2. **Terminal dependent**: требуется терминал с поддержкой ANSI
3. **No plotting**: нет line/scatter/bar charts (для этого — plotext, termcharts, etc.)

---

## Ссылки

- Репозиторий: https://github.com/textualize/rich
- PyPI: https://pypi.org/project/rich/
- Документация: https://rich.readthedocs.io/