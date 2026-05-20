from flask import Blueprint, render_template, abort, redirect, url_for
from storage import get_storage
import json

bp = Blueprint('web', __name__)
storage = get_storage()


def _load_live_positions():
    """Загрузить live позиции из Bitget + сопоставить с картами."""
    from account import BitgetAccountClient

    client = BitgetAccountClient()
    if not client.has_credentials:
        return [], []

    try:
        positions = client.get_positions()
    except Exception:
        return [], []

    all_cards = get_storage().list()

    position_card_data = []
    for p in positions:
        found = None
        for obj in all_cards:
            sym = obj.data.get('emoji_entry', {}).get('symbol', '')
            if sym.upper() == p.ticker.upper():
                found = {
                    "number": obj.data.get('emoji_entry', {}).get('number', ''),
                    "symbol": sym,
                    "deviation_pct": obj.data.get('deviation_pct', []),
                }
                break
        position_card_data.append(found)

    return positions, position_card_data


@bp.route('/')
def index():
    objects = storage.list()
    positions, position_card_data = _load_live_positions()
    
    # Build positions_by_ticker
    positions_by_ticker = {}
    for p in positions:
        ticker = p.ticker.upper()
        positions_by_ticker[ticker] = {
            "hold_side": p.hold_side,
            "days_open": p.days_open,
            "leverage": p.leverage,
            "unrealized_pl": p.unrealized_pl,
            "margin_size": p.margin_size,
            "current_price": p.current_price,
            "liquidation_price": p.liquidation_price,
        }
    
    # Split objects by state
    from copy import deepcopy
    
    live_objects = []
    monitoring_objects = []
    archived_objects = []
    
    # Fetch balance for risk calculations
    balance = 0.0
    try:
        from account import BitgetAccountClient
        bc = BitgetAccountClient()
        if bc.has_credentials:
            acc = bc.get_account_info()
            accounts = acc.get("data", [])
            if accounts:
                balance = float(accounts[0].get("available", 0))
    except Exception:
        balance = 0.0
    
    for obj in objects:
        entry = obj.data.get('emoji_entry', {})
        sym = entry.get('symbol', '').upper()
        pos = positions_by_ticker.get(sym)
        manual = obj.data.get('_manual_section', '')
        
        if manual:
            if manual == 'live':
                live_objects.append(obj)
            elif manual == 'monitoring':
                monitoring_objects.append({"obj": obj, "flags": ["manual"]})
            elif manual == 'archived':
                archived_objects.append(obj)
            continue
        
        if not pos:
            archived_objects.append(obj)
            continue
        
        # Calculate risk flags
        pnl = float(pos.get('unrealized_pl', 0))
        margin = float(pos.get('margin_size', 0))
        lev = float(pos.get('leverage', 0))
        liq = float(pos.get('liquidation_price', 0))
        price = float(pos.get('current_price', 0))
        
        flags = []
        roe = (pnl / margin * 100) if margin else 0
        exp_pct = (margin * lev / balance * 100) if balance else 0
        liq_delta = abs((price - liq) / price * 100) if price and liq else 0
        
        if roe < -50:
            flags.append(f"PnL {roe:.0f}% < -50%")
        if liq_delta < 5 and liq_delta > 0:
            flags.append(f"LiqΔ {liq_delta:.1f}% < 5%")
        if exp_pct > 50:
            flags.append(f"Exp {exp_pct:.0f}% > 50%")
        
        if flags:
            monitoring_objects.append({"obj": obj, "flags": flags})
        else:
            live_objects.append(obj)
    
    return render_template('index.html',
        objects=objects,
        live_objects=live_objects,
        monitoring_objects=monitoring_objects,
        archived_objects=archived_objects,
        positions=positions,
        position_card_data=position_card_data,
        positions_by_ticker=positions_by_ticker,
    )


@bp.route('/obj/<obj_id>')
def get_object(obj_id):
    print(f"[DEBUG] Loading object: {obj_id}")
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        print(f"[DEBUG] Object not found: {obj_id}")
        abort(404)
    print(f"[DEBUG] Rendering card for: {obj.name}")
    return render_template('card.html', obj=obj)


@bp.route('/card/<obj_id>')
def card(obj_id):
    return get_object(obj_id)


@bp.route('/delete/<obj_id>')
def delete_object(obj_id):
    try:
        storage.delete(obj_id)
    except FileNotFoundError:
        pass
    return redirect(url_for('web.index'))


@bp.route('/range_variants_demo')
def range_variants_demo():
    trade_data = None
    days_data = []

    try:
        obj = storage.load('d1b35262-3b28-423a-ab34-f0ab5f719c57')
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'ETC')
        obj_id = obj.id

        if storage.exists_1d(symbol, obj_id):
            trade_data = obj.data
            days_data = storage.load_1d(symbol, obj_id).get('days', [])
            trade_data = obj.data
            days_data = storage.load_1d(symbol, obj_id).get('days', [])
    except (FileNotFoundError, KeyError):
        pass

    return render_template('range_variants_demo.html', trade_data=trade_data, days_data=days_data)