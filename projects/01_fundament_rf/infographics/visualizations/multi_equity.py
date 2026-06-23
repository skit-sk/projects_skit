from typing import Dict, List, Any
from storage import get_storage


def _resolve_obj(obj_id: str):
    s = get_storage()
    try:
        obj = s.get(obj_id) if hasattr(s, "get") else None
    except Exception:
        obj = None
    if obj is not None:
        return obj
    for o in s.list():
        if o.id == obj_id:
            return o
    return None


def _equity_curve(symbol: str, obj_id: str) -> List[dict]:
    s = get_storage()
    if not s.exists_timeframe(symbol, obj_id, "1D"):
        return []
    data = s.read_timeframe(symbol, obj_id, "1D")
    candles = data.get("candles", [])
    pts = []
    for c in candles:
        pm = c.get("position_metrics", {})
        pnl = pm.get("pnl_usdt", 0)
        date = c.get("date", "")
        if date:
            pts.append({"date": date, "pnl_usdt": round(pnl, 2)})
    return pts


def compute(symbols: List[str], normalize: bool = True) -> Dict[str, Any]:
    s = get_storage()
    objs_by_symbol = {}
    for o in s.list():
        sym = o.data.get("emoji_entry", {}).get("symbol", "").upper()
        if sym in [x.upper() for x in symbols] and sym not in objs_by_symbol:
            objs_by_symbol[sym] = o

    series = []
    for sym in symbols:
        sym_u = sym.upper()
        obj = objs_by_symbol.get(sym_u)
        if obj is None:
            series.append({"symbol": sym_u, "error": "not found", "points": []})
            continue
        pts = _equity_curve(sym_u, obj.id)
        if normalize and pts:
            start = pts[0]["pnl_usdt"]
            for p in pts:
                p["pnl_usdt"] = round(p["pnl_usdt"] - start, 2)
        series.append({
            "symbol": sym_u,
            "obj_id": obj.id,
            "name": obj.name,
            "points": pts,
            "total_pnl": round(pts[-1]["pnl_usdt"], 2) if pts else 0,
        })

    all_dates = sorted({p["date"] for s_ in series for p in s_.get("points", [])})

    return {
        "symbols": [s_["symbol"] for s_ in series],
        "normalize": normalize,
        "dates": all_dates,
        "series": series,
    }
