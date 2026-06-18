"""Order Book utilities — normalize symbol, fetch from Bitget, aggregate levels."""

import json
import asyncio
import requests


def normalize_symbol(raw: str) -> str | None:
    """Привести символ к формату TICKERUSDT."""
    s = raw.strip().upper()
    if s.endswith("USDT"):
        return s
    if s.isalpha() and len(s) <= 10:
        return f"{s}USDT"
    return None


def fetch_order_book_raw(symbol: str, limit: int = 15) -> dict | None:
    """Получить стакан через публичный REST API Bitget."""
    url = "https://api.bitget.com/api/v2/spot/market/orderbook"
    params = {"symbol": symbol, "type": "step0", "limit": str(limit)}
    try:
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()
        if data.get("code") == "00000":
            return data["data"]
    except Exception as e:
        print(f"Error fetching OB: {e}")
    return None


def aggregate_levels(entries: list, bucket_size: float) -> list:
    """Группировка уровней стакана в корзины по цене.
    
    Вход: [["76670.49", "1.5"], ["76671.00", "2.3"], ...]
    Выход при bucket_size > 0: [("76670.00–76671.00", "3.8"), ...]
    Выход при bucket_size = 0: исходные пары (цена, объём)
    """
    if not bucket_size or bucket_size <= 0:
        return [(e[0], e[1]) for e in entries]

    buckets = {}
    for price_str, size_str in entries:
        p = float(price_str)
        s = float(size_str)
        bucket_start = (p // bucket_size) * bucket_size
        bucket_end = bucket_start + bucket_size

        if bucket_start in buckets:
            buckets[bucket_start]["vol"] += s
            buckets[bucket_start]["count"] += 1
        else:
            buckets[bucket_start] = {
                "label": f"{bucket_start:.2f}–{bucket_end:.2f}",
                "vol": s,
                "count": 1,
            }

    sorted_items = sorted(buckets.items(), key=lambda x: x[0])
    return [(v["label"], f"{v['vol']:.4f}") for _, v in sorted_items]


WS_URL = "wss://ws.bitget.com/v2/ws/public"


async def fetch_aggregated_ob_ws(symbol: str, depth: int = 15, bucket_size: float = 0, ws_timeout: float = 15) -> dict | None:
    """Получить стакан через Bitget v2 WebSocket (канал books, 500 уровней).
    
    Даёт 500 asks + 500 bids — достаточно для любых агрегаций.
    """
    import websockets

    subscribe = json.dumps({
        "op": "subscribe",
        "args": [{"channel": "books", "instId": symbol, "instType": "SPOT"}]
    })

    try:
        async with websockets.connect(WS_URL, ping_interval=10, ping_timeout=5) as ws:
            await ws.send(subscribe)

            # Response 1: subscribe-ack (пропускаем)
            try:
                raw = await asyncio.wait_for(ws.recv(), timeout=ws_timeout)
                ack = json.loads(raw)
                if ack.get("event") == "error":
                    print(f"WS subscribe error: {ack.get('msg', '')}")
                    return None
            except asyncio.TimeoutError:
                print("WS timeout waiting for subscribe-ack")
                return None

            # Response 2: snapshot (полный стакан)
            raw = await asyncio.wait_for(ws.recv(), timeout=ws_timeout)
            msg = json.loads(raw)
            if msg.get("action") != "snapshot":
                print(f"WS unexpected response: {json.dumps(msg)[:100]}")
                return None

            data_list = msg.get("data", [])
            if not data_list:
                return None
            data = data_list[0] if isinstance(data_list, list) else data_list

            asks_raw = data.get("asks", [])
            bids_raw = data.get("bids", [])

            asks = aggregate_levels(asks_raw, bucket_size)
            bids = aggregate_levels(bids_raw, bucket_size)

            return {
                "asks": asks[:depth],
                "bids": bids[:depth],
                "ts": data.get("ts", ""),
                "actual_asks": len(asks),
                "actual_bids": len(bids),
                "bucket_size": bucket_size,
                "requested_bucket_size": bucket_size,
                "source": "ws",
            }
    except asyncio.TimeoutError:
        print(f"WS timeout for {symbol}")
    except Exception as e:
        print(f"WS error for {symbol}: {e}")

    return None


def fetch_aggregated_ob(symbol: str, depth: int = 15, bucket_size: float = 0) -> dict | None:
    """Запросить стакан через REST API Bitget, агрегировать.
    
    Если задан bucket_size > 0 и после агрегации меньше depth уровней —
    автоматически уменьшает bucket_size (делит на 2) пока не достигнет depth
    или bucket_size не станет ≤ 0.01 (дальше мельчить смысла нет).
    Возвращает фактический bucket_size в поле `bucket_size`.
    """
    raw_limit = min(depth * 3, 150)
    data = fetch_order_book_raw(symbol, raw_limit)
    if not data:
        return None

    asks_raw = data.get("asks", [])
    bids_raw = data.get("bids", [])

    actual_bs = bucket_size
    if bucket_size > 0:
        for _ in range(10):
            asks = aggregate_levels(asks_raw, actual_bs)
            bids = aggregate_levels(bids_raw, actual_bs)
            if len(asks) >= depth and len(bids) >= depth:
                break
            actual_bs = round(actual_bs / 2, 2)
            if actual_bs < 0.01:
                actual_bs = bucket_size
                asks = aggregate_levels(asks_raw, actual_bs)
                bids = aggregate_levels(bids_raw, actual_bs)
                break
    else:
        asks = aggregate_levels(asks_raw, 0)
        bids = aggregate_levels(bids_raw, 0)

    return {
        "asks": asks[:depth],
        "bids": bids[:depth],
        "ts": data.get("ts", ""),
        "actual_asks": len(asks),
        "actual_bids": len(bids),
        "bucket_size": actual_bs,
        "requested_bucket_size": bucket_size,
    }
