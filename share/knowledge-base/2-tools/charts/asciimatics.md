# asciimatics — Full-Featured Terminal UI and Animation Library

**asciimatics** — кроссплатформенная Python-библиотека для создания полноэкранных текстовых UI (TUI), ASCII-анимаций, визуализаций данных и интерактивных форм.

**Репозиторий**: https://github.com/peterbrittain/asciimatics  
**PyPI**: `pip install asciimatics`  
**Версия**: v1.15.0  
**Stars**: 4.3k  
**Python**: 3.8+  
**Платформы**: Linux, macOS, Windows, Android (Termux)

---

## Установка

```bash
pip install asciimatics
```

**Зависимости** (устанавливаются автоматически):
- `pyfiglet >= 0.7.2` — FIGlet текст
- `Pillow >= 2.7.0` — обработка изображений
- `wcwidth` — поддержка Unicode ширины символов
- `pywin32 >= 1.0` — только для Windows

---

## Screen — базовый класс

### Создание Screen

```python
from asciimatics.screen import Screen

# Способ 1: Автоматическое управление (рекомендуется)
Screen.wrapper(demo_function)

# Способ 2: Ручное управление
screen = Screen.open()
try:
    # работа с экраном
finally:
    screen.close()
```

### Константы цветов

```python
Screen.COLOUR_DEFAULT   # 0
Screen.COLOUR_BLACK     # 0
Screen.COLOUR_RED       # 1
Screen.COLOUR_GREEN     # 2
Screen.COLOUR_YELLOW    # 3
Screen.COLOUR_BLUE      # 4
Screen.COLOUR_MAGENTA   # 5
Screen.COLOUR_CYAN      # 6
Screen.COLOUR_WHITE     # 7
```

### Константы атрибутов текста

```python
Screen.A_BOLD       # Жирный текст
Screen.A_NORMAL     # Обычный текст
Screen.A_REVERSE    # Инвертированный
Screen.A_UNDERLINE  # Подчёркнутый
```

### Константы клавиш

```python
# Функциональные клавиши
Screen.KEY_ESCAPE = -1
Screen.KEY_F1 = -2 ... KEY_F24 = -25

# Навигация
Screen.KEY_LEFT = -203
Screen.KEY_UP = -204
Screen.KEY_RIGHT = -205
Screen.KEY_DOWN = -206
Screen.KEY_HOME = -200
Screen.KEY_END = -201
Screen.KEY_PAGE_UP = -207
Screen.KEY_PAGE_DOWN = -208

# Специальные
Screen.KEY_TAB = -301
Screen.KEY_BACK_TAB = -302
Screen.KEY_ENTER = -32
Screen.KEY_DELETE = -102
Screen.KEY_INSERT = -101

# Модификаторы
Screen.KEY_SHIFT = -600
Screen.KEY_CONTROL = -601
```

### Основные методы Screen

```python
# Печать текста в указанную позицию
screen.print_at(text, x, y, colour=7, attr=0, bg=0, transparent=False)

# Центрирование текста по горизонтали
screen.centre(text, y, colour=7, attr=0, colour_map=None)

# Рисование с антиалиасингом
screen.move(x, y)           # Установить курсор
screen.draw(x, y, char, colour, bg, thin)  # Нарисовать линию

# Получение символа из позиции
char, fg, attr, bg = screen.get_from(x, y)  # -> (ascii_code, fg, attr, bg)

# Очистка буфера
screen.clear_buffer(fg, attr, bg, x, y, w, h)

# Прокрутка
screen.scroll(lines=1)         # Прокрутка вверх
screen.scroll_to(line)         # Прокрутка к конкретной строке

# Воспроизведение сцен
screen.play(scenes, stop_on_resize, start_scene, allow_int, duration)

# Получение ввода
event = screen.get_key()        # Блокирующий ввод
event = screen.get_event()      # Неблокирующий ввод
```

### Свойства Screen

```python
screen.width            # Ширина экрана в символах
screen.height           # Высота экрана в символах
screen.colours          # Количество поддерживаемых цветов (8, 16, 256)
screen.unicode_aware    # Поддержка Unicode
screen.dimensions      # Кортеж (height, width)
screen.palette          # Палитра для PIL
screen.start_line       # Текущая начальная строка для Canvas
```

---

## Scene — управление эффектами

```python
from asciimatics.scene import Scene

scene = Scene(effects, duration, clear, name)
```

### Параметры Scene

| Параметр | Тип | По умолчанию | Описание |
|----------|-----|--------------|----------|
| `effects` | `List[Effect]` | — | Список эффектов |
| `duration` | `int` | — | Длительность в кадрах (0=авто, -1=бесконечно) |
| `clear` | `bool` | — | Очищать ли экран перед сценой |
| `name` | `str` | `None` | Имя сцены |

### Методы Scene

```python
scene.add_effect(effect, reset=True)    # Добавить эффект
scene.remove_effect(effect)              # Удалить эффект
scene.reset(old_scene, screen)          # Сбросить состояние
scene.exit()                             # Сохранить состояние
```

### Воспроизведение

```python
# Простой пример
screen.play([Scene(effects, 500)])

# Несколько сцен с навигацией
scenes = [scene1, scene2, scene3]
screen.play(scenes, stop_on_resize=True)
```

---

## Effects — эффекты анимации

### 1. Scroll — прокрутка экрана

```python
from asciimatics.effects import Scroll

Scroll(screen, rate, **kwargs)
```

- `rate`: Число кадров между прокрутками

```python
effects.append(Scroll(screen, rate=5))
```

### 2. Cycle — циклическая смена цветов

```python
from asciimatics.effects import Cycle

Cycle(screen, renderer, y, **kwargs)
```

```python
from asciimatics.renderers import FigletText

effects.append(Cycle(screen, FigletText("HELLO"), y=10))
```

### 3. BannerText — бегущая строка

```python
from asciimatics.effects import BannerText

BannerText(screen, renderer, y, colour, bg, **kwargs)
```

```python
effects.append(BannerText(
    screen, FigletText("Moving text"),
    y=screen.height//2,
    colour=Screen.COLOUR_RED
))
```

### 4. Print — отображение текста

```python
from asciimatics.effects import Print

Print(screen, renderer, y, x, colour, attr, bg, clear, transparent, speed, **kwargs)
```

```python
effects.append(Print(screen, FigletText("Static"), y=5, speed=0))
```

### 5. Mirage — эффект появления

```python
from asciimatics.effects import Mirage

Mirage(screen, renderer, y, colour, **kwargs)
```

```python
effects.append(Mirage(screen, FigletText("Ghost"), y=10, colour=Screen.COLOUR_CYAN))
```

### 6. Stars — мерцающие звёзды

```python
from asciimatics.effects import Stars

Stars(screen, count, pattern, **kwargs)
```

```python
effects.append(Stars(screen, 200))
```

### 7. Matrix — эффект "Матрицы"

```python
from asciimatics.effects import Matrix

Matrix(screen, **kwargs)
```

```python
effects.append(Matrix(screen))
```

### 8. Wipe — стирание экрана

```python
from asciimatics.effects import Wipe

Wipe(screen, bg, **kwargs)
```

```python
effects.append(Wipe(screen, bg=Screen.COLOUR_BLACK))
```

### 9. Sprite — анимированный спрайт

```python
from asciimatics.effects import Sprite

Sprite(screen, renderer_dict, path, colour, clear, speed, **kwargs)
```

### 10. Snow — падающий снег

```python
from asciimatics.effects import Snow

Snow(screen, **kwargs)
```

```python
effects.append(Snow(screen))
```

### 11. Clock — ASCII часы

```python
from asciimatics.effects import Clock

Clock(screen, x, y, r, bg, **kwargs)
```

```python
effects.append(Clock(screen, screen.width//2, screen.height//2, 10))
```

### 12. Cog — вращающаяся шестерёнка

```python
from asciimatics.effects import Cog

Cog(screen, x, y, radius, direction, colour, **kwargs)
```

```python
effects.append(Cog(screen, 40, 15, 8, direction=1))
```

### 13. RandomNoise — белый шум

```python
from asciimatics.effects import RandomNoise

RandomNoise(screen, signal, jitter, **kwargs)
```

```python
effects.append(RandomNoise(screen, jitter=6))
```

### 14. Julia — множество Жюлиа

```python
from asciimatics.effects import Julia

Julia(screen, c, **kwargs)
```

```python
effects.append(Julia(screen, c=[-0.8, 0.156]))
```

### 15. Background — сплошной фон

```python
from asciimatics.effects import Background

Background(screen, bg, **kwargs)
```

```python
effects.append(Background(screen, bg=Screen.COLOUR_BLUE))
```

---

## Renderers — рендереры

### 1. FigletText — FIGlet шрифты

```python
from asciimatics.renderers import FigletText

renderer = FigletText("HELLO", font="big", width=200)
```

**Доступные шрифты**: `big`, `block`, `bubble`, `digital`, `ivrit`, `lean`, `mini`, `script`, `shadow`, `slant`, `small`, `smisome1`, `standard`, `term`, `usaflag`

### 2. Box — рамка

```python
from asciimatics.renderers import Box

renderer = Box(width, height, uni)
```

### 3. BarChart — горизонтальная диаграмма

```python
from asciimatics.renderers import BarChart, Y_AXIS

functions = [lambda: 50, lambda: 75, lambda: 30]
renderer = BarChart(
    15, 40, functions,
    keys=["A", "B", "C"],
    char="#",
    colour=Screen.COLOUR_GREEN,
    axes=Y_AXIS
)
```

### 4. VBarChart — вертикальная диаграмма

```python
from asciimatics.renderers import VBarChart, X_AXIS

renderer = VBarChart(15, 40, functions, axes=X_AXIS)
```

### 5. ImageFile — изображение в ASCII

```python
from asciimatics.renderers import ImageFile

renderer = ImageFile(filename, height=30, colours=8)
```

### 6. ColourImageFile — цветное изображение

```python
from asciimatics.renderers import ColourImageFile

renderer = ColourImageFile(
    screen, filename,
    height=30, bg=Screen.COLOUR_BLACK,
    fill_background=False, uni=False, dither=False
)
```

### 7. Fire — эффект огня

```python
from asciimatics.renderers import Fire

renderer = Fire(20, 60, "|  |", intensity=0.6, spot=5, colours=screen.colours)
```

### 8. Plasma — плазма эффект

```python
from asciimatics.renderers import Plasma

renderer = Plasma(height, width, colours)
```

### 9. Kaleidoscope — калейдоскоп

```python
from asciimatics.renderers import Kaleidoscope

renderer = Kaleidoscope(height, width, cell, symmetry=8)
```

### 10. Rainbow — радужный текст

```python
from asciimatics.renderers import Rainbow

renderer = Rainbow(screen, base_renderer)
```

### 11. SpeechBubble — облачко с текстом

```python
from asciimatics.renderers import SpeechBubble

renderer = SpeechBubble("Hello!", tail="L", uni=False)
```

**Позиции хвоста**: `"L"`, `"R"`, `"TL"`, `"TR"`, `"BL"`, `"BR"`

### 12. Typewriter — печатающий текст

```python
from asciimatics.renderers import Typewriter, StaticRenderer

renderer = Typewriter(StaticRenderer(images=[text]), speed=5)
```

---

## Particles — система частиц

### Базовые классы

```python
from asciimatics.particles import Particle, ParticleEmitter, ParticleEffect
```

### 1. StarFirework — фейерверк со звездой

```python
from asciimatics.particles import StarFirework

effects.append(StarFirework(screen, x, y, life_time))
```

### 2. RingFirework — кольцевой фейерверк

```python
from asciimatics.particles import RingFirework

effects.append(RingFirework(screen, x, y, life_time))
```

### 3. SerpentFirework — змеевидный фейерверк

```python
from asciimatics.particles import SerpentFirework

effects.append(SerpentFirework(screen, x, y, life_time))
```

### 4. PalmFirework — пальмовый фейерверк

```python
from asciimatics.particles import PalmFirework

effects.append(PalmFirework(screen, x, y, life_time))
```

### 5. Explosion — взрыв пламени

```python
from asciimatics.particles import Explosion

effects.append(Explosion(screen, x, y, life_time))
```

### 6. DropScreen — гравитационное падение

```python
from asciimatics.particles import DropScreen

effects.append(DropScreen(screen, life_time))
```

### 7. ShootScreen — выстрел

```python
from asciimatics.particles import ShootScreen

effects.append(ShootScreen(screen, x, y, life_time, diameter=None))
```

### 8. Rain — дождь

```python
from asciimatics.particles import Rain

effects.append(Rain(screen, life_time))
```

---

## Sprites — спрайты

### 1. Sprite — базовый класс

```python
from asciimatics.effects import Sprite
```

### 2. Sam — анимированный персонаж

```python
from asciimatics.sprites import Sam

sprite = Sam(screen, path, start_frame, stop_frame)
```

### 3. Arrow — стрелка

```python
from asciimatics.sprites import Arrow

sprite = Arrow(screen, path, colour, start_frame, stop_frame)
```

### 4. Plot — точка для отображения пути

```python
from asciimatics.sprites import Plot

sprite = Plot(screen, path, colour, start_frame, stop_frame)
```

### StaticRenderer для спрайтов

```python
from asciimatics.renderers import StaticRenderer

renderer = StaticRenderer(
    images=[ascii_art],  # Список ASCII-art изображений
    animation=_blink     # Функция выбора кадра
)

def _blink():
    import random
    return 0 if random.random() > 0.9 else 1
```

---

## Paths — пути движения

### 1. Path — статический путь

```python
from asciimatics.paths import Path

path = Path()
path.jump_to(x, y)                    # Телепортация
path.wait(delay)                        # Ожидание
path.move_straight_to(x, y, steps)    # Прямая линия
path.move_round_to(points, steps)       # Кривая Безье
path.reset()                           # Сброс в начало
x, y = path.next_pos()                 # Следующая позиция
path.is_finished()                     # Проверка завершения
```

### 2. DynamicPath — динамический путь

```python
from asciimatics.paths import DynamicPath

class MyPath(DynamicPath):
    def process_event(self, event):
        return event
```

---

## Widgets — виджеты TUI

### 1. Frame — контейнер

```python
from asciimatics.widgets import Frame, Layout

frame = Frame(
    screen, height, width,
    data=None,
    on_load=None,
    has_border=True,
    hover_focus=False,
    name=None,
    title=None,
    x=None, y=None,
    has_shadow=False,
    reduce_cpu=False,
    is_modal=False,
    can_scroll=True
)

layout = Layout([1, 18, 1])
frame.add_layout(layout)
frame.fix()
```

### 2. Layout — компоновка

```python
from asciimatics.widgets import Layout

layout = Layout([1, 1, 1], fill_frame=False)
frame.add_layout(layout)
layout.add_widget(widget, column_index)
```

### 3. Text — однострочное поле ввода

```python
from asciimatics.widgets import Text

layout.add_widget(Text(
    label="Name:",
    name="username",
    on_change=self._on_change,
    validator="^[a-zA-Z]*$",
    max_length=20
), 1)
```

### 4. TextBox — многострочное поле

```python
from asciimatics.widgets import TextBox
from asciimatics.parsers import AsciimaticsParser

layout.add_widget(TextBox(
    5,
    label="Comments:",
    name="comments",
    parser=AsciimaticsParser(),
    line_wrap=True
), 1)
```

### 5. Button — кнопка

```python
from asciimatics.widgets import Button

layout.add_widget(Button("Submit", self._submit), 1)
```

### 6. CheckBox — флажок

```python
from asciimatics.widgets import CheckBox

layout.add_widget(CheckBox(
    "I agree",
    label="Agreement:",
    name="agree",
    on_change=self._on_change
), 1)
```

### 7. RadioButtons — переключатели

```python
from asciimatics.widgets import RadioButtons

layout.add_widget(RadioButtons([
    ("Option 1", 1),
    ("Option 2", 2),
    ("Option 3", 3)
], label="Select:", name="choice", on_change=self._on_change), 1)
```

### 8. ListBox — список

```python
from asciimatics.widgets import ListBox

layout.add_widget(ListBox(
    height=5,
    options=lambda: [(item, i) for i, item in enumerate(items)],
    label="Items:",
    name="selected"
), 1)
```

### 9. MultiColumnListBox — многоколоночный список

```python
from asciimatics.widgets import MultiColumnListBox

layout.add_widget(MultiColumnListBox(
    height=5,
    columns=[3, 10, 10],
    options=...,
    labels=["#", "Name", "Status"]
), 1)
```

### 10. DropdownList — выпадающий список

```python
from asciimatics.widgets import DropdownList

layout.add_widget(DropdownList([
    ("Item 1", 1),
    ("Item 2", 2),
    ("Item 3", 3)
], label="Select:", name="dropdown"), 1)
```

### 11. DatePicker — выбор даты

```python
from asciimatics.widgets import DatePicker

layout.add_widget(DatePicker(
    label="Date:",
    name="date",
    year_range=range(1990, 2100),
    on_change=self._on_change
), 1)
```

### 12. TimePicker — выбор времени

```python
from asciimatics.widgets import TimePicker

layout.add_widget(TimePicker(
    label="Time:",
    name="time",
    on_change=self._on_change,
    seconds=True
), 1)
```

### 13. Label — текстовая метка

```python
from asciimatics.widgets import Label

layout.add_widget(Label("Title:", colour=Screen.COLOUR_YELLOW), 1)
```

### 14. Divider / VerticalDivider — разделители

```python
from asciimatics.widgets import Divider, VerticalDivider

layout.add_widget(Divider(height=2), 1)
layout.add_widget(VerticalDivider())
```

### 15. PopUpDialog — всплывающий диалог

```python
from asciimatics.widgets import PopUpDialog

self._scene.add_effect(PopUpDialog(
    screen,
    "Are you sure?",
    ["Yes", "No"],
    on_close=self._quit_on_yes
))
```

### 16. PopupMenu — всплывающее меню

```python
from asciimatics.widgets import PopupMenu

PopupMenu(screen, options, x, y)
# options: [(text, callback), ...]
```

### Управление данными формы

```python
frame.data              # Словарь {name: value}
frame.save()            # Сохранить данные
frame.reset()           # Сбросить форму

# Валидация
from asciimatics.exceptions import InvalidFields

try:
    frame.save(validate=True)
except InvalidFields as exc:
    print(f"Invalid fields: {exc.fields}")
```

### Темы Frame

```python
frame.set_theme("default")    # Стандартная
frame.set_theme("green")      # Зелёная
frame.set_theme("monochrome") # Монохром
frame.set_theme("bright")     # Яркая
frame.set_theme("tlj256")    # red/white (256 цветов)
```

---

## Events — события ввода

### KeyboardEvent — нажатие клавиши

```python
from asciimatics.event import KeyboardEvent

event = KeyboardEvent(key_code)

if isinstance(event, KeyboardEvent):
    if event.key_code == ord('Q'):
        return
```

### MouseEvent — событие мыши

```python
from asciimatics.event import MouseEvent

# Константы кнопок
MouseEvent.LEFT_CLICK = 1
MouseEvent.RIGHT_CLICK = 2
MouseEvent.DOUBLE_CLICK = 4
MouseEvent.SCROLL_UP = 8
MouseEvent.SCROLL_DOWN = 16

if event.buttons & MouseEvent.LEFT_CLICK:
    print(f"Left click at ({event.x}, {event.y})")
```

---

## Полный API Reference

### Модули

```python
asciimatics.screen          # Screen, Canvas
asciimatics.scene           # Scene
asciimatics.effects         # Effect, Scroll, Cycle, BannerText, Print, Mirage, Stars, Matrix, Wipe, Sprite, Snow, Clock, Cog, RandomNoise, Julia, Background
asciimatics.renderers       # FigletText, Box, BarChart, VBarChart, ImageFile, ColourImageFile, Fire, Plasma, Kaleidoscope, Rainbow, SpeechBubble, Typewriter
asciimatics.particles       # Particle, ParticleEmitter, StarFirework, RingFirework, SerpentFirework, PalmFirework, Explosion, DropScreen, ShootScreen, Rain
asciimatics.sprites         # Sprite, Sam, Arrow, Plot
asciimatics.paths          # Path, DynamicPath
asciimatics.widgets        # Frame, Layout, Text, TextBox, Button, CheckBox, RadioButtons, ListBox, MultiColumnListBox, DropdownList, DatePicker, TimePicker, Label, Divider, PopUpDialog, PopupMenu
asciimatics.event           # Event, KeyboardEvent, MouseEvent
asciimatics.exceptions      # InvalidFields
```

---

## Примеры использования

### Hello World

```python
from random import randint
from asciimatics.screen import Screen

def demo(screen):
    while True:
        screen.print_at(
            'Hello World!',
            randint(0, screen.width),
            randint(0, screen.height),
            colour=randint(0, 7),
            bg=randint(0, 7)
        )
        ev = screen.get_key()
        if ev in (ord('Q'), ord('q')):
            return
        screen.refresh()

Screen.wrapper(demo)
```

### Анимация с FIGlet и звёздами

```python
from asciimatics.effects import Cycle, Stars
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen

def demo(screen):
    effects = [
        Cycle(screen, FigletText("ASCIIMATICS", font='big'),
              int(screen.height / 2 - 8)),
        Cycle(screen, FigletText("ROCKS!", font='big'),
              int(screen.height / 2 + 3)),
        Stars(screen, 200)
    ]
    screen.play([Scene(effects, 500)])

Screen.wrapper(demo)
```

### Фейерверк

```python
from random import randint
from asciimatics.particles import StarFirework
from asciimatics.scene import Scene
from asciimatics.screen import Screen

def demo(screen):
    effects = []
    for _ in range(20):
        effects.append(StarFirework(
            screen,
            randint(3, screen.width - 4),
            randint(1, screen.height - 2),
            randint(20, 30),
            start_frame=randint(0, 250)
        ))
    screen.play([Scene(effects, -1)])

Screen.wrapper(demo)
```

### Интерактивная форма

```python
from asciimatics.widgets import Frame, Text, Button, Layout
from asciimatics.scene import Scene
from asciimatics.screen import Screen
from asciimatics.effects import Background

class DemoFrame(Frame):
    def __init__(self, screen):
        super().__init__(screen, 20, 60, has_shadow=True)
        layout = Layout([1, 1, 1])
        self.add_layout(layout)
        layout.add_widget(Text(label="Name:", name="name"), 0)
        layout.add_widget(Button("Submit", self._submit), 1)
        self.fix()

    def _submit(self):
        print(f"Name: {self.data['name']}")

def demo(screen):
    screen.play([Scene([Background(screen), DemoFrame(screen)], -1)])

Screen.wrapper(demo)
```

### Рисование линий

```python
from asciimatics.screen import Screen

def demo(screen):
    screen.move(0, screen.height // 2)
    screen.draw(screen.width, screen.height // 2, colour=Screen.COLOUR_GREEN)
    screen.refresh()
    screen.get_key()

Screen.wrapper(demo)
```

### Дождь с частицами

```python
from asciimatics.particles import Rain
from asciimatics.effects import Print
from asciimatics.renderers import FigletText
from asciimatics.scene import Scene
from asciimatics.screen import Screen

def demo(screen):
    effects = [
        Rain(screen, 200),
        Print(screen, FigletText("RAIN"), y=5)
    ]
    screen.play([Scene(effects, -1)])

Screen.wrapper(demo)
```

---

## Ограничения

1. **Терминал должен поддерживать ANSI escape sequences**
2. **Windows**: требуется pywin32 или Windows Terminal / WSL
3. **Требуется curses/ncurses**: на Windows можно использовать Windows Terminal или WSL
4. **Минимальная ширина терминала**: 80 символов для виджетов
5. **Python 3.8+**: старые версии не поддерживаются
6. **Zero dependencies** — НЕТ (требует pyfiglet, Pillow, wcwidth)

---

## Ссылки

- Репозиторий: https://github.com/peterbrittain/asciimatics
- PyPI: https://pypi.org/project/asciimatics/
- Документация: http://asciimatics.readthedocs.io/