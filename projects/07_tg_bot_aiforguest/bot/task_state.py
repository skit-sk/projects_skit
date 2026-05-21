import json
import time
import os
from pathlib import Path
from datetime import datetime

_log = None

TASK_FILE = Path(__file__).resolve().parent.parent / "TG_ALL" / "task_state.json"

CMD_CODES = {
    "text": "M01",
    "/audit_ip": "A01", "/audit_deep": "A02",
    "/sc": "S01", "/wg": "S02", "/wgc": "S03",
    "voice": "V01",
    "youtube": "Y01",
    "/start": "B01", "/info": "B02", "/models": "B03",
    "/sysinfo": "B04", "/sessions": "B05",
    "/menu": "B06", "/quota": "B07", "/files": "B08",
    "/rm": "B09", "/clean": "B10", "/format": "B11",
    "/new": "B12", "/switch": "B13", "/rename": "B14",
    "/drop": "B15", "/dropsession": "B16", "/purge": "B17",
    "/cd": "B18", "/build": "B19", "/plan": "B20",
    "/broadcast": "B21", "/users": "B22", "/adduser": "B23",
    "/removeuser": "B24", "/userinfo": "B25", "/view": "B26",
    "/setmodel": "B27", "/setlimit": "B28", "/approve": "B29",
    "/approve-model": "B30", "/deny": "B31", "/request": "B32",
    "/unauthorized": "B33", "/sandbox": "B34", "/shutdown": "B35",
    "/sc_positions": "C01", "/tg_positions": "C02",
    "/audit_ip": "A01", "/audit_deep": "A02",
    "/wgc": "S03", "/task_stats": "B36", "/task_errors": "B37",
}

CMD_REV = {v: k for k, v in CMD_CODES.items()}

TYPE_MAP = {
    "M01": "XOCX", "A01": "XADX", "A02": "XADX",
    "S01": "XSCX", "S02": "XWCX", "S03": "XWCX",
    "V01": "XVCX", "Y01": "XYTX",
}


def _log_init():
    global _log
    if _log is None:
        import logging
        _log = logging.getLogger("tg_bot")


def _load() -> dict:
    for attempt in range(3):
        try:
            if not TASK_FILE.exists():
                return {"counter_global": 0, "counter_type": {}, "users": {}, "tasks": {}, "stats": {}, "errors": {"global": {"count": 0, "by_code": {}}, "by_user": {}, "last_errors": []}}
            return json.loads(TASK_FILE.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError) as e:
            if _log:
                _log.warning(f"task_state._load attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(0.5)
    return {"counter_global": 0, "counter_type": {}, "users": {}, "tasks": {}, "stats": {}, "errors": {"global": {"count": 0, "by_code": {}}, "by_user": {}, "last_errors": []}}


def cleanup_stale(data: dict | None = None, max_age: int = 3600, save: bool = True) -> dict:
    if data is None:
        data = _load()
    now = int(time.time() * 1000)
    changed = False
    cnt = 0
    for tid, task in data.get("tasks", {}).items():
        if task.get("status") in ("running", "queued"):
            created = task.get("start_ms") or task.get("created_ms", 0)
            if created and now - created > max_age * 1000:
                task["status"] = "failed"
                task["error"] = task.get("error", "") + " stale>1h"
                changed = True
                cnt += 1
    if changed:
        if _log:
            _log.info(f"cleanup_stale: {cnt} tasks marked failed")
        if save:
            _save(data, force=True)
    return data


_last_save: float = 0  # debounce


def _save(data, force=False):
    global _last_save
    now = time.time()
    if not force and now - _last_save < 1.0:
        return  # debounce: не чаще 1 раза в секунду
    _last_save = now

    for attempt in range(3):
        try:
            TASK_FILE.parent.mkdir(parents=True, exist_ok=True)
            tmp = TASK_FILE.with_suffix(f".tmp.{os.getpid()}")
            tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
            tmp.rename(TASK_FILE)
            return
        except OSError as e:
            if _log:
                _log.warning(f"task_state._save attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(0.5)


def _cmd_code(cmd: str) -> str:
    parts = cmd.strip().split()
    base = parts[0].lower() if parts else "text"
    return CMD_CODES.get(base, "M01")


def cmd_type(code: str) -> str:
    return TYPE_MAP.get(code, "XSPX")


def task_create(uid: int, cmd: str) -> str:
    _log_init()
    data = _load()
    data["counter_global"] += 1
    code = _cmd_code(cmd)
    t = cmd_type(code)
    gnum = data["counter_global"]

    sid = str(uid)
    if sid not in data["users"]:
        data["users"][sid] = {"name": "", "counter_type": {}}
    data["users"][sid]["counter_type"][t] = data["users"][sid]["counter_type"].get(t, 0) + 1
    tnum = data["users"][sid]["counter_type"][t]

    task_id = f"{uid}-{t}-{code}-{tnum:03d}"
    data["tasks"][task_id] = {
        "uid": uid,
        "type": t,
        "cmd_code": code,
        "cmd": cmd[:200],
        "status": "queued",
        "created_ms": int(time.time() * 1000),
        "start_ms": None,
        "elapsed_ms": None,
    }
    _save(data)
    return task_id


def task_start(task_id: str):
    data = _load()
    task = data["tasks"].get(task_id)
    if task:
        task["status"] = "running"
        task["start_ms"] = int(time.time() * 1000)
        _save(data, force=True)


def task_complete(task_id: str):
    data = _load()
    task = data["tasks"].get(task_id)
    if task and task["start_ms"]:
        elapsed = int(time.time() * 1000) - task["start_ms"]
        task["status"] = "completed"
        task["elapsed_ms"] = elapsed
        _save(data)
        stats_update(task["cmd_code"], elapsed, task["uid"])
        return elapsed
    return 0


def task_fail(task_id: str, error: str):
    data = _load()
    task = data["tasks"].get(task_id)
    if task:
        task["status"] = "failed"
        task["error"] = error
        _save(data)
        stats_error(task["cmd_code"], task["uid"], error)


def task_get(task_id: str) -> dict | None:
    data = _load()
    return data["tasks"].get(task_id)


def stats_update(code: str, elapsed_ms: int, uid: int):
    data = _load()
    if "stats" not in data:
        data["stats"] = {}
    s = data["stats"].setdefault(code, {"count": 0, "total_ms": 0, "min_ms": None, "max_ms": 0, "dates": []})
    s["count"] += 1
    s["total_ms"] += elapsed_ms
    if s["min_ms"] is None or elapsed_ms < s["min_ms"]:
        s["min_ms"] = elapsed_ms
    if elapsed_ms > s["max_ms"]:
        s["max_ms"] = elapsed_ms
    s["dates"].append(datetime.now().strftime("%d.%m.%y %H:%M"))
    _save(data)


def stats_error(code: str, uid: int, msg: str):
    data = _load()
    if "errors" not in data:
        data["errors"] = {"global": {"count": 0, "by_code": {}}, "by_user": {}, "last_errors": []}
    e = data["errors"]
    e["global"]["count"] += 1
    e["global"]["by_code"][code] = e["global"]["by_code"].get(code, 0) + 1
    suid = str(uid)
    if suid not in e["by_user"]:
        e["by_user"][suid] = {"count": 0, "by_code": {}}
    e["by_user"][suid]["count"] += 1
    e["by_user"][suid]["by_code"][code] = e["by_user"][suid]["by_code"].get(code, 0) + 1
    e["last_errors"].append({"code": code, "uid": uid, "msg": msg[:200], "date": datetime.now().strftime("%d.%m.%y %H:%M")})
    if len(e["last_errors"]) > 20:
        e["last_errors"] = e["last_errors"][-20:]
    _save(data)


def get_user_name(uid: int) -> str:
    try:
        from session import get_user
        u = get_user(uid)
        return u.get("name", str(uid)) if u else str(uid)
    except Exception:
        return str(uid)
