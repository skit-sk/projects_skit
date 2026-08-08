"""TV routes: TradingView Embed Widgets and Lightweight Charts."""
from flask import Blueprint, render_template, request

bp = Blueprint('tv', __name__)


TV_WIDGETS = [
    {'slug': 'advanced', 'title': 'Advanced Chart', 'desc': 'Полноценный график TradingView', 'symbol': 'BINANCE:API3USDT', 'height': 600},
    {'slug': 'symbol-overview', 'title': 'Symbol Overview', 'desc': 'Мини-обзор символа', 'symbol': 'BINANCE:BTCUSDT', 'height': 400},
    {'slug': 'crypto-heatmap', 'title': 'Crypto Heatmap', 'desc': 'Тепловая карта крипторынка', 'symbol': '', 'height': 500},
    {'slug': 'stock-heatmap', 'title': 'Stock Heatmap', 'desc': 'Тепловая карта акций', 'symbol': '', 'height': 500},
    {'slug': 'market-overview', 'title': 'Market Overview', 'desc': 'Обзор рынков', 'symbol': '', 'height': 500},
    {'slug': 'ticker-tape', 'title': 'Ticker Tape', 'desc': 'Лента котировок', 'symbol': '', 'height': 80},
    {'slug': 'technical-analysis', 'title': 'Technical Analysis', 'desc': 'Технический анализ от TradingView', 'symbol': 'BINANCE:API3USDT', 'height': 500},
    {'slug': 'economic-calendar', 'title': 'Economic Calendar', 'desc': 'Экономический календарь', 'symbol': '', 'height': 600},
    {'slug': 'forex-heatmap', 'title': 'Forex Heatmap', 'desc': 'Тепловая карта валют', 'symbol': '', 'height': 500},
    {'slug': 'screener', 'title': 'Screener', 'desc': 'Скринер акций', 'symbol': '', 'height': 600},
]


@bp.route('/')
def index():
    return render_template('tv_dashboard.html', widgets=TV_WIDGETS)


@bp.route('/<slug>')
def widget(slug):
    widget = next((w for w in TV_WIDGETS if w['slug'] == slug), None)
    if not widget:
        return render_template('error.html', code=404, message='TV widget not found'), 404
    return render_template(f'tv/{slug}.html', widget=widget)
