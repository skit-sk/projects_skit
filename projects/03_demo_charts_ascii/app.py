import json, os, sys, re
from pathlib import Path
from flask import Flask, render_template, request, jsonify, send_from_directory

app = Flask(__name__)
BASE_DIR = os.path.dirname(__file__)
DATA_DIR = os.path.join(BASE_DIR, 'data')


def strip_ansi(text: str) -> str:
    """Remove ANSI escape sequences for clean HTML display."""
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

# Vercel: /var/task is read-only — writes must go to /tmp
OUTPUT_DIR = os.environ.get('DEMO_OUTPUT_DIR', '/tmp/outputs')
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Pre-generated infographics directory (read-only, committed)
PREBUILT_DIR = os.path.join(BASE_DIR, 'outputs')


def _resolve_output(symbol, filename):
    """Find file in /tmp first, then fallback to committed prebuilt."""
    tmp_path = os.path.join(OUTPUT_DIR, symbol, filename)
    if os.path.exists(tmp_path):
        return tmp_path
    prebuilt = os.path.join(PREBUILT_DIR, symbol, filename)
    if os.path.exists(prebuilt):
        return prebuilt
    return None


# ─── Data helpers ─────────────────────────────────────────────────────────

def _find_card_dir(symbol: str) -> Path:
    """Find the card directory for a symbol."""
    # Project-local data/ (committed for Vercel)
    card_dir = Path(BASE_DIR) / "data"
    if card_dir.exists():
        for subdir in card_dir.iterdir():
            if subdir.is_dir() and subdir.name.startswith(symbol + "_"):
                return subdir
    # Fallback to fundament_rf (local dev)
    card_dir = Path(BASE_DIR).parent / "01_fundament_rf" / "data" / "card"
    if card_dir.exists():
        for subdir in card_dir.iterdir():
            if subdir.is_dir() and subdir.name.startswith(symbol + "_"):
                return subdir
    return None


def _load_card_json(symbol: str):
    """Load the main JSON for a symbol."""
    d = _find_card_dir(symbol)
    if not d:
        return None
    for f in d.glob("*.json"):
        if not f.name.endswith(("_1D.json", "_RAW.json")):
            with open(f, 'r', encoding='utf-8') as fp:
                return json.load(fp)
    return None


def _load_1d_json(symbol: str):
    """Load the _1D.json for a symbol."""
    d = _find_card_dir(symbol)
    if not d:
        return None
    f = d / f"{d.name.split('_')[1]}_1D.json" if '_' in d.name else None
    if f and f.exists():
        with open(f, 'r', encoding='utf-8') as fp:
            return json.load(fp)
    # fallback: any _1D.json
    for f in d.glob("*_1D.json"):
        with open(f, 'r', encoding='utf-8') as fp:
            return json.load(fp)
    return None


# ─── Existing routes ──────────────────────────────────────────────────────

def build_file_tree():
    tree = []
    for d in sorted(os.listdir(DATA_DIR)):
        dp = os.path.join(DATA_DIR, d)
        if not os.path.isdir(dp):
            continue
        files = sorted(f for f in os.listdir(dp) if f.endswith('.json'))
        if files:
            sym = d.split('_')[0]
            children = [{'name': f, 'path': os.path.join(dp, f)} for f in files]
            tree.append({'name': d, 'symbol': sym, 'path': dp, 'children': children})
    return tree


@app.route('/')
def index():
    return render_template('index.html', tree=build_file_tree())


@app.route('/render', methods=['POST'])
def render():
    data_path = request.json.get('file_path', '')
    tools = request.json.get('tools', [])
    if not data_path or not os.path.exists(data_path):
        return jsonify({'error': 'File not found'})
    results = {}
    for tool in tools:
        try:
            if tool == 'asciichart':
                from generators.asciichart_gen import generate as gen
                results[tool] = gen(data_path, OUTPUT_DIR)
            elif tool == 'plotext':
                from generators.plotext_gen import generate as gen
                results[tool] = gen(data_path, OUTPUT_DIR)
            elif tool == 'termgraph':
                from generators.termgraph_gen import generate as gen
                results[tool] = gen(data_path, OUTPUT_DIR)
        except Exception as e:
            results[tool] = {'error': str(e)}
    if 'summary' in tools:
        try:
            from generators.summary_gen import generate as gen_s
            results['summary'] = gen_s(data_path, OUTPUT_DIR)
        except Exception as e:
            results['summary'] = {'error': str(e)}
    return jsonify(results)


@app.route('/file/<path:filepath>')
def serve_file(filepath):
    full = os.path.join(OUTPUT_DIR, filepath)
    if os.path.exists(full):
        with open(full) as f:
            return f.read()
    return 'File not found', 404


@app.route('/infographics/<symbol>')
def infographics(symbol):
    """Отобразить все ASCII инфографики для символа (ANSI stripped for HTML)."""
    files = {}
    for name in ['candlestick', 'deviation', 'histogram', 'box_plot',
                 'range_bar', 'heatmap', 'indicator', 'subplot_grid',
                 'radar', 'waterfall', 'pareto', 'sankey', 'treemap', 'indicators']:
        fpath = _resolve_output(symbol, f"{name}.txt")
        if fpath:
            with open(fpath, 'r', encoding='utf-8') as f:
                files[name] = strip_ansi(f.read())
        else:
            files[name] = f"[{name} not generated]"
    return render_template('infographics.html', symbol=symbol, files=files)


@app.route('/infographics/<symbol>/<model>')
def infographic_model(symbol, model):
    """Отдать один файл инфографики."""
    fpath = _resolve_output(symbol, f"{model}.txt")
    if fpath:
        with open(fpath, 'r', encoding='utf-8') as f:
            return f.read(), 200, {'Content-Type': 'text/plain; charset=utf-8'}
    return 'Not found', 404


# ─── NEW: Interactive web chart routes ────────────────────────────────────

def _get_chart_data(symbol: str) -> dict:
    """Load all chart data for a symbol."""
    obj = _load_card_json(symbol)
    days_1d = _load_1d_json(symbol)
    if not obj:
        return {}

    result = {
        'symbol': symbol,
        'entry_price': obj['data']['emoji_entry']['entry_price'],
        'current_price': obj['data']['emoji_upd']['current_price'],
        'roe_usdt': obj['data']['emoji_upd'].get('roe_usdt', 0),
        'pnl_usdt': obj['data']['emoji_upd'].get('pnl_usdt', 0),
        'pnl_percent': obj['data']['emoji_upd'].get('pnl_percent', 0),
        'leverage': obj['data'].get('leverage', 10),
    }

    if days_1d and 'days' in days_1d:
        days = days_1d['days']
        result['dates'] = [d['date'] for d in days]
        result['open'] = [d['ohlc']['open'] for d in days]
        result['high'] = [d['ohlc']['high'] for d in days]
        result['low'] = [d['ohlc']['low'] for d in days]
        result['close'] = [d['ohlc']['close'] for d in days]
        result['volume'] = [d.get('volatility', 0) for d in days]
        result['pnl_daily'] = [d.get('pnl_usdt', 0) for d in days]

        import indicators as ind
        ind_data = ind.compute_all_indicators(days)
        result['indicators'] = {
            'sma5': ind_data.get('sma5'),
            'sma20': ind_data.get('sma20'),
            'sma200': ind_data.get('sma200'),
            'bb_upper': ind_data.get('bb_upper'),
            'bb_lower': ind_data.get('bb_lower'),
            'bb_middle': ind_data.get('bb_middle'),
            'rsi': ind_data.get('rsi'),
            'macd': ind_data.get('macd'),
            'macd_signal': ind_data.get('macd_signal'),
            'macd_histogram': ind_data.get('macd_histogram'),
            'anomalies': ind_data.get('anomalies'),
        }

        ohlc = obj['data']['ohlc']
        roe = obj['data']['emoji_upd'].get('roe_usdt', 0)
        mx_pct = ohlc['max'].get('pct', 0)
        mn_pct = ohlc['min'].get('pct', 0)
        result['radar'] = {
            'body': min(1.0, abs(ohlc['current'].get('body_pct', 0)) / 10),
            'upper_wick': min(1.0, ohlc['current'].get('upper_wick', 0) / 0.001),
            'lower_wick': min(1.0, ohlc['current'].get('lower_wick', 0) / 0.001),
            'volatility': min(1.0, ohlc['max'].get('volatility', 0) * 1000),
            'range': min(1.0, (mx_pct - mn_pct) / 100) if mx_pct != mn_pct else 0,
            'roe': min(1.0, abs(roe) / 100),
        }

        rows, cols = 10, max(len(days) // 10, 7)
        vol_matrix = []
        pnl_matrix = []
        for r in range(rows):
            vrow = []
            prow = []
            for c in range(cols):
                idx = min(len(days) - 1, r * cols + c)
                vrow.append(days[idx].get('volatility', 0))
                prow.append(days[idx].get('roe_pct', 0))
            vol_matrix.append(vrow)
            pnl_matrix.append(prow)
        result['vol_matrix'] = vol_matrix
        result['pnl_matrix'] = pnl_matrix
    else:
        result['dates'] = []
        result['close'] = []
        result['indicators'] = {}
        result['radar'] = {}
        result['vol_matrix'] = []
        result['pnl_matrix'] = []

    return result


@app.route('/interactive/<symbol>')
def interactive_plotly(symbol):
    data = _get_chart_data(symbol)
    return render_template('plotly_chart.html', symbol=symbol, data=data)


@app.route('/chartjs/<symbol>')
def interactive_chartjs(symbol):
    data = _get_chart_data(symbol)
    return render_template('chartjs_view.html', symbol=symbol, data=data)


@app.route('/deckgl/<symbol>')
def interactive_deckgl(symbol):
    data = _get_chart_data(symbol)
    return render_template('deckgl_view.html', symbol=symbol, data=data)


# ─── NEW: ASCII-new route (renders new types on-the-fly) ──────────────────

@app.route('/ascii-new/<symbol>')
def ascii_new(symbol):
    """Render new ASCII types on-the-fly (radar, waterfall, pareto, sankey, treemap, indicators)."""
    os.environ["DEMO_OUTPUT_DIR"] = OUTPUT_DIR
    import charts as ch
    obj_id = None
    # find obj_id from card dir
    d = _find_card_dir(symbol)
    if d:
        for f in d.glob("*.json"):
            if not f.name.endswith(("_1D.json", "_RAW.json")):
                obj_id = f.stem
                break

    files = {}
    if obj_id:
        for name in ['radar', 'waterfall', 'pareto', 'sankey', 'treemap', 'indicators']:
            try:
                path = ch.generate_single(obj_id, name)
                with open(path, 'r', encoding='utf-8') as f:
                    files[name] = strip_ansi(f.read())
            except Exception as e:
                files[name] = f"[{name} error: {e}]"
    else:
        for name in ['radar', 'waterfall', 'pareto', 'sankey', 'treemap', 'indicators']:
            files[name] = f"[{name} not generated — no card data]"

    return render_template('infographics.html', symbol=symbol, files=files)


# ─── NEW: API data endpoint ───────────────────────────────────────────────

@app.after_request
def add_cors_headers(response):
    response.headers['Access-Control-Allow-Origin'] = '*'
    response.headers['Access-Control-Allow-Headers'] = 'Content-Type,Authorization'
    response.headers['Access-Control-Allow-Methods'] = 'GET,POST,OPTIONS'
    return response


@app.route('/api/data/<symbol>')
def api_data(symbol):
    """Return comprehensive JSON for a symbol: OHLCV, indicators, radar, matrices."""
    obj = _load_card_json(symbol)
    days_1d = _load_1d_json(symbol)

    if not obj:
        return jsonify({'error': f'No data for {symbol}'}), 404

    result = {
        'symbol': symbol,
        'entry_price': obj['data']['emoji_entry']['entry_price'],
        'current_price': obj['data']['emoji_upd']['current_price'],
        'roe_usdt': obj['data']['emoji_upd'].get('roe_usdt', 0),
        'pnl_usdt': obj['data']['emoji_upd'].get('pnl_usdt', 0),
        'pnl_percent': obj['data']['emoji_upd'].get('pnl_percent', 0),
        'leverage': obj['data'].get('leverage', 10),
    }

    if days_1d and 'days' in days_1d:
        days = days_1d['days']
        result['dates'] = [d['date'] for d in days]
        result['open'] = [d['ohlc']['open'] for d in days]
        result['high'] = [d['ohlc']['high'] for d in days]
        result['low'] = [d['ohlc']['low'] for d in days]
        result['close'] = [d['ohlc']['close'] for d in days]
        result['volume'] = [d.get('volatility', 0) for d in days]
        result['pnl_daily'] = [d.get('pnl_usdt', 0) for d in days]

        # Indicators
        import indicators as ind
        ind_data = ind.compute_all_indicators(days)
        result['indicators'] = {
            'sma5': ind_data.get('sma5'),
            'sma20': ind_data.get('sma20'),
            'sma200': ind_data.get('sma200'),
            'bb_upper': ind_data.get('bb_upper'),
            'bb_lower': ind_data.get('bb_lower'),
            'bb_middle': ind_data.get('bb_middle'),
            'rsi': ind_data.get('rsi'),
            'macd': ind_data.get('macd'),
            'macd_signal': ind_data.get('macd_signal'),
            'macd_histogram': ind_data.get('macd_histogram'),
            'anomalies': ind_data.get('anomalies'),
        }

        # Radar data
        ohlc = obj['data']['ohlc']
        roe = obj['data']['emoji_upd'].get('roe_usdt', 0)
        mx_pct = ohlc['max'].get('pct', 0)
        mn_pct = ohlc['min'].get('pct', 0)
        result['radar'] = {
            'body': min(1.0, abs(ohlc['current'].get('body_pct', 0)) / 10),
            'upper_wick': min(1.0, ohlc['current'].get('upper_wick', 0) / 0.001),
            'lower_wick': min(1.0, ohlc['current'].get('lower_wick', 0) / 0.001),
            'volatility': min(1.0, ohlc['max'].get('volatility', 0) * 1000),
            'range': min(1.0, (mx_pct - mn_pct) / 100) if mx_pct != mn_pct else 0,
            'roe': min(1.0, abs(roe) / 100),
        }

        # Matrices for Deck.gl
        rows, cols = 10, max(len(days) // 10, 7)
        vol_matrix = []
        pnl_matrix = []
        for r in range(rows):
            vrow = []
            prow = []
            for c in range(cols):
                idx = min(len(days) - 1, r * cols + c)
                vrow.append(days[idx].get('volatility', 0))
                prow.append(days[idx].get('roe_pct', 0))
            vol_matrix.append(vrow)
            pnl_matrix.append(prow)
        result['vol_matrix'] = vol_matrix
        result['pnl_matrix'] = pnl_matrix
    else:
        result['dates'] = []
        result['close'] = []
        result['indicators'] = {}
        result['radar'] = {}
        result['vol_matrix'] = []
        result['pnl_matrix'] = []

    return jsonify(result)


@app.route('/api/indicators/<symbol>')
def api_indicators(symbol):
    """Return only indicator summary."""
    days_1d = _load_1d_json(symbol)
    if not days_1d or 'days' not in days_1d:
        return jsonify({'error': f'No daily data for {symbol}'}), 404

    import indicators as ind
    days = days_1d['days']
    ind_data = ind.compute_all_indicators(days)
    summary = ind.indicator_summary(ind_data)
    return jsonify(summary)


@app.route('/debug/deps')
def debug_deps():
    """Check which chart libraries are available."""
    import sys
    deps = {}
    for mod in ['plotext', 'plotille', 'asciichart', 'numpy']:
        try:
            m = __import__(mod)
            deps[mod] = getattr(m, '__version__', 'installed')
        except Exception as e:
            deps[mod] = f"error: {e}"
    # Check ascii_charts module state
    try:
        import ascii_charts as ac
        deps['ascii_charts_plt'] = 'None' if ac.plt is None else 'ok'
        deps['ascii_charts_plotille'] = 'None' if ac.plotille is None else 'ok'
    except Exception as e:
        deps['ascii_charts_import'] = f"error: {e}"
    deps['python_version'] = sys.version
    deps['data_dir_exists'] = os.path.exists(DATA_DIR)
    deps['fundament_dir'] = str(Path(BASE_DIR) / "data")
    deps['fundament_exists'] = os.path.exists(Path(BASE_DIR) / "data")
    return jsonify(deps)


if __name__ == '__main__':
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=True, host='0.0.0.0', port=port)
