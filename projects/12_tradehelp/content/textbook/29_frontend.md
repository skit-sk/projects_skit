# Глава 29: Frontend — WebGL + Datashader

> **Источник:** `data/tradeLLm/06_technical_specs/Технический отчет_ Реализация визуального инструментария микроструктурного анализа на Python.docx`

## 29.1 Проблема производительности

**Классический TA:** 1 точка на свечу (минимальный объём данных)
**Микроструктура:** Тысячи тиков в секунду (экстремальный объём)

**Стандартный DOM/SVG** не справляется — Main Thread перегружается, FPS падает, интерфейс "замерзает".

## 29.2 Решение: WebGL + Canvas

Переход от DOM/SVG к **WebGL/Canvas** рендерингу:
- Делегирование отрисовки тысяч графических примитивов GPU
- Освобождение CPU для логики
- Стабильные 60 FPS

## 29.3 Архитектура визуализации Heatmap

### Pipeline обработки

```
DOM L2 Data (тики) 
    ↓ [Datashader Aggregation]
2D Histogram (растр)
    ↓ [Plotly Heatmapgl]
GPU Background Layer
    +
SVG Overlay (структура, OB, FVG)
```

### Преимущества:
1. **Тяжёлый фон** (Heatmap) — отдельный GPU-слой
2. **Лёгкие линии** (структура) — интерактивный SVG
3. **Изоляция** — не блокируют друг друга

## 29.4 Shadow DOM Visualization

```python
import datashader as ds
import plotly.graph_objects as go
import pandas as pd
import numpy as np

def render_shadow_dom(ticks_df, price_levels=200):
    """
    Рендер Shadow DOM через Datashader + Plotly.
    """
    # 1. Datashader агрегация в растр
    canvas = ds.Canvas(plot_width=800, plot_height=price_levels)
    agg = canvas.points(
        ticks_df, 'time', 'price',
        ds.sum('volume')
    )

    # 2. Нормализация интенсивности I
    I = agg.values
    I = (I - I.min()) / (I.max() - I.min())  # [0, 1]

    # 3. Цветовое кодирование
    colorscale = [
        [0.0, 'rgba(13,17,23,0)'],         # Прозрачный
        [0.3, 'rgba(248,81,73,0.3)'],      # Низкая плотность (красный)
        [0.7, 'rgba(57,197,207,0.6)'],      # Средняя (циан)
        [1.0, 'rgba(63,185,80,0.9)'],       # Высокая (зелёный = HVN)
    ]

    # 4. Plotly Heatmapgl
    fig = go.Figure(data=go.Heatmapgl(
        z=I,
        x=agg.x_axis,
        y=agg.y_axis,
        colorscale=colorscale,
        showscale=False,
        hoverinfo='skip',
    ))

    return fig
```

## 29.5 Логика цветового кодирования

```python
def color_density(intensity):
    """
    Нормализация интенсивности I для уровня L.
    I = (vol_L - vol_min) / (vol_max - vol_min)
    """
    if intensity > 0.8:
        return 'rgba(63, 185, 80, 0.9)'   # HVN (зелёный)
    elif intensity > 0.5:
        return 'rgba(57, 197, 207, 0.7)'  # Mid (циан)
    elif intensity > 0.3:
        return 'rgba(210, 153, 34, 0.5)'  # LVN (жёлтый)
    else:
        return 'rgba(248, 81, 73, 0.2)'   # Empty (красный)
```

## 29.6 Plotly Heatmapgl

```python
import plotly.graph_objects as go

# Heatmapgl — GPU-ускоренный heatmap
fig = go.Figure(data=go.Heatmapgl(
    z=I,                                  # 2D массив
    x=timestamps,
    y=prices,
    colorscale='Viridis',
    showscale=True,
    colorbar=dict(
        title=dict(text='Density', side='right'),
        tickfont=dict(color='#c9d1d9')
    ),
    hovertemplate=(
        '<b>Time:</b> %{x}<br>'
        '<b>Price:</b> %{y}<br>'
        '<b>Density:</b> %{z}<br>'
        '<extra></extra>'
    )
))
```

## 29.7 SVG Overlay (структура поверх Heatmap)

```python
# После создания Heatmapgl добавляем SVG-элементы
fig.add_shape(
    type='rect',
    x0=t1, x1=t2,
    y0=ob_low, y1=ob_high,
    fillcolor='rgba(0, 200, 83, 0.15)',
    line=dict(color='rgba(0, 200, 83, 0.5)', width=1),
    name='Order Block'
)

fig.add_shape(
    type='rect',
    x0=t3, x1=t4,
    y0=fvg_low, y1=fvg_high,
    fillcolor='rgba(0, 229, 255, 0.12)',
    line=dict(color='rgba(0, 229, 255, 0.4)', width=1),
    name='FVG'
)

# Линии уровней
fig.add_hline(y=poc_price, line_color='#d29922', line_width=2)
fig.add_hline(y=vah_price, line_color='#39c5cf', line_width=1, line_dash='dash')
fig.add_hline(y=val_price, line_color='#39c5cf', line_width=1, line_dash='dash')
```

## 29.8 Lightweight Charts Inline

**TradingView Lightweight Charts v5.2.0** в учебнике:

```javascript
async function initLWC(containerId, symbol, interval, indicators) {
    const script = document.createElement('script');
    script.src = 'https://unpkg.com/lightweight-charts@5.2.0/dist/lightweight-charts.standalone.production.js';
    await new Promise((r, j) => { s.onload = r; s.onerror = j; });

    const { createChart, CandlestickSeries, LineSeries } = LightweightCharts;
    const chart = createChart(container, {
        layout: { background: { type: 'solid', color: '#0d1117' } },
        grid: { vertLines: { color: '#21262d' }, horzLines: { color: '#21262d' } },
    });

    // Загрузка через прокси
    const r = await fetch(`/api/klines?symbol=${symbol}&interval=${interval}`);
    const klines = await r.json();

    // Добавление индикаторов
    chart.addSeries(CandlestickSeries, { upColor: '#3fb950', downColor: '#f85149' })
         .setData(klines.map(k => ({
             time: k[0]/1000, open: +k[1], high: +k[2], low: +k[3], close: +k[4]
         })));
}
```

## 29.9 TradingView Embed Widgets

```html
<!-- Advanced Chart -->
<script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
<script>
new TradingView.widget({
    "autosize": true,
    "symbol": "BINANCE:API3USDT",
    "interval": "D",
    "theme": "dark",
    "studies": ["MASimple@tv-basicstudies", "Volume@tv-basicstudies"]
});
</script>
```

## 29.10 Frontend Architecture (TradeHelp v3)

```
Browser
├── Plotly.js (CDN)
│   └── Heatmap (microstructure)
├── Lightweight Charts 5.2.0
│   └── Inline графики в учебнике
├── TradingView Embed
│   ├── Advanced Chart
│   ├── Ticker Tape (на каждой странице)
│   ├── Heatmap
│   └── Calendar
└── Vanilla JS
    ├── lwc-init.js
    ├── live.js (polling)
    ├── risk_calc.js
    └── tv-widgets.js
```

## 29.11 3-Tier Data Flow (Visual)

```
[Tier 1: Raw Ticks]
   ↓ Polars Normalization
[Tier 2: Microstructure: Delta, CVD, VP]
   ↓ Plotly Heatmapgl
   ↓ Datashader (background)
   ↓ SVG Overlay (structure)
[Tier 3: Structural Patterns: BOS, OB, FVG]
```

## 29.12 Cluster Footprint (WebGL)

```javascript
import * as THREE from 'three';

// 3D Footprint: x=time, y=price, z=volume
const geometry = new THREE.BoxGeometry(1, 1, 1);
const material = new THREE.MeshBasicMaterial({color: 0x3fb950});

const cubes = [];
for (const cluster of footprint_data) {
    const cube = new THREE.Mesh(geometry, material);
    cube.position.set(cluster.time, cluster.price, cluster.volume / 2);
    cube.scale.set(0.8, 0.5, cluster.volume);
    cubes.push(cube);
}

const scene = new THREE.Scene();
cubes.forEach(c => scene.add(c));
```

## 29.13 Сравнение технологий

| Технология | Use Case | Производительность |
|------------|----------|---------------------|
| **SVG** | Простые графики (<1000 элементов) | OK |
| **Canvas 2D** | Heatmap (100K точек) | Хорошо |
| **WebGL** | Footprint (1M+ точек) | Отлично (60 FPS) |
| **Datashader** | 2D-агрегация растров | Очень быстро |
| **Plotly Heatmapgl** | Heatmap с GPU | Быстро |
| **LWC 5.2.0** | Trading-стиль графики | 60 FPS |
| **TradingView TV.js** | Полноценный TV | Зависит от подписки |

## 29.14 CSS Variables (Dark Theme)

```css
:root {
  --bg-primary: #0d1117;
  --bg-secondary: #161b22;
  --bg-elevated: #21262d;
  --border: #30363d;
  --text-primary: #c9d1d9;
  --text-secondary: #8b949e;
  --bull: #3fb950;
  --bear: #f85149;
  --accent1: #ff9100;   /* POC */
  --accent2: #00e5ff;   /* FVG */
  --accent3: #d29922;   /* Sniper */
  --accent4: #bc8cff;   /* MidasFlow */
}
```

## 29.15 Что дальше

- **Глава 30:** Веб-терминал скальпинга (UX/архитектура, Vataga/TigerTrade benchmark)
