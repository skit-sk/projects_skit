# termcharts — Terminal Charts with Rich Compatibility

**termcharts** — Python-библиотека для создания bar, pie и doughnut диаграмм в терминале. Особенность — нативная совместимость с Rich.

**Репозиторий**: https://github.com/Abdur-rahmaanJ/termcharts  
**PyPI**: `pip install termcharts`  
**Версия**: v1.1.2 (Sep 2022)  
**Stars**: 41  
**Python**: 3.7+

---

## Установка

```bash
pip install termcharts
```

**Зависимости**:
- **Zero dependencies** (установка по умолчанию)
- **Опционально**: `rich` — для Rich-совместимости

---

## Полный API

### `bar(data, title='', rich=False, mode='h')`

Столбчатая диаграмма (bar chart).

```python
import termcharts
```

#### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `data` | `dict` или `list` | — | Данные: `{метка: значение}` или `[val1, val2, ...]` |
| `title` | `str` | `''` | Заголовок диаграммы |
| `rich` | `bool` | `False` | Если `True` — возвращает `rich.text.Text` |
| `mode` | `str` | `'h'` | `'h'` — горизонтальная, `'v'` — вертикальная |

#### Возвращает

`str` или `rich.text.Text` (при `rich=True`)

---

### `pie(data, rich=False, title='pie chart', screen=None)`

Круговая диаграмма (pie chart).

#### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `data` | `dict` | — | Данные: `{метка: значение}` |
| `rich` | `bool` | `False` | Если `True` — возвращает `rich.text.Text` |
| `title` | `str` | `'pie chart'` | Заголовок диаграммы |
| `screen` | `dict` | `None` | Внутренний экран для рендеринга |

#### Возвращает

`str` или `rich.text.Text` (при `rich=True`)

---

### `doughnut(data, rich=False, title='doughnut chart', screen=None)`

Кольцевая диаграмма (doughnut chart).

#### Параметры

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `data` | `dict` | — | Данные: `{метка: значение}` |
| `rich` | `bool` | `False` | Если `True` — возвращает `rich.text.Text` |
| `title` | `str` | `'doughnut chart'` | Заголовок диаграммы |
| `screen` | `dict` | `None` | Внутренний экран для рендеринга |

#### Возвращает

`str` или `rich.text.Text` (при `rich=True`)

---

## Все типы графиков с примерами

### 1. Bar Chart — горизонтальная (по умолчанию)

```python
import termcharts

# Из словаря
chart = termcharts.bar(
    {'roll': 24, 'bread': 10, 'rice': 30, 'pasta': 50},
    title='brunches'
)
print(chart)

# Из списка (метки не отображаются)
chart = termcharts.bar([10, 20, 30, 40], title='brunches')
print(chart)
```

**Вывод (схематично)**:
```
brunches
roll     ████████████████████ 24
bread   ██████████           10
rice    ████████████████████ 30
pasta   ██████████████████████████ 50
```

---

### 2. Bar Chart — вертикальная

```python
import termcharts

chart = termcharts.bar(
    {'roll': 24, 'bread': 10, 'rice': 30, 'pasta': 50},
    title='brunches',
    mode='v'  # вертикальная
)
print(chart)
```

---

### 3. Pie Chart

```python
import termcharts

chart = termcharts.pie(
    {'pencil': 10, 'eraser': 20, 'ruler': 30},
    title='stationary'
)
print(chart)
```

**Вывод (схематично)**:
```
stationary
  30%
    ████
   █████
  ███████
 ████████
██████████
    ██
  20% ██ 10%
   pencil
  eraser ruler
```

---

### 4. Doughnut Chart

```python
import termcharts

chart = termcharts.doughnut(
    {'a': 10, 'b': 20, 'c': 30, 'd': 20},
    title='alphabet dist'
)
print(chart)
```

---

## Rich-совместимость

При `rich=True` возвращает `rich.text.Text`, что позволяет интегрировать графики в Rich-интерфейсы.

### Интеграция с Rich Panel и Columns

```python
from termcharts import pie, doughnut, bar
from rich.console import Console
from rich.columns import Columns
from rich.panel import Panel

console = Console()

charts = [
    doughnut({'a': 10, 'b': 20, 'c': 30, 'd': 20}, title='alphabet dist', rich=True),
    pie({'pencil': 10, 'eraser': 20, 'ruler': 30}, title='stationary', rich=True),
    bar({'roll': 24, 'bread': 10, 'rice': 30, 'pasta': 50}, title='Brunches', rich=True)
]

user_renderables = [Panel(x, expand=True) for x in charts]
console.print(Columns(user_renderables))
```

---

## Внутренний движок (для расширенного использования)

### `termcharts.engine`

```python
from termcharts.engine import (
    screen,
    add_char,
    add_text,
    pie_add_text,
    coord_to_str,
    get_coord,
    coord_in_scr,
    render,
    pie_render,
    merge_screens
)
```

| Функция | Сигнатура | Описание |
|---------|-----------|----------|
| `screen()` | `() -> dict` | Создаёт пустой экран (словарь) |
| `add_char(screen_, coord, value)` | `(dict, list, str) -> None` | Добавляет символ `value` в позицию `coord=[x, y]` |
| `add_text(screen_, text, gx, gy, mode='h')` | `(dict, str, int, int, str) -> None` | Добавляет текст. `mode='h'` — горизонтально, `'v'` — вертикально |
| `pie_add_text(screen_, text, gx, gy, mode='h')` | `(dict, str, int, int, str) -> None` | Аналог `add_text` для pie-чартов |
| `coord_to_str(coord)` | `(list) -> str` | Конвертирует `[x, y]` в строку `'x-y'` |
| `get_coord(screen, coord)` | `(dict, list) -> str` | Получает символ по координате |
| `coord_in_scr(screen, coord)` | `(dict, list) -> bool` | Проверяет наличие координаты на экране |
| `render(screen, size_x, size_y)` | `(dict, int, int) -> str` | Рендерит экран в строку |
| `pie_render(screen, displayx, displayy, debug=False)` | `(dict, int, int, bool) -> str` | Рендерит pie/doughnut |
| `merge_screens(screens)` | `(list) -> dict` | Объединяет несколько экранов |

### `termcharts.colors`

```python
from termcharts.colors import Color, default_colors

# ANSI цвета
Color.RED       # "\033[31m"
Color.GREEN     # "\033[32m"
Color.ORANGE    # "\033[33m"
Color.PURPLE    # "\033[35m"
Color.WHITE     # "\033[37m"
Color.RESET     # "\033[39m"

# Циклический итератор цветов
for color in default_colors:
    print(color(next_color), end='')
```

### `termcharts.formula`

```python
from termcharts.formula import constrain

# Масштабирует значение из одного диапазона в другой
result = constrain(
    val=75,           # входное значение
    start=0,          # исходный минимум
    end=100,          # исходный максимум
    realstart=0,      # целевой минимум
    realend=50,       # целевой максимум
    lessthan_sym=None,
    morethan_sym=None
)
# result = 37.5
```

---

## Цветовая палитра

По умолчанию используются ANSI-цвета, циклически:

```python
default_colors = itertools.cycle([
    Color.red,    # "\033[31m"
    Color.green,  # "\033[32m"
    Color.orange, # "\033[33m"
    Color.purple  # "\033[35m"
])
```

---

## Ограничения

1. **Только Python 3.7+**
2. **Pie/Doughnut** принимают только `dict` (не list)
3. **Bar chart из list** — метки не отображаются (только значения)
4. **Нет автомасштабирования** — размер графика фиксирован
5. **Терминальные ANSI-символы** — работает только в терминалах с поддержкой ANSI
6. **Нет легенды в bar chart** — значения отображаются рядом со столбцами
7. **Нет datetime/timeseries** — только статические данные
8. **Нет scatter, line, histogram** — только bar, pie, doughnut

---

## Структура проекта

```
termcharts/
├── __init__.py          # Экспорт: bar, pie, doughnut
├── bar_chart.py         # bar_chart_raw_h, bar_chart_raw_v, bar
├── pie.py               # pie_chart_raw, pie_chart, doughnut_chart
├── colors.py            # Color class, default_colors
├── engine.py            # screen, add_char, add_text, render, etc.
├── formula.py           # constrain
├── setup.py
├── setup.cfg
├── CHANGELOG.md
├── README.md
├── assets/              # изображения примеров
│   ├── bar.png
│   ├── bar_h.png
│   └── pie.png
├── sandbox/             # примеры использования
├── tests/               # pytest тесты (неполные)
└── reqs/                # требования к разработке
```

---

## Ссылки

- Репозиторий: https://github.com/Abdur-rahmaanJ/termcharts
- PyPI: https://pypi.org/project/termcharts/
- Примеры: см. `sandbox/` в репозитории