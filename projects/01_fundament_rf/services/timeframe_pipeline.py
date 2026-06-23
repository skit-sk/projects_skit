import time
from datetime import datetime
from threading import Thread

from storage import get_storage
from data_providers import BitgetOHLCVProvider, OHLCVAggregator
from enrichers import (
    SessionsEnricher, TFBoundaryEnricher, LiqProximityEnricher,
    ExtremesFilterEnricher, FibonacciEnricher, PeriodAggregatesEnricher,
    PositionMetricsEnricher,
)


class TimeframePipeline:
    TIMEFRAMES = ["1D", "4h", "1h"]

    def __init__(self):
        self.storage = get_storage()
        self.ohlcv = BitgetOHLCVProvider()
        self.aggregator = OHLCVAggregator()
        self.sessions = SessionsEnricher()
        self.tf_boundary = TFBoundaryEnricher()
        self.liq_proximity = LiqProximityEnricher()
        self.extremes = ExtremesFilterEnricher()
        self.fibonacci = FibonacciEnricher()
        self.period_agg = PeriodAggregatesEnricher()
        self.position_metrics = PositionMetricsEnricher()

    def build(self, obj_id: str, timeframes: list[str] | None = None) -> dict:
        timing = {
            "operation": "build_tf",
            "obj_id": obj_id,
            "timestamp": datetime.now().isoformat(),
            "timeframes": {},
        }
        try:
            obj = self.storage.load(obj_id)
            emoji_entry = obj.data.get("emoji_entry", {})
            symbol = emoji_entry.get("symbol", obj.data.get("symbol", "UNKNOWN"))
            entry_price = float(emoji_entry.get("entry_price", obj.data.get("entry_price", 0)))
            entry_date = emoji_entry.get("entry_date", obj.data.get("entry_date", ""))
            leverage = float(obj.data.get("leverage", 10))
            volume = float(emoji_entry.get("volume", 1))

            if not entry_price or not entry_date:
                raise ValueError("Missing entry_price or entry_date")

            start_ts = self._parse_date(entry_date)
            end_ts = time.time()
            pre_history_days = int(obj.data.get("pre_history_days", 60))
            hist_start_ts = start_ts - pre_history_days * 86400 if pre_history_days > 0 else start_ts

            tfs = timeframes or self.TIMEFRAMES
            all_tf_data = {}

            for tf in tfs:
                tf_start = time.time()
                candles = self.ohlcv.fetch_range(symbol, tf, hist_start_ts, end_ts)
                # Enrich each timeframe
                candles = self.sessions.enrich_all(candles)
                candles = self.tf_boundary.enrich_all(candles, tf)
                candles = self.liq_proximity.enrich_all(candles, entry_price, leverage)
                candles = self.position_metrics.enrich_all(
                    candles, entry_price, leverage, volume, entry_date=entry_date
                )
                candles = self.extremes.enrich_all(candles, entry_price, threshold=0.5)
                candles = self.period_agg.enrich_all(candles)

                # Find high/low for fib
                if candles:
                    highs = [c["high"] for c in candles]
                    lows = [c["low"] for c in candles]
                    candles = self.fibonacci.enrich_all(candles, max(highs), min(lows))

                tf_data = {
                    "id": f"{obj_id}_{tf}",
                    "parent_id": obj_id,
                    "symbol": symbol.upper(),
                    "entry_price": entry_price,
                    "entry_date": entry_date,
                    "leverage": leverage,
                    "volume": volume,
                    "granularity": tf,
                    "candles": candles,
                    "count": len(candles),
                }
                self.storage.write_timeframe(symbol, obj_id, tf, tf_data)

                elapsed = int((time.time() - tf_start) * 1000)
                timing["timeframes"][tf] = {
                    "candles": len(candles),
                    "elapsed_ms": elapsed,
                    "status": "completed",
                }

            timing["result"] = {
                "status": "completed",
                "timeframes": list(tfs),
                "symbol": symbol.upper(),
            }

        except Exception as e:
            timing["result"] = {"status": "failed", "error": str(e)}

        return timing

    def build_async(self, obj_id: str, timeframes: list[str] | None = None):
        Thread(target=self.build, args=(obj_id, timeframes), daemon=True).start()

    def _parse_date(self, date_str: str) -> float:
        parts = date_str.split("-")
        return time.mktime((int(parts[0]), int(parts[1]), int(parts[2]), 0, 0, 0, 0, 0, 0))
