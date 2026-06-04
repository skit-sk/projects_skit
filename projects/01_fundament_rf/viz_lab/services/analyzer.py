import csv
import json
import re
from pathlib import Path
from typing import Optional


class DataProfile:
    def __init__(self):
        self.data_type: str = 'unknown'
        self.shape: tuple[int, int] = (0, 0)
        self.columns: list[dict] = []
        self.stats: dict = {}
        self.ohlcv: bool = False
        self.has_dates: bool = False
        self.has_categories: bool = False
        self.symbols: list[str] = []

    def to_dict(self) -> dict:
        return {
            'data_type': self.data_type,
            'shape': list(self.shape),
            'columns': self.columns[:5],
            'stats': self.stats,
            'ohlcv': self.ohlcv,
            'has_dates': self.has_dates,
            'has_categories': self.has_categories,
            'symbols': self.symbols,
        }


class PromptIntent:
    def __init__(self):
        self.chart_types: list[str] = []
        self.indicators: list[str] = []
        self.symbols: list[str] = []
        self.actions: list[str] = []
        self.comparison: bool = False
        self.summary: str = ''

    def to_dict(self) -> dict:
        return {
            'chart_types': self.chart_types,
            'indicators': self.indicators,
            'symbols': self.symbols,
            'actions': self.actions,
            'comparison': self.comparison,
            'summary': self.summary,
        }


class DataAnalyzer:
    CHART_KEYWORDS = {
        'candlestick': 'candlestick',
        'candle': 'candlestick',
        'line': 'line',
        'bar': 'bar',
        'area': 'area',
        'scatter': 'scatter',
        'heatmap': 'heatmap',
        'histogram': 'histogram',
        'pie': 'pie',
        'donut': 'donut',
        'box': 'box',
        'distribution': 'distribution',
        'waterfall': 'waterfall',
        'radar': 'radar',
        'sankey': 'sankey',
        'treemap': 'treemap',
        'ohlc': 'candlestick',
    }

    INDICATOR_KEYWORDS = {
        'sma': 'sma', 'ema': 'ema', 'ma': 'sma',
        'moving average': 'sma',
        'bollinger': 'bollinger', 'bb': 'bollinger',
        'rsi': 'rsi',
        'macd': 'macd',
        'volume': 'volume',
        'vwap': 'vwap',
        'atr': 'atr',
        'stochastic': 'stochastic',
        'ichimoku': 'ichimoku',
        'fibonacci': 'fibonacci',
        'support': 'support_resistance',
        'resistance': 'support_resistance',
        'trendline': 'trendline',
    }

    ACTION_KEYWORDS = {
        'compare': 'comparison',
        'vs': 'comparison',
        'versus': 'comparison',
        'difference': 'comparison',
        'correlation': 'correlation',
        'distribution': 'distribution',
        'aggregate': 'aggregation',
        'group': 'aggregation',
        'forecast': 'forecast',
        'predict': 'forecast',
        'anomaly': 'anomaly_detection',
    }

    def __init__(self):
        self._text_buffer = ''

    def analyze_file(self, file_path: str) -> DataProfile:
        path = Path(file_path)
        if not path.exists():
            return DataProfile()

        ext = path.suffix.lower()
        if ext == '.csv':
            return self._analyze_csv(path)
        elif ext == '.json':
            return self._analyze_json(path)
        elif ext in ('.png', '.jpg', '.jpeg', '.gif', '.svg'):
            return self._analyze_image(path)
        return DataProfile()

    def analyze_text(self, text: str) -> PromptIntent:
        intent = PromptIntent()
        text_lower = text.lower()
        self._text_buffer = text_lower

        intent.chart_types = self._find_keywords(text_lower, self.CHART_KEYWORDS)
        intent.indicators = self._find_keywords(text_lower, self.INDICATOR_KEYWORDS)
        intent.actions = self._find_keywords(text_lower, self.ACTION_KEYWORDS)
        intent.comparison = 'comparison' in intent.actions or 'vs' in text_lower.split()
        intent.symbols = self._extract_symbols(text)
        intent.summary = self._build_summary(intent)

        return intent

    def classify(self, profile: DataProfile, intent: PromptIntent) -> dict:
        result = {
            'primary_type': 'unknown',
            'complexity': 'simple',
            'suggested_models': [],
            'description': '',
        }

        if profile.ohlcv:
            result['primary_type'] = 'ohlcv'
            result['complexity'] = 'medium'
            result['description'] = 'OHLCV financial data'
            result['suggested_models'] = ['tv-screenshot', 'gemini-2.5-flash']
        elif profile.has_dates and profile.shape[1] >= 2:
            result['primary_type'] = 'timeseries'
            result['complexity'] = 'simple'
            result['description'] = 'Time series data'
            result['suggested_models'] = ['deepseek-free', 'gemini-2.5-flash']
        elif profile.has_categories and profile.shape[1] >= 2:
            result['primary_type'] = 'categorical'
            result['complexity'] = 'simple'
            result['description'] = 'Categorical data'
            result['suggested_models'] = ['deepseek-free']
        elif intent.chart_types:
            result['primary_type'] = intent.chart_types[0]
            result['complexity'] = 'medium'
            result['description'] = f"Requested: {', '.join(intent.chart_types)}"
            result['suggested_models'] = ['deepseek-free', 'gemini-2.5-flash']

        if intent.comparison:
            result['primary_type'] += '_comparison'
            result['complexity'] = 'medium'
            if 'deepseek-free' in result['suggested_models']:
                result['suggested_models'].insert(0, 'gemini-2.5-flash')

        if intent.indicators:
            result['complexity'] = 'complex'
            result['description'] += f" with {', '.join(intent.indicators)}"

        return result

    def _analyze_csv(self, path: Path) -> DataProfile:
        profile = DataProfile()
        try:
            with open(path, newline='', encoding='utf-8', errors='replace') as f:
                reader = csv.reader(f)
                rows = list(reader)
            if not rows:
                return profile

            header = rows[0]
            data = rows[1:]
            profile.shape = (len(data), len(header))

            profile.columns = self._classify_columns(header, data)
            profile.ohlcv = self._detect_ohlcv(header)
            profile.has_dates = any(c['type'] == 'date' for c in profile.columns)
            profile.has_categories = any(c['type'] == 'category' for c in profile.columns)

            if profile.ohlcv:
                profile.data_type = 'ohlcv'
            elif profile.has_dates:
                profile.data_type = 'timeseries'
            elif profile.has_categories:
                profile.data_type = 'categorical'
            else:
                profile.data_type = 'tabular'

            profile.stats = self._compute_stats(profile.columns, data)

        except Exception:
            pass
        return profile

    def _analyze_json(self, path: Path) -> DataProfile:
        profile = DataProfile()
        try:
            with open(path, encoding='utf-8', errors='replace') as f:
                data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                profile.shape = (len(data), len(data[0]) if isinstance(data[0], dict) else 1)
                if isinstance(data[0], dict):
                    header = list(data[0].keys())
                    profile.columns = self._classify_columns(header, [[str(v) for v in row.values()] for row in data])
                    profile.ohlcv = self._detect_ohlcv(header)
                    profile.data_type = 'tabular'
            elif isinstance(data, dict):
                profile.shape = (len(data), 2)
                profile.data_type = 'key_value'
        except Exception:
            pass
        return profile

    def _analyze_image(self, path: Path) -> DataProfile:
        profile = DataProfile()
        profile.data_type = 'image'
        profile.stats = {'format': path.suffix[1:], 'size_bytes': path.stat().st_size}
        return profile

    def _classify_columns(self, header: list[str], data: list[list[str]]) -> list[dict]:
        columns = []
        for i, name in enumerate(header):
            col_type = self._infer_column_type([row[i] for row in data if i < len(row)])
            columns.append({'name': name, 'type': col_type, 'index': i})
        return columns

    def _infer_column_type(self, values: list[str]) -> str:
        numbers = 0
        dates = 0
        for v in values:
            v = v.strip()
            if not v:
                continue
            if re.match(r'^-?\d+\.?\d*$', v):
                numbers += 1
            elif re.match(r'^\d{4}[-/]\d{1,2}[-/]\d{1,2}', v):
                dates += 1
        total = max(len([v for v in values if v.strip()]), 1)
        if numbers / total > 0.7:
            return 'numeric'
        if dates / total > 0.7:
            return 'date'
        return 'category'

    def _detect_ohlcv(self, header: list[str]) -> bool:
        h = [c.lower().strip() for c in header]
        ohlcv_keywords = {'open', 'high', 'low', 'close', 'volume'}
        found = sum(1 for kw in ohlcv_keywords if any(kw in col for col in h))
        return found >= 4

    def _compute_stats(self, columns: list[dict], data: list[list[str]]) -> dict:
        stats = {}
        for col in columns:
            if col['type'] == 'numeric':
                vals = []
                for row in data:
                    if col['index'] < len(row):
                        try:
                            vals.append(float(row[col['index']]))
                        except ValueError:
                            pass
                if vals:
                    stats[col['name']] = {
                        'min': min(vals),
                        'max': max(vals),
                        'mean': sum(vals) / len(vals),
                        'count': len(vals),
                    }
        return stats

    def _find_keywords(self, text: str, keywords: dict) -> list[str]:
        found = []
        for word, category in keywords.items():
            if len(word) <= 3:
                pattern = r'\b' + re.escape(word) + r'\b'
            else:
                pattern = re.escape(word)
            if re.search(pattern, text):
                if category not in found:
                    found.append(category)
        return found

    def _extract_symbols(self, text: str) -> list[str]:
        symbols = re.findall(r'\b[A-Z]{2,10}\b', text.upper())
        known = {'BTC', 'ETH', 'SOL', 'BNB', 'ADA', 'XRP', 'DOT', 'DOGE', 'AVAX', 'LINK',
                 'MATIC', 'UNI', 'ATOM', 'LTC', 'BCH', 'FIL', 'APT', 'SUI', 'OP', 'ARB',
                 'BTCUSDT', 'ETHUSDT', 'SOLUSDT', 'BNBUSDT'}
        return [s for s in symbols if s in known]

    def _build_summary(self, intent: PromptIntent) -> str:
        parts = []
        if intent.chart_types:
            parts.append(f"chart: {', '.join(intent.chart_types)}")
        if intent.indicators:
            parts.append(f"indicators: {', '.join(intent.indicators)}")
        if intent.symbols:
            parts.append(f"symbols: {', '.join(intent.symbols)}")
        if intent.comparison:
            parts.append('comparison mode')
        return ' | '.join(parts) if parts else 'general request'


analyzer = DataAnalyzer()


def get_analyzer() -> DataAnalyzer:
    return analyzer
