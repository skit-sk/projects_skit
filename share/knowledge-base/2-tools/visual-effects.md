# Визуальные эффекты — Terminal Visual Effects

Python-библиотеки для создания **ASCII-анимаций** и **визуальных эффектов** в терминале. Не являются графиками данных — это декоративные эффекты для презентаций, демо и wow-эффектов.

---

## TerminalTextEffects — Terminal Visual Effects Engine

**TerminalTextEffects (TTE)** — движок визуальных эффектов, работает как приложение и Python-библиотека.

**Репозиторий**: https://github.com/ChrisBuilds/terminaltexteffects  
**PyPI**: `pip install terminaltexteffects`  
**Stars**: 4k  
**Python**: 3.9+  
**Зависимости**: none

---

## Установка

```bash
pip install terminaltexteffects
```

### Как приложение

```bash
# После установки доступна команда `tte`
echo "Hello World" | tte matrix

# Или через Python модуль
echo "Hello" | python -m terminaltexteffects rain
```

---

## CLI — использование

```bash
# Базовый синтаксис
echo "TEXT" | tte <effect> [options]

# Справка по эффекту
tte decrypt -h

# Случайный эффект
echo "Random" | tte --random-effect

# Pipe из файла
cat myfile.txt | tte beams
```

---

## Все 32+ эффекта

| Эффект | Описание |
|--------|----------|
| `beams` | Лучи, освещающие символы |
| `binarypath` | Binary representations движутся к home coordinate |
| `blackhole` | Символы поглощаются чёрной дырой |
| `bouncyballs` | Bouncy balls падают сверху |
| `bubbles` | Пузыри плывут вниз и лопаются |
| `burn` | Вертикальное выжигание |
| `colorshift` | Градиент цветов |
| `crumble` | Символы осыпаются в пыль |
| `decrypt` | Movie-style decryption |
| `errorcorrect` | Символы исправляются в последовательности |
| `expand` | Расширение от одной точки |
| `fireworks` | Фейерверк |
| `highlight` | Specular highlight |
| `laseretch` | Лазерное выжигание |
| `matrix` | Matrix digital rain |
| `middleout` | Расширение от середины |
| `orbittingvolley` | 4 launcher orbiting |
| `overflow` | Overflow effect |
| `pour` | Заполнение от направления |
| `print` | Print head анимация |
| `rain` | Дождь символов |
| `randomsequence` | Random sequence печать |
| `rings` | Спинющиеся кольца |
| `scattered` | Разбросанный текст |
| `slice` | Разрезание пополам |
| `slide` | Слайд из-за пределов |
| `smoke` | Дым |
| `spotlights` | Прожекторы |
| `spray` | Разбрызгивание |
| `swarm` | Рой |
| `sweep` | Sweep reveal |
| `synthgrid` | Сетка растворяется |
| `thunderstorm` | Гроза |
| `unstable` | Нестабильный jumble |
| `vhstape` | VHS глитч |
| `waves` | Волны |
| `wipe` | Вытирание |

---

## Примеры эффектов

### Matrix

```bash
echo "Wake up Neo..." | tte matrix
```

### Decrypt

```bash
echo "Secret Message" | tte decrypt --typing-speed 2
```

### Fireworks

```bash
echo "WOW!" | tte fireworks
```

### Thunderstorm

```bash
echo "Storm" | tte thunderstorm
```

### VHSTape (глитч)

```bash
echo "Retro Vibes" | tte vhstape
```

### Rain

```bash
cat long_text.txt | tte rain
```

---

## Как Python библиотека

```python
from terminaltexteffects.effects import Rain

effect = Rain("your text here")

for frame in effect:
    print(frame)
```

```python
# С terminal_output context manager (авто-управление курсором)
from terminaltexteffects.effects import Fireworks

effect = Fireworks("WOW!")
with effect.terminal_output() as terminal:
    for frame in effect:
        terminal.print(frame)
```

---

## Возможности

- **Xterm 256 / RGB hex** color support
- **Complex character movement** via Paths, Waypoints, bezier curves
- **Motion easing** — плавное ускорение/замедление
- **Scenes** — сложные анимации слоями
- **Variable stop/step color gradients**
- **Event handling** — callbacks на Path/Scene state changes
- **Effect customization** — dataclass конфигурация автоматически → CLI args
- **Runs inline** — сохраняет состояние терминала

---

## Опции CLI (общие)

```bash
--frame-rate FRAME_RATE    # FPS (default 60)
--canvas-width WIDTH      # Ширина canvas
--canvas-height HEIGHT    # Высота canvas
--terminal-background-color # Цвет фона терминала
--no-color                # Отключить цвета
--xterm-colors            # Конвертировать RGB → Xterm 256
```

---

## Ограничения

1. **Не графики данных** — это визуальные эффекты, не диаграммы
2. **Терминал с ANSI** — требуется современный терминал
3. **GPU not used** — вся анимация текстовая
4. **Performance** — сложные эффекты могут тормозить

---

## Когда использовать

| Ситуация | Инструмент |
|----------|------------|
| ASCII-анимации для презентаций | TerminalTextEffects |
| Matrix rain / Fireworks демо | TerminalTextEffects |
| Визуальные эффекты для загрузчиков | TerminalTextEffects |
| Графики и диаграммы | plotext, termcharts, plotille |
| Полноэкранные TUI приложения | asciimatics |
| Интерактивные формы | asciimatics |

---

## Альтернативы

| Библиотека | Stars | Тип |
|------------|-------|-----|
| **TerminalTextEffects** | 4k | Effects engine |
| **asciimatics** | 4.3k | Effects + TUI + Particles |

---

## Ссылки

- Репозиторий: https://github.com/ChrisBuilds/terminaltexteffects
- PyPI: https://pypi.org/project/terminaltexteffects/
- Документация: https://chrisbuilds.github.io/terminaltexteffects/