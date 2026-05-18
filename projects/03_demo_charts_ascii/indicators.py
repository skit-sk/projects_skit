"""indicators.py — Technical indicators for ASCII overlay and JSON export.

Computes:
  - SMA / EMA (5, 20, 200)
  - Bollinger Bands
  - RSI
  - MACD
  - Volume proxy (volatility)
  - Anomaly detection (>2σ)

All functions accept a list of dicts representing daily data.
"""
from typing import Dict, List, Optional, Tuple


def _sma(data: List[float], period: int) -> List[Optional[float]]:
    """Simple moving average. Returns list same length as data (None for first period-1)."""
    if period <= 0 or len(data) < period:
        return [None] * len(data)
    result = [None] * (period - 1)
    window = []
    for i, val in enumerate(data):
        window.append(val)
        if len(window) > period:
            window.pop(0)
        if len(window) == period:
            result.append(sum(window) / period)
        else:
            result.append(None)
    return result


def _ema(data: List[float], period: int) -> List[Optional[float]]:
    """Exponential moving average."""
    if period <= 0 or len(data) < period:
        return [None] * len(data)
    k = 2.0 / (period + 1)
    result = [None] * (period - 1)
    # seed with SMA
    seed = sum(data[:period]) / period
    result.append(seed)
    prev = seed
    for val in data[period:]:
        ema = val * k + prev * (1 - k)
        result.append(ema)
        prev = ema
    return result


def _std(data: List[float], period: int) -> List[Optional[float]]:
    """Rolling standard deviation."""
    if period <= 0 or len(data) < period:
        return [None] * len(data)
    result = [None] * (period - 1)
    for i in range(period - 1, len(data)):
        window = data[i - period + 1:i + 1]
        mean = sum(window) / period
        var = sum((x - mean) ** 2 for x in window) / period
        result.append(var ** 0.5)
    return result


def compute_mas(values: List[float]) -> Dict[str, List[Optional[float]]]:
    """Compute SMA/EMA for 5, 20, 200."""
    return {
        "sma5": _sma(values, 5),
        "sma20": _sma(values, 20),
        "sma200": _sma(values, 200),
        "ema12": _ema(values, 12),
        "ema26": _ema(values, 26),
    }


def compute_bollinger(values: List[float], period: int = 20, mult: float = 2.0) -> Dict[str, List[Optional[float]]]:
    """Bollinger Bands: middle=SMA, upper/lower = SMA ± mult*std."""
    sma = _sma(values, period)
    stds = _std(values, period)
    upper = []
    lower = []
    for s, d in zip(sma, stds):
        if s is None or d is None:
            upper.append(None)
            lower.append(None)
        else:
            upper.append(s + mult * d)
            lower.append(s - mult * d)
    return {"bb_middle": sma, "bb_upper": upper, "bb_lower": lower}


def compute_rsi(values: List[float], period: int = 14) -> List[Optional[float]]:
    """RSI using standard Wilder's smoothing."""
    if len(values) < period + 1:
        return [None] * len(values)

    deltas = [values[i] - values[i - 1] for i in range(1, len(values))]
    gains = [max(0, d) for d in deltas]
    losses = [max(0, -d) for d in deltas]

    avg_gain = sum(gains[:period]) / period
    avg_loss = sum(losses[:period]) / period

    rsi_values = [None] * period
    if avg_loss == 0:
        rsi_values.append(100.0)
    else:
        rs = avg_gain / avg_loss
        rsi_values.append(100 - 100 / (1 + rs))

    for i in range(period, len(deltas)):
        avg_gain = (avg_gain * (period - 1) + gains[i]) / period
        avg_loss = (avg_loss * (period - 1) + losses[i]) / period
        if avg_loss == 0:
            rsi_values.append(100.0)
        else:
            rs = avg_gain / avg_loss
            rsi_values.append(100 - 100 / (1 + rs))

    return rsi_values


def compute_macd(values: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List[Optional[float]]]:
    """MACD line, signal line, histogram."""
    ema_fast = _ema(values, fast)
    ema_slow = _ema(values, slow)

    macd_line = []
    for f, s in zip(ema_fast, ema_slow):
        if f is None or s is None:
            macd_line.append(None)
        else:
            macd_line.append(f - s)

    # drop leading Nones for signal EMA
    valid_macd = [v for v in macd_line if v is not None]
    signal_ema = _ema(valid_macd, signal)

    # re-align
    signal_full = [None] * (len(macd_line) - len(signal_ema)) + signal_ema

    histogram = []
    for m, s in zip(macd_line, signal_full):
        if m is None or s is None:
            histogram.append(None)
        else:
            histogram.append(m - s)

    return {"macd": macd_line, "macd_signal": signal_full, "macd_histogram": histogram}


def compute_anomalies(values: List[float], period: int = 20, sigma: float = 2.0) -> List[bool]:
    """True where |value - SMA| > sigma * std."""
    sma = _sma(values, period)
    stds = _std(values, period)
    result = []
    for v, s, d in zip(values, sma, stds):
        if s is None or d is None or d == 0:
            result.append(False)
        else:
            result.append(abs(v - s) > sigma * d)
    return result


def compute_all_indicators(days: List[Dict]) -> Dict:
    """
    Compute all indicators from daily data.
    days[i] should have keys: 'deviation' dict with 'from_entry_pct',
    'roe_pct', 'volatility', 'pnl_usdt', 'date'.
    """
    if not days:
        return {}

    # extract series
    deviation = [d.get("deviation", {}).get("from_entry_pct", 0.0) for d in days]
    roe = [d.get("roe_pct", 0.0) for d in days]
    vol = [d.get("volatility", 0.0) for d in days]
    pnl = [d.get("pnl_usdt", 0.0) for d in days]
    dates = [d.get("date", "") for d in days]

    mas = compute_mas(deviation)
    bb = compute_bollinger(deviation)
    rsi = compute_rsi(deviation)
    macd = compute_macd(deviation)
    anomalies = compute_anomalies(deviation)

    return {
        "dates": dates,
        "deviation": deviation,
        "roe": roe,
        "volatility": vol,
        "pnl_usdt": pnl,
        **mas,
        **bb,
        "rsi": rsi,
        **macd,
        "anomalies": anomalies,
    }


def indicator_summary(ind: Dict) -> Dict[str, any]:
    """Return last-known values for dashboard display."""
    def last_valid(arr):
        for v in reversed(arr):
            if v is not None:
                return v
        return None

    return {
        "sma5": last_valid(ind.get("sma5", [])),
        "sma20": last_valid(ind.get("sma20", [])),
        "bb_upper": last_valid(ind.get("bb_upper", [])),
        "bb_lower": last_valid(ind.get("bb_lower", [])),
        "rsi": last_valid(ind.get("rsi", [])),
        "macd": last_valid(ind.get("macd", [])),
        "macd_signal": last_valid(ind.get("macd_signal", [])),
        "anomaly_count": sum(1 for a in ind.get("anomalies", []) if a),
    }
