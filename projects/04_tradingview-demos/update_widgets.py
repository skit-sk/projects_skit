#!/usr/bin/env python3
"""Update widget files to use dynamic iframe loading."""

import os
import json

WIDGETS_DIR = "/home/user_aioc/workspace/projects/04_tradingview-demos/widgets-full"

WIDGET_CONFIGS = {
    "advanced-chart.html": {
        "widget_path": "advanced-chart",
        "params": {
            "symbol": "BINANCE:BTCUSDT",
            "interval": "D",
            "timezone": "exchange",
            "theme": "dark",
            "style": "1",
            "locale": "en",
            "toolbar_bg": "#1e222d",
            "enable_publishing": False,
            "allow_symbol_change": True,
            "hide_top_toolbar": False,
            "hide_legend": False,
            "withdateranges": True,
            "hide_side_toolbar": False,
            "details": True,
            "hotlist": True
        }
    },
    "mini-chart.html": {
        "widget_path": "mini-chart",
        "params": {
            "symbol": "BINANCE:BTCUSDT",
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark",
            "autosize": True
        }
    },
    "symbol-overview.html": {
        "widget_path": "symbol-overview",
        "params": {
            "symbol": "BINANCE:BTCUSDT",
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark",
            "isTransparent": False,
            "autosize": True,
            "dateRange": "1M",
            "showVolume": True,
            "showMA": True
        }
    },
    "market-summary.html": {
        "widget_path": "market-summary",
        "params": {
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark"
        }
    },
    "market-overview.html": {
        "widget_path": "market-overview",
        "params": {
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark"
        }
    },
    "stock-market.html": {
        "widget_path": "stock-market",
        "params": {
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark"
        }
    },
    "market-data.html": {
        "widget_path": "market-data",
        "params": {
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark"
        }
    },
    "ticker-tape.html": {
        "widget_path": "ticker-tape",
        "params": {
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark",
            "autosize": True
        }
    },
    "single-ticker.html": {
        "widget_path": "single-ticker",
        "params": {
            "symbol": "BINANCE:BTCUSDT",
            "width": "100%",
            "height": "100%",
            "locale": "en",
            "colorTheme": "dark"
        }
    },
}

def get_title(filename):
    """Get title from filename."""
    name = filename.replace('.html', '').replace('-', ' ').title()
    return name

def generate_html(filename, config):
    """Generate new HTML with dynamic iframe."""
    widget_path = config["widget_path"]
    params = config["params"]
    title = get_title(filename)
    params_str = json.dumps(params, ensure_ascii=False)

    template = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #131722; height: 100vh; overflow: hidden; }}
        .widget-wrapper {{ width: 100%; height: 100%; position: relative; }}
        .widget-fallback {{ position: absolute; top: 0; left: 0; width: 100%; height: 100%; display: flex; flex-direction: column; align-items: center; justify-content: center; color: #888; font-family: -apple-system, sans-serif; }}
        .spinner {{ width: 40px; height: 40px; border: 3px solid #333; border-top-color: #2962FF; border-radius: 50%; animation: spin 1s linear infinite; }}
        @keyframes spin {{ to {{ transform: rotate(360deg); }} }}
    </style>
</head>
<body>
<div class="widget-wrapper" id="wrapper">
    <div class="widget-fallback" id="fallback">
        <div class="spinner"></div>
        <p style="margin-top: 15px;">Loading TradingView widget...</p>
    </div>
</div>

<script>
(function() {{
    function createWidget() {{
        var container = document.getElementById('wrapper');
        var fallback = document.getElementById('fallback');

        var iframe = document.createElement('iframe');
        iframe.src = 'https://www.tradingview-widget.com/embed-widget/{widget_path}/?locale=en#' + encodeURIComponent({params_str});

        iframe.style.width = '100%';
        iframe.style.height = '100%';
        iframe.style.border = 'none';
        iframe.setAttribute('frameborder', '0');
        iframe.setAttribute('scrolling', 'no');
        iframe.setAttribute('allowtransparency', 'true');
        iframe.setAttribute('title', '{title} TradingView widget');

        iframe.onload = function() {{
            fallback.style.display = 'none';
        }};

        iframe.onerror = function() {{
            fallback.innerHTML = '<p style="color:#ef5350;">Failed to load widget</p>';
        }};

        container.appendChild(iframe);

        setTimeout(function() {{
            if (fallback.style.display !== 'none') {{
                fallback.innerHTML = '<p style="color:#ffa500;">Widget taking long time to load...</p>';
            }}
        }}, 15000);
    }}

    if (document.readyState === 'loading') {{
        document.addEventListener('DOMContentLoaded', createWidget);
    }} else {{
        createWidget();
    }}
}})();
</script>
</body>
</html>'''

    return template.format(
        title=title,
        widget_path=widget_path,
        params_str=params_str
    )

def main():
    """Update all widget files."""
    for filename, config in WIDGET_CONFIGS.items():
        filepath = os.path.join(WIDGETS_DIR, filename)
        if os.path.exists(filepath):
            html = generate_html(filename, config)
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html)
            print(f"Updated: {filename}")
        else:
            print(f"Missing: {filename}")

if __name__ == "__main__":
    main()