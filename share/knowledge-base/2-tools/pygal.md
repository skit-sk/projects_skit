# Pygal — Dynamic SVG Charting Library

**Pygal** — Python-библиотека для генерации SVG-графиков. Генерирует векторные графики (не ASCII), которые можно отобразить в браузере или конвертировать в другие форматы.

**Репозиторий**: https://github.com/Kozea/pygal  
**PyPI**: `pip install pygal`  
**Stars**: 2.8k  
**Python**: 3.6+

**Особенности**: 20+ типов графиков, интерактивные SVG, экспорт в PNG/PDF

---

## Установка

```bash
pip install pygal
```

---

## Bar Chart

```python
import pygal

chart = pygal.Bar()
chart.title = 'Browser Usage'
chart.add('Firefox', [15, 35, 45, 60])
chart.add('Chrome', [70, 80, 85, 90])
chart.add('Safari', [10, 15, 20, 25])

chart.render()  # returns SVG
chart.render_to_file('bar_chart.svg')
```

---

## Line Chart

```python
import pygal

chart = pygal.Line()
chart.title = 'Stock Prices'
chart.x_labels = ['Jan', 'Feb', 'Mar', 'Apr']
chart.add('AAPL', [150, 155, 148, 160])
chart.add('GOOG', [100, 105, 110, 115])

chart.render()
```

---

## Pie Chart

```python
import pygal

chart = pygal.Pie()
chart.title = 'Market Share'
chart.add('Chrome', 70)
chart.add('Firefox', 15)
chart.add('Safari', 10)
chart.add('Other', 5)

chart.render()
```

---

## Box Plot

```python
import pygal

chart = pygal.Box()
chart.title = 'Distribution'
chart.add('A', [1, 2, 3, 4, 5, 6, 7, 8, 9, 10])
chart.add('B', [2, 3, 4, 5, 6, 7, 8, 9, 10, 11])

chart.render()
```

---

## Gauge

```python
import pygal

chart = pygal.Gauge(hue_range=(0, 100))
chart.title = 'CPU Usage'
chart.add('System', 45)
chart.add('User', 30)

chart.render()
```

---

## Types Charts

| Тип | Описание |
|-----|----------|
| `Bar`, `HorizontalBar` | Столбчатая диаграмма |
| `Line`, `StackedLine` | Линейный график |
| `Pie` | Круговая диаграмма |
| `Box` | Ящик с усами |
| `Gauge` | Индикатор |
| `Radar` | Радарная диаграмма |
| `Dot` | Точечная диаграмма |
| `Funnel` | Воронка |
| `Histogram` | Гистограмма |
| `XY` | Scatter plot |
| `DateTime` | Временные ряды |
| `DateXY` | Scatter с датами |
| `GeoMap` | Географическая карта |
| `Treemap` | Древовидная карта |

---

## Styling

```python
import pygal

chart = pygal.Bar(
    title='Styled Chart',
    style=pygal.style.DarkStyle,
    # или кастомный стиль
    style=pygal.style.Style(
        colors=('#FF0000', '#00FF00', '#0000FF'),
        font_family='Arial',
        title_font_size=18,
        legend_font_size=12,
        value_font_size=10,
    )
)
chart.add('Data', [10, 20, 30])
chart.render()
```

---

## Export

```python
chart = pygal.Bar()
chart.add('Data', [1, 2, 3])

# SVG (default)
svg = chart.render()

# PNG
chart.render_to_png('chart.png')

# PDF
chart.render_to_pdf('chart.pdf')

# IO Bytes
from io import BytesIO
buf = BytesIO()
chart.render_to_file(buf)
```

---

## Интерактивность

Pygal генерирует интерактивные SVG:
- Hover tooltips
- Click to select
- Zoom
- Legend toggle

```python
chart = pygal.Bar()
chart.add('Data', [10, 20, 30])

# Включить интерактивность
chart.interactive = True
```

---

## Ограничения

1. **Не ASCII**: генерирует SVG, не терминальные графики
2. **Requires viewer**: для просмотра нужен браузер/inkscape
3. **No real-time**: статические графики, нет потоковых данных
4. **Terminal**: не подходит для CLI-графиков (используйте plotext, termcharts)

---

## Когда использовать

| Ситуация | Инструмент |
|----------|------------|
| Веб-дашборды | Pygal (SVG) |
| Статические отчёты (PDF/PNG) | Pygal |
| Интерактивные графики | Pygal |
| Терминальные графики | plotext, termcharts, plotille |
| Быстрый просмотр в CLI | asciichart, termgraph |

---

## Ссылки

- Репозиторий: https://github.com/Kozea/pygal
- PyPI: https://pypi.org/project/pygal/
- Документация: http://pygal.readthedocs.io/