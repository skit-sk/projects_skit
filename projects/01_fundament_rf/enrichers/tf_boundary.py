class TFBoundaryEnricher:
    TF_SECONDS = {
        "1D": 86400,
        "4h": 14400,
        "1h": 3600,
    }

    def enrich_all(self, candles: list[dict], timeframe: str = "1D") -> list[dict]:
        if not candles:
            return candles
        tf_sec = self.TF_SECONDS.get(timeframe, 86400)
        result = []
        for i, c in enumerate(candles):
            ts_ms = c.get("timestamp_ms", 0)
            is_first = i == 0
            is_last = i == len(candles) - 1
            if i > 0:
                prev_ts = candles[i - 1].get("timestamp_ms", 0)
                gap = ts_ms - prev_ts
                is_new_tf = gap > tf_sec * 1000 * 1.5
            else:
                is_new_tf = False
            c["tf_boundary"] = {
                "is_first": is_first,
                "is_last": is_last,
                "is_new_tf": is_new_tf,
                "index": i,
                "total": len(candles),
            }
            result.append(c)
        return result
