# Глава 30: Веб-терминал скальпинга — UX/Архитектура

> **Источник:** `data/tradeLLm/06_technical_specs/Да, подготовь подробное ТЗ со всеми техническими р.docx`, `data/tradeLLm/06_technical_specs/давай отдельно сделаем глубокий анализ программ дл.docx`, `data/tradeLLm/06_technical_specs/Стратегический анализ и архитектура функциональных модулей веб-терминала для профессионального скальпинга.docx`

## 30.1 Анализ рынка веб-терминалов

### Сравнение Vataga / Tiger Trade / Web-решений

| Параметр | Vataga | Tiger Trade | Web-решения (GoCharting, Dhan) |
|----------|--------|-------------|---------------------------------|
| **Ориентация** | Intraday/Scalping | Универсальная | Кросс-платформенная |
| **Multi-window** | ✅ Tabs | ⚠️ Limited | ✅ Tabs |
| **TradingView Charts** | ✅ | ✅ | ✅ |
| **Deep order book** | ✅ USD | ❌ | ⚠️ Limited |
| **One-click switching** | ✅ | ❌ | ⚠️ |
| **PnL / Leverage** | ✅ Bulk | ✅ | ✅ |
| **Demo mode** | ❌ | ✅ | ✅ |
| **Latency** | Native (минимальная) | Native | Web (выше) |
| **Установка** | Desktop | Desktop | Не нужна (web) |

### Что брать как референс

**Vataga:** Логика скорости и плотности интерфейса — несколько окон, связка графика и стакана, быстрый доступ к leverage и PnL.

**Tiger Trade:** Универсальный интерфейс, режим обучения/демо, широкий охват рынков.

**Web-решения (GoCharting, Dhan):** Кросс-платформенность, централизованные обновления.

## 30.2 Сравнение методологий анализа

| Параметр | Классический TA (Retail) | Микроструктура (Order Flow) |
|----------|---------------------------|------------------------------|
| **Инструментарий** | RSI, MACD, Stochastic, Bollinger | Footprint, DOM, Volume Profile, Heatmaps |
| **Природа данных** | Третичные производные от OHLC | Прямая запись транзакций и лимитных ордеров |
| **Временной фактор** | Lagging | Real-time / Leading |
| **Цель** | Статистическая вероятность | Намерения Market Makers |
| **Объём данных** | 1 точка на свечу | Тысячи тиков в секунду |

## 30.3 Архитектурные преимущества и барьеры

**Преимущества веб-платформ:**
- Нет инсталляционного барьера
- Кросс-платформенность
- Централизованные обновления на сервере

**Главное ограничение:** **latency отрисовки**. Стандартные DOM/SVG для Footprint → перегрузка Main Thread → "фризы".

**Решение:** WebGL/Canvas → делегирование рендеринга GPU → стабильные 60 FPS.

## 30.4 Функционал веб-терминала

### 1. Общие сведения

- **Назначение:** Веб-торговля с упором на скальпинг и интрадей
- **Цель:** Быстрый анализ, оперативное выставление ордеров, контроль риска, журнал сделок
- **Особенность:** Web-only, без установки, поведение близкое к профессиональному десктоп-терминалу

### 2. Целевая аудитория

- Скальперы
- Intraday-трейдеры
- Order Flow трейдеры
- Продвинутые пользователи (web-only)

### 3. Терминология

| Сокр. | Расшифровка |
|-------|-------------|
| **DOM** | Depth of Market, стакан |
| **Order Flow** | Поток заявок + сделок (агрессивные покупки/продажи) |
| **Footprint** | Визуализация объёма внутри свечи по уровням |
| **PnL** | Profit and Loss |
| **OCO/OTO** | Связанные ордера |
| **WS** | WebSocket |
| **API** | Программный интерфейс биржи/брокера |
| **Risk Engine** | Модуль контроля риска |
| **Workspace** | Рабочее пространство (компоновка окон) |

## 30.5 Модули веб-терминала

### Multi-Window Workspace

- **Tabs** для нескольких графиков
- **Drag-and-drop** для кастомной компоновки
- **Snap-to-grid** для точного выравнивания
- **Save/Load layouts** в localStorage

### Глобальные настройки

- Дефолтные настройки по символу
- Шаблоны leverage
- One-click account switching
- Bulk leverage (применить ко всем позициям)

### Trading Panel (стакан + лента)

- **Order Book (DOM):** топ-20 bid/ask с объёмами
- **Time & Sales:** лента сделок
- **Quick Trade:** форма ввода ордера
- **OCO/OTO:** связанные ордера

### Risk Engine

- Max position size по символу
- Max leverage по символу
- Max daily loss
- Max open orders
- Auto-cancel при риске

### Positions & Orders Monitor

- Открытые позиции
- Активные ордера
- История сделок
- PnL в реальном времени (realized + unrealized)
- Risk flags (CRITICAL_RECOVERY)

### Analytics

- Win rate за период
- Average RR
- Profit factor
- Sharpe / Sortino
- Drawdown chart
- Equity curve

## 30.6 Панели Layout (макет)

```
┌──────────────────────────────────────────────────────────────┐
│  Top Bar:  Symbol Selector | Account | Settings | Notifications│
├──────┬───────────────────────────────────────────┬───────────┤
│      │                                           │           │
│ Side │  Main Chart (TradingView/LWC)            │ DOM      │
│ bar  │                                           │  (Order  │
│      │                                           │  Book)   │
│      │                                           │           │
│      ├───────────────────────────────────────────┤           │
│      │  Footprint (микроструктура)              │ Time &   │
│      │  Volume Profile (сбоку)                  │ Sales     │
│      │                                           │           │
├──────┴───────────────────────────────────────────┴───────────┤
│  Bottom Bar: Positions | Orders | History | PnL | Account  │
└──────────────────────────────────────────────────────────────┘
```

## 30.7 Горячие клавиши (Hotkeys)

| Клавиша | Действие |
|---------|----------|
| `Ctrl+B` | Buy (Market) |
| `Ctrl+S` | Sell (Market) |
| `Ctrl+L` | Buy (Limit) |
| `Ctrl+K` | Sell (Limit) |
| `Ctrl+Z` | Cancel all orders |
| `Ctrl+F` | Flatten position |
| `Ctrl+T` | Trailing stop |
| `Ctrl+/` | Toggle DOM panel |
| `Ctrl+Shift+/` | Toggle Footprint |
| `Esc` | Cancel current action |
| `F1` | Quick help |

## 30.8 Performance Targets

| Операция | Target | Метод |
|----------|--------|-------|
| Order placement | < 50ms | ASGI + WebSocket |
| DOM update | < 100ms | WebSocket tick stream |
| Chart update | 60 FPS | LWC 5.2.0 / WebGL |
| Footprint | 30 FPS | Datashader + WebGL |
| PnL update | < 1s | ASGI poll |
| Risk check | < 10ms | In-memory state |

## 30.9 State Management

```python
# Frontend state (Pinia/Vuex или vanilla)
state = {
    'symbol': 'API3USDT',
    'timeframe': '1m',
    'account': 'main',
    'positions': [],
    'orders': [],
    'pnl': {
        'realized': 0.0,
        'unrealized': 0.0,
        'total': 0.0
    },
    'risk': {
        'flags': [],
        'max_position': 0.0,
        'leverage': 10
    },
    'ui': {
        'active_tab': 'chart',
        'show_dom': True,
        'show_footprint': True
    }
}
```

## 30.10 Mockup панели инструментов

```
┌────────────────────────────────────────────────────┐
│  API3USDT ▼  | 1m ▼  | $0.2992 (+2.4%) | L: 10x   │
├────────────────────────────────────────────────────┤
│  [DOM]  [T&S]  [Trades]  [Footprint]  [Risk]  [...] │
└────────────────────────────────────────────────────┘
```

## 30.11 Risk Engine UI

```
┌────────────────────────────────────────────────────┐
│  RISK PANEL                                         │
├────────────────────────────────────────────────────┤
│  Equity:           $1,847.99                       │
│  Used Margin:      $185.20 (10.0%)                 │
│  Unrealized PnL:   -$5.46 (-218.3%)               │
│  Liquidation:      $0.2693                        │
│  Distance to Lp:   9.8%                           │
│                                                     │
│  ⚠️  FLAGS:                                         │
│  🔴 CRITICAL_RECOVERY                              │
│  🔴 PnL -218%                                      │
│                                                     │
│  [Smart Recovery Plan]                              │
│  → Look for Breaker Block mitigation               │
│  → Set stop at: 0.2750                             │
│  → Suggested TP: 0.2900                           │
└────────────────────────────────────────────────────┘
```

## 30.12 TradingView Integration (для аналитики)

- Advanced Chart на основном окне
- Symbol Overview в компактном виде
- Economic Calendar для макро
- Crypto/Stock/Forex Heatmap
- Ticker Tape на каждой странице

## 30.13 Journal & Analytics

```
┌────────────────────────────────────────────────────┐
│  JOURNAL                                            │
├────────────────────────────────────────────────────┤
│  Time   Symbol  Side  Price  Qty  PnL    Fee  Notes │
│  ─────  ──────  ────  ─────  ───  ────   ───  ───── │
│  14:30  API3    BUY   0.299  85   -7.4   0.03 Stopped │
│  13:15  BTC     SELL  65200  0.1  +12.5  0.05 Closed │
│  ...                                                │
├────────────────────────────────────────────────────┤
│  STATS (last 30d)                                   │
│  Win Rate: 58%  |  Avg RR: 2.1  |  Profit Factor: 1.7│
│  Sharpe: 1.4    |  Max DD: 12%                      │
└────────────────────────────────────────────────────┘
```

## 30.14 Стек технологий

| Слой | Технология |
|------|-----------|
| **Frontend Framework** | Vue 3 / React (или Vanilla JS) |
| **State** | Pinia / Redux / Custom |
| **Realtime** | WebSocket (ASGI) |
| **Charting** | TradingView LWC 5.2.0 + TV Embed |
| **Visualization** | Datashader + WebGL/Canvas |
| **Backend** | FastAPI + Polars + Numba |
| **DB** | TimescaleDB + Redis |
| **API** | REST + WebSocket |

## 30.15 Итоги

MidasFlow Matrix v4.0 — это полная экосистема из 30 глав + специализированные модули:

| Блок | Главы |
|------|-------|
| **Базовые концепции** | 1-5 (ADX, индикаторы, свечи) |
| **Теории рынка** | 6-11 (Wyckoff, SMC, CRT, Elliott, VP, OF) |
| **Зоны и уровни** | 12-17 (OTE, Derivatives, Sentiment, On-Chain, Execution, Cases) |
| **Soft Skills** | 18-21 (Psychology, Risk, Backtest, Macro) |
| **MidasFlow Suite** | 22-30 (Standards, Grid, Fractal, Position, CRP, Arch, Backend, Frontend, Terminal) |

## 30.16 Следующие шаги

- Углубить проработку backend реализации
- Создать интерактивный веб-терминал
- Добавить больше реальных кейсов
- Расширять JSON-протокол MidasFlow
