# Changelog — TradingView Demos

## v3.1.2 (2026-05-04 16:00 MSK) — Standalone widget samples

### Добавлено
- `standalone-widgets/` — 10 автономных HTML-файлов для локального тестирования
  Каждый файл открывается в браузере двойным кликом, без сервера.
  Доступны на Vercel: `https://tradingview-demos-sk.vercel.app/standalone-widgets/`

---

## v3.1.1 (2026-05-01 18:00 MSK) — TradingView JS embed with fallback

### Критическое изменение: обход блокировки www.tradingview-widget.com

Прямые `<iframe src="https://www.tradingview-widget.com/...">` не работают в РФ —
домен заблокирован, браузер выдаёт `ERR_CONNECTION_RESET`.

TradingView JS embed загружает скрипты с `s3.tradingview.com` и создаёт iframe
динамически. При блокировке основного домена, JS автоматически подменяет
`www.tradingview-widget.com` на `s.tradingview.com` (функция `_tryFixCSPIssueWithFallback`).

### Формат iframe-виджетов (29 шт.)

```html
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-XXX.js" async>
{ JSON config }
</script>
```

### Формат web component виджетов (3 шт.)

```html
<div class="tradingview-widget-container">
  <tv-mini-chart symbol="BINANCE:BTCUSDT" colorTheme="dark" locale="en" autosize></tv-mini-chart>
</div>
<script type="module" src="https://widgets.tradingview-widget.com/w/en/tv-mini-chart.js"></script>
```

### Web component виджеты (без изменений)
- mini-chart → `tv-mini-chart.js`
- economic-map, economics → `tv-economic-map.js`

---

## v3.0.2 (2026-05-01 17:30 MSK) — Removed CSP header

### Исправление
- Удалён CSP-заголовок из `vercel.json`, который блокировал виджеты
  (`frame-src` не содержал `'self'` → локальные iframe-превью заблокированы;
  `style-src` отсутствовал → inline CSS заблокирован)
- Возврат к исходному `vercel.json` с только `X-Content-Type-Options: nosniff`

---

## v3.0.1 (2026-05-01 17:15 MSK) — Direct iframes + CSP headers (ОТМЕНЕНО)

### Добавлено (ОТМЕНЕНО в v3.0.2)
- CSP-заголовок в `vercel.json` → вызвал ERR_BLOCKED_BY_CSP у пользователей

### Из v3.0.0 (сохранено)
- Revert с TradingView JS embed на прямые iframes
- Web components сохранены для mini-chart, economic-map, economics

### Откат с v3.1.0
- Возвращены прямые `<iframe>` для всех 29 iframe-виджетов (JS embed метод рендерил
  корректно, но давал пустые скриншоты в headless-браузере)
- Web components сохранены для mini-chart, economic-map, economics (нет iframe-альтернативы)
- Добавлен CSP заголовок в `vercel.json` (frame-src, script-src, connect-src для TradingView доменов)

### Из v3.0.0 (сохранено)
- 6 исправленных embed-widget типов: crypto-coins-heatmap, screener, events, forex-heat-map, single-quote, hotlists
- URL-кодировка `%22` во всех iframe URL
- 24 SVG-заглушки заменены на реальные TradingView iframes в превью

---

## v3.1.0 (2026-05-01 17:00 MSK) — TradingView JS embed method (ОТМЕНЕНО)

### Изменение: все iframe-виджеты переведены на TradingView JS embed

Вместо прямых `<iframe src="...">` используется официальный метод TradingView:
```html
<div class="tradingview-widget-container">
  <div class="tradingview-widget-container__widget"></div>
</div>
<script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-XXX.js" async>
{ JSON config }
</script>
```

Преимущества:
- JS-скрипт автоматически создаёт iframe с правильной URL-кодировкой
- Обработка CSP (fallback на `s.tradingview.com`)
- Автоматический ресайз виджетов
- Copyright-ссылка от TradingView
- Нет проблем с `\"` / `%22` кодировкой

### Web components (mini-chart, economic-map, economics)

Оставлены как `<tv-minimal-chart>`, `<tv-economic-map>` — TradingView не поддерживает iframe для этих виджетов.

### Прочее
- Добавлен `viewport` meta tag во все страницы
- Добавлен CSP-заголовок в `vercel.json` для `tradingview-widget.com` и `s.tradingview.com`

---

## v3.0.0 (2026-05-01 16:45 MSK) — Breaking changes

### Breaking: изменены embed-widget типы TradingView

Ряд виджетов использовали устаревшие/несуществующие типы `embed-widget`, что приводило к HTTP 404 от `tradingview-widget.com`. Исправлено на актуальные:

| Файл | Старый тип (404) | Новый тип (200) |
|------|-----------------|-----------------|
| `crypto-heatmap` | `crypto-heatmap` | `crypto-coins-heatmap` |
| `crypto-market` | `crypto-screener` | `screener` |
| `economic-calendar`, `calendars` | `economic-calendar` | `events` |
| `forex-heatmap` | `forex-heatmap` | `forex-heat-map` |
| `single-ticker` | `single-ticker` | `single-quote` |
| `stock-market` | `stock-market` | `hotlists` |

### Breaking: конвертация 3 виджетов в web components

TradingView убрал iframe-версии для `mini-chart`, `economic-map`. Переведены на `<tv-*>` web components:

| Файл | Web component script |
|------|----------------------|
| `mini-chart` | `tv-mini-chart.js` |
| `economic-map` | `tv-economic-map.js` |
| `economics` | `tv-economic-map.js` |

### Прочее

- URL-кодировка: `%22` вместо `\"` во всех 31 widgets-full и 24 preview файлах
- 24 SVG-заглушки в preview заменены на реальные TradingView iframes
- Все 32 виджета загружаются корректно (подтверждено скриншотами)

---

## v2.5.7 (2026-05-01 15:30 MSK)

- 3 недостающих widgets-full добавлены: `company-profile`, `fundamental-data`, `symbol-info`
- 9 сломанных виджетов заменены на прямые iframe (без JS-обёртки)
- 14 новых preview-страниц
- Исправлены ссылки «Open Full» во всех виджетов
- Добавлен MSK timestamp в футер

---

## v2.5.6 (2026-05-01 05:24 MSK)

- Все виджеты переведены на прямые iframe (без JS-обёртки widget-loader)

---

## v2.5.5 (2026-05-01 05:02 MSK)

- Ticker / Ticker Tag исправлены
- Виджеты работают

---

## v2.5.4 (2026-05-01 04:46 MSK)

- Очищен widget loader

---

## v2.5.3 (2026-05-01 04:44 MSK)

- Обновлена версия виджетов

---

## v2.5.2 и ранее

- Начальная структура: gallery + widgets-full + widgets превью
- Динамическая загрузка iframes через JS