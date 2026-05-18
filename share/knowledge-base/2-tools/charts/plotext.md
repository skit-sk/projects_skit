# plotext — Feature-Rich Terminal Plotting Library

**plotext** —Python-библиотека для создания полноценных цветных графиков в терминале. Поддерживает множество типов графиков, datetime, изображения, CLI.

**Репозиторий**: https://github.com/piccolomo/plotext  
**PyPI**: `pip install plotext`  
**Версия**: 5.2.8 (Oct 2022)  
**Stars**: 2.1k  
**Python**: 3.6+  
**Зависимости**: none (кроме опциональных для image/video)

---

## Установка

```bash
pip install plotext
```

**Опциональные зависимости** (для image/video):
```bash
pip install Pillow  # для image_plot, play_gif, play_video
```

---

## Основные функции

### `plotext.plot(X, Y, ...)`

Линейный график.

```python
import plotext as plt

y = plt.sin(length=100)
plt.plot(y, label="sin")
plt.title("Line Plot")
plt.xlabel("X")
plt.ylabel("Y")
plt.show()
```

### `plotext.scatter(X, Y, ...)`

Точечный график.

```python
y = plt.sin(length=100)
plt.scatter(y, label="scatter")
plt.show()
```

### `plotext.bar(X, Y, ...)`

Столбчатая диаграмма.

```python
labels = ['Sausage', 'Pepperoni', 'Mushrooms', 'Cheese', 'Chicken', 'Beef']
percentages = [14, 36, 11, 8, 7, 4]
plt.bar(labels, percentages)
plt.title("Most Favored Pizzas")
plt.show()
```

### `plotext.hist(X, bins, ...)`

Гистограмма.

```python
import random
data = [random.gauss(0, 1) for _ in range(10000)]
plt.hist(data, bins=60, label="Gaussian")
plt.show()
```

---

## Datetime — временные ряды

```python
import plotext as plt
import yfinance as yf

plt.date_form('d/m/Y')
start = plt.string_to_datetime('11/04/2022')
end = plt.today_datetime()
data = yf.download('goog', start, end)
dates = plt.datetimes_to_strings(data.index)
plt.plot(dates, list(data['Close']))
plt.title('Google Stock Price')
plt.xlabel('Date')
plt.ylabel('Stock Price $')
plt.show()
```

---

## Candlestick — свечные графики

```python
import plotext as plt
import yfinance as yf

plt.date_form('d/m/Y')
start = plt.string_to_datetime('11/04/2022')
end = plt.today_datetime()
data = yf.download('goog', start, end)
dates = plt.datetimes_to_strings(data.index)
plt.candlestick(dates, data)
plt.title('Google Stock Price Candlesticks')
plt.xlabel('Date')
plt.ylabel('Stock Price $')
plt.show()
```

**Формат data для candlestick:**
```python
# data должен содержать: Open, High, Low, Close
data['Open']   # открытие
data['High']   # максимум
data['Low']    # минимум
data['Close']  # закрытие
```

---

## Error Bars — ошибки

```python
import plotext as plt
from random import random

l = 20
n = 1
ye = [random() * n for i in range(l)]
xe = [random() * n for i in range(l)]
y = plt.sin(length=l)
plt.error(y, xerr=xe, yerr=ye)
plt.title('Error Plot')
plt.show()
```

---

## Box Plot — ящик с усами

```python
import plotext as plt

labels = ['apple', 'orange', 'banana', 'pear']
weights = [
    [1, 2, 3, 5, 10, 8],
    [4, 9, 6, 12, 20, 13],
    [1, 2, 3, 4, 5, 6],
    [3, 9, 12, 16, 9, 8, 3, 7, 2]
]
plt.box(labels, weights, width=0.3)
plt.title('The Weight of the Fruits')
plt.show()
```

---

## Logarithmic Scale — логарифмическая шкала

```python
import plotext as plt

l = 10 ** 4
y = plt.sin(periods=2, length=l)
plt.plot(y)
plt.xscale('log')
plt.yscale('linear')
plt.grid(0, 1)
plt.title('Logarithmic Plot')
plt.xlabel('logarithmic scale')
plt.ylabel('linear scale')
plt.show()
```

---

## Streaming Data — потоковые данные

```python
import plotext as plt

l = 1000
frames = 200
plt.title('Streaming Data')
for i in range(frames):
    plt.cld()  # clear display
    plt.clt()  # clear terminal
    plt.plot(plt.sin(periods=2, length=l, phase=2 * i / frames))
    plt.sleep(0.00)
    plt.show()
```

---

## Multiple Axes — несколько осей

```python
import plotext as plt

y1 = plt.sin()
y2 = plt.sin(2, phase=-1)
plt.plot(y1, xside='lower', yside='left', label='lower left')
plt.plot(y2, xside='upper', yside='right', label='upper right')
plt.title('Multiple Axes Plot')
plt.show()
```

---

## Multiple Series — несколько серий

```python
import plotext as plt

y1 = plt.sin()
y2 = plt.sin(phase=-1)
plt.plot(y1, label='plot')
plt.scatter(y2, label='scatter')
plt.title('Multiple Data Set')
plt.show()
```

---

## Stem Plot — стеблевая диаграмма

```python
import plotext as plt

y = plt.sin(length=100)
plt.plot(y, fillx=True)
plt.title('Stem Plot')
plt.show()
```

---

## Multiple Bar Plot — групповые бары

```python
import plotext as plt

pizzas = ['Sausage', 'Pepperoni', 'Mushrooms', 'Cheese', 'Chicken', 'Beef']
male = [14, 36, 11, 8, 7, 4]
female = [12, 20, 35, 15, 2, 1]
plt.multiple_bar(pizzas, [male, female], labels=['men', 'women'])
plt.title('Most Favored Pizzas by Gender')
plt.show()
```

---

## Stacked Bar Plot — стопка

```python
import plotext as plt

pizzas = ['Sausage', 'Pepperoni', 'Mushrooms', 'Cheese', 'Chicken', 'Beef']
male = [14, 36, 11, 8, 7, 4]
female = [12, 20, 35, 15, 2, 1]
plt.stacked_bar(pizzas, [male, female], labels=['men', 'women'])
plt.title('Most Favored Pizzas by Gender')
plt.show()
```

---

## Matrix Plot — матрица

```python
import plotext as plt

cols, rows = 200, 45
p = 1
matrix = [[(abs(r - rows/2) + abs(c - cols/2)) ** p for c in range(cols)] for r in range(rows)]
plt.matrix_plot(matrix)
plt.plotsize(cols, rows)
plt.title('Matrix Plot')
plt.show()
```

---

## Confusion Matrix — матрица ошибок

```python
import plotext as plt
from random import randrange

l = 300
actual = [randrange(0, 4) for i in range(l)]
predicted = [randrange(0, 4) for i in range(l)]
labels = ['Autumn', 'Spring', 'Summer', 'Winter']
plt.cmatrix(actual, predicted, labels)
plt.show()
```

---

## Event Plot — события

```python
import plotext as plt
from random import randint
from datetime import datetime, timedelta

plt.date_form('H:M')
times = [datetime(2022, 3, 27, randint(0, 23), randint(0, 59), randint(0, 59)) for i in range(100)]
times = plt.datetimes_to_strings(times)
plt.plotsize(None, 20)
plt.eventplot(times)
plt.show()
```

---

## Extra Lines — дополнительные линии

```python
import plotext as plt

y = plt.sin()
plt.scatter(y)
plt.title('Extra Lines')
plt.vline(100, 'magenta')   # вертикальная линия
plt.hline(0.5, 'blue+')      # горизонтальная линия
plt.plotsize(100, 30)
plt.show()
```

---

## Text Plot — текстовые метки

```python
import plotext as plt

pizzas = ['Sausage', 'Pepperoni', 'Mushrooms', 'Cheese', 'Chicken', 'Beef']
percentages = [14, 36, 11, 8, 7, 4]
plt.bar(pizzas, percentages)
plt.title('Labelled Bar Plot')
for i in range(len(pizzas)):
    plt.text(pizzas[i], i + 1, y=percentages[i] + 1.5, alignment='center', color='red')
plt.ylim(0, 38)
plt.plotsize(100, 30)
plt.show()
```

---

## Shapes — фигуры

```python
import plotext as plt

plt.clf()
plt.title('Shapes')
plt.polygon()              # многоугольник
plt.rectangle()            # прямоугольник
plt.polygon(sides=100)     # многоугольник со 100 сторонами
plt.show()
```

---

## Indicator — индикатор

```python
import plotext as plt

plt.indicator(45.3, 'Price')
plt.plotsize(30, 10)
plt.show()
```

---

## Image Plot — изображение

```python
import plotext as plt

path = 'cat.jpg'
plt.download(plt.test_image_url, path)
plt.image_plot(path)
plt.title('A very Cute Cat')
plt.show()
plt.delete_file(path)
```

---

## GIF Plot — анимация

```python
import plotext as plt

path = 'homer.gif'
plt.download(plt.test_gif_url, path)
plt.play_gif(path)
plt.show()
plt.delete_file(path)
```

---

## Video Plot — видео

```python
import plotext as plt

path = 'moonwalk.mp4'
plt.download(plt.test_video_url, path)
plt.play_video(path, from_youtube=True)
plt.delete_file(path)
```

---

## YouTube Plot — YouTube видео

```python
import plotext as plt

plt.play_youtube(plt.test_youtube_url)
```

---

## Subplots — подграфики

```python
import plotext as plt
import random
import yfinance as yf

plt.date_form('d/m/Y')
start = plt.string_to_datetime('28/03/2022')
end = plt.today_datetime()
data = yf.download('goog', start, end)
dates = plt.datetimes_to_strings(data.index)
pizzas = ['Sausage', 'Pepperoni', 'Mushrooms', 'Cheese', 'Chicken', 'Beef']
mp = [14, 36, 11, 8, 7, 4]
fp = [12, 20, 35, 15, 2, 1]
hd = [random.gauss(1, 1) for _ in range(3 * 10**5)]
path = 'cat.jpg'
plt.download(plt.test_image_url, path)

plt.clf()
plt.subplots(1, 2)
plt.subplot(1, 1).plotsize(plt.tw() // 2, None)
plt.subplot(1, 1).subplots(3, 1)
plt.subplot(1, 2).subplots(2, 1)
plt.subplot(1, 1).ticks_style('bold')
plt.subplot(1, 1).subplot(1, 1)
plt.theme('windows')
plt.candlestick(dates, data)
plt.title('Google Stock Price CandleSticks')
plt.subplot(1, 1).subplot(2, 1)
plt.theme('dreamland')
plt.stacked_bar(pizzas, [mp, fp], labels=['men', 'women'])
plt.title('Most Favored Pizzas in the World by Gender')
plt.subplot(1, 1).subplot(3, 1)
plt.theme('matrix')
bins = 18
plt.hist(hd, bins, label='Gaussian Noise Distribution', marker='fhd')
plt.yfrequency(0)
plt.title('Histogram Plot')
plt.subplot(1, 2).subplot(1, 1).title('Default Theme')
plt.plot(plt.sin(periods=3), marker='fhd', label='3 periods')
plt.plot(plt.sin(periods=2), marker='fhd', label='2 periods')
plt.plot(plt.sin(periods=1), marker='fhd', label='1 period')
plt.subplot(1, 2).subplot(2, 1)
plt.plotsize(2 * plt.tw() // 3, plt.th() // 2)
plt.image_plot(path)
plt.title('A very Cute Cat')
plt.show()
plt.delete_file(path)
```

---

## CLI — командная строка

```bash
# Scatter plot
plotext scatter --path test --xcolumn 1 --ycolumns 2 --lines 5000 --title "Scatter Plot Test" --marker braille

# Line plot
plotext plot --path test --xcolumn 1 --ycolumns 2 --sleep 0.1 --lines 2500 --color magenta+ --title "Line Plot Test"

# Plotter
plotext plotter --path test --xcolumn 1 --ycolumns 2 --sleep 0.1 --lines 120 --marker hd --title "Plotter Test"

# Bar plot
plotext bar --path test --xcolumn 1 --title "Bar Plot Test" --xlabel Animals --ylabel Count

# Histogram plot
plotext hist --path test --xcolumn 1 --ycolumns 2 --lines 5000 --title "Histogram Test"

# Image plot
plotext image --path test

# GIF plot
plotext gif --path test

# Video plot
plotext video --path test --from_youtube True

# YouTube
plotext youtube --url test
```

---

## Темы

```python
plt.theme("dark")       # dark, pro, clear, mermaid, etc
plt.theme("windows")
plt.theme("matrix")
plt.theme("dreamland")
plt.plot(close)
plt.show()
```

---

## Marker — маркеры

```python
plt.plot(y, marker='hd')   # hd, dot, fhd, block, etc
plt.plot(y, marker='fhd')  # fine hd
plt.plot(y, marker='dot')
plt.plot(y, marker='braille')
```

**Доступные маркеры**: `dot`, `hd`, `fhd`, `block`, `braille`, `point`, `heavy`, `filled`, `circle`, `star`

---

## Цвета

```python
plt.plot(y, color='magenta+')   # с + для яркости
plt.plot(y, color='red')
plt.plot(y, color='blue+')
```

**Доступные цвета**: `black`, `red`, `green`, `yellow`, `blue`, `magenta`, `cyan`, `white` (с `+` для яркой версии)

---

## Утилиты

### `plt.sin()` / `plt.cos()`

```python
y = plt.sin(length=100, periods=1, phase=0)
y = plt.cos(length=100, periods=2)
```

### `plt.string_to_datetime()` / `plt.today_datetime()`

```python
start = plt.string_to_datetime('11/04/2022')
end = plt.today_datetime()
```

### `plt.datetimes_to_strings()`

```python
dates = plt.datetimes_to_strings(data.index)
```

### `plt.date_form()`

```python
plt.date_form('d/m/Y')
plt.date_form('Y-m-d H:M:S')
```

### `plt.download()`

```python
plt.download(url, path)
```

### `plt.delete_file()`

```python
plt.delete_file(path)
```

### `plt.cld()` / `plt.clt()`

```python
plt.cld()  # clear display
plt.clt()  # clear terminal
```

### `plt.tc()` / `plt.tcl()`

```python
plt.tc()   # text color (forground)
plt.tcl()  # text color (background)
```

### `plt.test()`

```python
plt.test()  # тест всех возможностей
```

### `plt.markers()` / `plt.colors()` / `plt.styles()` / `plt.themes()`

```python
plt.markers()  # показать все маркеры
plt.colors()   # показать все цвета
plt.styles()   # показать все стили
plt.themes()   # показать все темы
```

---

## Все функции API

```python
# Основные
plt.plot(y, label, color, marker, xside, yside)
plt.scatter(y, label, color, marker, xside, yside)
plt.bar(x, y, label, color, orientation, width)
plt.hist(x, bins, label, color)
plt.candlestick(dates, data)
plt.error(x, y, xerr, yerr)
plt.box(labels, data, width)
plt.eventplot(times)
plt.matrix_plot(matrix)
plt.cmatrix(actual, predicted, labels)

# Утилиты
plt.title(text)
plt.xlabel(text)
plt.ylabel(text)
plt.xlim(min, max)
plt.ylim(min, max)
plt.xscale('log' | 'linear')
plt.yscale('log' | 'linear')
plt.grid(x, y)
plt.legend()
plt.theme(name)
plt.marker(name)
plt.color(name)
plt.ticks_color(color)
plt.ticks_style(style)
plt.plotsize(width, height)
plt.show()
plt.sleep(seconds)

# Очистка
plt.clf()     # clear figure
plt.cld()     # clear display
plt.clt()     # clear terminal

# Subplots
plt.subplots(rows, cols)
plt.subplot(row, col).subplot(row, col)
plt.subplots(rows, cols)

# Линии
plt.vline(x, color)
plt.hline(y, color)
plt.rectangle()
plt.polygon(sides)
plt.text(x, y, text, alignment, color)

# Data utilities
plt.sin(length, periods, phase)
plt.cos(length, periods, phase)
plt.date_form(format)
plt.string_to_datetime(string)
plt.today_datetime()
plt.datetimes_to_strings(datetimes)
plt.download(url, path)
plt.delete_file(path)

# Индикатор
plt.indicator(value, label)

# Медиа
plt.image_plot(path)
plt.play_gif(path)
plt.play_video(path, from_youtube)
plt.play_youtube(url)

# Тесты
plt.test()
plt.markers()
plt.colors()
plt.styles()
plt.themes()
```

---

## Ограничения

1. **Python 3.6+**: старые версии не поддерживаются
2. **TTY required**: для цветного вывода (при redirect/pipe цвета убираются)
3. **Максимальный размер**: зависит от размера терминала
4. **Даты**: требуется формат через `plt.date_form()`
5. **CLI**: базовые возможности (не полноценный интерфейс)

---

## Ссылки

- Репозиторий: https://github.com/piccolomo/plotext
- PyPI: https://pypi.org/project/plotext/
- Документация: Wiki на GitHub (readme/)