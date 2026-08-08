# Глава 26: Микроструктурный детектив — CRP + Shadow DOM

> **Источник:** `data/tradeLLm/05_analytical_reports/Аналитический отчет_ Микроструктурный детектив — CRP и Shadow DOM.docx`

## 26.1 Концепция

**Микроструктурный детектив** — это метод идентификации зон институционального равновесия через:
- **CRP (Cluster Risk Projection)** — статистический профиль объёма
- **Shadow DOM** — визуализация скрытой плотности лимитных ордеров

## 26.2 CRP (Cluster Risk Projection)

**Определение:** Метод идентификации зон институционального равновесия через теорию аукционного рынка.

**Требование:** Статистическая значимость — профиль объёма должен быть заякорен на **Wyckoff-консолидации**, содержащей от **15 до 25 свечей**.

### Ключевые метрики CRP

| Метрика | Описание | Сигнал |
|---------|----------|--------|
| **POC** | Уровень максимальной транзакционной активности | В нижней трети = накопление (бычий) |
| **VAH/VAL** | Value Area High/Low (68.2% объёма) | 70-80% подтверждённых пробоев делают Pullback к VAH/VAL |
| **D-Shape** | Асимметричный профиль | Бычье накопление |
| **b-Shape** | Симметричный | Нейтральный |
| **P-Shape** | p-shape | Медвежья дистрибуция |

## 26.3 Логика CRP

```
1. Выбрать Wyckoff-консолидацию (15-25 свечей)
2. Построить Volume Profile для этого диапазона
3. Определить POC, VAH, VAL
4. Оценить форму профиля (D / b / P)
5. Сгенерировать сигнал:
   - POC в нижней трети + D-shape = Strong Bullish
   - POC в верхней трети + P-shape = Strong Bearish
```

## 26.4 Shadow DOM

**Shadow DOM** — концепция визуализации плотности лимитных ордеров, невидимых на стандартном DOM.

### Архитектура Shadow DOM

```
┌─────────────────────────────────┐
│  Price Ladder (y-axis)          │
│  ─────────────────────────────  │
│  │████████████│ ← L2 (visible) │  Tier 1: Видимые ордера
│  │█│       █│                   │  Tier 2: Shadow (inferred)
│  │█│       █│ ← Iceberg       │  Tier 3: Скрытые (расчёт)
│  │█│       █│                   │
│  ─────────────────────────────  │
│  Time (x-axis)                   │
└─────────────────────────────────┘
```

### Цветовое кодирование Shadow DOM

```python
def color_density(intensity):
    """Интенсивность I для уровня L."""
    if intensity > 0.8:
        return 'rgba(63, 185, 80, 0.8)'  # Green - HVN
    elif intensity > 0.5:
        return 'rgba(57, 197, 207, 0.6)'  # Cyan - Mid
    elif intensity > 0.3:
        return 'rgba(210, 153, 34, 0.4)'  # Yellow - LVN
    else:
        return 'rgba(248, 81, 73, 0.2)'  # Red - Empty
```

## 26.5 Концептуальная модель данных

**Модуль Heatmap** предназначен для визуализации "институциональных отпечатков" — зон концентрации крупных лимитных заявок.

### Типы рыночной активности

| Тип | Описание | Визуализация |
|-----|----------|--------------|
| **Пассивное размещение** | Лимитные ордера (стены) | Bright blocks |
| **Агрессивное исполнение** | Рыночные ордера (эрозия) | Faded areas |
| **Iceberg** | Скрытая заявка | Static visible + volume spike |

## 26.6 Алгоритм CRP на Python

```python
def calc_crp(candles, consolidation_period=20):
    """
    Cluster Risk Projection.
    :param candles: DataFrame с колонками OHLCV
    :param consolidation_period: 15-25 (Wyckoff range)
    :return: CRP-метрики
    """
    if len(candles) < consolidation_period:
        return None

    # Выбрать последний консолидационный диапазон
    range_data = candles[-consolidation_period:]
    high = range_data['high'].max()
    low = range_data['low'].min()
    price_min, price_max = low, high
    step = (price_max - price_min) / 30

    # Построить профиль
    bins = {}
    for _, candle in range_data.iterrows():
        for price in [candle['low'], candle['high']]:
            bin_idx = int((price - price_min) / step)
            bins[bin_idx] = bins.get(bin_idx, 0) + candle['volume']

    # POC
    poc_bin = max(bins, key=bins.get)
    poc = price_min + (poc_bin + 0.5) * step

    # Value Area (68.2%)
    total_vol = sum(bins.values())
    sorted_bins = sorted(bins.items(), key=lambda x: -x[1])
    cum_vol = 0
    va_bins = []
    for bin_idx, vol in sorted_bins:
        cum_vol += vol
        va_bins.append(bin_idx)
        if cum_vol >= total_vol * 0.682:
            break

    vah = price_min + (max(va_bins) + 1) * step
    val = price_min + min(va_bins) * step

    # Относительная позиция POC
    poc_pos = (poc - price_min) / (price_max - price_min)
    if poc_pos < 0.33:
        position = 'Lower_Third'  # Бычье накопление
        signal = 'Bullish'
    elif poc_pos > 0.67:
        position = 'Upper_Third'  # Медвежья дистрибуция
        signal = 'Bearish'
    else:
        position = 'Middle_Third'
        signal = 'Neutral'

    # Форма профиля
    upper_vol = sum(v for b, v in bins.items() if b > poc_bin)
    lower_vol = sum(v for b, v in bins.items() if b < poc_bin)
    if lower_vol > upper_vol * 1.5:
        shape = 'D-Shape'
    elif upper_vol > lower_vol * 1.5:
        shape = 'P-Shape'
    else:
        shape = 'b-Shape'

    return {
        'poc': poc,
        'poc_position': position,
        'vah': vah,
        'val': val,
        'shape': shape,
        'signal': signal,
        'reference_range': [price_min, price_max]
    }
```

## 26.7 Параметры CRP

| Параметр | Значение | Обоснование |
|----------|----------|-------------|
| `consolidation_period` | 15-25 | Wyckoff range |
| `value_area_pct` | 68.2% | 1σ нормальное распределение |
| `poc_position_lower` | < 33% | Бычье накопление |
| `poc_position_upper` | > 67% | Медвежья дистрибуция |
| `D-shape_threshold` | lower > upper × 1.5 | Асимметрия |
| `hvn_threshold` | vol > avg × 1.5 | High Volume Node |

## 26.8 Интеграция с MidasFlow JSON-протоколом

```json
{
  "crp_ribbons": {
    "phase": "Manipulation",
    "reference_range": [5400.00, 5410.50],
    "manipulation_extreme": 5412.75,
    "confirmation_status": "re-entry_confirmed",
    "metrics": {
      "poc": 5405.25,
      "poc_relative_position": "Lower_Third",
      "vah": 5408.50,
      "val": 5402.00,
      "shape": "D-Shape",
      "signal": "Bullish"
    }
  }
}
```

## 26.9 Visual Implementation (Datashader + Plotly)

Для рендеринга миллионов тиков используется **Datashader** + **Plotly**:

```python
import datashader as ds
import plotly.graph_objects as go
import pandas as pd

def render_shadow_dom(ticks, price_levels=200):
    """
    Рендер Shadow DOM через Datashader → Plotly Heatmapgl.
    """
    # 1. Datashader агрегация в 2D-растр
    canvas = ds.Canvas(plot_width=400, plot_height=price_levels)
    agg = canvas.points(ticks, 'time', 'price', ds.sum('volume'))

    # 2. Конвертация в numpy массив
    z = agg.values  # 2D массив (time × price)

    # 3. Plotly Heatmapgl (GPU-ускоренный)
    fig = go.Figure(data=go.Heatmapgl(
        z=z, x=agg.x_axis, y=agg.y_axis,
        colorscale=[[0, 'rgba(0,0,0,0)'], [0.3, 'rgba(248,81,73,0.3)'],
                    [0.7, 'rgba(57,197,207,0.6)'], [1, 'rgba(63,185,80,0.8)']],
        showscale=True
    ))

    # 4. Overlay: SVG-элементы (структура, линии)
    # (изолированы от тяжелого фона)
    return fig
```

## 26.10 Pipeline обработки

```
Order Book Data (L2) → Datashader (растр) → Plotly Heatmapgl (фон)
                                    ↓
                                    ↓
                        Static SVG overlay (структура, OB, FVG)
```

**Shadow DOM logic** — изоляция тяжёлого фона от интерактивных SVG-элементов, предотвращающая падение FPS.

## 26.11 Сигналы CRP для входа

```python
def crp_entry_signal(crp, current_price):
    """Генерация сигнала входа на основе CRP."""
    if crp is None:
        return None

    # POC в нижней трети + D-Shape + цена в Discount zone
    if (crp['poc_position'] == 'Lower_Third'
        and crp['shape'] == 'D-Shape'
        and current_price < crp['vah']):
        return {
            'signal': 'LONG',
            'entry_zone': [crp['val'], crp['poc']],
            'stop': crp['val'] * 0.99,
            'target_1': crp['vah'],
            'target_2': crp['vah'] * 1.236,
            'rationale': 'D-Shape accumulation, price in POC/VAL discount zone'
        }
    return None
```

## 26.12 Кейс: ES_U26 (фьючерс S&P 500)

**Данные из MidasFlow JSON:**
```
Reference Range: [5400.00, 5410.50]
POC: 5425.50  ← вне диапазона (выше)
POC Position: Lower_Third
VAH: 5440.00
VAL: 5410.00
Shape: D-Shape
```

**Интерпретация:** POC в нижней трети + D-Shape = **бычье накопление**. Цель — VAH 5440.00.

## 26.13 Что дальше

- **Глава 27:** Архитектура данных (3 Tier + Polars)
- **Глава 28:** Backend (FastAPI + Numba)
