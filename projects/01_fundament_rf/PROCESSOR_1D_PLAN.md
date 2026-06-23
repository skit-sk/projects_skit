# PROCESSOR_1D_PLAN
## Дата: 2026-04-28
## Статус: MIGRATED TO TimeframePipeline (2026-06-23)

---

## 1. Структура Blueprint: processor_1d

| Endpoint | Метод | Назначение |
|----------|-------|------------|
| `/processor_1d/create/<obj_id>` | POST | Создать 1D + RAW (initial) |
| `/processor_1d/sync/<obj_id>` | POST | Авто-синхронизация |
| `/processor_1d/force/<obj_id>` | POST | Полный пересчёт + отчёт |
| `/processor_1d/status/<obj_id>` | GET | Статус |
| `/processor_1d/data/<obj_id>` | GET | 1D данные |
| `/processor_1d/raw/<obj_id>` | GET | RAW данные |
| `/processor_1d/delete/<obj_id>` | DELETE | Удалить 1D + RAW |
| `/processor_1d/batch` | POST | Пакетная обработка |

---

## 2. Страница /metrics

| Endpoint | Метод | Назначение |
|----------|-------|------------|
| `/metrics` | GET | HTML страница |
| `/metrics/data` | GET | JSON records |

---

## 3. JSON структуры

### RAW_{uuid}.json
```json
{
  "id": "RAW_{parent_uuid}",
  "parent_id": "{uuid}",
  "symbol": "CAKE",
  "granularity": "1day",
  "source": "bitget",
  "fetched_at": "2026-04-28T17:35:00",
  "created_at": "2026-04-28T17:35:00",
  "updated_at": "2026-04-28T17:35:00",
  "candles": [
    {
      "date": "2026-02-19",
      "timestamp_ms": 1746144000000,
      "open": 1.230,
      "high": 1.245,
      "low": 1.228,
      "close": 1.240,
      "volume": 12345.67
    }
  ],
  "total_candles": 68
}
```

### 1D_{uuid}.json
```json
{
  "id": "1D_{parent_uuid}",
  "parent_id": "{uuid}",
  "symbol": "CAKE",
  "entry_price": 1.23355,
  "entry_date": "2026-02-19",
  "leverage": 10,
  "volume": 1.89,
  "status": "completed",
  "fetched_at": "2026-04-28T17:35:00",
  "created_at": "2026-04-28T17:35:00",
  "updated_at": "2026-04-28T17:35:00",
  "days": [
    {
      "date": "2026-02-19",
      "day_index": 0,
      "ohlc": {
        "open": 1.230,
        "high": 1.245,
        "low": 1.228,
        "close": 1.240,
        "body": 0.010,
        "body_pct": 0.81,
        "upper_wick": 0.005,
        "lower_wick": 0.012
      },
      "deviation": {
        "from_entry_usdt": 0.007,
        "from_entry_pct": 0.57,
        "from_open_usdt": 0.010,
        "from_open_pct": 0.81
      },
      "roe_pct": 5.7,
      "pnl_usdt": 0.108,
      "volatility": 0.017,
      "profitable": true
    }
  ],
  "chart_data": [
    {"date": "2026-02-19", "deviation_pct": 0.57, "profitable": true}
  ],
  "summary": {
    "total_days": 68,
    "profitable_days": 67,
    "loss_days": 1,
    "neutral_days": 0,
    "current_roe_pct": 201.41,
    "current_pnl_usdt": 3.81,
    "avg_roe_pct": 45.2,
    "avg_volatility": 0.023,
    "max_profit_day": {"date": "2026-04-15", "roe_pct": 35.06, "pnl_usdt": 0.663},
    "max_loss_day": {"date": "2026-03-10", "roe_pct": -5.31, "pnl_usdt": -0.100},
    "max_drawdown_pct": -5.31,
    "max_drawdown_usdt": -0.100,
    "streak_profit": 15,
    "streak_loss": 1
  }
}
```

### metrics.json
```json
{
  "records": [
    {
      "id": "timing_uuid",
      "obj_id": "uuid",
      "operation": "create|sync|force|batch",
      "timestamp": "2026-04-28T17:35:00",
      "duration_ms": {
        "api_request_start": 1745848500000,
        "api_request_end": 1745848500480,
        "api_request_ms": 480,
        "processing_start": 1745848500481,
        "processing_end": 1745848500520,
        "processing_ms": 39,
        "writing_start": 1745848500521,
        "writing_end": 1745848500530,
        "writing_ms": 9,
        "total_ms": 530
      },
      "result": {
        "status": "completed|failed|partial",
        "days_processed": 68,
        "added": 0,
        "changed": 0,
        "skipped": 0
      }
    }
  ],
  "aggregated": {
    "total_operations": 150,
    "avg_api_ms": 520,
    "avg_processing_ms": 45,
    "avg_writing_ms": 10,
    "avg_total_ms": 575,
    "failed_count": 3,
    "last_operation": "2026-04-28T17:35:00"
  }
}
```

---

## 4. Формулы расчёта

| Поле | Формула |
|------|---------|
| `body` | abs(close - open) |
| `body_pct` | abs(close - open) / open * 100 |
| `upper_wick` | high - max(open, close) |
| `lower_wick` | min(open, close) - low |
| `deviation.from_entry_pct` | (close - entry_price) / entry_price * 100 |
| `deviation.from_entry_usdt` | close - entry_price |
| `volatility` | high - low |
| `roe_pct` | deviation.from_entry_pct * leverage |
| `pnl_usdt` | roe_pct * volume / 100 |

---

## 5. Режимы пересчёта

### Sync (auto)
1. chart_updated основного JSON vs updated_at 1D файла
2. Если равны → SKIP
3. Если chart_updated > → пересчитать рассинхронизированные дни
4. Добавить новые (если есть)
5. Отчёт: {updated_days, skipped}

### Force (полный)
1. Запрос Bitget: entry_date → now (весь период)
2. Пересчёт ВСЕХ дней
3. Отчёт: {recalculated, added, changed, skipped, previous_max_roe, current_max_roe}

---

## 6. Параметры

| Параметр | Значение |
|----------|----------|
| Threading | threading.Thread |
| Timeout | 5 сек |
| Retry | 3 попытки |
| Timestamp | ISO8601 |
| История | хранить ВСЮ |

---

## 7. Файлы для реализации

| Файл | Действие |
|------|----------|
| routes/processor_1d.py | СОЗДАТЬ |
| storage.py | ДОБАВИТЬ методы 1D/RAW/metrics |
| app.py | ДОБАВИТЬ register |
| templates/metrics.html | СОЗДАТЬ |
| templates/base.html | ДОБАВИТЬ ссылку /metrics |
| static/css/style.css | ДОБАВИТЬ стили |

---

## 8. НОВЫЙ ФОРМАТ (TimeframePipeline, 2026-06-23)

Миграция: теперь 1D файл `{uuid}_1D.json` хранится в **новом формате** с `candles[]` (обогащённые свечи).

### 1D_{uuid}.json (новый формат)
```json
{
  "id": "1D_{parent_uuid}",
  "parent_id": "{uuid}",
  "symbol": "CAKE",
  "entry_price": 1.23355,
  "entry_date": "2026-02-19",
  "leverage": 10,
  "volume": 1.89,
  "granularity": "1D",
  "candles": [
    {
      "timestamp_ms": 1746144000000,
      "datetime": "2026-02-19T00:00:00",
      "date": "2026-02-19",
      "open": 1.230,
      "high": 1.245,
      "low": 1.228,
      "close": 1.240,
      "volume": 12345.67,
      "quote_volume": 15234.56,
      "sessions": {"active": ["london"]},
      "tf_boundary": {"is_first": true, "is_last": false},
      "liq_proximity": {"entry_price": 1.23, "liq_price_10x": 1.107},
      "position_metrics": {
        "body": 0.010, "body_pct": 0.81,
        "upper_wick": 0.005, "lower_wick": 0.012,
        "deviation": {
          "from_entry_usdt": 0.007, "from_entry_pct": 0.57,
          "from_open_usdt": 0.010, "from_open_pct": 0.81
        },
        "roe_pct": 5.7, "pnl_usdt": 0.108,
        "volatility": 0.017, "profitable": true,
        "pre_entry": false
      },
      "strength": {"value": 0.5, "is_extremum": false},
      "candle_metrics": {"body": 0.010, "body_pct": 0.81, ...},
      "fibonacci": {"levels": {"0.0": ..., "1.618": ...}}
    }
  ],
  "count": 28
}
```

### Архитектура enrichers
- `PositionMetricsEnricher` — `body/body_pct/upper_wick/lower_wick/deviation/roe_pct/pnl_usdt/volatility/profitable/pre_entry`
- `SessionsEnricher` — `sessions.active[]` (London, NY, etc.)
- `TFBoundaryEnricher` — `tf_boundary.is_first/is_last/is_new_tf`
- `LiqProximityEnricher` — `liq_proximity.liq_price_10x/5x/2x/at_risk`
- `ExtremesFilterEnricher` — `strength.value/is_extremum`
- `PeriodAggregatesEnricher` — `candle_metrics.body_pct/upper_wick/lower_wick`
- `FibonacciEnricher` — `fibonacci.levels{0.0, 0.236, ..., 1.618}`

### RAW_{uuid}.json (без изменений)
Хранит 8-полевую форму для backward-compat с `api/ma_data.py:MADataLoader`.

### Legacy fallback
`storage._candles_to_legacy(symbol, obj_id, new_data)` — конвертирует новый формат в legacy (days[]/chart_data[]/summary) для templates и `/processor_1d/data/<id>` endpoint.