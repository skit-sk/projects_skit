# plotille — Terminal Plotting with Braille Dots

**plotille** — Python-библиотека для создания графиков в терминале с использованием брайлевских точек и цветов. Zero dependencies.

**Репозиторий**: https://github.com/tammoippen/plotille  
**PyPI**: `pip install plotille`  
**Версия**: v6.0.5 (Feb 2026)  
**Stars**: 516  
**Python**: 3.10+, PyPy 3.11+

---

## Установка

```bash
pip install plotille
```

**Зависимости**: **none** (zero dependencies)

---

## Цветовые режимы

### `names` — ISO 6429 ANSI colors (3/4 bit)

```python
from plotille import color

color("text", fg="red")
color("text", fg="green")
color("text", bg="cyan")
color("text", fg="white", bg="blue")
```

**Доступные цвета (имена)**:

| Имя | Описание |
|-----|----------|
| `black` | Чёрный |
| `red` | Красный |
| `green` | Зелёный |
| `yellow` | Жёлтый |
| `blue` | Синий |
| `magenta` | Пурпурный |
| `cyan` | Голубой |
| `white` | Белый |
| `bright_black` | Яркий чёрный |
| `bright_red` | Яркий красный |
| `bright_green` | Яркий зелёный |
| `bright_yellow` | Яркий жёлтый |
| `bright_blue` | Яркий синий |
| `bright_magenta` | Яркий пурпурный |
| `bright_cyan` | Яркий голубой |
| `bright_white` | Яркий белый |

### `byte` — 8-bit / 256 colors

```python
color("text", fg=126, bg=87, mode="byte")  # int ∈ [0, 255]
```

### `rgb` — 24-bit true color

```python
color("text", fg=(50, 50, 50), bg=(166, 237, 240), mode="rgb")
color("text", fg="0x323232", mode="rgb")  # hex format
```

### `color()` — функция окрашивания

```python
plotille.color(
    text: str,
    fg: ColorDefinition = None,
    bg: ColorDefinition = None,
    mode: Literal['names', 'byte', 'rgb'] = 'names',
    no_color: bool = False,
    full_reset: bool = True,
) -> str
```

### `hsl()` — конвертация HSL в RGB

```python
plotille.hsl(hue: float, saturation: float, lightness: float) -> tuple[int, int, int]

r, g, b = plotille.hsl(120, 0.5, 0.5)  # зелёный
```

---

## Класс Figure — композиция графиков

Рекомендуемый способ создания сложных графиков с несколькими plots.

### Инициализация

```python
import plotille

fig = plotille.Figure()
```

### Свойства Figure

| Свойство | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `width` | `int` | `80` | Количество символов по X |
| `height` | `int` | `40` | Количество символов по Y |
| `x_label` | `str` | `'X'` | Метка оси X |
| `y_label` | `str` | `'Y'` | Метка оси Y |
| `color_mode` | `str` | `'names'` | Режим цвета: `'names'`, `'byte'`, `'rgb'` |
| `with_colors` | `bool` | `True` | Использовать ли цвета |
| `background` | `ColorDefinition` | `None` | Цвет фона графика |
| `origin` | `bool` | `True` | Показывать ли оси координат |
| `with_x_axis` | `bool` | `True` | Показывать ли ось X |
| `with_y_axis` | `bool` | `True` | Показывать ли ось Y |
| `linesep` | `str` | `'\n'` | Разделитель строк |

### Методы Figure

#### `set_x_limits(min_=None, max_=None)` / `set_y_limits(min_=None, max_=None)`

```python
fig.set_x_limits(min_=-3, max_=3)
fig.set_y_limits(min_=-1, max_=1)
```

Поддерживают `datetime.datetime` значения.

#### `set_x_display_timezone(tz)` / `set_y_display_timezone(tz)`

```python
from zoneinfo import ZoneInfo

fig.set_x_display_timezone(ZoneInfo("America/New_York"))
```

#### `register_label_formatter(type_, formatter)` / `register_float_converter(type_, converter)`

Регистрация кастомных форматтеров для меток и конвертеров типов.

### Методы построения графиков в Figure

#### `plot(X, Y, lc=None, interp='linear', label=None, marker=None)`

Линейный график с интерполяцией между точками.

```python
fig.plot(X, Y, lc='red', interp='linear', label='sin')
fig.plot(X, Y, lc=100, color_mode='byte', label='cos')
```

#### `scatter(X, Y, lc=None, label=None, marker=None)`

Точечный график БЕЗ интерполяции.

```python
fig.scatter(X, Y, lc='blue', label='points')
```

#### `histogram(X, bins=160, lc=None)`

Гистограмма снизу вверх (2D).

```python
fig.histogram(X, bins=100)
```

#### `text(X, Y, texts, lc=None)`

Текстовые метки в координатах.

```python
fig.text([1, 2, 3], [1, 2, 3], ['a', 'b', 'c'])
```

#### `axvline(x, ymin=0, ymax=1, lc=None)`

Вертикальная линия на позиции x (относительные координаты 0-1).

```python
fig.axvline(0.5, ymin=0.2, ymax=0.8)
```

#### `axhline(y, xmin=0, xmax=1, lc=None)`

Горизонтальная линия.

```python
fig.axhline(0.5)
```

#### `axvspan(xmin, xmax, ymin=0, ymax=1, lc=None)`

Вертикальный прямоугольник.

```python
fig.axvspan(0.2, 0.4, ymin=0.1, ymax=0.9)
```

#### `axhspan(ymin, ymax, xmin=0, xmax=1, lc=None)`

Горизонтальный прямоугольник.

```python
fig.axhspan(0.2, 0.8, xmin=0.1, xmax=0.9)
```

#### `imgshow(X, cmap=None)`

Отображение данных как изображения.

```python
fig.imgshow(data, cmap='plasma')
```

**Формат данных**:
- `(M, N)` — скалярные данные (значения 0-1, мапятся через colormap)
- `(M, N, 3)` — RGB данные (0-1 float или 0-255 int)

#### `clear()`

Очистка всех plots, texts, spans и images.

```python
fig.clear()
```

#### `show(legend=False)` -> str

Рендеринг графика в строку.

```python
print(fig.show(legend=True))
```

---

## Класс Canvas — низкоуровневый API

### Инициализация

```python
import plotille

cvs = plotille.Canvas(
    width=40,
    height=20,
    xmin=0,
    ymin=0,
    xmax=1,
    ymax=1,
    background=None,
    color_mode='names'
)
```

**Координаты**: Canvas имеет 2 системы координат:
- **Reference system**: непрерывные координаты от (xmin, ymin) до (xmax, ymax)
- **Canvas system**: дискретные точки (0..width*2, 0..height*4)

Один символ брайля = 2x4 точки.

### Свойства Canvas

| Свойство | Тип | Описание |
|----------|-----|----------|
| `width` | `int` | Количество символов по X |
| `height` | `int` | Количество символов по Y |
| `xmin`, `ymin` | `RefCoord` | Минимум X/Y в reference system |
| `xmax`, `ymax` | `RefCoord` | Максимум X/Y в reference system |
| `xmax_inside` | `float` | Макс X ещё внутри canvas |
| `ymax_inside` | `float` | Макс Y ещё внутри canvas |

### Методы Canvas

#### `point(x, y, set_=True, color=None, marker=None)`

Точка в координате (x, y).

```python
cvs = Canvas(40, 20)
cvs.point(0.5, 0.5, color='red')
cvs.point(0.3, 0.7, marker='*')
```

#### `line(x0, y0, x1, y1, set_=True, color=None)`

Линия между двумя точками.

```python
cvs.line(0.1, 0.1, 0.6, 0.6, color='blue')
```

#### `rect(xmin, ymin, xmax, ymax, set_=True, color=None)`

Прямоугольник по двум углам.

```python
cvs.rect(0.1, 0.1, 0.6, 0.6, color='green')
```

#### `fill_char(x, y, set_=True)`

Заполнить весь символ в точке (x, y).

```python
cvs.fill_char(0.5, 0.5)
```

#### `text(x, y, text, set_=True, color=None)`

Текст начиная с координаты (x, y).

```python
cvs.text(0.1, 0.9, "Hello World", color='cyan')
```

#### `braille_image(pixels, threshold=127, inverse=False, color=None, set_=True)`

Изображение брайлевскими точками (1 пиксель = 1 точка).

```python
from PIL import Image
from plotille import Canvas

img = Image.open('image.jpg').convert('L').resize((80, 80))
cvs = Canvas(40, 20)
cvs.braille_image(img.getdata(), threshold=125)
print(cvs.plot())
```

Требуется canvas размером `width//2` x `height//2` от изображения.

#### `image(pixels, set_=True)`

Изображение с RGB цветами фона (1 пиксель = 1 символ).

```python
from PIL import Image
from plotille import Canvas

img = Image.open('image.jpg').convert('RGB').resize((40, 40))
cvs = Canvas(40, 40, color_mode='rgb')
cvs.image(img.getdata())
print(cvs.plot())
```

Требуется canvas точного размера изображения.

#### `dots_between(x0, y0, x1, y1)` -> tuple[int, int]

Количество точек между двумя координатами.

```python
dx, dy = cvs.dots_between(0, 0, 1, 1)
```

#### `plot(linesep='\n')` -> str

Рендеринг canvas в строку.

```python
print(cvs.plot())
```

---

## Быстрые функции (Graphing Functions)

### `plotille.plot()`

```python
plotille.plot(
    X: Sequence[float | int] | Sequence[datetime.datetime],
    Y: Sequence[float | int] | Sequence[datetime.datetime],
    width: int = 80,
    height: int = 40,
    X_label: str = 'X',
    Y_label: str = 'Y',
    linesep: str = '\n',
    interp: Optional[Literal['linear']] = 'linear',
    x_min: float | int | datetime.datetime | None = None,
    x_max: float | int | datetime.datetime | None = None,
    y_min: float | int | datetime.datetime | None = None,
    y_max: float | int | datetime.datetime | None = None,
    lc: ColorDefinition = None,
    bg: ColorDefinition = None,
    color_mode: Literal['names', 'byte', 'rgb'] = 'names',
    origin: bool = True,
    marker: str | None = None,
) -> str
```

### `plotille.scatter()`

```python
plotille.scatter(
    X: Sequence[float | int] | Sequence[datetime.datetime],
    Y: Sequence[float | int] | Sequence[datetime.datetime],
    width: int = 80,
    height: int = 40,
    X_label: str = 'X',
    Y_label: str = 'Y',
    linesep: str = '\n',
    x_min: float | int | datetime.datetime | None = None,
    x_max: float | int | datetime.datetime | None = None,
    y_min: float | int | datetime.datetime | None = None,
    y_max: float | int | datetime.datetime | None = None,
    lc: ColorDefinition = None,
    bg: ColorDefinition = None,
    color_mode: Literal['names', 'byte', 'rgb'] = 'names',
    origin: bool = True,
    marker: str | None = None,
) -> str
```

### `plotille.hist()`

```python
plotille.hist(
    X: Sequence[float | int] | Sequence[datetime.datetime],
    bins: int = 40,
    width: int = 80,
    log_scale: bool = False,
    linesep: str = '\n',
    lc: ColorDefinition = None,
    bg: ColorDefinition = None,
    color_mode: Literal['names', 'byte', 'rgb'] = 'names',
) -> str
```

Горизонтальная гистограмма (слева направо).

### `plotille.hist_aggregated()`

```python
plotille.hist_aggregated(
    counts: list[int],
    bins: Sequence[float] | None = None,
    labels: Sequence[str] | None = None,
    width: int = 80,
    log_scale: bool = False,
    linesep: str = '\n',
    lc: ColorDefinition = None,
    bg: ColorDefinition = None,
    color_mode: Literal['names', 'byte', 'rgb'] = 'names',
    meta: DataMetadata | None = None,
) -> str
```

Гистограмма для агрегированных данных (уже посчитанные count и bins).

### `plotille.histogram()`

```python
plotille.histogram(
    X: Sequence[float | int] | Sequence[datetime.datetime],
    bins: int = 160,
    width: int = 80,
    height: int = 40,
    X_label: str = 'X',
    Y_label: str = 'Counts',
    linesep: str = '\n',
    x_min: float | int | datetime.datetime | None = None,
    x_max: float | int | datetime.datetime | None = None,
    y_min: float | int | datetime.datetime | None = None,
    y_max: float | int | datetime.datetime | None = None,
    lc: ColorDefinition = None,
    bg: ColorDefinition = None,
    color_mode: Literal['names', 'byte', 'rgb'] = 'names',
) -> str
```

Вертикальная гистограмма (снизу вверх, классический вид).

---

## Colormaps

```python
from plotille import Colormap, ListedColormap
from plotille import cmaps
```

### Встроенные colormaps

- `magma`
- `inferno`
- `plasma`
- `viridis`
- `jet`
- `copper`
- `gray`

### Использование

```python
cmap = cmaps["plasma"]()
rgb = cmap(0.5)  # float в [0, 1] -> RGB tuple
```

### `ListedColormap.from_relative()`

Создание colormap из относительных значений (0-1).

```python
colors = [[0, 0.5, 1], [1, 0.5, 0]]  # RGB в 0-1
my_cmap = ListedColormap.from_relative("my_cmap", colors)
```

---

## Datetime / Timeseries Support

Plotille поддерживает `datetime.datetime` и `numpy.datetime64` начиная с версии 3.2.

### Использование

```python
import datetime
import numpy as np
import plotille

# datetime
times = [datetime.datetime(2024, 1, i) for i in range(1, 30)]
values = list(range(29))
print(plotille.plot(times, values))

# numpy datetime64
np_times = np.array(['2024-01-01', '2024-01-02', '2024-01-03'], dtype='datetime64')
print(plotille.scatter(np_times, [1, 2, 3]))
```

### Ограничения datetime

- Нельзя смешивать numeric и datetime на одной оси
- Нельзя смешивать timezone-aware и timezone-naive datetime на одной оси

---

## Примеры использования

### Простой line plot

```python
import numpy as np
import plotille

X = np.linspace(0, 2*np.pi, 100)
print(plotille.plot(X, np.sin(X), height=30, width=80))
```

### Scatter plot

```python
import numpy as np

X = np.random.normal(size=1000)
print(plotille.scatter(X, np.sin(X), height=30, width=80))
```

### Figure с легендой

```python
import numpy as np
import plotille

fig = plotille.Figure()
fig.width = 60
fig.height = 30
fig.set_x_limits(min_=-3, max_=3)
fig.set_y_limits(min_=-1, max_=1)
fig.color_mode = 'byte'

X = np.sort(np.random.normal(size=1000))
fig.plot([-0.5, 1], [-1, 1], lc=25, label='First line')
fig.scatter(X, np.sin(X), lc=100, label='sin')
fig.plot(X, (X+2)**2, lc=200, label='square')

print(fig.show(legend=True))
```

### Гистограмма

```python
import numpy as np

# Левая направо
print(plotille.hist(np.random.normal(size=10000)))

# Снизу вверх
print(plotille.histogram(np.random.normal(size=10000)))
```

### Агрегированная гистограмма

```python
counts = [1945, 0, 0, 0, 0, 0, 10555, 798, 0, 28351, 0]
bins = [float('-inf'), 10, 50, 100, 200, 300, 500, 800, 1000, 2000, 10000, float('+inf')]
print(plotille.hist_aggregated(counts, bins))
```

### Рисование на Canvas — дом

```python
from plotille import Canvas

c = Canvas(width=40, height=20)
c.rect(0.1, 0.1, 0.6, 0.6)
c.line(0.1, 0.1, 0.6, 0.6)
c.line(0.1, 0.6, 0.6, 0.1)
c.line(0.1, 0.6, 0.35, 0.8)
c.line(0.35, 0.8, 0.6, 0.6)
print(c.plot())
```

### Изображение брайлевскими точками

```python
from PIL import Image
from plotille import Canvas

img = Image.open('photo.jpg').convert('L').resize((80, 80))
cvs = Canvas(40, 20)
cvs.braille_image(img.getdata(), threshold=125)
print(cvs.plot())
```

### Изображение с цветами фона

```python
from PIL import Image
from plotille import Figure

img = Image.open('photo.jpg').convert('RGB').resize((80, 40))
data = [[data[row*80 + col] for col in range(80)] for row in range(40)]

fig = Figure()
fig.width = 80
fig.height = 40
fig.color_mode = 'byte'
fig.imgshow(data, cmap='gray')
print(fig.show())
```

---

## Полный API Reference

### Exports (`plotille.__all__`)

```python
[
    "Canvas",
    "Colormap",
    "Figure",
    "ListedColormap",
    "color",
    "hist",
    "hist_aggregated",
    "histogram",
    "hsl",
    "plot",
    "scatter",
]
```

### Все классы и их методы

#### `Figure`

| Метод | Сигнатура |
|-------|-----------|
| `__init__` | `() -> None` |
| `set_x_limits` | `(min_=None, max_=None) -> None` |
| `set_y_limits` | `(min_=None, max_=None) -> None` |
| `set_x_display_timezone` | `(tz: tzinfo) -> None` |
| `set_y_display_timezone` | `(tz: tzinfo) -> None` |
| `register_label_formatter` | `(type_: type, formatter: Formatter) -> None` |
| `register_float_converter` | `(type_: type, converter: Converter) -> None` |
| `plot` | `(X, Y, lc=None, interp='linear', label=None, marker=None) -> None` |
| `scatter` | `(X, Y, lc=None, label=None, marker=None) -> None` |
| `histogram` | `(X, bins=160, lc=None) -> None` |
| `text` | `(X, Y, texts, lc=None) -> None` |
| `axvline` | `(x, ymin=0, ymax=1, lc=None) -> None` |
| `axvspan` | `(xmin, xmax, ymin=0, ymax=1, lc=None) -> None` |
| `axhline` | `(y, xmin=0, xmax=1, lc=None) -> None` |
| `axhspan` | `(ymin, ymax, xmin=0, xmax=1, lc=None) -> None` |
| `imgshow` | `(X, cmap=None) -> None` |
| `clear` | `() -> None` |
| `show` | `(legend=False) -> str` |

#### `Canvas`

| Метод | Сигнатура |
|-------|-----------|
| `__init__` | `(width, height, xmin=0, ymin=0, xmax=1, ymax=1, background=None, **color_kwargs) -> None` |
| `point` | `(x, y, set_=True, color=None, marker=None) -> None` |
| `line` | `(x0, y0, x1, y1, set_=True, color=None) -> None` |
| `rect` | `(xmin, ymin, xmax, ymax, set_=True, color=None) -> None` |
| `fill_char` | `(x, y, set_=True) -> None` |
| `text` | `(x, y, text, set_=True, color=None) -> None` |
| `braille_image` | `(pixels, threshold=127, inverse=False, color=None, set_=True) -> None` |
| `image` | `(pixels, set_=True) -> None` |
| `dots_between` | `(x0, y0, x1, y1) -> tuple[DotCoord, DotCoord]` |
| `plot` | `(linesep='\n') -> str` |

#### `Colormap`

| Метод | Сигнатура |
|-------|-----------|
| `__init__` | `(name: str, lookup_table: Sequence[Sequence[float]]) -> None` |
| `__call__` | `(X) -> Sequence[Number] | list[Sequence[Number] | None] | None` |

#### `ListedColormap`

| Метод | Сигнатура |
|-------|-----------|
| `__init__` | `(name: str, colors: Sequence[Sequence[int]]) -> None` |
| `from_relative` | `classmethod (name: str, colors: Sequence[Sequence[float]]) -> 'ListedColormap'` |

---

## Ограничения

1. **Python 2.7** больше не поддерживается (с v5)
2. **TTY required** для цветного вывода (при redirect/pipe цвета убираются)
3. **Максимальный размер canvas** ограничен доступной памятью
4. **1 пиксель изображения = 1 точка/символ** — требуется resize для больших изображений
5. **Нет bar, pie, doughnut** — только line, scatter, histogram
6. **Нет CLI** — только Python API

---

## Ссылки

- Репозиторий: https://github.com/tammoippen/plotille
- PyPI: https://pypi.org/project/plotille/
- Документация: в README репозитория