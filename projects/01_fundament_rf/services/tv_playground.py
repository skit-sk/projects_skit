import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from services.market_data_provider import fetch_ohlcv, detect_symbol_type

STATIC_ROOT = Path('/home/user_aioc/workspace/projects/01_fundament_rf/static/sandbox/04')
DEFAULT_WIDGET = 'widgets/charts/advanced-chart/index.html'


def widget_path_to_full(path: str) -> Path:
    """Resolve widget path under static/sandbox/04."""
    if not path:
        path = DEFAULT_WIDGET
    return STATIC_ROOT / path


def is_tradingview_widget(html: str) -> bool:
    return 'TradingView.widget' in html or 'tradingview-widget-container' in html


def is_lightweight_chart(html: str) -> bool:
    return 'createChart' in html or 'LightweightCharts' in html or 'lightweight-charts' in html


def extract_tv_widget_config(html: str) -> Optional[Dict[str, Any]]:
    """Extract TradingView.widget({...}) config from HTML."""
    m = re.search(r'new\s+TradingView\.widget\(\s*(\{.*?\})\s*\)', html, re.DOTALL)
    if not m:
        return None
    config_str = m.group(1)
    # Try to parse as JSON (handles simple configs)
    try:
        return json.loads(config_str)
    except json.JSONDecodeError:
        # Fallback: regex key-value extraction
        config = {}
        for km in re.finditer(r'"(\w+)"\s*:\s*"([^"]*)"', config_str):
            config[km.group(1)] = km.group(2)
        for km in re.finditer(r'"(\w+)"\s*:\s*(true|false|\d+)', config_str):
            config[km.group(1)] = json.loads(km.group(2))
        return config


EMBED_WIDGET_RE = re.compile(
    r'<script([^>]*)src="([^"]*embed-widget-[^"]*)"([^>]*)>(.*?)</script>',
    re.IGNORECASE | re.DOTALL,
)


def is_embed_tv_widget(html: str) -> bool:
    """Detect vendorized TradingView embed-widget script with inline JSON config."""
    return EMBED_WIDGET_RE.search(html) is not None


def extract_embed_tv_config(html: str) -> Tuple[Optional[str], Optional[Dict[str, Any]]]:
    """Extract src and config dict from an embed-widget <script> tag."""
    m = EMBED_WIDGET_RE.search(html)
    if not m:
        return None, None
    raw_json = m.group(4).strip()
    try:
        return m.group(2), json.loads(raw_json)
    except Exception:
        return m.group(2), {}


def update_embed_tv_widget(html: str, params: Dict[str, Any]) -> str:
    """Update embed-widget inline JSON config with user params and return new HTML."""
    m = EMBED_WIDGET_RE.search(html)
    if not m:
        return html
    src = m.group(2)
    raw_json = m.group(4)
    try:
        config = json.loads(raw_json.strip())
    except Exception:
        config = {}

    for key in ['symbol', 'interval', 'theme', 'locale', 'autosize', 'width', 'height',
                'timezone', 'style', 'range', 'hide_top_toolbar', 'hide_legend',
                'hide_side_toolbar', 'save_image', 'calendar', 'details']:
        if key in params:
            config[key] = params[key]

    new_json = json.dumps(config, ensure_ascii=False, indent=4)
    # Preserve original whitespace envelope around JSON
    prefix = raw_json[:len(raw_json) - len(raw_json.lstrip())]
    suffix = raw_json[len(raw_json.rstrip()):]
    replacement = prefix + new_json + suffix
    return html[:m.start(4)] + replacement + html[m.end(4):]


def build_tv_widget_html(config: Dict[str, Any], params: Dict[str, Any]) -> Tuple[str, str]:
    """Generate TradingView widget HTML and code preview."""
    cfg = dict(config)
    # Apply params
    for key in ['symbol', 'interval', 'theme', 'locale', 'autosize', 'width', 'height',
                'timezone', 'style', 'range', 'hide_top_toolbar', 'hide_legend',
                'hide_side_toolbar', 'save_image', 'calendar', 'details']:
        if key in params:
            cfg[key] = params[key]
    
    # Ensure container_id exists
    container_id = cfg.get('container_id', 'tv-chart-container')
    cfg['container_id'] = container_id
    
    html = f'''<!-- TradingView Widget BEGIN -->
<div class="tradingview-widget-container">
  <div id="{container_id}"></div>
  <script type="text/javascript" src="/static/vendor/tradingview/tv.js"></script>
  <script type="text/javascript">
  new TradingView.widget({json.dumps(cfg, ensure_ascii=False, indent=4)});
  </script>
</div>
<!-- TradingView Widget END -->'''
    
    return html, html


def extract_lightweight_data(html: str) -> Optional[list]:
    """Try to extract data array from Lightweight Charts example."""
    m = re.search(r'setData\(\s*(\[[\s\S]*?\])\s*\)', html)
    if m:
        try:
            return json.loads(m.group(1))
        except Exception:
            pass
    return None


def build_lightweight_html(original_html: str, params: Dict[str, Any]) -> Tuple[str, str]:
    """Generate Lightweight Charts HTML with real data and code preview."""
    symbol = params.get('symbol', 'BTCUSDT')
    interval = params.get('interval', '1D')
    theme = params.get('theme', 'dark')
    series_type = params.get('seriesType', 'candlestick')
    active_sources = params.get('active_sources', ['binance', 'bitget', 'yahoo', 'synthetic'])
    limit = int(params.get('limit', 200))
    
    # Fetch data
    ohlcv_result = fetch_ohlcv(symbol, interval, limit, active_sources)
    data = ohlcv_result['data']
    
    # Determine time format for Lightweight Charts
    # Lightweight expects 'yyyy-mm-dd' for D+ and Unix timestamp for intraday
    use_timestamp = interval not in ('D', '1D', 'W', '1W', 'M', '1M')
    from datetime import datetime
    chart_data = []
    for row in data:
        if use_timestamp:
            ts = int(datetime.strptime(row['time'], '%Y-%m-%d %H:%M:%S').timestamp())
            item = {'time': ts}
        else:
            item = {'time': row['time'][:10]}
        if series_type in ('candlestick', 'bar'):
            item.update({
                'open': row['open'],
                'high': row['high'],
                'low': row['low'],
                'close': row['close']
            })
        elif series_type in ('line', 'area', 'baseline'):
            item['value'] = row['close']
        elif series_type == 'histogram':
            item['value'] = row['volume']
        chart_data.append(item)
    
    data_json = json.dumps(chart_data, ensure_ascii=False)
    
    bg = '#131722' if theme == 'dark' else '#ffffff'
    text = '#d1d4dc' if theme == 'dark' else '#131722'
    grid = '#2a2e39' if theme == 'dark' else '#e0e3eb'
    
    html = f'''<!DOCTYPE html>
<html>
<head>
  <meta charset="UTF-8">
  <title>{symbol} — {series_type}</title>
  <script src="/static/vendor/lightweight-charts@5.2.0/lightweight-charts.standalone.production.js"
    onerror="document.getElementById('status').textContent='Failed to load lightweight-charts script'; document.getElementById('status').style.color='#f85149';"></script>
  <style>html, body {{ width:100%; height:100%; margin:0; background:{bg}; }} #status {{ font-family:monospace; padding:1rem; color:#888; }} #chart {{ width:100%; height:100%; }}</style>
</head>
<body>
  <div id="status">Loading chart script...</div>
  <div id="chart"></div>
  <script>
    document.getElementById('status').textContent = 'Script loaded, creating chart...';
    (function() {{
      try {{
        const chartEl = document.getElementById('chart');
        const chart = LightweightCharts.createChart(chartEl, {{
          width: chartEl.clientWidth || window.innerWidth,
          height: chartEl.clientHeight || window.innerHeight,
          layout: {{ background: {{ type: 'solid', color: '{bg}' }}, textColor: '{text}' }},
          grid: {{ vertLines: {{ color: '{grid}' }}, horzLines: {{ color: '{grid}' }} }},
          rightPriceScale: {{ borderColor: '{grid}' }},
          timeScale: {{ borderColor: '{grid}' }},
        }});
        const {{ CandlestickSeries, LineSeries, AreaSeries, BarSeries, HistogramSeries, BaselineSeries }} = LightweightCharts;
        document.getElementById('status').textContent = 'Chart created, adding data...';
        const data = {data_json};
        let series;
        if ('{series_type}' === 'candlestick') {{
          series = chart.addSeries(CandlestickSeries, {{ upColor: '#26a69a', downColor: '#ef5350', borderVisible: false, wickUpColor: '#26a69a', wickDownColor: '#ef5350' }});
        }} else if ('{series_type}' === 'line') {{
          series = chart.addSeries(LineSeries, {{ color: '#2962FF', lineWidth: 2 }});
        }} else if ('{series_type}' === 'area') {{
          series = chart.addSeries(AreaSeries, {{ lineColor: '#2962FF', topColor: 'rgba(41,98,255,0.4)', bottomColor: 'rgba(41,98,255,0.05)' }});
        }} else if ('{series_type}' === 'bar') {{
          series = chart.addSeries(BarSeries, {{ upColor: '#26a69a', downColor: '#ef5350' }});
        }} else if ('{series_type}' === 'histogram') {{
          series = chart.addSeries(HistogramSeries, {{ color: '#2962FF' }});
        }} else if ('{series_type}' === 'baseline') {{
          series = chart.addSeries(BaselineSeries, {{}});
        }}
        series.setData(data);
        chart.timeScale().fitContent();
        document.getElementById('status').style.display = 'none';
        window.addEventListener('resize', () => chart.applyOptions({{ width: chartEl.clientWidth || window.innerWidth, height: chartEl.clientHeight || window.innerHeight }}));
      }} catch (e) {{
        console.error('Lightweight chart error:', e);
        const status = document.getElementById('status');
        status.style.color = '#f85149';
        status.textContent = 'Lightweight chart error: ' + e.message + '\\n' + (e.stack || '');
      }}
    }})();
  </script>
</body>
</html>'''
    
    return html, html


def render_widget(widget_path: str, params: Dict[str, Any]) -> Dict[str, Any]:
    """Render a widget with given params. Returns html and metadata."""
    full_path = widget_path_to_full(widget_path)
    if not full_path.exists():
        return {'error': f'Widget not found: {widget_path}', 'html': '', 'code': ''}
    
    html = full_path.read_text(encoding='utf-8')

    if is_embed_tv_widget(html):
        src, config = extract_embed_tv_config(html)
        rendered = update_embed_tv_widget(html, params)
        return {
            'type': 'tradingview_embed_widget',
            'html': rendered,
            'code': rendered,
            'config': config or {}
        }
    elif is_tradingview_widget(html):
        config = extract_tv_widget_config(html) or {}
        rendered, code = build_tv_widget_html(config, params)
        return {
            'type': 'tradingview_widget',
            'html': rendered,
            'code': code,
            'config': config
        }
    elif is_lightweight_chart(html):
        rendered, code = build_lightweight_html(html, params)
        return {
            'type': 'lightweight_chart',
            'html': rendered,
            'code': code
        }
    else:
        # Fallback: just serve original with absolute URLs
        return {
            'type': 'original',
            'html': html,
            'code': html
        }


def get_default_params(widget_path: str) -> Dict[str, Any]:
    """Extract default params from original widget for initial form values."""
    full_path = widget_path_to_full(widget_path)
    if not full_path.exists():
        return {}
    html = full_path.read_text(encoding='utf-8')
    params = {
        'symbol': 'BTCUSDT',
        'interval': '1D',
        'theme': 'dark',
        'seriesType': 'candlestick',
        'active_sources': ['binance', 'bitget', 'yahoo', 'synthetic'],
        'limit': 200
    }
    
    if is_embed_tv_widget(html):
        _, config = extract_embed_tv_config(html)
    elif is_tradingview_widget(html):
        config = extract_tv_widget_config(html) or {}
    else:
        config = {}

    if 'symbol' in config:
        params['symbol'] = config['symbol']
    if 'interval' in config:
        params['interval'] = config['interval']
    if 'theme' in config:
        params['theme'] = config['theme']

    return params
