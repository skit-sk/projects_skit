from flask import Blueprint, jsonify, request, render_template
from storage import get_storage
from services.timeframe_pipeline import TimeframePipeline

bp = Blueprint("timeframe_api", __name__, url_prefix="/api/tf")
pipeline = TimeframePipeline()


@bp.route("/build/<obj_id>", methods=["POST"])
def build(obj_id):
    data = request.get_json() or {}
    tfs = data.get("timeframes")
    result = pipeline.build(obj_id, tfs)
    status_code = 202 if result["result"]["status"] == "completed" else 500
    return jsonify(result), status_code


@bp.route("/build-all", methods=["POST"])
def build_all():
    storage = get_storage()
    objs = storage.list()
    tfs = (request.get_json() or {}).get("timeframes")
    results = []
    for obj in objs:
        result = pipeline.build(obj.id, tfs)
        results.append(result)
    return jsonify({"processed": len(objs), "results": results})


@bp.route("/status/<obj_id>", methods=["GET"])
def status(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get("emoji_entry", {}).get("symbol", "UNKNOWN")
        statuses = {}
        for tf in pipeline.TIMEFRAMES:
            exists = storage.exists_timeframe(symbol, obj.id, tf)
            if exists:
                data = storage.read_timeframe(symbol, obj.id, tf)
                statuses[tf] = {
                    "exists": True,
                    "count": data.get("count", 0),
                    "updated_at": data.get("updated_at"),
                }
            else:
                statuses[tf] = {"exists": False}
        return jsonify({"obj_id": obj_id, "timeframes": statuses})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/data/<obj_id>/<timeframe>", methods=["GET"])
def get_data(obj_id, timeframe):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get("emoji_entry", {}).get("symbol", "UNKNOWN")
        data = storage.read_timeframe(symbol, obj.id, timeframe)
        return jsonify(data)
    except FileNotFoundError:
        return jsonify({"error": f"{timeframe} data not found"}), 404
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@bp.route("/<obj_id>", methods=["GET"])
def get_all_tf(obj_id):
    storage = get_storage()
    try:
        obj = storage.load(obj_id)
        symbol = obj.data.get("emoji_entry", {}).get("symbol", "UNKNOWN")
        result = {"obj_id": obj_id, "symbol": symbol, "granularities": {}}
        for tf in pipeline.TIMEFRAMES:
            try:
                data = storage.read_timeframe(symbol, obj.id, tf)
                result["granularities"][tf] = data
            except FileNotFoundError:
                result["granularities"][tf] = None

        return jsonify(result)
    except Exception as e:
        return jsonify({"error": str(e)}), 500
