"""Flask application for trading dashboard."""

import sys
from flask import Flask, render_template, jsonify, request
from data import MarketDataFetcher, generate_test_data, detect_patterns, pattern_to_dict
from data.generator import generate_test_pnl
from charts import create_candlestick_chart, create_pnl_chart, create_combined_chart
from charts.svg_charts import generate_svg_candlestick, generate_svg_pnl, generate_svg_combined


app = Flask(__name__)

fetcher = MarketDataFetcher()


@app.route('/')
def index():
    return render_template('alt.html')


@app.route('/plotly')
def plotly_page():
    return render_template('index.html')


@app.route('/svg')
def svg_page():
    return render_template('alt.html')


@app.route('/api/symbols')
def api_symbols():
    try:
        symbols = fetcher.get_symbols()
        return jsonify(symbols)
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/candles')
def api_candles():
    symbol = request.args.get('symbol', 'BTCUSDT')
    timeframe = request.args.get('timeframe', '1d')
    limit = int(request.args.get('limit', 90))
    
    try:
        candles = fetcher.fetch_candles(symbol, timeframe, limit)
        if not candles:
            candles = generate_test_data(symbol, limit)
        return jsonify(candles)
    except Exception as e:
        candles = generate_test_data(symbol, limit)
        return jsonify(candles)


@app.route('/api/patterns')
def api_patterns():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        return jsonify([pattern_to_dict(p) for p in patterns])
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        return jsonify([pattern_to_dict(p) for p in patterns])


@app.route('/api/pnl')
def api_pnl():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        return jsonify(pnl_data)
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        return jsonify(pnl_data)


@app.route('/api/summary')
def api_summary():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        last = candles[-1]
        prev = candles[-2] if len(candles) > 1 else last
        price_change = last['close'] - prev['close']
        price_change_pct = (price_change / prev['close'] * 100) if prev['close'] != 0 else 0
        return jsonify({
            'symbol': symbol,
            'currentPrice': last['close'],
            'priceChange24h': round(price_change, 2),
            'priceChangePct24h': round(price_change_pct, 2),
            'volume24h': last['volume'],
            'totalPnl': pnl_data['totalPnl'],
            'winRate': pnl_data['winRate'],
            'sharpeRatio': pnl_data['sharpeRatio'],
            'maxDrawdown': pnl_data['maxDrawdown'],
        })
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        last = candles[-1]
        return jsonify({
            'symbol': symbol,
            'currentPrice': last['close'],
            'priceChange24h': 0,
            'priceChangePct24h': 0,
            'volume24h': last['volume'],
            'totalPnl': pnl_data['totalPnl'],
            'winRate': pnl_data['winRate'],
            'sharpeRatio': pnl_data['sharpeRatio'],
            'maxDrawdown': pnl_data['maxDrawdown'],
        })


@app.route('/api/chart/candlestick')
def api_chart_candlestick():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        chart_html = create_candlestick_chart(candles, patterns_dicts)
        return jsonify({'chart': chart_html})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        chart_html = create_candlestick_chart(candles, patterns_dicts)
        return jsonify({'chart': chart_html})


@app.route('/api/chart/pnl')
def api_chart_pnl():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        chart_html = create_pnl_chart(pnl_data['points'])
        return jsonify({'chart': chart_html})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        chart_html = create_pnl_chart(pnl_data['points'])
        return jsonify({'chart': chart_html})


@app.route('/api/chart/combined')
def api_chart_combined():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        pnl_data = generate_test_pnl(candles)
        chart_html = create_combined_chart(candles, patterns_dicts, pnl_data['points'])
        return jsonify({'chart': chart_html})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        pnl_data = generate_test_pnl(candles)
        chart_html = create_combined_chart(candles, patterns_dicts, pnl_data['points'])
        return jsonify({'chart': chart_html})


@app.route('/api/chart/svg/candlestick')
def api_chart_svg_candlestick():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        pattern_times = [p.time for p in patterns]
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        svg = generate_svg_candlestick(candles, pattern_times=pattern_times, patterns=patterns_dicts)
        return jsonify({'svg': svg})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        pattern_times = [p.time for p in patterns]
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        svg = generate_svg_candlestick(candles, pattern_times=pattern_times, patterns=patterns_dicts)
        return jsonify({'svg': svg})


@app.route('/api/chart/svg/pnl')
def api_chart_svg_pnl():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        svg = generate_svg_pnl(pnl_data['points'])
        return jsonify({'svg': svg})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        pnl_data = generate_test_pnl(candles)
        svg = generate_svg_pnl(pnl_data['points'])
        return jsonify({'svg': svg})


@app.route('/api/chart/svg/combined')
def api_chart_svg_combined():
    symbol = request.args.get('symbol', 'BTCUSDT')
    try:
        candles = fetcher.fetch_candles(symbol, '1d', 90)
        if not candles:
            candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        pattern_times = [p.time for p in patterns]
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        pnl_data = generate_test_pnl(candles)
        svg = generate_svg_combined(candles, pnl_data['points'], pattern_times, patterns_dicts)
        return jsonify({'svg': svg})
    except Exception as e:
        candles = generate_test_data(symbol, 90)
        patterns = detect_patterns(candles)
        pattern_times = [p.time for p in patterns]
        patterns_dicts = [pattern_to_dict(p) for p in patterns]
        pnl_data = generate_test_pnl(candles)
        svg = generate_svg_combined(candles, pnl_data['points'], pattern_times, patterns_dicts)
        return jsonify({'svg': svg})


if __name__ == '__main__':
    print("Starting Trading Dashboard...")
    print("Open http://localhost:5000")
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 5000
    app.run(debug=False, host="0.0.0.0", port=port)