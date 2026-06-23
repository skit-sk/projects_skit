import statistics


class ExtremesFilterEnricher:
    def enrich_all(self, candles: list[dict], entry_price: float = 0,
                   threshold: float = 0.5, max_extremes: int = 4,
                   method: str = "m1_simple", params: dict | None = None) -> list[dict]:
        if not candles:
            return candles
        params = params or {}
        closes = [c["close"] for c in candles]
        highs = [c["high"] for c in candles]
        lows = [c["low"] for c in candles]

        strengths = self._compute_strengths(
            closes, highs, lows, method, params, entry_price
        )
        for i, c in enumerate(candles):
            s = strengths[i] if i < len(strengths) else 0
            c["strength"] = {
                "value": round(s, 4),
                "method": method,
                "is_extremum": s >= threshold,
                "is_peak": False,
                "is_trough": False,
            }
        extrema = self._find_extrema(candles, threshold, max_extremes, closes)
        for idx in extrema["peaks"]:
            if idx < len(candles):
                candles[idx]["strength"]["is_peak"] = True
        for idx in extrema["troughs"]:
            if idx < len(candles):
                candles[idx]["strength"]["is_trough"] = True
        return candles

    def _compute_strengths(self, closes, highs, lows, method, params, entry_price):
        if method == "m1_simple":
            return self._m1_simple(closes, params)
        elif method == "m2_volume_weighted":
            return self._m2_volume_weighted(closes, highs, lows, params)
        elif method == "m3_bodies":
            return self._m3_bodies(closes, params, entry_price)
        return [0] * len(closes)

    def _ema(self, values, period):
        if len(values) < period:
            return [0] * len(values)
        k = 2 / (period + 1)
        ema = [values[0]]
        for v in values[1:]:
            ema.append(v * k + ema[-1] * (1 - k))
        return ema

    def _atr(self, highs, lows, closes, period):
        if len(highs) < 2:
            return [0] * len(highs)
        tr = [max(highs[i] - lows[i], abs(highs[i] - closes[i-1]), abs(lows[i] - closes[i-1])) for i in range(1, len(highs))]
        tr = [highs[0] - lows[0]] + tr
        return self._ema(tr, period)

    def _m1_simple(self, closes, params):
        period = params.get("ema_period", 20)
        atr_period = params.get("atr_period", 14)
        if len(closes) <= max(period, atr_period):
            return [0] * len(closes)
        ema = self._ema(closes, period)
        strengths = []
        for i in range(len(closes)):
            if i < period or i < atr_period:
                strengths.append(0)
            else:
                strengths.append(abs(closes[i] - ema[i]) / closes[i] * 100)
        return strengths

    def _m2_volume_weighted(self, closes, highs, lows, params):
        period = params.get("ema_period", 20)
        atr_period = params.get("atr_period", 14)
        vol_window = params.get("volume_window", 30)
        if len(closes) <= max(period, atr_period, vol_window):
            return [0] * len(closes)
        ema = self._ema(closes, period)
        strengths = []
        for i in range(len(closes)):
            if i < period or i < atr_period:
                strengths.append(0)
            else:
                strengths.append(abs(closes[i] - ema[i]) / closes[i] * 100)
        return strengths

    def _m3_bodies(self, closes, params, entry_price):
        window = params.get("window", 3)
        direction = params.get("direction", "both")
        threshold_pct = params.get("threshold_pct")
        threshold_pts = params.get("threshold_pts")
        use = params.get("use", "max")
        if len(closes) < window:
            return [0] * len(closes)
        strengths = []
        for i in range(len(closes)):
            if i < window:
                strengths.append(0)
                continue
            body = abs(closes[i] - closes[i-1])
            body_pct = body / closes[i-1] * 100 if closes[i-1] else 0
            strengths.append(max(body_pct, body))
        return strengths

    def _find_extrema(self, candles, threshold, max_extremes, closes):
        candidates = [(i, c["strength"]["value"]) for i, c in enumerate(candles)
                      if c["strength"]["is_extremum"]]
        peaks = sorted([(i, v) for i, v in candidates if v > 0], key=lambda x: x[1], reverse=True)
        troughs = sorted([(i, v) for i, v in candidates if v <= 0], key=lambda x: x[1])
        half = max_extremes // 2
        return {
            "peaks": [i for i, _ in peaks[:half]],
            "troughs": [i for i, _ in troughs[:half]],
        }
