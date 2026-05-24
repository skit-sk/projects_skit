import numpy as np
from typing import List, Optional, Dict


def compute_rsi(prices: List[float], period: int = 14) -> List[Optional[float]]:
    arr = np.array(prices, dtype=float)
    deltas = np.diff(arr)
    gains = np.where(deltas > 0, deltas, 0.0)
    losses = np.where(deltas < 0, -deltas, 0.0)
    avg_gain = np.full_like(arr, np.nan)
    avg_loss = np.full_like(arr, np.nan)
    avg_gain[period] = np.mean(gains[:period])
    avg_loss[period] = np.mean(losses[:period])
    for i in range(period + 1, len(arr)):
        avg_gain[i] = (avg_gain[i - 1] * (period - 1) + gains[i - 1]) / period
        avg_loss[i] = (avg_loss[i - 1] * (period - 1) + losses[i - 1]) / period
    rs = avg_gain / avg_loss
    rsi = 100.0 - (100.0 / (1.0 + rs))
    result: List[Optional[float]] = [None] * len(arr)
    for i in range(period, len(arr)):
        result[i] = round(float(rsi[i]), 2)
    return result


def compute_ema(prices: List[float], period: int) -> List[Optional[float]]:
    arr = np.array(prices, dtype=float)
    result = np.full_like(arr, np.nan)
    k = 2.0 / (period + 1)
    valid_start = np.where(~np.isnan(arr))[0]
    if len(valid_start) == 0:
        return [None] * len(arr)
    first_valid = valid_start[0]
    if first_valid + period > len(arr):
        return [None] * len(arr)
    init_slice = arr[first_valid:first_valid + period]
    if np.all(np.isnan(init_slice)):
        return [None] * len(arr)
    result[first_valid + period - 1] = np.nanmean(init_slice)
    for i in range(first_valid + period, len(arr)):
        if np.isnan(arr[i]):
            result[i] = result[i - 1]
        else:
            result[i] = (arr[i] - result[i - 1]) * k + result[i - 1]
    return [round(float(v), 4) if not np.isnan(v) else None for v in result]


def compute_macd(prices: List[float], fast: int = 12, slow: int = 26,
                 signal: int = 9) -> Dict[str, List]:
    ema_fast = compute_ema(prices, fast)
    ema_slow = compute_ema(prices, slow)
    macd_line = []
    for ef, es in zip(ema_fast, ema_slow):
        if ef is not None and es is not None:
            macd_line.append(round(ef - es, 4))
        else:
            macd_line.append(None)
    signal_line = compute_ema([v if v is not None else 0 for v in macd_line], signal)
    histogram = []
    for m, s in zip(macd_line, signal_line):
        if m is not None and s is not None:
            histogram.append(round(m - s, 4))
        else:
            histogram.append(None)
    return {"macd": macd_line, "signal": signal_line, "histogram": histogram}


def compute_sma(values: List[float], period: int) -> List[Optional[float]]:
    result: List[Optional[float]] = []
    for i in range(len(values)):
        if i < period - 1:
            result.append(None)
        else:
            s = sum(values[i - period + 1:i + 1])
            result.append(round(s / period, 4))
    return result


def compute_oi(volumes: List[float], decay: float = 0.92,
               sensitivity: float = 0.08) -> List[float]:
    arr = np.array(volumes, dtype=float)
    oi = np.zeros_like(arr)
    base = np.mean(arr[:5]) if len(arr) >= 5 else arr[0]
    oi[0] = base
    for i in range(1, len(arr)):
        window = np.mean(arr[max(0, i - 3):i])
        vol_change = (arr[i] - window) / window if window > 0 else 0
        oi[i] = oi[i - 1] * decay + base * sensitivity * (1 + vol_change * 2)
        oi[i] = max(oi[i], base * 0.3)
    oi = oi / np.max(oi) * 100
    return [round(float(v), 2) for v in oi]