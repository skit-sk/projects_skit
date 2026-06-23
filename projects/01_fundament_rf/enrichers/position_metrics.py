class PositionMetricsEnricher:
    def enrich_all(self, candles: list[dict], entry_price: float,
                   leverage: float = 10, volume: float = 1,
                   side: str = "long", entry_date: str | None = None) -> list[dict]:
        for c in candles:
            o, h, l, cl = c["open"], c["high"], c["low"], c["close"]

            body = (cl - o) if cl > o else (o - cl)
            body_pct_raw = (body / o * 100) if o else 0.0
            upper_wick = h - max(o, cl)
            lower_wick = min(o, cl) - l

            deviation_from_entry_usdt = cl - entry_price
            diff_pct = ((cl - entry_price) / entry_price * 100) if entry_price else 0.0
            deviation_from_open_usdt = cl - o
            deviation_from_open_pct = ((cl - o) / o * 100) if o else 0.0

            volatility = h - l
            is_pre = (entry_date is not None and c.get("date", "") < entry_date)

            # Exact rounding cascade from calculator/calc_day_metrics + processor_1d._calculate_day
            # Key: do NOT round diff_pct before mul (calc_day_metrics rounds at return only)
            body_pct_4 = round(body_pct_raw, 4)
            deviation_pct_4 = round(diff_pct, 4)
            roe_pct_now = diff_pct * leverage
            roe_pct_4 = round(roe_pct_now, 4)
            pnl_usdt_now = roe_pct_now * volume / 100
            pnl_usdt_6 = round(pnl_usdt_now, 6)

            pm = {
                "body": round(body, 6),
                "body_pct": round(body_pct_4, 2),
                "upper_wick": round(upper_wick, 6),
                "lower_wick": round(lower_wick, 6),
                "deviation": {
                    "from_entry_usdt": round(deviation_from_entry_usdt, 6),
                    "from_entry_pct": round(deviation_pct_4, 2),
                    "from_open_usdt": round(deviation_from_open_usdt, 6),
                    "from_open_pct": round(deviation_from_open_pct, 2),
                },
                "roe_pct": round(roe_pct_4, 2) if not is_pre else 0,
                "pnl_usdt": round(pnl_usdt_6, 4) if not is_pre else 0,
                "volatility": round(volatility, 6),
                "profitable": roe_pct_now > 0 if not is_pre else False,
                "pre_entry": is_pre,
            }
            c["position_metrics"] = pm
        return candles
