#!/usr/bin/env python3
"""Regenerate TradingView widget preview files using local vendor scripts.

- Web components (mini-chart, economic-map) use local module scripts.
- All other widgets use local embed-widget-*.js + TradingView.widget().
"""
import json
from pathlib import Path

BASE_DIR = Path(__file__).parent
WIDGETS_DIR = BASE_DIR / "widgets"

VENDOR_BASE = "/static/vendor/tradingview"

# Map embed_path -> local embed script name.
# crypto-mkt-screener reuses the generic screener script.
EMBED_SCRIPT_MAP = {
    "events": "embed-widget-events.js",
    "advanced-chart": "embed-widget-advanced-chart.js",
    "symbol-overview": "embed-widget-symbol-overview.js",
    "market-quotes": "embed-widget-market-quotes.js",
    "market-overview": "embed-widget-market-overview.js",
    "hotlists": "embed-widget-hotlists.js",
    "ticker-tape": "embed-widget-ticker-tape.js",
    "single-quote": "embed-widget-single-quote.js",
    "stock-heatmap": "embed-widget-stock-heatmap.js",
    "crypto-coins-heatmap": "embed-widget-crypto-coins-heatmap.js",
    "forex-cross-rates": "embed-widget-forex-cross-rates.js",
    "etf-heatmap": "embed-widget-etf-heatmap.js",
    "forex-heat-map": "embed-widget-forex-heat-map.js",
    "screener": "embed-widget-screener.js",
    "crypto-mkt-screener": "embed-widget-screener.js",
    "symbol-info": "embed-widget-symbol-info.js",
    "technical-analysis": "embed-widget-technical-analysis.js",
    "financials": "embed-widget-financials.js",
    "symbol-profile": "embed-widget-symbol-profile.js",
    "timeline": "embed-widget-timeline.js",
}


def embed_script_for(embed_path: str) -> str:
    if embed_path not in EMBED_SCRIPT_MAP:
        raise ValueError(f"No local embed script mapped for embed_path: {embed_path}")
    return EMBED_SCRIPT_MAP[embed_path]


# Map widget file path (relative to widgets/) -> embed path and params
WIDGET_CONFIGS = {
    "calendars/economic-calendar/index.html": {
        "name": "Economic Calendar",
        "embed_path": "events",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "charts/advanced-chart/index.html": {
        "name": "Advanced Chart",
        "embed_path": "advanced-chart",
        "params": {"symbol": "BINANCE:BTCUSDT", "interval": "D", "timezone": "exchange", "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#1e222d", "enable_publishing": False, "allow_symbol_change": True, "hide_top_toolbar": False, "hide_legend": False, "withdateranges": True, "hide_side_toolbar": False, "details": True, "hotlist": True, "width": "100%", "height": "100%", "autosize": True},
    },
    "charts/symbol-overview/index.html": {
        "name": "Symbol Overview",
        "embed_path": "symbol-overview",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True, "dateRange": "1M", "showVolume": True, "showMA": True},
    },
    "watchlists/market-summary/index.html": {
        "name": "Market Summary",
        "embed_path": "market-quotes",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "watchlists/market-overview/index.html": {
        "name": "Market Overview",
        "embed_path": "market-overview",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "watchlists/stock-market/index.html": {
        "name": "Stock Market",
        "embed_path": "hotlists",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "watchlists/market-data/index.html": {
        "name": "Market Data",
        "embed_path": "market-quotes",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "tickers/ticker-tape/index.html": {
        "name": "Ticker Tape",
        "embed_path": "ticker-tape",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "tickers/single-ticker/index.html": {
        "name": "Single Ticker",
        "embed_path": "single-quote",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "tickers/ticker/index.html": {
        "name": "Ticker",
        "embed_path": "ticker-tape",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "tickers/ticker-tag/index.html": {
        "name": "Ticker Tag",
        "embed_path": "ticker-tape",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "heatmaps/stock-heatmap/index.html": {
        "name": "Stock Heatmap",
        "embed_path": "stock-heatmap",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "heatmaps/crypto-heatmap/index.html": {
        "name": "Crypto Heatmap",
        "embed_path": "crypto-coins-heatmap",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "heatmaps/forex-cross-rates/index.html": {
        "name": "Forex Cross Rates",
        "embed_path": "forex-cross-rates",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "heatmaps/etf-heatmap/index.html": {
        "name": "ETF Heatmap",
        "embed_path": "etf-heatmap",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "heatmaps/forex-heatmap/index.html": {
        "name": "Forex Heatmap",
        "embed_path": "forex-heat-map",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "screeners/screener/index.html": {
        "name": "Screener",
        "embed_path": "screener",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "screeners/crypto-market/index.html": {
        "name": "Crypto Market",
        "embed_path": "crypto-mkt-screener",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "symbol-details/symbol-info/index.html": {
        "name": "Symbol Info",
        "embed_path": "symbol-info",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "symbol-details/technical-analysis/index.html": {
        "name": "Technical Analysis",
        "embed_path": "technical-analysis",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "symbol-details/fundamental-data/index.html": {
        "name": "Fundamental Data",
        "embed_path": "financials",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "symbol-details/company-profile/index.html": {
        "name": "Company Profile",
        "embed_path": "symbol-profile",
        "params": {"symbol": "BINANCE:BTCUSDT", "colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
    "news/top-stories/index.html": {
        "name": "Top Stories",
        "embed_path": "timeline",
        "params": {"colorTheme": "dark", "isTransparent": False, "locale": "en", "width": "100%", "height": "100%", "autosize": True},
    },
}

# Full-page widget configs (widgets-full/*.html) - embed-script widgets
WIDGETS_FULL_CONFIGS = {
    "advanced-chart.html": {"name": "Advanced Chart", "embed_path": "advanced-chart", "params": {"symbol": "BINANCE:BTCUSDT", "interval": "D", "timezone": "exchange", "theme": "dark", "style": "1", "locale": "en", "toolbar_bg": "#1e222d", "enable_publishing": False, "allow_symbol_change": True, "hide_top_toolbar": False, "hide_legend": False, "withdateranges": True, "hide_side_toolbar": False, "details": True, "hotlist": True, "width": "100%", "height": "100%", "autosize": True}},
    "symbol-overview.html": {"name": "Symbol Overview", "embed_path": "symbol-overview", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "isTransparent": False, "autosize": True, "dateRange": "1M", "showVolume": True, "showMA": True}},
    "market-summary.html": {"name": "Market Summary", "embed_path": "market-quotes", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "market-overview.html": {"name": "Market Overview", "embed_path": "market-overview", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "stock-market.html": {"name": "Stock Market", "embed_path": "hotlists", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "market-data.html": {"name": "Market Data", "embed_path": "market-quotes", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "ticker-tape.html": {"name": "Ticker Tape", "embed_path": "ticker-tape", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "single-ticker.html": {"name": "Single Ticker", "embed_path": "single-quote", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "stock-heatmap.html": {"name": "Stock Heatmap", "embed_path": "stock-heatmap", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "crypto-heatmap.html": {"name": "Crypto Heatmap", "embed_path": "crypto-coins-heatmap", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "forex-cross-rates.html": {"name": "Forex Cross Rates", "embed_path": "forex-cross-rates", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "etf-heatmap.html": {"name": "ETF Heatmap", "embed_path": "etf-heatmap", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "forex-heatmap.html": {"name": "Forex Heatmap", "embed_path": "forex-heat-map", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "screener.html": {"name": "Screener", "embed_path": "screener", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "crypto-market.html": {"name": "Crypto Market", "embed_path": "crypto-mkt-screener", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "symbol-info.html": {"name": "Symbol Info", "embed_path": "symbol-info", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "technical-analysis.html": {"name": "Technical Analysis", "embed_path": "technical-analysis", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "fundamental-data.html": {"name": "Fundamental Data", "embed_path": "financials", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "company-profile.html": {"name": "Company Profile", "embed_path": "symbol-profile", "params": {"symbol": "BINANCE:BTCUSDT", "width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "top-stories.html": {"name": "Top Stories", "embed_path": "timeline", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
    "economic-calendar.html": {"name": "Economic Calendar", "embed_path": "events", "params": {"width": "100%", "height": "100%", "locale": "en", "colorTheme": "dark", "autosize": True}},
}

# Full-page web components (no embed script equivalent)
WIDGETS_FULL_WEBCOMPONENTS = {
    "economic-map.html": {"name": "Economic Map", "tag": "tv-economic-map", "script": "tv-economic-map.js", "attrs": 'color-theme="dark" locale="en"'},
    "mini-chart.html": {"name": "Mini Chart", "tag": "tv-mini-chart", "script": "tv-mini-chart.js", "attrs": 'symbol="BINANCE:BTCUSDT" color-theme="dark" locale="en"'},
}

# Widgets that should stay as web components (known to work)
WEB_COMPONENT_WIDGETS = {
    "charts/mini-chart/index.html": {
        "tag": "tv-mini-chart",
        "script": "tv-mini-chart.js",
        "attrs": 'symbol="BINANCE:BTCUSDT" color-theme="dark" locale="en"',
    },
    "economics/economic-map/index.html": {
        "tag": "tv-economic-map",
        "script": "tv-economic-map.js",
        "attrs": 'color-theme="dark" locale="en"',
    },
}


TEMPLATE_EMBED_SCRIPT = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #131722; height: 100vh; overflow: hidden; }}
        .tradingview-widget-container {{ width: 100%; height: 100%; }}
    </style>
</head>
<body>
<div class="tradingview-widget-container">
    <div id="tv-chart-container"></div>
    <script type="text/javascript" src="{vendor_base}/{embed_script}">
    {params_json}
    </script>
</div>
</body>
</html>'''


TEMPLATE_WEBCOMPONENT = '''<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title}</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{ background: #131722; height: 100vh; overflow: hidden; }}
        .tradingview-widget-container {{ height: 100%; width: 100%; }}
    </style>
</head>
<body>
<div class="tradingview-widget-container">
    <{tag} {attrs}></{tag}>
</div>
<script type="module" src="{vendor_base}/{script}"></script>
</body>
</html>'''


def generate_embed_script_widget(title, embed_path, params):
    return TEMPLATE_EMBED_SCRIPT.format(
        title=title,
        vendor_base=VENDOR_BASE,
        embed_script=embed_script_for(embed_path),
        params_json=json.dumps(params, ensure_ascii=False, indent=4),
    )


def generate_webcomponent_widget(title, tag, script, attrs):
    return TEMPLATE_WEBCOMPONENT.format(
        title=title,
        tag=tag,
        script=script,
        attrs=attrs,
        vendor_base=VENDOR_BASE,
    )


def main():
    for rel_path, config in WIDGET_CONFIGS.items():
        file_path = WIDGETS_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        html = generate_embed_script_widget(
            config["name"],
            config["embed_path"],
            config["params"],
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"  ✅ widgets/{rel_path} -> embed-script/{config['embed_path']}")

    for rel_path, config in WEB_COMPONENT_WIDGETS.items():
        file_path = WIDGETS_DIR / rel_path
        file_path.parent.mkdir(parents=True, exist_ok=True)
        html = generate_webcomponent_widget(
            config["tag"].replace("tv-", "").replace("-", " ").title(),
            config["tag"],
            config["script"],
            config["attrs"],
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"  ✅ widgets/{rel_path} -> web component/{config['tag']}")

    widgets_full_dir = BASE_DIR / "widgets-full"
    widgets_full_dir.mkdir(parents=True, exist_ok=True)
    for filename, config in WIDGETS_FULL_CONFIGS.items():
        file_path = widgets_full_dir / filename
        html = generate_embed_script_widget(
            config["name"],
            config["embed_path"],
            config["params"],
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"  ✅ widgets-full/{filename} -> embed-script/{config['embed_path']}")

    for filename, config in WIDGETS_FULL_WEBCOMPONENTS.items():
        file_path = widgets_full_dir / filename
        html = generate_webcomponent_widget(
            config["name"],
            config["tag"],
            config["script"],
            config["attrs"],
        )
        file_path.write_text(html, encoding="utf-8")
        print(f"  ✅ widgets-full/{filename} -> web component/{config['tag']}")

    print("\nDone!")


if __name__ == "__main__":
    main()
