"""Live routes: real-time data from 01_fundament_rf/data/account/."""
from flask import Blueprint, render_template, jsonify, abort
import json
import config
from datetime import datetime

bp = Blueprint('live', __name__)


def _read_json(name, default=None):
    try:
        p = config.DATA_LIVE / name
        if p.exists():
            return json.loads(p.read_text(encoding='utf-8'))
    except Exception as e:
        return {'error': str(e)}
    return default if default is not None else {}


@bp.route('/')
def dashboard():
    totals = _read_json('totals.json', {})
    balance = _read_json('balance.json', {})
    orders = _read_json('orders.json', {})
    return render_template('live_dashboard.html',
                          totals=totals, balance=balance, orders=orders)


@bp.route('/balance')
def balance_page():
    return render_template('live_balance.html', data=_read_json('balance.json', {}))


@bp.route('/orders')
def orders_page():
    return render_template('live_orders.html', data=_read_json('orders.json', {}))


@bp.route('/fills')
def fills_page():
    fills_data = _read_json('fills.json', {})
    return render_template('live_fills.html', data=fills_data)
