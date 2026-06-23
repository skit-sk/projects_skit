from typing import Optional


class OHLCVAggregator:
    TF_ORDER = ["1D", "4h", "1h"]

    def merge(self, *datasets: list[dict]) -> dict[str, list[dict]]:
        tfs = {}
        for ds in datasets:
            if not ds:
                continue
            tf = "1D"
            if len(ds) > 1:
                pass
            if tf not in tfs:
                tfs[tf] = []
            tfs[tf].extend(ds)
        for tf in list(tfs.keys()):
            tfs[tf] = self._deduplicate(tfs[tf])
        return tfs

    def _deduplicate(self, candles: list[dict]) -> list[dict]:
        seen = set()
        result = []
        for c in candles:
            key = c.get("date") or c.get("datetime", "")
            if key not in seen:
                seen.add(key)
                result.append(c)
        return result

    def build_output(self, tf_data: dict[str, list[dict]],
                     symbol: str, obj_id: str,
                     entry_price: Optional[float] = None,
                     entry_date: Optional[str] = None,
                     leverage: float = 10,
                     volume: float = 1) -> dict:
        output = {
            "id": f"{obj_id}_TF",
            "parent_id": obj_id,
            "symbol": symbol.upper(),
            "entry_price": entry_price,
            "entry_date": entry_date,
            "leverage": leverage,
            "volume": volume,
            "granularities": {},
        }
        for tf in self.TF_ORDER:
            candles = tf_data.get(tf, [])
            output["granularities"][tf] = {
                "candles": candles,
                "count": len(candles),
            }
        return output
