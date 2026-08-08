# AI-Манифест: Генерация иллюстраций и видео для TradeHelp

> **Стиль:** Dark + Institutional (Bloomberg-эстетика, премиальный dark mode)
> **Целевая аудитория:** трейдеры, обучающиеся институциональным методам
> **Дата:** 2026-07-02
> **Провайдеры:** `apiyi` (image_gen), `routerai` (vision/image), будущий Veo 3.1 (video)

---

## 🎨 Общая стилистика для всех промптов

```
STYLE BASE:
  aesthetic: "Dark institutional financial UI, Bloomberg Terminal inspired"
  palette: "deep navy (#0d1117), graphite (#161b22), neon cyan (#39c5cf), 
            bullish green (#3fb950), bearish red (#f85149), signal yellow (#d29922), 
            accent blue (#58a6ff), institutional purple (#bc8cff)"
  background: "Smooth dark gradient from #0d1117 to #1a1a2e, subtle depth, 
               no harsh shadows, premium dark mode"
  lighting: "Cinematic side-lighting with cool blue tones, selective neon glow on 
             key data points, dark glass morphism panels"
  typography: "Modern monospace for data (JetBrains Mono), clean sans-serif for 
               labels (Inter), institutional feel"
  composition: "Wide 16:9, rule of thirds, technical chart aesthetic, 
                minimal but data-rich"
  mood: "Sophisticated, premium, technical, professional trader workstation, 
         akin to a hedge fund trading desk at night"
  negative_prompt: "Bright colors, cartoon, childish, low quality, watermark, 
                    text, blurry, realistic human faces"
```

---

## 🖼 Image Generation — концептуальные иллюстрации (15+ идей)

### 1. **Hero Image — обложка учебника**
**Назначение:** главная страница TradeHelp
```
PROMPT:
Hyperrealistic 3D render of a modern institutional trading workstation 
at night, multiple curved ultra-wide monitors displaying real-time 
financial charts (candlestick patterns, order flow, depth of market), 
dark sleek environment with ambient blue backlighting, holographic 
data overlays glowing in cyan and green, premium Bloomberg Terminal 
aesthetic, dark navy background (#0d1117), cinematic depth of field, 
4K resolution, professional photography style, NO humans, NO text,
16:9 aspect ratio

engine: "dall-e-3" или "flux-2-max" или "seedream-5-0-260128"
resolution: "1792x1024"
```

### 2. **Иконка раздела "Учебник"** (для sidebar/nav)
```
PROMPT:
Minimal dark mode icon depicting an open book with floating candlestick 
chart pages, glowing cyan outlines on graphite background (#161b22), 
institutional UI design, vector-style simplicity, modern flat design 
with subtle neon accents, dark glassmorphism, 512x512 icon size,
NO text, NO watermarks

engine: "dall-e-3"  или "flux-2-pro"
```

### 3. **SMC: BOS/CHoCH/MSS диаграмма**
```
PROMPT:
Technical financial chart diagram showing three sequential market structure 
breaks: BOS (break of structure) with green arrow continuation, CHoCH 
(change of character) with yellow caution signal, MSS (market structure 
shift) with powerful red reversal arrow, dark mode candlestick chart 
background, institutional visualization style, glowing neon highlights 
in cyan, yellow, and red, premium Bloomberg chart aesthetic, 
clean vector graphics, NO text labels, isolated on #0d1117

engine: "flux-2-pro"  (best for technical diagrams)
```

### 4. **Order Flow / DOM heatmap**
```
PROMPT:
Stylized heatmap visualization of order book depth (DOM), buy-side in 
green and sell-side in red colors with intensity gradients, central 
price column with glowing white, depth bars on both sides showing 
volume distribution, dark glassmorphism panels, Bloomberg Terminal 
aesthetic, premium institutional trading UI, dark navy background, 
subtle grid pattern, vector style, NO text, NO watermarks

engine: "flux-2-pro"
```

### 5. **Wyckoff 5 фаз A-E**
```
PROMPT:
Conceptual diagram of Wyckoff accumulation cycle in 5 phases (A-B-C-D-E), 
phase A showing panic selling climax with red volume spike, phase B 
showing sideways consolidation building cause, phase C showing spring 
test with V-shaped recovery, phase D showing sign of strength breakout, 
phase E showing markup rally, dark mode aesthetic with neon color 
coding (red, yellow, green, cyan, white), institutional chart style, 
premium dark UI, NO text labels, isolated elements on #0d1117

engine: "flux-2-pro"
```

### 6. **Liquidation Heatmap**
```
PROMPT:
Financial liquidation heatmap visualization, horizontal price level 
bands colored by intensity (yellow-orange-red gradient), glowing 
clusters showing magnetic zones, dark navy background with subtle 
grid, premium trading UI style, institutional Bloomberg aesthetic, 
neon highlights, depth perception, vector style, NO text, 
isolated on #0d1117

engine: "flux-2-max"  (high quality for hero images)
```

### 7. **Volume Profile — POC, VA, HVN/LVN**
```
PROMPT:
Volume Profile chart visualization with horizontal histogram bars, 
bright orange POC line glowing, cyan value area shaded, high volume 
nodes (HVN) in green, low volume nodes (LVN) in red, candlestick 
chart background, dark institutional trading terminal aesthetic, 
premium dark mode, Bloomberg style, glowing data points, NO text,
isolated on #0d1117 background

engine: "flux-2-pro"
```

### 8. **Psychology: FOMO / Revenge Trading / Discipline**
```
PROMPT:
Conceptual art depicting emotional trading psychology: a broken compass 
made of candlestick chart fragments representing FOMO, a dark shadowy 
reflection of a trader in the mirror representing revenge trading, 
and a perfectly aligned balance scale made of bullish and bearish 
candles representing discipline, dark mode moody aesthetic, 
institutional art style, deep shadows with selective cyan and red 
neon highlights, premium dramatic lighting, NO human faces, 
NO text, isolated on #0d1117

engine: "flux-2-max"
```

### 9. **Elliott Wave — Expanded Flat**
```
PROMPT:
Abstract 3D wave structure representing Elliott Wave Expanded Flat 
correction pattern, three A-B-C waves where B wave breaks start of A 
and C wave breaks end of A, rendered as flowing cyan neon light ribbons 
in 3D space, dark navy void background, premium data visualization 
aesthetic, scientific and mathematical feel, clean modern lines, 
NO text, NO labels

engine: "flux-2-pro"
```

### 10. **Confluence Score gauge**
```
PROMPT:
Futuristic digital score gauge for trading confluence, circular 
progress meter with 10 segments, colors transitioning from red (0/10) 
to yellow (5/10) to green (10/10), central digital readout area, 
glowing neon outline, dark mode premium UI, Bloomberg Terminal 
aesthetic, dark glassmorphism, NO numbers, NO text, isolated on #0d1117

engine: "flux-2-pro"
```

### 11. **On-Chain Whale Activity**
```
PROMPT:
Abstract 3D visualization of cryptocurrency whale transactions, 
massive glowing blockchain nodes connected by neon cyan transaction 
flows, particles representing token movements, dark void background, 
premium fintech aesthetic, deep space atmosphere with subtle stars, 
institutional data art style, volumetric lighting, NO text, 
NO human elements

engine: "flux-2-pro"
```

### 12. **Risk Management: Kelly Criterion**
```
PROMPT:
Mathematical risk visualization showing Kelly Criterion curve, 
two intersecting curves forming a bell-like probability distribution, 
green zone (optimal), yellow zone (half-Kelly), red zone (over-leverage), 
clean mathematical graph rendered in 3D space with neon glowing lines, 
dark institutional background, premium academic aesthetic, NO text 
labels, isolated on #0d1117

engine: "flux-2-pro"
```

### 13. **Live Portfolio Dashboard** (mockup)
```
PROMPT:
Premium dark mode trading dashboard UI mockup, multiple panels 
showing portfolio metrics, equity curve, pie chart, recent trades 
table, all glowing in cyan/green on dark navy background, modern 
glassmorphism design, Bloomberg Terminal inspired layout, 
institutional finance aesthetic, sharp typography, data-rich 
visualization, NO actual text, isolated on #0d1117

engine: "flux-2-pro" или "gpt-5-image"
```

### 14. **CRT: AMD цикл**
```
PROMPT:
Three-phase cycle diagram showing Accumulation-Manipulation-Distribution 
in institutional trading, phase 1 horizontal box (accumulation), 
phase 2 sharp V-shape (manipulation with stop hunt), phase 3 trending 
movement (distribution), all glowing neon colors on dark navy 
background, minimalist technical chart aesthetic, clean vector 
graphics, NO text, isolated on #0d1117

engine: "flux-2-pro"
```

### 15. **Macro & Intermarket Globe**
```
PROMPT:
Futuristic 3D global market visualization, Earth globe with overlaid 
financial data streams connecting major financial centers, neon 
cyan and green data flows representing capital movement, dark 
space background with stars, Bloomberg Terminal inspired, premium 
institutional fintech aesthetic, volumetric lighting, NO text,
NO labels

engine: "flux-2-max"
```

### 16. **TradingView Lightweight Charts (close-up)**
```
PROMPT:
Macro close-up of a sleek modern candlestick chart on ultra-wide 
curved monitor, dark UI with green and red candles, glowing cyan 
indicators and overlays, professional trader workstation, shallow 
depth of field, premium product photography, Bloomberg Terminal 
aesthetic, dark navy environment, NO human elements, NO text,
isolated on #0d1117

engine: "flux-2-pro" или "dall-e-3"
```

### 17. **Свечные паттерны — коллаж**
```
PROMPT:
Grid of glowing candlestick patterns isolated on dark navy background: 
hammer, doji, engulfing, morning star, evening star, each pattern 
rendered as premium 3D candles with realistic wax appearance and 
neon glow, dark glassmorphism panels, institutional chart aesthetic, 
professional photography style, soft volumetric lighting, 
clean composition, NO text, isolated on #0d1117

engine: "flux-2-pro"
```

### 18. **Iceberg Order Detection**
```
PROMPT:
Conceptual 3D illustration of iceberg order, small visible ice peak 
above water with massive glowing crystal structure hidden below, 
water represented as dark navy depth with subtle currents, premium 
dark mode aesthetic, cool blue and white neon accents, deep sea 
atmosphere, institutional art style, clean and minimal, NO text,
isolated on #0d1117

engine: "flux-2-pro"
```

---

## 🎬 Video Generation — Veo 3.1 (запланировано)

### V1. **Walk-through: API3 #4 trade**
**Длительность:** 3-5 минут
```
PROMPT:
Slow cinematic walkthrough of a cryptocurrency trade setup on a 
trading chart, dark mode professional interface, candlestick patterns 
forming progressively showing institutional structure breaks (BOS, 
CHoCH, MSS) with animated highlights, order flow visualization with 
bid-ask volume clusters, volume profile appearing as horizontal 
histogram, liquidation heatmap with glowing clusters, smooth camera 
pans and zooms, premium Bloomberg Terminal aesthetic, no humans, 
no voiceover, just chart animation, dark navy color scheme with 
neon cyan and green highlights, 4K cinematic quality

engine: "veo-3.1-generate-preview"
duration: 180  # seconds
```

### V2. **Backtest Animation**
```
PROMPT:
Animated equity curve backtest visualization, line drawing itself 
across the chart with glowing green trajectory, individual trade 
markers appearing as green and red dots, drawdown periods highlighted 
in red shaded regions, win rate and profit factor statistics appearing 
in HUD overlays, time-lapse effect, dark mode trading interface, 
Bloomberg Terminal aesthetic, smooth motion graphics, no humans,
premium institutional quality, dark navy background, 4K

engine: "veo-3.1-generate-preview"
duration: 120
```

### V3. **Wyckoff Cycle Explanation**
```
PROMPT:
Educational animation of Wyckoff accumulation cycle, 5 phases A-E 
appearing sequentially with smooth transitions, candlestick chart 
animating each phase: A (selling climax), B (cause building), 
C (spring with V-recovery), D (SOS breakout), E (markup), 
annotations appearing as glowing text labels, dark mode professional 
UI, institutional chart aesthetic, smooth educational animation,
no human figures, 4K dark navy background

engine: "veo-3.1-generate-preview"
duration: 240
```

---

## 🤖 Доступные модели (найдено в каталоге проекта 09)

### Image Generation (`apiyi` провайдер):
- `dall-e-3` — высокое качество, концептуальные изображения
- `flux-2-max` — топ-качество, фотореализм
- `flux-2-pro` — профессиональные диаграммы
- `flux-2-flex` — гибкий стиль
- `flux-2-klein-4b/9b` — быстрая генерация
- `seedream-4.0/4.5/5.0` — ByteDance модели

### Vision/Image via LLM (`routerai` провайдер):
- `openai/gpt-5-image`, `gpt-5.4-image-2` — генерация через vision LLM
- `google/gemini-3-pro-image` — мультимодальная
- `black-forest-labs/flux.2-pro/max` — открытые модели

### Video Generation (`apiyi` провайдер):
- `veo-3.1-generate-preview` — Google Veo 3.1
- `veo-3.1-fast-generate-preview` — ускоренная версия

---

## 📋 Workflow генерации

1. **Выбрать провайдера** через `opencode` (уже интегрирован в `models_catalog.json`)
2. **Загрузить промпт** из этого манифеста
3. **Сгенерировать** через API
4. **Сохранить** в `static/img/chapter-XX/` или `static/img/hero/`
5. **Подключить** в HTML шаблонах

## ⚠️ Статус

- **Запланировано, НЕ реализовано** в этой версии (согласно плану v3)
- Для генерации потребуется API-ключ `apiyi` или `routerai`
- После генерации — обновить шаблоны с новыми изображениями

---

*Манифест создан 2026-07-02 · TradeHelp v3*
*Источник: `data/tradeLLm/` + проект 09 `model_catalog`*
