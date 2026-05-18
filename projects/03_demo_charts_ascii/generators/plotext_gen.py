import json, os, sys, re
from .base import load_data, enrich_summary, legend

def make_html(plots, m):
    s = m.get('summary', {})
    leg = legend(m)
    tabs = []
    for p in plots:
      tabs.append('<button class="tab-btn" data-tabtool="plotext" data-tabid="' + p["id"] + '">' + p["title"] + '</button>')
    tabs_html = ''.join(tabs)

    divs = []
    for i, p in enumerate(plots):
        style = 'block' if i == 0 else 'none'
        clean_html = strip_ansi(p["html"])
        divs.append('<pre class="plotext-chart" id="plotext-' + p["id"] + '" style="display:' + style + '">' + clean_html + '</pre>')
    divs_html = ''.join(divs)

    metrics_items = []
    for k, v in {'ROE': s.get('current_roe_pct'), 'PnL': s.get('current_pnl_usdt'),
                  'Vol': s.get('avg_volatility'), 'Win': s.get('win_rate'),
                  'DD': s.get('max_drawdown_pct')}.items():
        if v is None: continue
        if isinstance(v, float):
            if k == 'ROE': metrics_items.append(f'<span class="metric"><b>{k}:</b> {v:+.1f}%</span>')
            elif k == 'PnL': metrics_items.append(f'<span class="metric"><b>{k}:</b> ${v:.2f}</span>')
            elif k == 'Vol': metrics_items.append(f'<span class="metric"><b>{k}:</b> {v:.3f}</span>')
            elif k == 'Win': metrics_items.append(f'<span class="metric"><b>{k}:</b> {v:.0f}%</span>')
            elif k == 'DD': metrics_items.append(f'<span class="metric"><b>{k}:</b> {v:+.1f}%</span>')
            else: metrics_items.append(f'<span class="metric"><b>{k}:</b> {v}</span>')
        else:
            metrics_items.append(f'<span class="metric"><b>{k}:</b> {v}</span>')

    header = '<div class="chart-header"><span class="chart-legend">' + leg + '</span></div>'
    tabs_section = '<div class="plotext-tabs">' + tabs_html + '</div>'
    divs_section = divs_html
    metrics_section = '<div class="chart-metrics">' + ' | '.join(metrics_items) + '</div>' if metrics_items else ''
    return '<div class="plotext-container">' + header + tabs_section + divs_section + metrics_section + '</div>'


def strip_ansi(text):
    return re.sub(r'\x1b\[[0-9;]*[a-zA-Z]', '', text)

def generate_chart(plt, m):
    r = m.get('raw', {})
    s = m.get('summary', {})
    close = r.get('close', [])
    high = r.get('high', [])
    low = r.get('low', [])
    opn = r.get('open', [])
    vol = r.get('volume', [])
    d = m.get('daily', {})
    dev = d.get('deviation_pct', [])

    charts = []

    # 1 Close Price
    plt.clear_figure()
    plt.plot(close, label=m['symbol'] + ' Close')
    plt.title(m['symbol'] + ' - Daily Close Price')
    plt.xlabel('Days'); plt.ylabel('Price (USDT)')
    charts.append({'id': 'close', 'title': 'Close', 'html': strip_ansi(plt.build())})

    # 2 OHLC Range
    plt.clear_figure()
    plt.plot(close, label='Close')
    plt.plot(high, label='High')
    plt.plot(low, label='Low')
    plt.title(m['symbol'] + ' - OHLC Range')
    plt.xlabel('Days'); plt.ylabel('Price')
    charts.append({'id': 'ohlc', 'title': 'OHLC', 'html': strip_ansi(plt.build())})

    # 3 Volume
    plt.clear_figure()
    plt.bar(vol, label='Volume')
    plt.title(m['symbol'] + ' - Trading Volume')
    plt.xlabel('Days'); plt.ylabel('Volume')
    charts.append({'id': 'volume', 'title': 'Volume', 'html': strip_ansi(plt.build())})

    # 4 Deviation
    if dev:
        plt.clear_figure()
        plt.plot(dev, label='Deviation %')
        plt.title(m['symbol'] + ' - Deviation from Entry')
        plt.xlabel('Days'); plt.ylabel('Deviation %')
        charts.append({'id': 'deviation', 'title': 'Deviation', 'html': strip_ansi(plt.build())})

    # 5 Volatility
    if len(high) == len(low) == len(close):
        plt.clear_figure()
        daily_vol = [(high[i] - low[i]) / (close[i] or 1) * 100 for i in range(len(close))]
        plt.plot(daily_vol, label='Daily Vol %')
        plt.title(m['symbol'] + ' - Daily Volatility')
        plt.xlabel('Days'); plt.ylabel('Volatility %')
        charts.append({'id': 'volatility', 'title': 'Volatility', 'html': strip_ansi(plt.build())})

    # 6 Scatter
    plt.clear_figure()
    plt.scatter(opn, close, label='Open > Close')
    plt.title(m['symbol'] + ' - Open vs Close')
    plt.xlabel('Open Price'); plt.ylabel('Close Price')
    charts.append({'id': 'scatter', 'title': 'Scatter', 'html': strip_ansi(plt.build())})

    return charts


def generate(data_path, output_dir):
    m = enrich_summary(load_data(data_path))
    r = m.get('raw', {})
    close = r.get('close', [])
    if len(close) < 2:
        return {'error': 'Not enough data (' + str(len(close)) + ' points)'}

    import plotext as plt
    charts = generate_chart(plt, m)
    html = make_html(charts, m)

    out_file = os.path.join(output_dir, 'plotext', m['symbol'] + '_charts.html')
    os.makedirs(os.path.dirname(out_file), exist_ok=True)
    with open(out_file, 'w') as f:
        f.write(html)

    return {'html_file': out_file, 'content': html, 'symbol': m['symbol'], 'charts': charts}


if __name__ == '__main__':
    generate(sys.argv[1], sys.argv[2] if len(sys.argv) > 2 else 'outputs')
