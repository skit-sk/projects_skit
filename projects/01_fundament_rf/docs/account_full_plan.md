# Account — Полный пакет (Вариант 1)

## Обзор

Надстройка над базовым `account/` модулем. Добавляет:

- **AccountStorage** — сохранение снепшотов по времени
- **PortfolioAnalyzer** — распределение, риск-метрики, ликвидации
- **Расширенный дашборд** — графики equity, PnL по времени, allocation

---

## 1. AccountStorage

Хранит снепшоты полного состояния аккаунта в `data/account/snapshots/`.

### Директория

```
data/account/
├── current.json              # последний fetched-снапшот (кэш)
├── snapshots/
│   ├── 2024-01-15T10:00:00.json
│   ├── 2024-01-16T10:00:00.json
│   └── ...
└── keys.json                 # зашифрованные/сохранённые ключи (опционально)
```

### AccountStorage — методы

| Метод | Описание |
|--------|----------|
| `save_snapshot(overview: AccountOverview)` | Сохранить полный снепшот с timestamp |
| `list_snapshots(limit=30)` | Список сохранённых снепшотов (дата, total_equity, pos_count) |
| `load_snapshot(snapshot_id)` | Загрузить конкретный снепшот |
| `delete_snapshot(snapshot_id)` | Удалить снепшот |
| `get_equity_curve()` | Массив {date, total_equity, spot, futures} для Plotly |
| `get_latest()` | Загрузить `current.json` |
| `save_current(overview)` | Сохранить `current.json` |

### Пример данных снепшота

```json
{
  "id": "2024-01-15T10:00:00",
  "timestamp": 1705312800000,
  "overview": {
    "total_equity_usdt": 1234.56,
    "spot_total_usdt": 500.0,
    "futures_equity_usdt": 734.56,
    "futures_unrealized_pl": 23.45,
    "open_positions_count": 3
  },
  "spot_assets": [
    {"coin": "USDT", "total": 500.0, "available": 450.0, "frozen": 50.0}
  ],
  "positions": [
    {
      "symbol": "BTCUSDT",
      "margin_size": 0.1,
      "open_price_avg": 42000.0,
      "unrealized_pl": 50.0,
      "leverage": 10,
      "liquidation_price": 38000.0
    }
  ]
}
```

---

## 2. PortfolioAnalyzer

### Класс `account/analyzer.py`

```python
class PortfolioAnalyzer:
    def __init__(self, storage: AccountStorage):
        ...

    def get_allocation(self, positions) -> dict:
        """Распределение портфеля по символам (% от equity)"""
        return {'BTC': 45.0, 'ETH': 30.0, 'SOL': 25.0}

    def get_risk_metrics(self, positions) -> dict:
        """Риск-метрики: концентрация, плечо, ликвидации"""
        return {
            'avg_leverage': 8.5,
            'max_leverage': 20,
            'total_margin_used': 500.0,
            'margin_used_pct': 35.0,
            'closest_liquidation': {'symbol': 'SOLUSDT', 'distance_pct': 12.3},
            'concentration': {'top_symbol': 'BTC', 'top_pct': 45.0},
        }

    def get_pnl_timeline(self, snapshots) -> list:
        """PNL по времени на основе снепшотов"""
        return [{'date': '2024-01-15', 'pnl': 50.0}, ...]

    def get_equity_curve_data(self, snapshots) -> dict:
        """Equity curve + drawdown для Plotly"""
        return {'dates': [...], 'equity': [...], 'drawdown': [...]}
```

### Аналитические метрики

| Метрика | Формула / Описание |
|---------|-------------------|
| **Concentration** | % самого крупного символа от общего margin |
| **Avg Leverage** | Среднее плечо по всем позициям |
| **Margin Usage** | Используемая маржа / Futures equity × 100 |
| **Liq. Distance** | (Current − Liq.) / Current × 100 для ближайшей |
| **Daily PnL** | Разница equity между соседними снепшотами |
| **Sharpe (TODO)** | (Средний дневной PnL) / Std(PnL) |
| **Max Drawdown** | Максимальное падение equity от пика |

---

## 3. Новые/расширенные эндпоинты

| Эндпоинт | Метод | Описание |
|----------|-------|----------|
| `/account-api/api/snapshot` | POST | Сохранить текущий снепшот |
| `/account-api/api/snapshots` | GET | Список снепшотов |
| `/account-api/api/snapshots/<id>` | GET | Детали снепшота |
| `/account-api/api/snapshots/<id>` | DELETE | Удалить снепшот |
| `/account-api/api/allocation` | GET | Распределение портфеля |
| `/account-api/api/risk` | GET | Риск-метрики |
| `/account-api/api/equity-curve` | GET | Данные equity curve для Plotly |
| `/account-api/api/portfolio` | GET | Полный портфельный отчёт |

---

## 4. Дополнительные партиалы (HTMX)

| Партиал | Описание |
|---------|----------|
| `partials/allocation.html` | Круговая диаграмма (SVG/Plotly) распределения |
| `partials/risk.html` | Карточки риск-метрик + таблица ближайших ликвидаций |
| `partials/history.html` | График equity curve + drawdown (Plotly) |
| `partials/snapshots.html` | Таблица снепшотов с diff |

---

## 5. Ключи API — UI для ввода

Добавить форму на страницу аккаунта для ввода/смены ключей без `.env`:

```
┌─ API Keys ──────────────────────┐
│ API Key:    [________________]  │
│ Secret:     [________________]  │
│ Passphrase: [________________]  │
│ [Save] [Clear]                  │
└─────────────────────────────────┘
```

Ключи хранятся в `sessionStorage` или в `data/account/keys.json` (с предупреждением о безопасности).

---

## 6. План реализации

1. Создать `account/storage.py` — `AccountStorage` (сохранение/загрузка снепшотов)
2. Создать `account/analyzer.py` — `PortfolioAnalyzer` (распределение, риск, equity curve)
3. Дополнить `routes/account_api.py` — новые эндпоинты
4. Создать партиалы для allocation, risk, history, snapshots
5. Добавить Plotly на страницу аккаунта
6. Добавить UI для ввода ключей
