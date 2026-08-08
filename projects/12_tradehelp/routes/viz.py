"""Viz routes: interactive Plotly charts and Lightweight Charts integration."""
from flask import Blueprint, render_template
import config

bp = Blueprint('viz', __name__)


VIZ_PAGES = [
    {'slug': 'candles', 'title': 'Свечной график', 'desc': 'OHLCV + Bollinger + ATR + Volume (Plotly + LWC)', 'symbol': 'API3USDT'},
    {'slug': 'volume-profile', 'title': 'Volume Profile', 'desc': 'POC, Value Area, HVN/LVN', 'symbol': 'API3USDT'},
    {'slug': 'footprint', 'title': 'Order Flow / Footprint', 'desc': 'Bid/Ask кластеры', 'symbol': 'API3USDT'},
    {'slug': 'onchain', 'title': 'On-Chain метрики', 'desc': 'MVRV, SOPR, NVT (симуляция на ценах API3)', 'symbol': 'API3USDT'},
    {'slug': 'sentiment', 'title': 'Sentiment', 'desc': 'Fear & Greed + Funding Rate', 'symbol': 'API3USDT'},
    {'slug': 'macro', 'title': 'Macro & Intermarket', 'desc': 'DXY, rates, корреляции', 'symbol': 'BTCUSDT'},
    {'slug': 'backtest', 'title': 'Backtest', 'desc': 'Walk-forward симуляция', 'symbol': 'API3USDT'},
    {'slug': 'risk-calc', 'title': 'Risk Calculator', 'desc': 'Kelly, fixed-fraction, ATR-stop', 'symbol': 'API3USDT'},
    {'slug': 'fibo-grid', 'title': 'MidasFlow Grid 2.0', 'desc': '33 уровня Фибоначчи от -1.0 до 2.618', 'symbol': 'API3USDT'},
    {'slug': 'crp-ribbon', 'title': 'CRP Ribbon', 'desc': 'Cluster Risk Projection — POC, VA, D-Shape', 'symbol': 'API3USDT'},
    {'slug': 'shadow-dom', 'title': 'Shadow DOM', 'desc': 'Скрытая плотность лимитных ордеров (Iceberg)', 'symbol': 'API3USDT'},
    {'slug': 'tier3-flow', 'title': '3-Tier Data Flow', 'desc': 'Tier 1 (Raw) → Tier 2 (Micro) → Tier 3 (Structural)', 'symbol': 'API3USDT'},
    {'slug': 'position-waterfall', 'title': 'Position Engineering', 'desc': 'Scaling In (1/8 → 8/8) + TP (1/4 → 4/4)', 'symbol': 'API3USDT'},
    {'slug': 'portfolio-metrics', 'title': 'Портфель 2026', 'desc': '12 сделок × 245 полей: OHLCV, Fibo, PnL, Risk, Sessions', 'symbol': 'ALL'},
]


@bp.route('/')
def index():
    return render_template('viz_dashboard.html', pages=VIZ_PAGES)


@bp.route('/<slug>')
def page(slug):
    page = next((p for p in VIZ_PAGES if p['slug'] == slug), None)
    if not page:
        return render_template('error.html', code=404, message='Viz page not found'), 404
    return render_template(f'viz/{slug}.html', page=page)
