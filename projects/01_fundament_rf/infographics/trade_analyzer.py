import numpy as np
from scipy.signal import argrelextrema
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, field
from storage import JSONStorage


# ──────────────────────────────────────────────
# 8 типов скользящих средних
# ──────────────────────────────────────────────

def sma(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(arr, np.nan)
    if len(arr) < period:
        return result
    for i in range(period - 1, len(arr)):
        window = arr[i - period + 1:i + 1]
        if np.all(np.isnan(window)):
            result[i] = np.nan
        else:
            result[i] = np.nanmean(window)
    return result


def ema(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(arr, np.nan)
    if len(arr) < period:
        return result
    k = 2.0 / (period + 1)
    valid_start = np.where(~np.isnan(arr))[0]
    if len(valid_start) == 0:
        return result
    first_valid = valid_start[0]
    if first_valid + period > len(arr):
        return result
    init_slice = arr[first_valid:first_valid + period]
    if np.all(np.isnan(init_slice)):
        return result
    result[first_valid + period - 1] = np.nanmean(init_slice)
    for i in range(first_valid + period, len(arr)):
        if np.isnan(arr[i]):
            result[i] = result[i - 1]
        else:
            result[i] = (arr[i] - result[i - 1]) * k + result[i - 1]
    return result


def wma(arr: np.ndarray, period: int) -> np.ndarray:
    result = np.full_like(arr, np.nan)
    if len(arr) < period:
        return result
    weights = np.arange(1, period + 1, dtype=float)
    wsum = weights.sum()
    for i in range(period - 1, len(arr)):
        window = arr[i - period + 1:i + 1]
        if np.any(np.isnan(window)):
            mask = ~np.isnan(window)
            if mask.sum() < 1:
                continue
            w = weights[mask]
            result[i] = np.dot(window[mask], w) / w.sum()
        else:
            result[i] = np.dot(window, weights) / wsum
    return result


def hma(arr: np.ndarray, period: int) -> np.ndarray:
    half = int(period / 2)
    sqrt_n = int(np.sqrt(period))
    if len(arr) < period:
        return np.full_like(arr, np.nan)
    wma_half = wma(arr, half)
    wma_full = wma(arr, period)
    raw = 2 * wma_half - wma_full
    result = wma(raw, sqrt_n)
    return result


def dema(arr: np.ndarray, period: int) -> np.ndarray:
    e1 = ema(arr, period)
    e2 = ema(e1, period)
    result = 2 * e1 - e2
    return result


def tema(arr: np.ndarray, period: int) -> np.ndarray:
    e1 = ema(arr, period)
    e2 = ema(e1, period)
    e3 = ema(e2, period)
    result = 3 * e1 - 3 * e2 + e3
    return result


def kama(arr: np.ndarray, period: int = 10, fast: int = 2, slow: int = 30) -> np.ndarray:
    result = np.full_like(arr, np.nan)
    if len(arr) < period:
        return result
    fast_sc = 2.0 / (fast + 1)
    slow_sc = 2.0 / (slow + 1)
    result[period - 1] = np.mean(arr[:period])
    for i in range(period, len(arr)):
        momentum = abs(arr[i] - arr[i - period])
        volatility = np.sum(np.abs(np.diff(arr[i - period:i + 1])))
        er = momentum / volatility if volatility > 0 else 0
        sc = er * (fast_sc - slow_sc) + slow_sc
        result[i] = arr[i] * sc + result[i - 1] * (1 - sc)
    return result


def zlema(arr: np.ndarray, period: int) -> np.ndarray:
    lag = int((period - 1) / 2)
    if len(arr) < period + lag:
        return np.full_like(arr, np.nan)
    shifted = np.full_like(arr, np.nan)
    shifted[lag:] = arr[:-lag]
    shifted[:lag] = arr[:lag]
    result = ema(shifted, period)
    return result


MA_FUNCTIONS = {
    'sma': sma,
    'ema': ema,
    'wma': wma,
    'hma': hma,
    'dema': dema,
    'tema': tema,
    'kama': kama,
    'zlema': zlema,
}

MA_NAMES = list(MA_FUNCTIONS.keys())

SINGLE_MA_PERIODS = [5, 10, 15, 20, 25, 30, 34, 40, 50, 55, 75, 89, 100,
                     125, 150, 175, 200, 210, 233, 250, 270, 289, 300]

FAST_PERIODS = [5, 8, 9, 10, 13, 20, 21, 30, 34, 40, 50, 55, 75, 89]

SLOW_PERIODS = [20, 25, 30, 34, 40, 50, 55, 60, 75, 100, 125, 150,
                175, 200, 210, 233, 250, 270, 289, 300]

TRIPLE_MA_COMBOS = [
    ('sma', 5, 'sma', 20, 'sma', 50),
    ('sma', 10, 'sma', 20, 'sma', 50),
    ('sma', 10, 'sma', 50, 'sma', 200),
    ('sma', 20, 'sma', 50, 'sma', 200),
    ('ema', 13, 'ema', 34, 'ema', 89),
    ('ema', 9, 'ema', 21, 'ema', 55),
    ('sma', 7, 'sma', 14, 'sma', 28),
    ('sma', 10, 'sma', 30, 'sma', 100),
    ('sma', 20, 'sma', 100, 'sma', 250),
    ('sma', 50, 'sma', 100, 'sma', 200),
]

CRISIS_PERIODS = {
    'dotcom': ('2000-03-01', '2002-10-31'),
    'gfc': ('2007-10-01', '2009-03-31'),
    'covid': ('2020-02-01', '2020-03-31'),
    'bear_2022': ('2022-01-01', '2022-10-31'),
}

DECADE_RANGES = [
    ('1970s', '1970-01-01', '1979-12-31'),
    ('1980s', '1980-01-01', '1989-12-31'),
    ('1990s', '1990-01-01', '1999-12-31'),
    ('2000s', '2000-01-01', '2009-12-31'),
    ('2010s', '2010-01-01', '2019-12-31'),
    ('2020s', '2020-01-01', '2029-12-31'),
]


# ──────────────────────────────────────────────
# BacktestMetrics
# ──────────────────────────────────────────────

@dataclass
class BacktestMetrics:
    cagr: float = 0.0
    max_dd: float = 0.0
    sharpe: float = 0.0
    win_rate: float = 0.0
    total_trades: int = 0
    exposure: float = 0.0
    cagr_per_maxdd: float = 0.0

    def to_dict(self) -> Dict[str, Any]:
        return {
            'cagr': round(self.cagr * 100, 2),
            'max_dd': round(self.max_dd * 100, 2),
            'sharpe': round(self.sharpe, 3),
            'win_rate': round(self.win_rate * 100, 1),
            'total_trades': self.total_trades,
            'exposure': round(self.exposure * 100, 1),
            'cagr_per_maxdd': round(self.cagr_per_maxdd, 3),
        }


# ──────────────────────────────────────────────
# TradeAnalyzer (расширенная версия)
# ──────────────────────────────────────────────

class TradeAnalyzer:
    def __init__(self, storage: Optional[JSONStorage] = None):
        self.storage = storage or JSONStorage()

    # ── публичный метод MA ──

    @staticmethod
    def compute_ma(prices: List[float], ma_type: str, period: int) -> List[Optional[float]]:
        if ma_type not in MA_FUNCTIONS:
            raise ValueError(f"Unknown MA type: {ma_type}. Choose from {list(MA_FUNCTIONS.keys())}")
        arr = np.array(prices, dtype=float)
        fn = MA_FUNCTIONS[ma_type]
        result = fn(arr, period)
        output = []
        for v in result:
            if np.isnan(v):
                output.append(None)
            else:
                output.append(round(float(v), 6))
        return output

    @staticmethod
    def compute_all_ma(prices: List[float], ma_types: Optional[List[str]] = None,
                       periods: Optional[List[int]] = None) -> Dict[str, List[Optional[float]]]:
        if ma_types is None:
            ma_types = ['sma', 'ema']
        if periods is None:
            periods = [50, 100, 200]
        result = {}
        for t in ma_types:
            for p in periods:
                key = f'{t}_{p}'
                result[key] = TradeAnalyzer.compute_ma(prices, t, p)
        return result

    # ── существующие методы ──

    def load_data(self, symbol: str, obj_id: str) -> Tuple[Dict, Dict, Dict]:
        card = self.storage.load(obj_id).to_dict()
        days_data = self.storage.load_1d(symbol, obj_id)
        raw_data = self.storage.load_raw(symbol, obj_id)
        return card, days_data, raw_data

    @staticmethod
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

    @staticmethod
    def compute_ema(prices: List[float], period: int) -> List[Optional[float]]:
        return TradeAnalyzer.compute_ma(prices, 'ema', period)

    @staticmethod
    def compute_macd(prices: List[float], fast: int = 12, slow: int = 26, signal: int = 9) -> Dict[str, List]:
        ema_fast = TradeAnalyzer.compute_ema(prices, fast)
        ema_slow = TradeAnalyzer.compute_ema(prices, slow)
        macd_line = []
        for ef, es in zip(ema_fast, ema_slow):
            if ef is not None and es is not None:
                macd_line.append(round(ef - es, 6))
            else:
                macd_line.append(None)
        signal_line = [None] * signal
        valid_macd = [m for m in macd_line if m is not None]
        if valid_macd:
            sig = TradeAnalyzer.compute_ema(valid_macd, signal)
            signal_line = [None] * (len(macd_line) - len(valid_macd)) + sig
        histogram = []
        for m, s in zip(macd_line, signal_line):
            if m is not None and s is not None:
                histogram.append(round(m - s, 6))
            else:
                histogram.append(None)
        return {'macd': macd_line, 'signal': signal_line, 'histogram': histogram}

    @staticmethod
    def find_pivot_points(values: List[float], window: int = 3) -> List[Dict]:
        arr = np.array(values, dtype=float)
        if len(arr) < window * 2 + 1:
            return []
        local_max = argrelextrema(arr, np.greater, order=window)[0]
        local_min = argrelextrema(arr, np.less, order=window)[0]
        result = []
        for idx in local_max:
            result.append({'index': int(idx), 'value': float(arr[idx]), 'type': 'peak'})
        for idx in local_min:
            result.append({'index': int(idx), 'value': float(arr[idx]), 'type': 'trough'})
        result.sort(key=lambda x: x['index'])
        return result

    # ──────────────────────────────────────────
    # Стратегия A: цена пересекает одну MA
    # ──────────────────────────────────────────

    @staticmethod
    def _simulate_single_ma(close: np.ndarray, ma: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = len(close)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(1, n):
            if np.isnan(ma[i]):
                equity[i] = equity[i - 1]
                continue
            if not in_position and close[i] > ma[i]:
                in_position = True
                entry_idx = i
            elif in_position and close[i] < ma[i]:
                in_position = False
                ret = close[i] / close[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (close[i] / close[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = close[-1] / close[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return equity, np.array(trades)

    def backtest_single_ma(self, closes: List[float], ma_type: str = 'sma',
                           period: int = 200) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        ma_arr = np.array(TradeAnalyzer.compute_ma(closes, ma_type, period), dtype=float)
        equity, trades = self._simulate_single_ma(arr, ma_arr)
        return self._calc_metrics(equity, trades, arr)

    def backtest_single_ma_grid(self, closes: List[float],
                                ma_types: Optional[List[str]] = None,
                                periods: Optional[List[int]] = None) -> List[Dict]:
        if ma_types is None:
            ma_types = ['sma', 'ema', 'wma', 'hma', 'dema', 'tema', 'kama', 'zlema']
        if periods is None:
            periods = SINGLE_MA_PERIODS
        results = []
        for t in ma_types:
            for p in periods:
                try:
                    m = self.backtest_single_ma(closes, t, p)
                    results.append({'ma_type': t, 'period': p, **m.to_dict()})
                except Exception:
                    pass
        return results

    # ──────────────────────────────────────────
    # Стратегия B: кроссовер двух MA
    # ──────────────────────────────────────────

    @staticmethod
    def _simulate_crossover(close: np.ndarray, fast_ma: np.ndarray, slow_ma: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        n = len(close)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(1, n):
            if np.isnan(fast_ma[i]) or np.isnan(slow_ma[i]):
                equity[i] = equity[i - 1]
                continue
            fast_crossed_above = not np.isnan(fast_ma[i - 1]) and not np.isnan(slow_ma[i - 1]) and fast_ma[i] > slow_ma[i] and fast_ma[i - 1] <= slow_ma[i - 1]
            fast_crossed_below = not np.isnan(fast_ma[i - 1]) and not np.isnan(slow_ma[i - 1]) and fast_ma[i] < slow_ma[i] and fast_ma[i - 1] >= slow_ma[i - 1]
            if not in_position and fast_crossed_above:
                in_position = True
                entry_idx = i
            elif in_position and fast_crossed_below:
                in_position = False
                ret = close[i] / close[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (close[i] / close[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = close[-1] / close[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return equity, np.array(trades)

    def backtest_crossover(self, closes: List[float],
                           fast_type: str, fast_period: int,
                           slow_type: str, slow_period: int) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        fast_arr = np.array(TradeAnalyzer.compute_ma(closes, fast_type, fast_period), dtype=float)
        slow_arr = np.array(TradeAnalyzer.compute_ma(closes, slow_type, slow_period), dtype=float)
        equity, trades = self._simulate_crossover(arr, fast_arr, slow_arr)
        return self._calc_metrics(equity, trades, arr)

    def backtest_crossover_grid(self, closes: List[float],
                                fast_periods: Optional[List[int]] = None,
                                slow_periods: Optional[List[int]] = None,
                                ma_types: Optional[List[str]] = None) -> List[Dict]:
        if fast_periods is None:
            fast_periods = FAST_PERIODS
        if slow_periods is None:
            slow_periods = SLOW_PERIODS
        if ma_types is None:
            ma_types = ['sma', 'ema', 'wma']
        results = []
        for t in ma_types:
            for fp in fast_periods:
                for sp in slow_periods:
                    if fp >= sp:
                        continue
                    try:
                        m = self.backtest_crossover(closes, t, fp, t, sp)
                        results.append({
                            'fast_type': t, 'fast_period': fp,
                            'slow_type': t, 'slow_period': sp,
                            **m.to_dict()
                        })
                    except Exception:
                        pass
        return results

    # ──────────────────────────────────────────
    # Стратегия C: буферная зона / подтверждение
    # ──────────────────────────────────────────

    @staticmethod
    def _simulate_buffer(close: np.ndarray, ma: np.ndarray, buffer_pct: float) -> Tuple[np.ndarray, np.ndarray]:
        n = len(close)
        in_position = False
        trades = []
        equity = np.ones(n)
        buf = buffer_pct / 100.0
        for i in range(1, n):
            if np.isnan(ma[i]):
                equity[i] = equity[i - 1]
                continue
            above = close[i] > ma[i] * (1 + buf)
            below = close[i] < ma[i] * (1 - buf)
            if not in_position and above:
                in_position = True
                entry_idx = i
            elif in_position and below:
                in_position = False
                ret = close[i] / close[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (close[i] / close[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = close[-1] / close[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return equity, np.array(trades)

    @staticmethod
    def _simulate_confirmation(close: np.ndarray, ma: np.ndarray, confirm_days: int) -> Tuple[np.ndarray, np.ndarray]:
        n = len(close)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(confirm_days, n):
            if np.isnan(ma[i]):
                equity[i] = equity[i - 1]
                continue
            above_streak = all(close[j] > ma[j] for j in range(i - confirm_days + 1, i + 1) if not np.isnan(ma[j]))
            below_streak = all(close[j] < ma[j] for j in range(i - confirm_days + 1, i + 1) if not np.isnan(ma[j]))
            if not in_position and above_streak:
                in_position = True
                entry_idx = i
            elif in_position and below_streak:
                in_position = False
                ret = close[i] / close[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (close[i] / close[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = close[-1] / close[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return equity, np.array(trades)

    def backtest_buffer(self, closes: List[float], ma_type: str = 'sma',
                        period: int = 200, buffer_pct: float = 5.0) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        ma_arr = np.array(TradeAnalyzer.compute_ma(closes, ma_type, period), dtype=float)
        equity, trades = self._simulate_buffer(arr, ma_arr, buffer_pct)
        return self._calc_metrics(equity, trades, arr)

    def backtest_confirmation(self, closes: List[float], ma_type: str = 'sma',
                              period: int = 200, confirm_days: int = 3) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        ma_arr = np.array(TradeAnalyzer.compute_ma(closes, ma_type, period), dtype=float)
        equity, trades = self._simulate_confirmation(arr, ma_arr, confirm_days)
        return self._calc_metrics(equity, trades, arr)

    def backtest_buffer_grid(self, closes: List[float], ma_type: str = 'sma',
                             period: int = 200) -> List[Dict]:
        results = []
        for buf in [1.0, 3.0, 5.0]:
            m = self.backtest_buffer(closes, ma_type, period, buf)
            results.append({'ma_type': ma_type, 'period': period, 'buffer_pct': buf, **m.to_dict()})
        for days in [3, 5]:
            m = self.backtest_confirmation(closes, ma_type, period, days)
            results.append({'ma_type': ma_type, 'period': period, 'confirm_days': days, **m.to_dict()})
        return results

    # ──────────────────────────────────────────
    # Стратегия D: тройная MA
    # ──────────────────────────────────────────

    def backtest_triple_ma(self, closes: List[float],
                           fast_type: str, fast_p: int,
                           mid_type: str, mid_p: int,
                           slow_type: str, slow_p: int,
                           label: str = '') -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        fast_arr = np.array(TradeAnalyzer.compute_ma(closes, fast_type, fast_p), dtype=float)
        mid_arr = np.array(TradeAnalyzer.compute_ma(closes, mid_type, mid_p), dtype=float)
        slow_arr = np.array(TradeAnalyzer.compute_ma(closes, slow_type, slow_p), dtype=float)
        n = len(arr)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(1, n):
            if np.isnan(fast_arr[i]) or np.isnan(mid_arr[i]) or np.isnan(slow_arr[i]):
                equity[i] = equity[i - 1]
                continue
            aligned = fast_arr[i] > mid_arr[i] > slow_arr[i]
            broken = fast_arr[i] < mid_arr[i] or mid_arr[i] < slow_arr[i]
            if not in_position and aligned:
                in_position = True
                entry_idx = i
            elif in_position and broken:
                in_position = False
                ret = arr[i] / arr[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (arr[i] / arr[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = arr[-1] / arr[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return self._calc_metrics(equity, np.array(trades), arr)

    def backtest_triple_ma_grid(self, closes: List[float]) -> List[Dict]:
        results = []
        for ft, fp, mt, mp, st, sp in TRIPLE_MA_COMBOS:
            try:
                m = self.backtest_triple_ma(closes, ft, fp, mt, mp, st, sp)
                label = f'{ft.upper()} {fp} / {mt.upper()} {mp} / {st.upper()} {sp}'
                results.append({'label': label, **m.to_dict()})
            except Exception:
                pass
        return results

    # ──────────────────────────────────────────
    # Стратегия E: MA + фильтры
    # ──────────────────────────────────────────

    def backtest_with_filters(self, closes: List[float],
                              fast_type: str, fast_period: int,
                              slow_type: str, slow_period: int,
                              rsi_threshold: Optional[float] = None,
                              slope_days: int = 0,
                              volume_filter: bool = False,
                              volumes: Optional[List[float]] = None) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        fast_arr = np.array(TradeAnalyzer.compute_ma(closes, fast_type, fast_period), dtype=float)
        slow_arr = np.array(TradeAnalyzer.compute_ma(closes, slow_type, slow_period), dtype=float)
        rsi_arr = None
        if rsi_threshold is not None:
            rsi_list = TradeAnalyzer.compute_rsi(closes, 14)
            rsi_arr = np.array([v if v is not None else np.nan for v in rsi_list], dtype=float)
        vol_arr = None
        if volume_filter and volumes:
            vol_arr = np.array(volumes, dtype=float)
            vol_ma = sma(vol_arr, 20)

        n = len(arr)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(1, n):
            if np.isnan(fast_arr[i]) or np.isnan(slow_arr[i]):
                equity[i] = equity[i - 1]
                continue
            fast_crossed_above = not np.isnan(fast_arr[i - 1]) and not np.isnan(slow_arr[i - 1]) and fast_arr[i] > slow_arr[i] and fast_arr[i - 1] <= slow_arr[i - 1]
            fast_crossed_below = not np.isnan(fast_arr[i - 1]) and not np.isnan(slow_arr[i - 1]) and fast_arr[i] < slow_arr[i] and fast_arr[i - 1] >= slow_arr[i - 1]
            if not in_position and fast_crossed_above:
                ok = True
                if rsi_threshold is not None and rsi_arr is not None and not np.isnan(rsi_arr[i]):
                    ok = ok and rsi_arr[i] > rsi_threshold
                if slope_days > 0 and i >= slope_days:
                    ok = ok and slow_arr[i] > slow_arr[i - slope_days]
                if volume_filter and vol_arr is not None and vol_ma is not None and i >= 20 and not np.isnan(vol_ma[i]):
                    ok = ok and vol_arr[i] > vol_ma[i]
                if ok:
                    in_position = True
                    entry_idx = i
            elif in_position and fast_crossed_below:
                in_position = False
                ret = arr[i] / arr[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (arr[i] / arr[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = arr[-1] / arr[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return self._calc_metrics(equity, np.array(trades), arr)

    # ──────────────────────────────────────────
    # Стратегия F: MA как динамический стоп-лосс
    # ──────────────────────────────────────────

    def backtest_trailing_stop(self, closes: List[float],
                               fast_type: str, fast_period: int,
                               slow_type: str, slow_period: int,
                               stop_type: str, stop_period: int) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        fast_arr = np.array(TradeAnalyzer.compute_ma(closes, fast_type, fast_period), dtype=float)
        slow_arr = np.array(TradeAnalyzer.compute_ma(closes, slow_type, slow_period), dtype=float)
        stop_arr = np.array(TradeAnalyzer.compute_ma(closes, stop_type, stop_period), dtype=float)
        n = len(arr)
        in_position = False
        trades = []
        equity = np.ones(n)
        for i in range(1, n):
            if np.isnan(fast_arr[i]) or np.isnan(slow_arr[i]) or np.isnan(stop_arr[i]):
                equity[i] = equity[i - 1]
                continue
            fast_crossed_above = not np.isnan(fast_arr[i - 1]) and not np.isnan(slow_arr[i - 1]) and fast_arr[i] > slow_arr[i] and fast_arr[i - 1] <= slow_arr[i - 1]
            if not in_position and fast_crossed_above:
                in_position = True
                entry_idx = i
            elif in_position and arr[i] < stop_arr[i]:
                in_position = False
                ret = arr[i] / arr[entry_idx]
                trades.append(ret)
                equity[i] = equity[entry_idx] * ret
            else:
                if in_position:
                    equity[i] = equity[entry_idx] * (arr[i] / arr[entry_idx])
                else:
                    equity[i] = equity[i - 1]
        if in_position:
            ret = arr[-1] / arr[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return self._calc_metrics(equity, np.array(trades), arr)

    def backtest_trailing_grid(self, closes: List[float]) -> List[Dict]:
        results = []
        crossovers = [('sma', 20, 'sma', 50), ('sma', 50, 'sma', 200)]
        stop_periods = [10, 15, 20, 30, 50]
        for ft, fp, st, sp in crossovers:
            for sp_stop in stop_periods:
                try:
                    m = self.backtest_trailing_stop(closes, ft, fp, st, sp, 'sma', sp_stop)
                    results.append({
                        'fast': f'{ft.upper()} {fp}', 'slow': f'{st.upper()} {sp}',
                        'stop_type': 'sma', 'stop_period': sp_stop, **m.to_dict()
                    })
                except Exception:
                    pass
        return results

    # ──────────────────────────────────────────
    # Стратегия G: Золотой крест / крест смерти
    # ──────────────────────────────────────────

    def backtest_golden_cross(self, closes: List[float], fast_period: int = 50,
                              slow_period: int = 200, delay_days: int = 0,
                              contrar: bool = False, hold_days: int = 0) -> BacktestMetrics:
        arr = np.array(closes, dtype=float)
        fast_arr = np.array(TradeAnalyzer.compute_ma(closes, 'sma', fast_period), dtype=float)
        slow_arr = np.array(TradeAnalyzer.compute_ma(closes, 'sma', slow_period), dtype=float)
        n = len(arr)
        in_position = False
        trades = []
        equity = np.ones(n)
        entry_idx = 0
        for i in range(1, n):
            if np.isnan(fast_arr[i]) or np.isnan(slow_arr[i]):
                equity[i] = equity[i - 1]
                continue
            golden = not np.isnan(fast_arr[i - 1]) and not np.isnan(slow_arr[i - 1]) and fast_arr[i] > slow_arr[i] and fast_arr[i - 1] <= slow_arr[i - 1]
            death = not np.isnan(fast_arr[i - 1]) and not np.isnan(slow_arr[i - 1]) and fast_arr[i] < slow_arr[i] and fast_arr[i - 1] >= slow_arr[i - 1]
            if contrar:
                signal = death
            else:
                signal = golden
            if not in_position and signal:
                if delay_days > 0:
                    delayed_entry = min(i + delay_days, n - 1)
                    entry_idx = delayed_entry
                    in_position = True
                else:
                    in_position = True
                    entry_idx = i
            elif in_position:
                if hold_days > 0 and i - entry_idx >= hold_days:
                    in_position = False
                    ret = arr[i] / arr[entry_idx]
                    trades.append(ret)
                    equity[i] = equity[entry_idx] * ret
                elif hold_days == 0:
                    exit_signal = death if not contrar else golden
                    if exit_signal:
                        in_position = False
                        ret = arr[i] / arr[entry_idx]
                        trades.append(ret)
                        equity[i] = equity[entry_idx] * ret
                    else:
                        equity[i] = equity[entry_idx] * (arr[i] / arr[entry_idx])
                else:
                    equity[i] = equity[entry_idx] * (arr[i] / arr[entry_idx])
            else:
                equity[i] = equity[i - 1]
        if in_position:
            ret = arr[-1] / arr[entry_idx]
            trades.append(ret)
            equity[-1] = equity[entry_idx] * ret
        return self._calc_metrics(equity, np.array(trades), arr)

    def backtest_golden_cross_grid(self, closes: List[float]) -> List[Dict]:
        results = []
        configs = [
            {'label': 'Golden Cross', 'contrar': False, 'delay_days': 0, 'hold_days': 0},
            {'label': 'Golden Cross +5d delay', 'contrar': False, 'delay_days': 5, 'hold_days': 0},
            {'label': 'Contrarian (252d hold)', 'contrar': True, 'delay_days': 0, 'hold_days': 252},
            {'label': 'Contrarian (30d hold)', 'contrar': True, 'delay_days': 0, 'hold_days': 30},
        ]
        for cfg in configs:
            try:
                m = self.backtest_golden_cross(closes, 50, 200, cfg['delay_days'], cfg['contrar'], cfg['hold_days'])
                results.append({'label': cfg['label'], **m.to_dict()})
            except Exception:
                pass
        return results

    # ──────────────────────────────────────────
    # Стратегия H: сравнение рынков (обёртка)
    # ──────────────────────────────────────────

    def backtest_market_comparison(self, closes_list: Dict[str, List[float]]) -> Dict[str, List[Dict]]:
        results = {}
        top5 = [('ema', 50, 'sma', 250), ('sma', 50, 'sma', 300),
                ('sma', 34, 'sma', 300), ('ema', 50, 'sma', 200),
                ('sma', 40, 'sma', 300)]
        for market_name, prices in closes_list.items():
            market_res = []
            for ft, fp, st, sp in top5:
                try:
                    m = self.backtest_crossover(prices, ft, fp, st, sp)
                    market_res.append({
                        'fast': f'{ft.upper()} {fp}', 'slow': f'{st.upper()} {sp}',
                        **m.to_dict()
                    })
                except Exception:
                    pass
            results[market_name] = market_res
        return results

    # ──────────────────────────────────────────
    # Стратегия I: по десятилетиям и кризисам
    # ──────────────────────────────────────────

    def backtest_decades(self, closes: List[float], dates: List[str],
                         fast_type: str = 'ema', fast_period: int = 50,
                         slow_type: str = 'sma', slow_period: int = 250) -> List[Dict]:
        results = []
        for label, start, end in DECADE_RANGES:
            indices = [i for i, d in enumerate(dates) if start <= d <= end]
            if len(indices) < 50:
                continue
            sub_closes = [closes[i] for i in indices]
            try:
                m = self.backtest_crossover(sub_closes, fast_type, fast_period, slow_type, slow_period)
                results.append({'decade': label, **m.to_dict()})
            except Exception:
                pass
        return results

    def backtest_crises(self, closes: List[float], dates: List[str],
                        fast_type: str = 'ema', fast_period: int = 50,
                        slow_type: str = 'sma', slow_period: int = 250) -> List[Dict]:
        results = []
        for crisis_name, (start, end) in CRISIS_PERIODS.items():
            indices = [i for i, d in enumerate(dates) if start <= d <= end]
            if len(indices) < 10:
                continue
            sub_closes = [closes[i] for i in indices]
            try:
                m = self.backtest_crossover(sub_closes, fast_type, fast_period, slow_type, slow_period)
                results.append({'crisis': crisis_name, **m.to_dict()})
            except Exception:
                pass
        return results

    # ──────────────────────────────────────────
    # Расчёт метрик
    # ──────────────────────────────────────────

    @staticmethod
    def _calc_metrics(equity: np.ndarray, trades: np.ndarray, close: np.ndarray) -> BacktestMetrics:
        n = len(equity)
        if n < 2:
            return BacktestMetrics()
        years = n / 252.0
        total_ret = equity[-1] / equity[0]
        cagr = total_ret ** (1.0 / years) - 1.0 if years > 0 else 0.0
        peak = np.maximum.accumulate(equity)
        dd = (equity - peak) / peak
        max_dd = float(np.min(dd))
        daily_returns = equity[1:] / equity[:-1] - 1.0
        sharpe = float(np.mean(daily_returns) / np.std(daily_returns) * np.sqrt(252)) if np.std(daily_returns) > 0 else 0.0
        win_rate = float(np.sum(trades >= 1.0) / len(trades)) if len(trades) > 0 else 0.0
        total_trades = len(trades)
        days_in_market = int(np.sum(~np.isnan(equity) & (equity != np.nan)))
        exposure = n / (n + 1) if n > 0 else 0
        cagr_per_maxdd = cagr / abs(max_dd) if max_dd != 0 else 0
        return BacktestMetrics(
            cagr=cagr, max_dd=max_dd, sharpe=sharpe,
            win_rate=win_rate, total_trades=total_trades,
            exposure=exposure, cagr_per_maxdd=cagr_per_maxdd
        )

    # ──────────────────────────────────────────
    # Генератор сигналов
    # ──────────────────────────────────────────

    def ma_signal_generator(self, closes: List[float], dates: List[str],
                            ma_types: Optional[List[str]] = None) -> Dict[str, Any]:
        if ma_types is None:
            ma_types = ['sma', 'ema']
        signals = []
        arr = np.array(closes, dtype=float)
        current_price = closes[-1] if closes else 0

        for t in ma_types:
            for p in [50, 100, 200]:
                ma_list = self.compute_ma(closes, t, p)
                ma_val = ma_list[-1] if ma_list and ma_list[-1] is not None else None
                if ma_val is None or ma_val == 0:
                    continue
                divergence = (current_price / ma_val - 1) * 100
                if current_price > ma_val:
                    confidence = min(100, int(abs(divergence) * 5 + 50))
                    signals.append({
                        'type': 'trend', 'direction': 'bullish',
                        'source': f'price_above_{t.upper()}_{p}',
                        'label': f'Цена выше {t.upper()}({p}) на {divergence:.1f}%',
                        'confidence': confidence
                    })
                else:
                    confidence = min(100, int(abs(divergence) * 5 + 50))
                    signals.append({
                        'type': 'trend', 'direction': 'bearish',
                        'source': f'price_below_{t.upper()}_{p}',
                        'label': f'Цена ниже {t.upper()}({p}) на {abs(divergence):.1f}%',
                        'confidence': confidence
                    })

        for t in ma_types:
            fast_list = self.compute_ma(closes, t, 13)
            slow_list = self.compute_ma(closes, t, 50)
            if fast_list[-1] is not None and slow_list[-1] is not None and fast_list[-2] is not None and slow_list[-2] is not None:
                if fast_list[-1] > slow_list[-1] and fast_list[-2] <= slow_list[-2]:
                    signals.append({
                        'type': 'crossover', 'direction': 'bullish',
                        'source': f'{t.upper()}_13_50_cross_above',
                        'label': f'{t.upper()} 13 / {t.upper()} 50 — пересечение вверх',
                        'confidence': 72
                    })
                elif fast_list[-1] < slow_list[-1] and fast_list[-2] >= slow_list[-2]:
                    signals.append({
                        'type': 'crossover', 'direction': 'bearish',
                        'source': f'{t.upper()}_13_50_cross_below',
                        'label': f'{t.upper()} 13 / {t.upper()} 50 — пересечение вниз',
                        'confidence': 72
                    })

        rsi_list = self.compute_rsi(closes, 14)
        rsi_last = rsi_list[-1] if rsi_list and rsi_list[-1] is not None else 50
        if rsi_last > 50:
            signals.append({
                'type': 'filter', 'direction': 'bullish',
                'source': 'rsi_above_50',
                'label': f'RSI > 50 ({rsi_last:.1f}) — подтверждение импульса',
                'confidence': 60
            })
        else:
            signals.append({
                'type': 'filter', 'direction': 'bearish',
                'source': 'rsi_below_50',
                'label': f'RSI < 50 ({rsi_last:.1f}) — ослабление импульса',
                'confidence': 60
            })

        bullish_count = sum(1 for s in signals if s['direction'] == 'bullish')
        bearish_count = sum(1 for s in signals if s['direction'] == 'bearish')
        avg_conf = np.mean([s['confidence'] for s in signals]) if signals else 0

        if bullish_count > bearish_count:
            composite = 'bullish'
        elif bearish_count > bullish_count:
            composite = 'bearish'
        else:
            composite = 'neutral'

        return {
            'symbol': '',
            'current_price': current_price,
            'signals': signals,
            'composite': composite,
            'overall_confidence': int(avg_conf),
            'bullish_signals': bullish_count,
            'bearish_signals': bearish_count,
        }

    def compute_ma_analysis(self, symbol: str, obj_id: str) -> Dict[str, Any]:
        card, days_data, raw_data = self.load_data(symbol, obj_id)
        candles = raw_data.get('candles', [])
        days = days_data.get('days', [])

        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        opens = [c['open'] for c in candles]
        volumes = [c['volume'] for c in candles]
        dates = [c.get('date', '') for c in candles]

        ma_all = self.compute_all_ma(closes, ['sma', 'ema', 'wma'], [50, 100, 200])
        ma_all.update(self.compute_all_ma(closes, ['hma', 'kama'], [50]))
        ma_all.update(self.compute_all_ma(closes, ['ema'], [13, 21, 55]))

        rsi = self.compute_rsi(closes, 14)
        macd = self.compute_macd(closes, 12, 26, 9)

        signals_data = self.ma_signal_generator(closes, dates)
        signals_data['symbol'] = symbol

        backtest_single = self.backtest_single_ma_grid(closes, ['sma', 'ema'], [50, 100, 200])
        backtest_cross = self.backtest_crossover_grid(closes, [13, 20, 50], [50, 100, 200, 250], ['sma', 'ema'])
        backtest_buffer = self.backtest_buffer_grid(closes, 'sma', 200)
        backtest_golden = self.backtest_golden_cross_grid(closes)
        backtest_decades = self.backtest_decades(closes, dates)
        backtest_crises = self.backtest_crises(closes, dates)
        backtest_triple = self.backtest_triple_ma_grid(closes)
        backtest_trail = self.backtest_trailing_grid(closes)

        return {
            'meta': {
                'symbol': symbol,
                'obj_id': obj_id,
                'current_price': closes[-1] if closes else 0,
                'total_days': len(days),
            },
            'prices': {
                'close': closes,
                'high': highs,
                'low': lows,
                'open': opens,
                'volume': volumes,
            },
            'dates': dates,
            'ma_lines': {k: v for k, v in ma_all.items()},
            'indicators': {
                'rsi': rsi,
                'macd': macd,
            },
            'signals': signals_data,
            'backtest': {
                'single_ma': {
                    'best_by_sharpe': sorted(backtest_single, key=lambda x: x.get('sharpe', 0), reverse=True)[:5],
                    'best_by_cagr': sorted(backtest_single, key=lambda x: x.get('cagr', 0), reverse=True)[:5],
                    'all': backtest_single,
                },
                'crossover': {
                    'best_by_sharpe': sorted(backtest_cross, key=lambda x: x.get('sharpe', 0), reverse=True)[:5],
                    'best_by_cagr': sorted(backtest_cross, key=lambda x: x.get('cagr', 0), reverse=True)[:5],
                    'all': backtest_cross,
                },
                'golden_cross': backtest_golden,
                'buffer_zone': backtest_buffer,
                'decades': backtest_decades,
                'crises': backtest_crises,
                'triple_ma': backtest_triple,
                'trailing_stop': backtest_trail,
            },
        }

    # ── существующие вспомогательные методы ──

    def generate_report(self, symbol: str, obj_id: str) -> Dict[str, Any]:
        card, days_data, raw_data = self.load_data(symbol, obj_id)
        days = days_data.get('days', [])
        candles = raw_data.get('candles', [])

        dates = [d['date'] for d in days]
        closes = [c['close'] for c in candles]
        highs = [c['high'] for c in candles]
        lows = [c['low'] for c in candles]
        volumes = [c['volume'] for c in candles]
        opens = [c['open'] for c in candles]

        roe_pcts = [d['roe_pct'] for d in days]

        entry_price = float(days_data.get('entry_price', card['data'].get('emoji_entry', {}).get('entry_price', 0.0)))
        leverage = int(days_data.get('leverage', card['data'].get('leverage', 10)))
        trade_volume = float(days_data.get('volume', card['data'].get('emoji_entry', {}).get('volume', 0.36)))

        volatilities = [round((d['volatility'] / closes[i]) * 100, 2) if closes[i] else 0 for i, d in enumerate(days)]
        volBxLev = [round(v * leverage, 2) for v in volatilities]
        pnl_usdts = [d['pnl_usdt'] for d in days]
        upper_wicks = [d['ohlc']['upper_wick'] for d in days]
        lower_wicks = [d['ohlc']['lower_wick'] for d in days]

        liq_price = entry_price * (1 - 1.0 / leverage) if leverage > 1 else 0

        rsi = self.compute_rsi(closes, 14)
        ema9 = self.compute_ema(closes, 9)
        ema21 = self.compute_ema(closes, 21)
        ema55 = self.compute_ema(closes, 55)
        macd = self.compute_macd(closes, 12, 26, 9)

        oi = self._simulate_oi(volumes)

        liq_days = []
        for i, c in enumerate(candles):
            risk = c['low'] < liq_price
            liq_days.append({
                'date': c['date'],
                'low': c['low'],
                'liq_price': round(liq_price, 4),
                'at_risk': risk,
                'distance_pct': round((c['low'] - liq_price) / liq_price * 100, 2),
                'simulated_liq_volume': round(volumes[i] * 0.15, 2) if risk else 0
            })

        roe_pivots = self.find_pivot_points(roe_pcts, 3)
        price_pivots = self.find_pivot_points(closes, 3)
        vol_pivots = self.find_pivot_points(volumes, 3)
        volatility_pivots = self.find_pivot_points(volatilities, 3)

        extremes = {
            'price': {'max': max(highs), 'min': min(lows),
                      'max_date': highs.index(max(highs)), 'min_date': lows.index(min(lows)),
                      'max_close': max(closes), 'min_close': min(closes),
                      'max_close_date': closes.index(max(closes)), 'min_close_date': closes.index(min(closes))},
            'roe': {'max': max(roe_pcts), 'min': min(roe_pcts),
                    'max_date': roe_pcts.index(max(roe_pcts)), 'min_date': roe_pcts.index(min(roe_pcts))},
            'volume': {'max': max(volumes), 'min': min(volumes),
                       'max_date': volumes.index(max(volumes)), 'min_date': volumes.index(min(volumes))},
            'volatility': {'max': max(volatilities), 'min': min(volatilities),
                           'max_date': volatilities.index(max(volatilities)), 'min_date': volatilities.index(min(volatilities))}
        }

        summary = days_data.get('summary', {})
        meta = {
            'symbol': symbol,
            'obj_id': obj_id,
            'entry_price': entry_price,
            'leverage': leverage,
            'volume': trade_volume,
            'liq_price': round(liq_price, 4),
            'total_days': len(days),
            'current_price': closes[-1] if closes else entry_price,
            'current_roe_pct': roe_pcts[-1] if roe_pcts else 0,
            'current_pnl_usdt': pnl_usdts[-1] if pnl_usdts else 0,
            'avg_volatility_pct': round(sum(volatilities) / len(volatilities), 2) if volatilities else 0,
        }

        return {
            'meta': meta,
            'dates': dates,
            'ohlc': {
                'open': opens,
                'high': highs,
                'low': lows,
                'close': closes,
                'volume': volumes,
                'upper_wick': upper_wicks,
                'lower_wick': lower_wicks,
            },
            'metrics': {
                'roe_pct': roe_pcts,
                'pnl_usdt': pnl_usdts,
                'volatility_pct': volatilities,
                'volatility_lev': volBxLev,
            },
            'indicators': {
                'rsi': rsi,
                'macd': macd,
                'ema9': ema9,
                'ema21': ema21,
                'ema55': ema55,
                'open_interest': oi,
            },
            'liquidation': {
                'price': round(liq_price, 4),
                'days': liq_days,
                'days_at_risk': sum(1 for d in liq_days if d['at_risk']),
            },
            'pivots': {
                'roe': self._annotate_pivots(roe_pivots, dates, roe_pcts, 'roe_pct'),
                'price': self._annotate_pivots(price_pivots, dates, closes, 'price'),
                'volume': self._annotate_pivots(vol_pivots, dates, volumes, 'volume'),
                'volatility': self._annotate_pivots(volatility_pivots, dates, volatilities, 'volatility_pct'),
            },
            'extremes': extremes,
            'summary': summary,
            'entry_dates': {
                'entry_date': days_data.get('entry_date', ''),
                'start_date': dates[0] if dates else '',
                'end_date': dates[-1] if dates else '',
            }
        }

    @staticmethod
    def _simulate_oi(volumes: List[float], decay: float = 0.92, sensitivity: float = 0.08) -> List[float]:
        arr = np.array(volumes, dtype=float)
        oi = np.zeros_like(arr)
        base = np.mean(arr[:5]) if len(arr) >= 5 else arr[0]
        oi[0] = base
        for i in range(1, len(arr)):
            vol_change = (arr[i] - np.mean(arr[max(0, i - 3):i])) / np.mean(arr[max(0, i - 3):i]) if np.mean(arr[max(0, i - 3):i]) > 0 else 0
            oi[i] = oi[i - 1] * decay + base * sensitivity * (1 + vol_change * 2)
            oi[i] = max(oi[i], base * 0.3)
        oi = oi / np.max(oi) * 100
        return [round(float(v), 2) for v in oi]

    @staticmethod
    def _annotate_pivots(pivots: List[Dict], dates: List[str], values: List, value_key: str) -> List[Dict]:
        result = []
        for p in pivots:
            idx = p['index']
            result.append({
                'index': idx,
                'date': dates[idx] if idx < len(dates) else '',
                'type': p['type'],
                value_key: round(float(p['value']), 4),
            })
        return result
