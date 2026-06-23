# Сравнительный анализ браузерных инструментов

**Сайт:** https://tradingview-demos-sk.vercel.app
**Дата:** 2026-05-01
**Инструменты:** Agent-Browser, Playwright (Python), Lightpanda

---

## 1. Agent-Browser v0.26.0

### Снимки экрана (Screenshots)

| Файл | Размер | Описание |
|------|--------|----------|
| `screenshot-1777598194081.png` | 81 KB | Главная галерея |
| `screenshot-1777598202656.png` | 3.8 KB | Symbol Overview полная страница |
| `screenshot-1777598214958.png` | 48 KB | Fixed Size страница |
| `screenshot-1777598241829.png` | 55 KB | Прокрутка галереи #1 |
| `screenshot-1777598244273.png` | 67 KB | Прокрутка галереи #2 |

### Данные Snapshot

```
- heading "TradingView Charts Demo Gallery" [level=1, ref=e1]
- heading "📊 Chart Types — Типы графиков (Lightweight)" [level=2, ref=e2]
- Iframe [ref=e3]
  - link "Charting by TradingView" [ref=e162]
- link "Open Full ↗" [ref=e4]
- link "📄 Doc" [ref=e5]
- link "⚡ Official" [ref=e6]
...
```

**Всего элементов:** 161 интерактивных элементов

### Команды и результаты

| Команда | Результат | Время |
|---------|-----------|-------|
| `open <url>` | ✅ | <1 сек |
| `goto <url>` | ✅ | <1 сек |
| `snapshot -i` | ✅ 161 элемент | ~2 сек |
| `snapshot -i --urls` | ✅ захватил href | ~2 сек |
| `screenshot` | ✅ | ~1 сек |
| `scroll down` | ✅ | <1 сек |
| `close` | ✅ | <1 сек |

### Оценка эффективности

| Метрика | Оценка |
|---------|--------|
| Скорость | ⭐⭐⭐⭐⭐ |
| Надёжность | ⭐⭐⭐⭐⭐ |
| Снимки экрана | ⭐⭐⭐⭐ |
| Покрытие | ⭐⭐⭐⭐⭐ |

**Общая:** 5/5

---

## 2. Playwright (Python)

### Конфигурация

```python
executable_path="/tmp/.agent-browser/browsers/chrome-148.0.7778.97/chrome"
env={"LD_LIBRARY_PATH": "/tmp/pango_libs/usr/lib/x86_64-linux-gnu:..."}
```

### Результаты

```json
{
  "title": "TradingView Charts Demo Gallery",
  "url": "https://tradingview-demos-sk.vercel.app/",
  "iframes_count": 43,
  "links_count": 113,
  "headings": [
    {"tag": "H1", "text": "TradingView Charts Demo Gallery"},
    {"tag": "H2", "text": "📊 Chart Types — Типы графиков (Lightweight)"},
    {"tag": "H2", "text": "📈 Series Types — Типы серий (Lightweight)"},
    {"tag": "H2", "text": "🎨 Conditions — Условия/Темы (Lightweight)"},
    {"tag": "H2", "text": "🧩 Widgets — TradingView Widgets (iframe)"}
  ],
  "widget_title": "Symbol Overview"
}
```

### Оценка эффективности

| Метрика | Оценка |
|---------|--------|
| Скорость | ⭐⭐⭐⭐ |
| Надёжность | ⭐⭐⭐ |
| Снимки экрана | ⭐⭐⭐ |
| Покрытие | ⭐⭐⭐⭐ |

**Общая:** 4/5

**Проблемы:**
- Требует ручной настройки LD_LIBRARY_PATH
- Ошибки запуска при отсутствии системных библиотек

---

## 3. Lightpanda

### Конфигурация

```bash
/tmp/lightpanda fetch --dump semantic_tree_text --wait-ms 5000 <url>
```

### Результаты (Semantic Tree)

```
1 RootWebArea 'TradingView Charts Demo Gallery'
4 heading 'TradingView Charts Demo Gallery'
5 paragraph
  6 'Lightweight Charts™ v5.2 + Widgets — Все варианты создания графиков'
8 heading '📊 Chart Types — Типы графиков (Lightweight)'
15 '1. Standard Time Chart'
17 'createChart() — стандартный time-based график'
19 [i] link 'Open Full ↗'
20 [i] link '📄 Doc'
21 [i] link '⚡ Official'
...
```

### Оценка эффективности

| Метрика | Оценка |
|---------|--------|
| Скорость | ⭐⭐⭐⭐⭐ |
| Надёжность | ⭐⭐⭐⭐ |
| Снимки экрана | ⭐ |
| Покрытие | ⭐⭐⭐⭐ |

**Общая:** 3.5/5

**Плюсы:**
- Мгновенный запуск, не требует настройки
- Отличный semantic tree вывод
- JSON/markdown/semantics доступны

**Минусы:**
- Нет скриншотов
- Нет интерактивности

---

## Сравнительная таблица

| Критерий | Agent-Browser | Playwright | Lightpanda |
|----------|---------------|-----------|------------|
| **Простота запуска** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Скорость** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Интерактивность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐ |
| **Скриншоты** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐ |
| **Semantic анализ** | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ |
| **Надёжность** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ |
| **Без настройки** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐⭐⭐⭐ |

---

## Выводы

### Рекомендации по использованию

| Задача | Инструмент |
|--------|------------|
| Быстрый анализ страницы | Lightpanda |
| Интерактивное тестирование | Agent-Browser |
| Скриншоты с аннотациями | Agent-Browser |
| Программное тестирование | Playwright |
| SEO/Accessibility анализ | Lightpanda |

### Лучший инструмент

**Agent-Browser** — универсальный лидер:
- Простой CLI интерфейс
- Референсы @eN для надёжного взаимодействия
- Отличные скриншоты с аннотациями
- Работает "из коробки" с правильной конфигурацией

### Проблемы обнаруженные

1. **CORS блокировка** — TradingView embed скрипты блокируются в iframe браузером (не код)
2. **Отсутствие Doc ссылки** — Economic Map не имеет локальной ссылки на документацию
3. **Lightpanda скриншоты** — инструмент не поддерживает визуальные снимки

---

## Файлы с результатами

- `agent-browser-snapshots/` — 5 скриншотов Agent-Browser
- `playwright-snapshots/` — 2 скриншота Playwright
- `lightpanda-snapshots/symbol-overview.txt` — HTML дамп виджета
- `agent-browser-report.md` — детальный отчёт Agent-Browser