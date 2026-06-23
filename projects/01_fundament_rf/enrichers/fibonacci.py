class FibonacciEnricher:
    RETRACEMENTS = {
        "0.0": 0.0, "0.236": 0.236, "0.382": 0.382, "0.5": 0.5,
        "0.618": 0.618, "0.786": 0.786, "1.0": 1.0,
    }
    EXTENSIONS_INSIDE = {"-0.382": -0.382, "-0.618": -0.618}
    EXTENSIONS_OUTSIDE = {
        "1.272": 1.272, "1.414": 1.414, "1.618": 1.618,
        "2.0": 2.0, "2.618": 2.618,
    }

    def enrich_all(self, candles: list[dict], high_price: float = 0,
                   low_price: float = 0, max_extremes: int = 4,
                   enabled_retracements: dict | None = None,
                   enabled_extensions_inside: dict | None = None,
                   enabled_extensions_outside: dict | None = None) -> list[dict]:
        if not candles or not high_price or not low_price or high_price == low_price:
            return candles
        range_val = high_price - low_price
        levels = {}
        enabled_retracements = enabled_retracements or {k: True for k in self.RETRACEMENTS}
        enabled_extensions_inside = enabled_extensions_inside or {k: False for k in self.EXTENSIONS_INSIDE}
        enabled_extensions_outside = enabled_extensions_outside or {
            "1.272": True, "1.414": True, "1.618": True,
            "2.0": False, "2.618": False,
        }
        for key, ratio in self.RETRACEMENTS.items():
            if enabled_retracements.get(key, False):
                levels[key] = high_price - range_val * ratio
        for key, ratio in self.EXTENSIONS_INSIDE.items():
            if enabled_extensions_inside.get(key, False):
                levels[key] = high_price - range_val * (1 + abs(ratio))
        for key, ratio in self.EXTENSIONS_OUTSIDE.items():
            if enabled_extensions_outside.get(key, False):
                levels[key] = high_price - range_val * ratio
        fib_data = {
            "high_price": high_price,
            "low_price": low_price,
            "range": range_val,
            "levels": {k: round(v, 6) for k, v in sorted(levels.items(), key=lambda x: float(x[0]))},
        }
        for c in candles:
            c["fibonacci"] = fib_data
        return candles
