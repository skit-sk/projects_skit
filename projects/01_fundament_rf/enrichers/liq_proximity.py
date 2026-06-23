class LiqProximityEnricher:
    LEVERAGES = [10, 5, 2]

    def enrich_all(self, candles: list[dict], entry_price: float,
                   leverage: float = 10) -> list[dict]:
        liq_price = self._compute_liq_price(entry_price, leverage)
        result = []
        for c in candles:
            high = c.get("high", 0)
            low = c.get("low", 0)
            close = c.get("close", 0)
            side = "long" if entry_price and close >= entry_price else "short"
            c["liq_proximity"] = {
                "entry_price": entry_price,
                "leverage": leverage,
                "liq_price_10x": self._compute_liq_price(entry_price, 10),
                "liq_price_5x": self._compute_liq_price(entry_price, 5),
                "liq_price_2x": self._compute_liq_price(entry_price, 2),
                "closest_liq": None,
                "at_risk": False,
            }
            liq_info = c["liq_proximity"]
            for lev in self.LEVERAGES:
                lp = self._compute_liq_price(entry_price, lev)
                touched = (low <= lp <= high) if side == "long" else (low <= lp <= high)
                if touched:
                    liq_info["closest_liq"] = lp
                    liq_info["at_risk"] = True
                    liq_info[f"touched_{lev}x"] = True
                else:
                    liq_info[f"touched_{lev}x"] = False
            result.append(c)
        return result

    def _compute_liq_price(self, entry: float, lev: float, side: str = "long") -> float:
        if side == "long":
            return entry * (1 - 1 / lev)
        return entry * (1 + 1 / lev)
