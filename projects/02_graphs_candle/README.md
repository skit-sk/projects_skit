# Trading Python Graphs - Технический план

## Архитектура проекта

```
graphs_candle/
├── main.py                  # Точка входа (Flask сервер)
├── requirements.txt         # Зависимости
├── README.md               # Документация
│
├── data/                   # Работа с данными
│   ├── __init__.py
│   ├── fetcher.py          # Получение данных (CCXT + Bitget)
│   ├── generator.py        # Генерация тестовых данных
│   └── patterns.py         # Обнаружение паттернов
│
├── charts/                 # Построение графиков
│   ├── __init__.py
│   ├── candlestick.py      # Свечные графики (Plotly)
│   ├── pnl.py              # P&L графики
│   └── combined.py         # Комбинированные графики
│
├── templates/              # HTML шаблоны
│   └── index.html          # Главная страница
│
└── static/                 # Статика
    └── style.css           # Стили
```

## API Endpoints

| Endpoint | Описание |
|----------|----------|
| `GET /` | Главная страница с графиками |
| `GET /api/symbols` | Список доступных тикеров |
| `GET /api/candles?symbol=BTCUSDT&timeframe=1d&limit=100` | OHLCV данные |
| `GET /api/patterns?symbol=BTCUSDT` | Обнаруженные паттерны |
| `GET /api/pnl?symbol=BTCUSDT` | P&L статистика |
| `GET /api/summary?symbol=BTCUSDT` | Сводка (цена, объём, винрейт) |

## Стек технологий

- **Backend:** Flask
- **Data:** CCXT (Bitget API)
- **Charts:** Plotly (интерактивные HTML графики)
- **Data processing:** pandas, numpy

## Источник данных

**CCXT** - универсальная библиотека для работы с криптовалютными биржами

- Биржа: **Bitget**
- API: https://www.bitget.com/api-doc/spot/market-data/Get-Candle-Data

## Доступные символы (Bitget)

- BTCUSDT, ETHUSDT, SOLUSDT, BNBUSDT, ADAUSDT
- И другие пары USDT

## Таймфреймы

- 1m, 5m, 15m, 1h, 4h, 1d

## Паттерны для обнаружения

1. **Hammer** - бычий разворот
2. **Shooting Star** - медвежий разворот  
3. **Doji** - неопределённость
4. **Bullish Engulfing** - бычье поглощение
5. **Bearish Engulfing** - медвежье поглощение
6. **Morning Star** - утренняя звезда (3 свечи)
7. **Evening Star** - вечерняя звезда (3 свечи)
8. **Marubozu** - сильный тренд

## Графики

1. **Candlestick Chart** - свечной график с паттернами
2. **P&L Chart** - кумулятивный профит/лосс + drawdown
3. **Combined Chart** - свечи + P&L на одном графике

## KPI Метрики

- Current Price
- 24h Change (%)
- 24h Volume
- Total P&L (симуляция)
- Win Rate (симуляция)
- Sharpe Ratio (симуляция)
- Max Drawdown

## Запуск

```bash
pip install -r requirements.txt
python main.py
# Открыть http://localhost:5000
```

## Пример API вызова (CCXT)

```python
import ccxt

exchange = ccxt.bitget()
ohlcv = exchange.fetch_ohlcv('BTC/USDT', '1d', limit=100)
# [[timestamp, open, high, low, close, volume], ...]
```

## Деплой

- Vercel (через Flask)
- Render.com
- Railway