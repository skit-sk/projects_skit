"""Tools routes: journal, checklists, risk calculator."""
from flask import Blueprint, render_template, request, jsonify
import json
import config

bp = Blueprint('tools', __name__)


@bp.route('/')
def index():
    return render_template('tools.html')


@bp.route('/journal')
def journal():
    fills = _read_fills()
    # Convert to journal format
    journal = []
    for f in fills:
        journal.append({
            'time': f.get('c_time', ''),
            'symbol': f.get('symbol', ''),
            'side': f.get('side', ''),
            'price': f.get('price', 0),
            'qty': f.get('quantity', 0),
            'pnl': f.get('profit', 0),
            'fee': f.get('fee_ccy', ''),
            'fee_amount': _extract_fee(f),
            'leverage': f.get('leverage', ''),
            'order_id': f.get('order_id', ''),
        })
    return render_template('tools_journal.html', journal=journal)


@bp.route('/checklist')
def checklist():
    return render_template('tools_checklist.html')


@bp.route('/risk')
def risk():
    return render_template('tools_risk.html')


@bp.route('/score')
def score():
    return render_template('tools_score.html')


@bp.route('/midasflow-builder')
def midasflow_builder():
    return render_template('tools/midasflow-builder.html')


def _read_fills():
    try:
        p = config.DATA_LIVE / 'fills.json'
        if p.exists():
            d = json.loads(p.read_text(encoding='utf-8'))
            return d.get('fills', [])
    except Exception:
        pass
    return []


def _extract_fee(fill):
    """Try to extract fee amount from fill dict."""
    if 'fee' in fill and isinstance(fill['fee'], dict):
        return fill['fee'].get('amount', 0)
    if 'fee_amount' in fill:
        return fill['fee_amount']
    return 0
