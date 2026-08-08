# MidasFlow Matrix v4.0 — JSON Protocol Reference

> **Версия протокола:** 1.1.0
> **Источник:** `data/tradeLLm/06_technical_specs/Технический отчет_ Спецификация Единой матрицы данных и JSON-протокола MidasFlow Matrix.docx`

## Обзор

JSON-протокол MidasFlow Matrix — это **формальная схема обмена данными** между модулями системы. Каждый снапшот матрицы содержит:

- Метаданные (session)
- Активные зоны (OB, FVG, BB)
- CRP-метрики
- Структурную информацию
- Пулы ликвидности
- Volume Profile

## Полная схема

```json
{
  "matrix_metadata": {
    "protocol_version": "1.1.0",
    "timestamp": "2026-05-15T14:30:00.001Z",
    "symbol": "ES_U26",
    "timeframe": "M15",
    "active_killzone": "LONDON_OPEN"
  },
  "active_zones": [
    {
      "type": "Order_Block",
      "range_type": "IRL",
      "direction": "Bullish",
      "proximal_line": 5420.25,
      "distal_line": 5415.50,
      "status": "unmitigated"
    }
  ],
  "crp_ribbons": {
    "phase": "Manipulation",
    "reference_range": [5400.00, 5410.50],
    "manipulation_extreme": 5412.75,
    "confirmation_status": "re-entry_confirmed"
  },
  "market_structure": {
    "bias": "Bullish",
    "last_break": "MSS",
    "displacement_magnitude": "High",
    "dealing_range": {"high": 5450.00, "low": 5400.00}
  },
  "liquidity_pools": {
    "ERL_targets": {"BSL": 5460.00, "SSL": 5390.00},
    "current_cycle": "ERL_to_IRL",
    "liquidity_sweep_confirmed": true
  },
  "volume_profile_metrics": {
    "POC": 5425.50,
    "poc_relative_position": "Lower_Third",
    "VAH": 5440.00,
    "VAL": 5410.00,
    "profile_shape": "D-Shape"
  }
}
```

## Справочник полей

### `matrix_metadata`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `protocol_version` | string | Версия протокола | "1.1.0" |
| `timestamp` | string (ISO8601) | Время снапшота | "2026-05-15T14:30:00.001Z" |
| `symbol` | string | Торговый символ | "ES_U26", "BTCUSDT" |
| `timeframe` | string | Таймфрейм | "M1", "M5", "M15", "H1", "H4", "D1" |
| `active_killzone` | string | Активная торговая сессия | "ASIA", "LONDON_OPEN", "NY_OPEN", "LONDON_CLOSE" |

### `active_zones[]`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `type` | string | Тип зоны | "Order_Block", "FVG", "Breaker_Block" |
| `range_type` | string | Внутр/Внешн | "IRL" (Internal), "ERL" (External) |
| `direction` | string | Направление | "Bullish", "Bearish" |
| `proximal_line` | float | Ближняя граница | цена |
| `distal_line` | float | Дальняя граница | цена |
| `status` | string | Состояние | "unmitigated", "mitigated", "broken" |

### `crp_ribbons`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `phase` | string | Фаза CRP | "Accumulation", "Manipulation", "Distribution", "Re-entry" |
| `reference_range` | array[2] | Базовый диапазон | [low, high] |
| `manipulation_extreme` | float | Экстремум манипуляции | цена |
| `confirmation_status` | string | Статус | "pending", "re-entry_confirmed", "rejected" |
| `metrics.POC` | float | Point of Control | цена |
| `metrics.poc_relative_position` | string | Позиция POC | "Lower_Third", "Middle_Third", "Upper_Third" |
| `metrics.VAH` | float | Value Area High | цена |
| `metrics.VAL` | float | Value Area Low | цена |
| `metrics.profile_shape` | string | Форма профиля | "D-Shape", "b-Shape", "P-Shape" |
| `metrics.sniper_entry` | float | Уровень 0.705 | цена |
| `metrics.ote_zone` | array[2] | OTE зона | [0.618, 0.786] |

### `market_structure`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `bias` | string | Направление | "Bullish", "Bearish", "Neutral" |
| `last_break` | string | Последний слом | "BOS", "CHoCH", "MSS", null |
| `displacement_magnitude` | string | Сила импульса | "Low", "Medium", "High" |
| `dealing_range.high` | float | Верх диапазона | цена |
| `dealing_range.low` | float | Низ диапазона | цена |
| `invalidation` | float | Уровень MSS | цена |

### `liquidity_pools`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `ERL_targets.BSL` | float | Buy-side Liquidity | цена |
| `ERL_targets.SSL` | float | Sell-side Liquidity | цена |
| `current_cycle` | string | Текущий цикл | "ERL_to_IRL", "IRL_to_ERL" |
| `liquidity_sweep_confirmed` | bool | Подтверждён ли sweep | true/false |

### `volume_profile_metrics`

| Поле | Тип | Описание | Возможные значения |
|------|-----|----------|---------------------|
| `POC` | float | Point of Control | цена |
| `poc_relative_position` | string | Позиция POC | "Lower_Third", "Middle_Third", "Upper_Third" |
| `VAH` | float | Value Area High | цена |
| `VAL` | float | Value Area Low | цена |
| `profile_shape` | string | Форма профиля | "D-Shape", "b-Shape", "P-Shape" |

### `fibo_grid_2_0` (расширение MidasFlow)

```json
"fibo_grid_2_0": {
  "sweet_spot": 0.275,
  "ote_start": 0.270,
  "ote_deep": 0.276,
  "invalidation": 0.32,
  "tp1_early_deviation": 0.34,
  "tp2_whale_alpha": 0.36,
  "scaling": [
    {"step": 1, "fraction": 0.125, "level": "0.0 (MSS)"},
    {"step": 2, "fraction": 0.25, "level": "0.618 (OTE Start)"},
    {"step": 3, "fraction": 0.625, "level": "1.0 (BOS)"}
  ]
}
```

## Расширенный пример: Order Block (v1.1.0)

```json
{
  "object_id": "OB_H1_a7f2_24052026_14:30",
  "type": "ORDER_BLOCK",
  "timeframe": "H1",
  "timestamp": 1716561000000,
  "candle_offset": 42,
  "coordinates": {
    "proximal_line": 1.1250,
    "distal_line": 1.1235,
    "mean_threshold": 1.12425
  },
  "validation": {
    "has_displacement": true,
    "associated_bos_id": "BOS_H1_b2e1_24052026_15:00",
    "is_mitigated": false
  }
}
```

## Пример: Risk Position (API3 #1)

```json
{
  "liquidation_price": -0.56892107235,
  "mark_price": 0.2249,
  "risk_to_liquidation": 0,
  "unrealized_pl": -5.458596920939,
  "risk_flags": ["PnL -218%", "CRITICAL_RECOVERY"]
}
```

## Naming Convention (ID объектов)

| Объект | Формат | Пример |
|--------|--------|--------|
| Order Block | `OB_{TF}_{id}_{date}_{time}` | `OB_H1_a7f2_24052026_14:30` |
| FVG | `FVG_{TF}_{id}_{date}` | `FVG_H4_b3e1_24052026` |
| BOS | `BOS_{TF}_{id}_{date}_{time}` | `BOS_H1_b2e1_24052026_15:00` |
| MSS | `MSS_{TF}_{id}_{date}_{time}` | `MSS_D1_c5f2_24052026` |
| Liquidity Pool | `LP_{type}_{level}_{date}` | `LP_BSL_82500_24052026` |
| Killzone | `KZ_{name}_{date}` | `KZ_LONDON_OPEN_24052026` |

## WebSocket Streaming

```json
{
  "type": "market_update",
  "symbol": "API3USDT",
  "timestamp": 1716561000000,
  "data": {
    "price": 0.2992,
    "cvd": 1234.56,
    "delta": 45.78,
    "imbalance": 0.65,
    "ob_count": 3,
    "fvg_count": 2,
    "mss_detected": true,
    "ote_position": 0.705,
    "killzone": "LONDON_OPEN"
  }
}
```

## Типы сообщений WebSocket

| `type` | Описание |
|--------|----------|
| `market_update` | Обновление цены и метрик |
| `crp_update` | Обновление CRP-метрик |
| `structure_update` | Изменение BOS/CHoCH/MSS |
| `liquidity_sweep` | Подтверждение sweep |
| `risk_flag` | Новый risk flag |
| `position_update` | Изменение PnL позиции |

## Валидация (Python)

```python
from pydantic import BaseModel, Field
from typing import Literal
from datetime import datetime

class MatrixMetadata(BaseModel):
    protocol_version: str = "1.1.0"
    timestamp: datetime
    symbol: str
    timeframe: Literal["M1", "M5", "M15", "H1", "H4", "D1"]
    active_killzone: Literal["ASIA", "LONDON_OPEN", "NY_OPEN", "LONDON_CLOSE"]

class ActiveZone(BaseModel):
    type: Literal["Order_Block", "FVG", "Breaker_Block"]
    range_type: Literal["IRL", "ERL"]
    direction: Literal["Bullish", "Bearish"]
    proximal_line: float
    distal_line: float
    status: Literal["unmitigated", "mitigated", "broken"]

class CRPRibbon(BaseModel):
    phase: Literal["Accumulation", "Manipulation", "Distribution", "Re-entry"]
    reference_range: list[float]
    manipulation_extreme: float
    confirmation_status: Literal["pending", "re-entry_confirmed", "rejected"]

class MarketStructure(BaseModel):
    bias: Literal["Bullish", "Bearish", "Neutral"]
    last_break: Literal["BOS", "CHoCH", "MSS", None] = None
    displacement_magnitude: Literal["Low", "Medium", "High"]
    dealing_range: dict  # {"high": float, "low": float}

class MidasFlowMatrix(BaseModel):
    matrix_metadata: MatrixMetadata
    active_zones: list[ActiveZone]
    crp_ribbons: CRPRibbon
    market_structure: MarketStructure
    liquidity_pools: dict
    volume_profile_metrics: dict
```

## Заключение

JSON-протокол MidasFlow Matrix — это **production-grade schema** для обмена данными между модулями системы. Совместим с Pydantic, TypeScript, и любыми другими валидаторами.

См. также:
- **Глава 22:** MidasFlow v4.0 Standards
- **Глава 23:** Grid 2.0 (33 уровня)
- **Tools → MidasFlow Quick Builder:** интерактивный генератор JSON
