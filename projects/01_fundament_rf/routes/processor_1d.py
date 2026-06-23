import re
import time
import uuid
from threading import Thread
from datetime import datetime
from flask import Blueprint, request, jsonify, render_template
from storage import get_storage, get_metrics_storage

bp = Blueprint('processor_1d', __name__, url_prefix='/processor_1d')
storage = get_storage()
metrics_storage = get_metrics_storage()


def _process_object(obj_id, operation='create'):
    from services.timeframe_pipeline import TimeframePipeline

    timing = {
        "operation": operation,
        "obj_id": obj_id,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": {}
    }

    symbol = 'UNKNOWN'

    try:
        obj = storage.load(obj_id)
        emoji_entry = obj.data.get('emoji_entry', {})
        symbol = emoji_entry.get('symbol', obj.data.get('symbol', 'UNKNOWN'))
        entry_price = float(emoji_entry.get('entry_price', obj.data.get('entry_price', 0)))
        entry_date = emoji_entry.get('entry_date', obj.data.get('entry_date'))
        leverage = obj.data.get('leverage', 10)
        volume = float(emoji_entry.get('volume', 1))

        if not entry_price or not entry_date:
            raise Exception("Missing entry_price or entry_date")

        api_start = int(time.time() * 1000)

        # Step 1: Use TimeframePipeline to fetch + enrich (writes new format)
        pipeline = TimeframePipeline()
        pipeline.build(obj_id, timeframes=["1D"])

        api_end = int(time.time() * 1000)

        processing_start = int(time.time() * 1000)

        # Step 2: Get days count from new format
        # (read_timeframe + inline build of days array)
        tf_data = storage.read_timeframe(symbol, obj_id, "1D")
        legacy = storage._candles_to_legacy(symbol, obj_id, tf_data)
        days_data = legacy.get("days", [])

        processing_end = int(time.time() * 1000)

        writing_start = int(time.time() * 1000)

        # Step 3: Save RAW (for api/ma_data.py:MADataLoader backward compat)
        enriched_candles = storage.read_timeframe(symbol, obj_id, "1D").get("candles", [])
        raw_candles = []
        for c in enriched_candles:
            raw_candles.append({
                "date": c.get("date", ""),
                "timestamp_ms": c.get("timestamp_ms", 0),
                "open": c.get("open", 0),
                "high": c.get("high", 0),
                "low": c.get("low", 0),
                "close": c.get("close", 0),
                "volume": c.get("volume", 0),
                "pre_entry": c.get("position_metrics", {}).get("pre_entry", False),
            })
        raw_data = {
            "id": f"{obj_id}_RAW",
            "parent_id": obj_id,
            "symbol": symbol.upper(),
            "granularity": "1day",
            "source": "bitget",
            "fetched_at": datetime.now().isoformat(),
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "candles": raw_candles,
            "total_candles": len(raw_candles)
        }
        storage.save_raw(symbol, obj_id, raw_data)

        obj.data['chart_updated'] = datetime.now().strftime("%Y-%m-%d %H:%M")
        storage.save(obj)

        writing_end = int(time.time() * 1000)

        timing['duration_ms'] = {
            "api_request_start": api_start,
            "api_request_end": api_end,
            "api_request_ms": api_end - api_start,
            "processing_start": processing_start,
            "processing_end": processing_end,
            "processing_ms": processing_end - processing_start,
            "writing_start": writing_start,
            "writing_end": writing_end,
            "writing_ms": writing_end - writing_start,
            "total_ms": writing_end - api_start
        }
        timing['result'] = {
            "status": "completed",
            "days_processed": len(days_data),
            "added": 0,
            "changed": 0,
            "skipped": 0
        }

    except Exception as e:
        timing['result'] = {"status": "failed", "error": str(e)}

    metrics_storage.add_record(timing)
    return timing


def _sync_object(obj_id):
    timing = {
        "operation": "sync",
        "obj_id": obj_id,
        "timestamp": datetime.now().isoformat(),
        "duration_ms": {}
    }

    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')

        chart_updated = obj.data.get('chart_updated')

        if storage.exists_timeframe(symbol, obj_id, "1D"):
            tf_data = storage.read_timeframe(symbol, obj_id, "1D")
            d1_updated = tf_data.get('updated_at')

            if chart_updated and d1_updated and chart_updated == d1_updated:
                timing['duration_ms'] = {"total_ms": 0}
                timing['result'] = {"status": "skipped", "reason": "chart_updated equals d1_updated"}
                metrics_storage.add_record(timing)
                return timing

        result = _process_object(obj_id, 'sync')
        result['result']['skipped'] = 1
        return result

    except Exception as e:
        timing['result'] = {"status": "failed", "error": str(e)}
        metrics_storage.add_record(timing)
        return timing


@bp.route('/create/<obj_id>', methods=['POST'])
def create_1d(obj_id):
    thread = Thread(target=_process_object, args=(obj_id, 'create'))
    thread.start()
    return jsonify({"status": "processing", "obj_id": obj_id}), 202


@bp.route('/sync/<obj_id>', methods=['POST'])
def sync_1d(obj_id):
    thread = Thread(target=_sync_object, args=(obj_id,))
    thread.start()
    return jsonify({"status": "syncing", "obj_id": obj_id}), 202


@bp.route('/status/<obj_id>', methods=['GET'])
def status(obj_id):
    status_data = {"obj_id": obj_id}
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        status_data['d1_exists'] = storage.exists_timeframe(symbol, obj_id, "1D")
        status_data['raw_exists'] = storage.exists_raw(symbol, obj_id)
        if storage.exists_timeframe(symbol, obj_id, "1D"):
            tf_data = storage.read_timeframe(symbol, obj_id, "1D")
            status_data['d1_status'] = 'completed'
            status_data['d1_updated'] = tf_data.get('updated_at')
        status_data['main_updated'] = obj.data.get('chart_updated')
        return jsonify(status_data)
    except FileNotFoundError:
        return jsonify({"error": "Object not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/data/<obj_id>', methods=['GET'])
def get_data(obj_id):
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        tf_data = storage.read_timeframe(symbol, obj_id, "1D")
        legacy = storage._candles_to_legacy(symbol, obj_id, tf_data)
        return jsonify(legacy)
    except FileNotFoundError:
        return jsonify({"error": "1D data not found"}), 404


@bp.route('/raw/<obj_id>', methods=['GET'])
def get_raw(obj_id):
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        data = storage.load_raw(symbol, obj_id)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": "RAW data not found"}), 404


@bp.route('/delete/<obj_id>', methods=['DELETE'])
def delete_1d_raw(obj_id):
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        storage.delete_1d_raw(symbol, obj_id)
        return jsonify({"ok": True})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route('/batch', methods=['POST'])
def batch_process():
    obj_ids = request.json.get('obj_ids', [])
    if not obj_ids:
        return jsonify({"error": "No obj_ids provided"}), 400

    results = []
    for obj_id in obj_ids:
        result = _process_object(obj_id, 'batch')
        results.append(result)

    return jsonify({
        "processed": len(obj_ids),
        "results": results
    })


@bp.route('/metrics', methods=['GET'])
def metrics_page():
    return render_template('metrics.html')


@bp.route('/metrics/data', methods=['GET'])
def metrics_data():
    data = metrics_storage.load()
    return jsonify(data)


@bp.route('/metrics/clear', methods=['POST'])
def metrics_clear():
    metrics_storage.clear()
    return jsonify({"ok": True})


@bp.route('/chart/<obj_id>', methods=['GET'])
def get_chart_data(obj_id):
    """Возвращает days для OHLC графика"""
    try:
        obj = storage.load(obj_id)
    except FileNotFoundError:
        return jsonify({'error': 'Object not found'}), 404
    try:
        symbol = obj.data.get('emoji_entry', {}).get('symbol', 'UNKNOWN')
        tf_data = storage.read_timeframe(symbol, obj_id, "1D")
        legacy = storage._candles_to_legacy(symbol, obj_id, tf_data)
        if not legacy or not legacy.get('days'):
            return jsonify({'error': 'No data file'}), 404
        return jsonify({
            'days': legacy.get('days', []),
            'symbol': legacy.get('symbol'),
            'entry_price': legacy.get('entry_price')
        })
    except FileNotFoundError:
        return jsonify({'error': 'No data file'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500