"""TradeHelp configuration."""
import os
from pathlib import Path

BASE_DIR = Path(__file__).parent
WORKSPACE = BASE_DIR.parent.parent
ROOT = WORKSPACE  # alias for workspace root

PORT = int(os.environ.get('TRADEHELP_PORT', 5012))
HOST = os.environ.get('TRADEHELP_HOST', '127.0.0.1')
DEBUG = os.environ.get('TRADEHELP_DEBUG', '0') == '1'

DATA_LIVE = BASE_DIR / 'data' / 'live'        # symlink to project 01 account
DATA_HISTORY = BASE_DIR / 'data' / 'history'  # symlink to project 01 card
DATA_CARD = WORKSPACE / 'projects' / '01_fundament_rf' / 'data' / 'card'
CONTENT_DIR = BASE_DIR / 'content'
DOCS_DIR = BASE_DIR / 'docs'
VIZ_DIR = BASE_DIR / 'viz' / 'interactive'
TEMPLATES = BASE_DIR / 'templates'
STATIC = BASE_DIR / 'static'

SECRET_KEY = os.environ.get('TRADEHELP_SECRET', 'tradehelp-dev-key')

TICKER_SYMBOLS = [
    {"proName": "BINANCE:BTCUSDT", "title": "BTC"},
    {"proName": "BINANCE:ETHUSDT", "title": "ETH"},
    {"proName": "BINANCE:API3USDT", "title": "API3"},
    {"proName": "BINANCE:ATOMUSDT", "title": "ATOM"},
    {"proName": "BINANCE:ADAUSDT", "title": "ADA"},
    {"proName": "BINANCE:DOTUSDT", "title": "DOT"},
    {"proName": "BINANCE:CAKEUSDT", "title": "CAKE"},
    {"proName": "BINANCE:AVAXUSDT", "title": "AVAX"},
]
