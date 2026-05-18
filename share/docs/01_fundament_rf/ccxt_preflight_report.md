# Preflight Report: CCXT Public Methods — bitget

**Date:** 2026-05-12 20:15 UTC  
**Methods tested:** 17 unique (after dedup, from 20 total across categories)  
**Base URL:** `http://localhost:5000`

---

## ✅ Working (13/17)

### REST API (8)

| # | Method | Params | Response | Timing |
|---|--------|--------|----------|--------|
| 1 | `fetch_ohlcv` | `BTC/USDT, 1d, limit=1` | `list(1)` candle | gen=10ms, rtt~3100ms |
| 2 | `fetch_ticker` | `BTC/USDT` | `dict(22)` fields | gen=8ms, rtt~3000ms |
| 3 | `fetch_trades` | `BTC/USDT, limit=1` | `list(1)` trade | gen=8ms, rtt~3000ms |
| 4 | `fetch_order_book` | `BTC/USDT` | `dict(6)` bids/asks | gen=8ms, rtt~3000ms |
| 5 | `fetch_markets` | `{}` | `list(1309)` markets | gen=9ms, rtt~2200ms |
| 6 | `fetch_currencies` | `{}` | `dict(2076)` currencies | gen=9ms, rtt~600ms |
| 7 | `fetch_funding_rate_history` | default | `list(1)` entry | gen=10ms, rtt~3000ms |

### WebSocket SSE Stream (5)

| # | Method | Channel | Stream Status |
|---|--------|---------|---------------|
| 8 | `fetch_ticker_ws` | `ticker` | ✅ snapshot + live updates every ~200ms |
| 9 | `fetch_order_book_ws` | `books5` | ✅ snapshot + live depth updates |
| 10 | `fetch_trades_ws` | `trade` | ✅ snapshot + live trades |
| 11 | `fetch_tickers_ws` | `ticker` (all) | ✅ snapshot + live tickers |
| 12 | `fetch_order_book_ws` | `books5` | ✅ (дубль из `Market Data` + `Orders`) |

---

## ❌ Failed (4/17)

| # | Method | Reason | Workaround |
|---|--------|--------|------------|
| 1 | `fetch_funding_rate` | Требует **swap symbol**: `BTC/USDT:USDT` | Использовать swap-символ |
| 2 | `fetch_funding_rates` | HTTP 500 с любыми `symbols` | Вызывать **без** параметров `symbols` (`{}`) |
| 3 | `fetch_tickers` | HTTP 500 с `symbols` | Вызывать **без** параметра `symbols` (`{}`) |
| 4 | `fetch_contract_ohlcv` | `not supported yet` — ccxt не реализовал | Использовать `fetch_ohlcv` (спот) |
| 5 | `fetch_ohlcv_ws` | timeframe `1d` не поддерживается WS | Использовать `1m`, `5m`, `15m`, `30m`, `1M` |
| 6 | `fetch_order_books` | HTTP 500 — метод не поддерживается | Использовать `fetch_order_book` по одному |

---

## Правила форматирования параметров

| Параметр | Формат | Пример |
|----------|--------|--------|
| `symbol` (spot) | `BTC/USDT` | `ETH/USDT`, `BTC/USDT` |
| `symbol` (swap) | `BTC/USDT:USDT` | `ETH/USDT:USDT` |
| `symbols` | **не передавать** для tickers/funding_rates | `{}` |
| `timeframe` (WS) | `1m`, `5m`, `15m`, `30m`, `1M` | только они поддерживаются WS |
| `timeframe` (REST) | `1m..1d` | все стандартные |
| `limit` | число | default: varies |
| `since` | `YYYY-MM-DD` или ms timestamp | не обязателен |
| `params` | `{"key":"value"}` | не обязателен |

---

## Дубли в категориях

Методы `fetch_order_book`, `fetch_order_book_ws`, `fetch_order_books` попадают в две категории (`Market Data` и `Orders`) из-за пересечения ключевых слов `order`/`book`. При подсчёте уникальных методов дубли удалены.

---

**Полные данные:** `ccxt_preflight_report.json`
