# graphs_candle — Свечные графики

**Расположение:** `projects/02_graphs_candle/`

## Назначение

Интерактивные свечные графики (Plotly) с обнаружением паттернов.

## Стек

- **Flask** (веб-фреймворк)
- **ccxt** (Bitget API через библиотеку ccxt v4.5.50)
- **plotly** (интерактивные графики HTML)
- **pandas, numpy** (анализ данных)

## Архитектура

```
projects/02_graphs_candle/
├── main.py                         # Входная точка Flask
├── routes/
│   ├── api.py                      # API-эндпоинты
│   ├── web.py                      # Веб-маршруты
│   └── graphics.py                 # Построение графиков Plotly
├── venv/                           # Виртуальное окружение (ccxt, plotly и т.д.)
└── templates/                      # HTML-шаблоны
```

## Ключевые особенности

- **ccxt v4.5.50** — используется `ccxt.async_support` для Bitget
- **Plotly** — генерация интерактивных HTML-графиков
- **Паттерны** — обнаружение свечных паттернов (numpy)

## Запуск

```bash
cd projects/02_graphs_candle
source venv/bin/activate
python main.py
# или
./scripts/flask.sh start 02
```

## Связанные KB

- [ccxt Bitget API](../1-exchanges/ccxt-bitget.md) — полный справочник
