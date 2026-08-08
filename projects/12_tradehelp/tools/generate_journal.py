"""TradeHelp — generate journal templates (JSON/CSV)."""
import json
from pathlib import Path
from datetime import datetime, timedelta

ROOT = Path('/home/user_aioc/workspace/projects/12_tradehelp')
DATA_DIR = ROOT / 'data'
DATA_DIR.mkdir(exist_ok=True)

# JSON template
journal_json = {
    "version": "1.0",
    "created": datetime.utcnow().isoformat() + "Z",
    "description": "TradeHelp — Trading Journal template",
    "schema": {
        "time": "ISO8601 datetime",
        "symbol": "string (e.g. BTCUSDT)",
        "side": "buy | sell",
        "type": "market | limit | stop",
        "price": "float",
        "quantity": "float",
        "leverage": "int (default 1)",
        "stop_loss": "float (optional)",
        "take_profit": "float (optional)",
        "fee_paid": "float",
        "pnl": "float (realized profit/loss)",
        "roe_pct": "float (return on equity)",
        "duration_minutes": "int",
        "strategy": "string (SMC, Wyckoff, OrderFlow, etc.)",
        "confluence_score": "int 0-10",
        "factors": "list of matched factors",
        "entry_reason": "string (notes)",
        "exit_reason": "string (notes)",
        "emotional_state": "FOMO | Calm | Revenge | Euphoria | Fear | Neutral",
        "screenshot_url": "string (path to chart screenshot)",
        "tags": "list of strings",
        "rating": "int 1-5 (self-grade)"
    },
    "examples": [
        {
            "time": "2026-06-28T10:32:00Z",
            "symbol": "API3USDT",
            "side": "buy",
            "type": "limit",
            "price": 0.2992,
            "quantity": 85.2,
            "leverage": 10,
            "stop_loss": 0.2693,
            "take_profit": 0.3500,
            "fee_paid": 0.025,
            "pnl": -7.4,
            "roe_pct": -40.2,
            "duration_minutes": 14400,
            "strategy": "OB Retest + OTE",
            "confluence_score": 4,
            "factors": ["OB", "OTE", "OI", "RR"],
            "entry_reason": "Spring + 62% OTE + BOS on 1D",
            "exit_reason": "Stop loss hit",
            "emotional_state": "Calm",
            "screenshot_url": "/static/img/journal/2026-06-28_api3.png",
            "tags": ["API3", "long", "SMC"],
            "rating": 3
        }
    ]
}

with open(DATA_DIR / 'journal_template.json', 'w') as f:
    json.dump(journal_json, f, indent=2, ensure_ascii=False)
print(f"✓ {DATA_DIR/'journal_template.json'}")

# CSV template
import csv
csv_path = DATA_DIR / 'journal_template.csv'
with open(csv_path, 'w', newline='') as f:
    w = csv.writer(f)
    w.writerow(['time', 'symbol', 'side', 'type', 'price', 'quantity', 'leverage',
                'stop_loss', 'take_profit', 'fee_paid', 'pnl', 'roe_pct',
                'duration_minutes', 'strategy', 'confluence_score', 'factors',
                'entry_reason', 'exit_reason', 'emotional_state', 'screenshot_url',
                'tags', 'rating'])
    w.writerow(['2026-06-28T10:32:00Z', 'API3USDT', 'buy', 'limit', '0.2992', '85.2', '10',
                '0.2693', '0.3500', '0.025', '-7.4', '-40.2', '14400',
                'OB+OTE', '4', 'OB|OTE|OI|RR', 'Spring 62% OTE BOS 1D',
                'SL hit', 'Calm', '/static/img/journal/2026-06-28_api3.png',
                'API3;long;SMC', '3'])
print(f"✓ {csv_path}")
