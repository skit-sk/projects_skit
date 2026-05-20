"""Order Book utilities — normalize symbol, fetch from Bitget, aggregate levels."""

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


def fetch_aggregated_ob(symbol: str, depth: int = 15, bucket_size: float = 0) -> dict | None:
    """Запросить стакан, агрегировать, гарантировать глубину depth корзин.
    
    Если после агрегации корзин меньше чем depth — дозапрашивает с большим limit.
    """
    raw_limit = depth * 3  # первая попытка: в 3 раза больше нужной глубины
    max_limit = 2000
    last_result = None

    while raw_limit <= max_limit:
        data = fetch_order_book_raw(symbol, raw_limit)
        if not data:
            return last_result

        asks_raw = data.get("asks", [])
        bids_raw = data.get("bids", [])

        asks = aggregate_levels(asks_raw, bucket_size)
        bids = aggregate_levels(bids_raw, bucket_size)

        result = {
            "asks": asks[:depth],
            "bids": bids[:depth],
            "ts": data.get("ts", ""),
        }
        last_result = result

        if len(asks) >= depth and len(bids) >= depth:
            return result

        raw_limit *= 2  # дозапрос

    return last_result
