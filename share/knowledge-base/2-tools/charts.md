# CLI-графики: визуализация данных в терминале

Полный обзор Python-библиотек для построения графиков прямо в терминале.

---

## Быстрая справка

| Библиотека | pip | Типы графиков | Docs |
|------------|-----|---------------|------|
| [asciichart](charts/asciichart.md) | `pip install asciichart` | Line | краткая |
| [plotext](charts/plotext.md) | `pip install plotext` | Line, Bar, Scatter, Hist, Candlestick, Error, Box, Matrix, Image, GIF, Video, Subplots | **глубокая** |
| [termgraph](charts/termgraph.md) | `pip install termgraph` | Bar | краткая |
| [termcharts](charts/termcharts.md) | `pip install termcharts` | Bar, Pie, Doughnut | **глубокая** |
| [plotille](charts/plotille.md) | `pip install plotille` | Line, Scatter, Hist, Image (Braille/color) | **глубокая** |
| [asciimatics](charts/asciimatics.md) | `pip install asciimatics` | Line, Bar, Scatter, Hist, Image, Particles, Sprites, TUI Widgets | **глубокая** |
| [rich](../rich.md) | `pip install rich` | Table, Progress, Tree | краткая |
| [pygal](../pygal.md) | `pip install pygal` | 20+ типов (Bar, Line, Pie, Box, Gauge...) | краткая |
| [Визуальные эффекты](../visual-effects.md) | `pip install terminaltexteffects` | 32+ Effects (Matrix, Fireworks, Decrypt...) | **глубокая** |

---

## Таблица сравнения

| Библиотека | Линии | Бары | Pie | Scatter | Histogram | Heatmap | Изображения | GIF/Video | Цвет | Даты | Zero-dep | CLI | Docs |
|------------|-------|------|-----|---------|-----------|---------|-------------|-----------|------|------|----------|-----|------|
| asciichart | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | краткая |
| plotext | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | **глубокая** |
| termgraph | ❌ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ✅ | краткая |
| termcharts | ❌ | ✅ | ✅ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | **глубокая** |
| plotille | ✅ | ❌ | ❌ | ✅ | ✅ | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ | **глубокая** |
| asciimatics | ✅ | ✅ | ❌ | ✅ | ✅ | ❌ | ✅ | ❌ | ✅ | ❌ | ❌ | ❌ | **глубокая** |
| Rich | Table | Progress | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ | ❌ | ✅ | ❌ | краткая |
| Pygal | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ | ❌ | ❌ | ✅ | ✅ | ✅ | ❌ | краткая |

---

## Глубокие справки (man-файлы)

### [termcharts](charts/termcharts.md) — Bar, Pie, Doughnut + Rich

```bash
pip install termcharts
```

```python
import termcharts

# Bar (h/v)
termcharts.bar({'roll': 24, 'bread': 10}, title='brunches', mode='v')

# Pie
termcharts.pie({'pencil': 10, 'eraser': 20}, title='stationary')

# Doughnut
termcharts.doughnut({'a': 10, 'b': 20}, title='alphabet')

# Rich integration
from rich.panel import Panel
chart = termcharts.bar(data, rich=True)
```

**Особенности**: Rich-совместимость, ANSI цвета

---

### [plotille](charts/plotille.md) — Line, Scatter, Hist, Image + Braille

```bash
pip install plotille
```

```python
import plotille

# Figure API (композиция)
fig = plotille.Figure()
fig.plot(X, Y, lc='red', label='sin')
fig.scatter(X, np.cos(X), lc='blue', label='cos')
print(fig.show(legend=True))

# Canvas API (низкоуровневый)
cvs = plotille.Canvas(40, 20)
cvs.rect(0.1, 0.1, 0.6, 0.6)
cvs.line(0.1, 0.1, 0.6, 0.6)
print(cvs.plot())

# Быстрые функции
plotille.plot(X, Y)
plotille.scatter(X, Y)
plotille.hist(X, bins=40)
```

**Особенности**: Zero dependencies, braille dots, datetime support, 3 color modes

---

### [asciimatics](charts/asciimatics.md) — Effects, Particles, Sprites, TUI Widgets

```bash
pip install asciimatics
```

```python
from asciimatics.screen import Screen
from asciimatics.scene import Scene
from asciimatics.effects import Stars, Matrix
from asciimatics.particles import StarFirework

# Анимации
effects = [
    Stars(screen, 200),
    Matrix(screen),
    StarFirework(screen, x, y, life_time)
]
screen.play([Scene(effects, -1)])

# TUI Widgets
from asciimatics.widgets import Frame, Text, Button, Layout
frame = Frame(screen, 20, 60, has_shadow=True)
layout = Layout([1, 1, 1])
frame.add_layout(layout)
layout.add_widget(Text(label="Name:", name="name"), 0)
layout.add_widget(Button("Submit", self._submit), 1)
```

**Особенности**: Полноэкранные анимации, Particle system, Sprites, TUI widgets (Form, Buttons, ListBox...)

---

### [plotext](charts/plotext.md) — Candlestick, Error, Box, Image, Video, Subplots

```bash
pip install plotext
```

```python
import plotext as plt

# Все типы графиков
plt.plot(y)              # Line
plt.scatter(y)           # Scatter
plt.bar(labels, data)    # Bar
plt.hist(data, bins)     # Histogram
plt.candlestick(dates, data)  # Candlestick
plt.error(y, xerr, yerr) # Error bars
plt.box(labels, data)    # Box plot
plt.matrix_plot(matrix)  # Matrix heatmap
plt.image_plot(path)      # Image
plt.play_gif(path)       # GIF

# Subplots
plt.subplots(2, 2)
plt.subplot(1, 1).plot(y1)
plt.subplot(1, 2).plot(y2)

# CLI
# plotext plot --path data.csv --xcolumn 1 --ycolumns 2
```

**Особенности**: Full-featured, CLI tool, themes, markers, datetime

---

## Краткие справки

### [asciichart](charts/asciichart.md) — простые линейные графики

```bash
pip install asciichart
```

```python
import asciichart
print(asciichart.plot([0.4064, 0.4012, 0.4072, 0.4278, 0.4388]))
print(asciichart.plot([close, high], {'colors': ['red', 'blue']}))
```

---

### [termgraph](charts/termgraph.md) — гистограммы

```bash
pip install termgraph
```

```python
from termgraph import termgraph
data = {'12-17': 0.4064, '12-18': 0.4012, '12-19': 0.4072}
termgraph(data)

# CLI
# termgraph data.dat --color {green,red} --width 50
```

---

### [rich](../rich.md) — Tables, Progress, Trees

```bash
pip install rich
```

```python
from rich.console import Console
from rich.table import Table

console = Console()
table = Table(title="Portfolio")
table.add_column("Symbol")
table.add_column("Price")
table.add_row("BTC", "45000")
table.add_row("ETH", "3000")
console.print(table)
```

**Особенности**: Используется в termcharts для `rich=True`

---

### [pygal](../pygal.md) — 20+ типов SVG-графиков

```bash
pip install pygal
```

```python
import pygal

chart = pygal.Bar()
chart.title = 'Browser usage'
chart.add('Firefox', [15, 35, 45])
chart.add('Chrome', [70, 45, 80])
chart.render()  # returns SVG
```

**Особенности**: Не ASCII, генерирует SVG, 20+ типов графиков

---

## Когда что использовать

| Ситуация | Инструмент |
|----------|------------|
| Быстрый просмотр цены в терминале | asciichart |
| Цветной график с датами и осями | plotext |
| Полнофункциональный CLI-график | plotext |
| Гистограмма распределения | termgraph, plotille |
| Pie/Doughnut диаграмма | termcharts |
| Изображения в терминале | plotille (braille), asciimatics |
| ASCII-анимации и эффекты | asciimatics |
| Полноэкранные TUI-приложения | asciimatics |
| Таблицы и прогресс-бары | Rich |
| Классические графики (не ASCII) | Pygal |
| Минималистичный встраиваемый | asciichart |
| Rich-интеграция | termcharts + Rich |

---

## Данные для примеров

```python
close = [0.4064, 0.4012, 0.4072, 0.4278, 0.4388, 0.4144, 0.4396, 0.4444,
         0.4521, 0.4640, 0.4530, 0.4438, 0.4399, 0.4361, 0.4445, 0.4632,
         0.4633, 0.4735, 0.4733, 0.4815, 0.4599, 0.4589, 0.4533, 0.4477,
         0.4756, 0.4520, 0.4563, 0.4716, 0.4435, 0.4308]

high = [0.4442, 0.4070, 0.4098, 0.5054, 0.4444, 0.4479, 0.4724, 0.4677,
        0.4860, 0.4691, 0.4696, 0.4582, 0.4644, 0.4458, 0.4490, 0.4961,
        0.4735, 0.4756, 0.4795, 0.4920, 0.4862, 0.4738, 0.4624, 0.4588,
        0.5403, 0.4844, 0.4577, 0.4728, 0.4766, 0.4454]

low = [0.3921, 0.3732, 0.3992, 0.4072, 0.4110, 0.4134, 0.4140, 0.4394,
       0.4283, 0.4458, 0.4525, 0.4369, 0.4331, 0.4342, 0.4219, 0.4430,
       0.4583, 0.4626, 0.4610, 0.4689, 0.4560, 0.4451, 0.4479, 0.4417,
       0.4465, 0.4443, 0.4420, 0.4554, 0.4383, 0.4278]

vol = [121631, 99195, 59058, 1356860, 183208, 134856, 1347696, 408297,
       796230, 446586, 143926, 189275, 216782, 66519, 108340, 246689,
       54245, 44752, 130890, 159064, 92955, 64243, 59358, 45172,
       576053, 266226, 137946, 138610, 81147, 64053]

dates = ['2025-12-17', '2025-12-18', '2025-12-19', '2025-12-20',
         '2025-12-21', '2025-12-22', '2025-12-23', '2025-12-24',
         '2025-12-25', '2025-12-26', '2025-12-27', '2025-12-28',
         '2025-12-29', '2025-12-30', '2025-12-31', '2026-01-01',
         '2026-01-02', '2026-01-03', '2026-01-04', '2026-01-05',
         '2026-01-06', '2026-01-07', '2026-01-08', '2026-01-09',
         '2026-01-10', '2026-01-11', '2026-01-12', '2026-01-13',
         '2026-01-14', '2026-01-15']
```

---

## Связанные

- [Визуальные эффекты (visual-effects.md)](visual-effects.md)
- [Таблицы и форматирование (as-table)](as-table.md)
- [ccxt Bitget API](../1-exchanges/ccxt-bitget.md)