from flask import Blueprint, jsonify, current_app
from threading import Thread
from storage import get_storage

bp = Blueprint('processor', __name__, url_prefix='/api')
storage = get_storage()


def _sync_card(obj_id: str) -> dict:
    """Sync одной карты: exchange → все JSON (1 вызов биржи на карту)"""
    from routes.graphics import _get_storage, _get_current_price, _get_1m_price, _get_daily_price
    from routes.processor_1d import _process_object
    from account import BitgetAccountClient
    from calculator import calc_deviation, calc_pnl_pct_lev, calc_pnl_usdt
    from datetime import datetime

    result = {"obj_id": obj_id, "steps": {}}
    g_storage = _get_storage()

    try:
        obj = g_storage.load(obj_id)
    except FileNotFoundError:
        return {"error": "Object not found"}

    data = obj.data or {}
    emoji_entry = data.get("emoji_entry", {})
    symbol = emoji_entry.get("symbol", data.get("symbol", ""))
    entry_price = emoji_entry.get("entry_price", data.get("entry_price"))

    if not symbol or not entry_price:
        return {"error": "Missing symbol or entry_price"}

    # Step 1: candles → emoji_upd + ohlc
    try:
        price = _get_current_price(symbol)
        if price is None:
            price = _get_1m_price(symbol)
        if price is None:
            price = _get_daily_price(symbol)

        diff_usdt, diff_pct = calc_deviation(entry_price, price) if price else (0, 0)
        leverage = data.get("leverage", 10)
        volume = float(emoji_entry.get("volume", 1))
        pnl_pct_lev = calc_pnl_pct_lev(diff_pct, leverage)
        pnl_usdt_calc = calc_pnl_usdt(pnl_pct_lev, volume)

        data["emoji_upd"] = {
            "current_price": price,
            "entry_time": emoji_entry.get("entry_time", 0),
            "pnl_percent": round(pnl_pct_lev, 2),
            "pnl_usdt": round(pnl_usdt_calc, 4) if abs(pnl_usdt_calc) < 1000 else round(pnl_usdt_calc, 2),
            "result": "🟢" if diff_usdt >= 0 else "🔴",
            "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M"),
        }
        result["steps"]["emoji_upd"] = "ok"
    except Exception as e:
        result["steps"]["emoji_upd"] = str(e)

    # Step 2: 1D processor → _1D.json + _RAW.json
    try:
        _process_object(obj_id, operation='create')
        result["steps"]["1d"] = "ok"
    except Exception as e:
        result["steps"]["1d"] = str(e)

    # Step 3: position → live_position
    try:
        client = BitgetAccountClient()
        if client.has_credentials:
            for p in client.get_positions():
                if p.ticker.upper() == symbol.upper():
                    margin = p.margin_size or 1
                    balance = 0.0
                    try:
                        acc = client.get_account_info()
                        accounts = acc.get("data", [])
                        if accounts:
                            balance = float(accounts[0].get("available", 0))
                    except Exception:
                        pass

                    roe = (p.unrealized_pl / margin * 100) if margin else 0
                    liq_delta = abs((p.current_price - p.liquidation_price) / p.current_price * 100) \
                                if p.current_price and p.liquidation_price > 0 else 99
                    exp_pct = (margin * p.leverage / balance * 100) if balance else 0

                    flags = []
                    if roe < -50:
                        flags.append(f"PnL {roe:.0f}%")
                    if liq_delta < 5:
                        flags.append(f"LiqΔ {liq_delta:.1f}%")
                    if exp_pct > 50:
                        flags.append(f"Exp {exp_pct:.0f}%")

                    data["live_position"] = {
                        "hold_side": p.hold_side,
                        "leverage": p.leverage,
                        "margin_size": p.margin_size,
                        "total_coin": p.total_coin,
                        "position_value_usdt": p.position_value_usdt,
                        "unrealized_pl": p.unrealized_pl,
                        "pl_percent": p.pl_percent,
                        "achieved_profits": p.achieved_profits,
                        "total_fee": p.total_fee,
                        "mark_price": p.current_price,
                        "liquidation_price": p.liquidation_price,
                        "risk_to_liquidation": p.risk_to_liquidation,
                        "stop_loss_price": p.stop_loss_price,
                        "take_profit_price": p.take_profit_price,
                        "days_open": p.days_open,
                        "risk_flags": flags,
                        "updated_at": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    }
                    result["steps"]["live_position"] = "ok"
                    break
            else:
                result["steps"]["live_position"] = "skipped (no match)"
        else:
            result["steps"]["live_position"] = "skipped (no credentials)"
    except Exception as e:
        result["steps"]["live_position"] = str(e)

    # Step 4: save
    try:
        g_storage.save(obj)
        result["steps"]["save"] = "ok"
    except Exception as e:
        result["steps"]["save"] = str(e)

    from storage import clear_positions_cache
    clear_positions_cache()

    return result


def _obj_to_dict(obj):
    """Convert Bitget API objects to plain dicts for JSON serialization."""
    if hasattr(obj, '__dict__'):
        return {k: _obj_to_dict(v) for k, v in obj.__dict__.items()}
    if isinstance(obj, (list, tuple)):
        return [_obj_to_dict(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _obj_to_dict(v) for k, v in obj.items()}
    return obj


def _sync_all_cards():
    """Sync всех карт + account данных (параллельно в тредах)"""
    cards = storage.list()
    threads = []
    for obj in cards:
        t = Thread(target=_sync_card, args=(obj.id,))
        t.start()
        threads.append(t)
    for t in threads:
        t.join()

    # Sync account: balance, orders, fills
    try:
        from account import BitgetAccountClient
        client = BitgetAccountClient()
        if client.has_credentials:
            spot_assets = [_obj_to_dict(a) for a in client.get_spot_assets()]
            mix_accounts = [_obj_to_dict(m) for m in client.get_mix_accounts()]
            storage.save_balance({"spot": spot_assets, "futures": mix_accounts})

            spot_orders = [_obj_to_dict(o) for o in client.get_spot_orders()]
            mix_orders = [_obj_to_dict(o) for o in client.get_mix_orders()]
            storage.save_orders({"spot": spot_orders, "futures": mix_orders})

            fills_data = _obj_to_dict(client.fetch_all_fills(market='all'))
            storage.save_fills(fills_data)
    except Exception as e:
        import logging
        logging.getLogger("processor").error(f"sync account data failed: {e}")

    # Calculator pipeline: recompute all derived fields
    try:
        _run_calculator_pipeline()
    except Exception as e:
        import logging
        logging.getLogger("processor").error(f"calculator pipeline failed: {e}")

    return {"ok": True, "count": len(cards)}


def _run_calculator_pipeline():
    """Пересчёт computed-полей для всех карт после sync."""
    from calculator import calc_aggregate, save_aggregate, calc_margin_pct
    from calculator import calc_roe, calc_ror
    from calculator import calc_liq_delta, calc_risk_flags
    from calculator import calc_bal_pct, calc_exp_pct
    from calculator import calc_kpi, calc_day_metrics, calc_volatility_pct, calc_volatility_lev
    from calculator import compute_rsi, compute_macd, compute_ema, compute_sma, compute_oi

    cards = storage.list()
    balance_data = storage.load_balance()
    balance = 0.0
    for item in balance_data.get('futures', []):
        if item.get('margin_coin') == 'USDT':
            balance = float(item.get('available', 0))
            break
    if not balance:
        for item in balance_data.get('spot', []):
            if item.get('coin') == 'USDT':
                balance = float(item.get('available', 0))
                break

    # 1. aggregate + kpi
    totals = calc_aggregate(cards)
    save_aggregate(totals)
    total_margin = totals.get('total_margin', 0)
    kpi_data = calc_kpi(cards)

    # 2. per-card computations
    for obj in cards:
        lp = obj.data.get('live_position')
        if not lp or not lp.get('hold_side'):
            continue
        margin = float(lp.get('margin_size', 0))
        pl = float(lp.get('unrealized_pl', 0))
        lev = float(lp.get('leverage', 10))
        current_price = float(lp.get('mark_price', 0))
        liq_price = float(lp.get('liquidation_price', 0))

        roe = calc_roe(pl, margin)
        ror = calc_ror(pl, balance)
        liq_delta = calc_liq_delta(current_price, liq_price)
        bal_pct = calc_bal_pct(margin, balance)
        exp_pct = calc_exp_pct(margin, lev, balance)
        mgn_pct = calc_margin_pct(margin, total_margin)
        flags = calc_risk_flags(roe, liq_delta, exp_pct)

        computed = {
            'mgn_pct': mgn_pct,
            'bal_pct': bal_pct,
            'exp_pct': exp_pct,
            'roe': roe,
            'ror': ror,
            'liq_delta': liq_delta,
            'risk_flags': flags,
            'kpi': kpi_data,
        }

        # 3. indicators from RAW/1D data (if available)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', '')
        if symbol and storage.exists_raw(symbol, obj.id) and storage.exists_1d(symbol, obj.id):
            try:
                raw = storage.load_raw(symbol, obj.id)
                days_data = storage.load_1d(symbol, obj.id)
                candles = raw.get('candles', [])
                days = days_data.get('days', [])
                if candles and days and len(candles) == len(days):
                    closes = [c['close'] for c in candles]
                    volumes = [c['volume'] for c in candles]
                    leverages = int(days_data.get('leverage', lev))

                    computed['indicators'] = {
                        'rsi': compute_rsi(closes, 14),
                        'macd': compute_macd(closes, 12, 26, 9),
                        'ema9': compute_ema(closes, 9),
                        'ema21': compute_ema(closes, 21),
                        'ema55': compute_ema(closes, 55),
                        'sma3': compute_sma(volumes, 3),
                        'sma5': compute_sma(volumes, 5),
                        'sma7': compute_sma(volumes, 7),
                        'sma14': compute_sma(volumes, 14),
                        'oi': compute_oi(volumes),
                    }

                    vol_pcts = [calc_volatility_pct(c['high'], c['low'], c['close']) for c in candles]
                    computed['candle_avg'] = {
                        'volatility_pct_avg': round(sum(vol_pcts) / len(vol_pcts), 2) if vol_pcts else 0,
                        'volatility_lev_avg': round(calc_volatility_lev(
                            sum(vol_pcts) / len(vol_pcts), leverages
                        ), 2) if vol_pcts else 0,
                    }
            except Exception:
                pass

        obj.data['computed'] = computed
        storage.save(obj)


@bp.route('/sync-card/<obj_id>', methods=['POST'])
def sync_card(obj_id):
    result = _sync_card(obj_id)
    if "error" in result:
        return jsonify(result), 404
    return jsonify(result)


@bp.route('/sync-all', methods=['POST'])
def sync_all():
    result = _sync_all_cards()
    return jsonify(result)
