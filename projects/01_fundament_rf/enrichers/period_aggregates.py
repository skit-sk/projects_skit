import statistics


class PeriodAggregatesEnricher:
    def enrich_all(self, candles: list[dict]) -> list[dict]:
        if not candles:
            return candles
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]
        volumes = [c.get("volume", 0) for c in candles]
        n = len(candles)
        aggregates = {
            "period_high": max(highs),
            "period_low": min(lows),
            "period_open": candles[0]["open"],
            "period_close": candles[-1]["close"],
            "period_change_pct": round((closes[-1] - closes[0]) / closes[0] * 100, 2) if closes[0] else 0,
            "avg_volume": round(statistics.mean(volumes), 2) if volumes else 0,
            "total_volume": round(sum(volumes), 2),
            "avg_body_pct": 0,
            "max_body_pct": 0,
        }
        body_pcts = []
        for c in candles:
            o, h, l, cl = c["open"], c["high"], c["low"], c["close"]
            body = abs(cl - o)
            body_pct = body / o * 100 if o else 0
            upper_wick = h - max(o, cl)
            lower_wick = min(o, cl) - l
            body_pcts.append(body_pct)
            c["candle_metrics"] = {
                "body": round(body, 6),
                "body_pct": round(body_pct, 2),
                "upper_wick": round(upper_wick, 6),
                "lower_wick": round(lower_wick, 6),
                "total_range": round(h - l, 6),
                "is_green": cl > o,
                "is_red": cl < o,
            }
        if body_pcts:
            aggregates["avg_body_pct"] = round(statistics.mean(body_pcts), 2)
            aggregates["max_body_pct"] = round(max(body_pcts), 2)
        return candles
