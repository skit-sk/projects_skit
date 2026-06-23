import time
from datetime import datetime
from typing import Optional
from .base import BaseProvider


GRANULARITY_MAP = {
    "1D": "1day",
    "4h": "4h",
    "1h": "1h",
}


class BitgetOHLCVProvider(BaseProvider):
    BASE_URL = "https://api.bitget.com/api/v2/spot/market/candles"

    def __init__(self, retries: int = 3, timeout: int = 15, cache_ttl: float = 300.0):
        super().__init__(retries, timeout, cache_ttl)

    def fetch(self, symbol: str, granularity: str = "1D",
              start_ts: Optional[float] = None, end_ts: Optional[float] = None,
              limit: int = 1000) -> list[dict]:
        # Normalize: keep case (Bitget needs lowercase for 4h/1h, uppercase for 1D)
        bg_gran = GRANULARITY_MAP.get(granularity)
        if not bg_gran:
            raise ValueError(f"Unsupported granularity: {granularity}. Use 1D, 4h, 1h.")

        cache_args = (symbol.upper(), granularity, start_ts, end_ts, limit)
        cache_key = self._cache_key(*cache_args)
        cached = self._cached(cache_key)
        if cached is not None:
            return cached

        sym = symbol.upper().replace("/", "")
        if not sym.endswith("USDT"):
            sym += "USDT"

        params = {
            "symbol": sym,
            "granularity": bg_gran,
            "limit": str(limit),
        }
        if start_ts is not None:
            params["startTime"] = str(int(start_ts * 1000))
        if end_ts is not None:
            params["endTime"] = str(int(end_ts * 1000))

        url = self.BASE_URL + "?" + "&".join(f"{k}={v}" for k, v in params.items())
        data = self._fetch_with_retry(url)

        if data.get("code") != "00000":
            raise RuntimeError(f"Bitget API error: {data.get('msg', 'unknown')}")

        rows = data.get("data", [])
        rows_sorted = sorted(rows, key=lambda r: int(r[0]))
        result = []
        for r in rows_sorted:
            ts_ms = int(r[0])
            result.append({
                "timestamp_ms": ts_ms,
                "datetime": datetime.utcfromtimestamp(ts_ms / 1000).isoformat(),
                "date": time.strftime("%Y-%m-%d", time.gmtime(ts_ms / 1000)),
                "open": float(r[1]),
                "high": float(r[2]),
                "low": float(r[3]),
                "close": float(r[4]),
                "volume": float(r[5]),
                "quote_volume": float(r[6]) if len(r) > 6 else 0,
            })

        self._store_cache(cache_key, result)
        return result

    def fetch_range(self, symbol: str, granularity: str,
                    start_ts: float, end_ts: float) -> list[dict]:
        all_candles = []
        cursor = start_ts
        while cursor < end_ts:
            chunk = self.fetch(symbol, granularity, start_ts=cursor, end_ts=end_ts, limit=1000)
            if not chunk:
                break
            all_candles.extend(chunk)
            last_ts = chunk[-1]["timestamp_ms"] / 1000
            if last_ts <= cursor:
                break
            cursor = last_ts + 1
        seen_dates = set()
        unique = []
        for c in all_candles:
            key = c.get("date", c["datetime"])
            if key not in seen_dates:
                seen_dates.add(key)
                unique.append(c)
        return unique
