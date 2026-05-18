import json
import time
from pathlib import Path
from config import STATE_FILE, UNAUTHORIZED_FILE, TG_ALL_DIR, SUPER_USER

_EMPTY_SESSION = {
    "super": SUPER_USER,
    "default_model": "opencode/gpt-5.1-codex",
    "users": {},
    "files": {},
}


def _load():
    if not STATE_FILE.exists():
        return dict(_EMPTY_SESSION)
    with open(STATE_FILE, encoding="utf-8") as f:
        return json.load(f)


def _save(state):
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(STATE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2, ensure_ascii=False)


def _user_dir(uid):
    return TG_ALL_DIR / f"TG_{uid}"


def get_quota(uid):
    d = _user_dir(uid)
    size = 0
    count = 0
    if d.exists():
        for f in d.rglob("*"):
            if f.is_file():
                count += 1
                size += f.stat().st_size
    return count, size


def user_exists(uid):
    state = _load()
    return str(uid) in state["users"]


def get_user(uid):
    state = _load()
    return state["users"].get(str(uid))


def add_user(uid, name, msg_limit=None, token_limit=None, storage_mb=None, file_limit=None):
    state = _load()
    sid = str(uid)
    if sid not in state["users"]:
        state["users"][sid] = {
            "name": name,
            "role": "normal",
            "model": None,
            "limits": {
                "msg": msg_limit or 50,
                "token": token_limit or 1_000_000,
                "storage_mb": storage_mb or 500,
                "file_count": file_limit or 1000,
            },
            "sessions": {"current": None, "list": {}},
        }
        _user_dir(uid).mkdir(parents=True, exist_ok=True)
        (_user_dir(uid) / "uploads").mkdir(exist_ok=True)
    _save(state)


def remove_user(uid):
    state = _load()
    state["users"].pop(str(uid), None)
    _save(state)


def list_users():
    state = _load()
    return state["users"]


def ensure_super():
    state = _load()
    sid = str(SUPER_USER)
    if sid not in state["users"]:
        state["users"][sid] = {
            "name": "SK",
            "role": "super",
            "model": None,
            "limits": None,
            "sessions": {"current": None, "list": {}},
        }
    _save(state)


def set_session_opencode_id(uid, key, opencode_id):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        u["sessions"]["list"][key]["opencode_id"] = opencode_id
        _save(state)
        return True
    return False


def set_session_tokens(uid, key, total):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        u["sessions"]["list"][key]["tokens"] = total
        _save(state)
        return True
    return False


def get_session_opencode_id(uid, key):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        return u["sessions"]["list"][key].get("opencode_id")
    return None


def get_session_agent(uid, key):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        return u["sessions"]["list"][key].get("agent")
    return None


def create_session(uid, name=None):
    state = _load()
    sid = str(uid)
    if sid not in state["users"]:
        return None
    ts = int(time.time())
    key = f"ses_{uid}_{ts}"
    if not name:
        nick = state["users"][sid].get("name", str(uid))
        from datetime import datetime
        ts_str = datetime.now().strftime("%d%m%Y_%H%M")
        name = f"[TG] {uid}_{nick}_{ts_str}"
    state["users"][sid]["sessions"]["current"] = key
    sess = {
        "name": name,
        "created": ts,
        "messages": 0,
        "model": None,
        "opencode_id": None,
    }
    if str(uid) != str(SUPER_USER):
        sess["agent"] = "tg-reader"
    state["users"][sid]["sessions"]["list"][key] = sess
    _save(state)
    return key


def switch_session(uid, key):
    state = _load()
    sid = str(uid)
    if sid in state["users"] and key in state["users"][sid]["sessions"]["list"]:
        state["users"][sid]["sessions"]["current"] = key
        _save(state)
        return True
    return False


def rename_session(uid, key, new_name):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        u["sessions"]["list"][key]["name"] = new_name
        _save(state)
        return True
    return False


def drop_session(uid):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u["sessions"]["current"]:
        key = u["sessions"]["current"]
        u["sessions"]["list"].pop(key, None)
        keys = list(u["sessions"]["list"].keys())
        u["sessions"]["current"] = keys[-1] if keys else None
        _save(state)
        return True
    return False


def get_current_session(uid):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u["sessions"]["current"]:
        key = u["sessions"]["current"]
        s = u["sessions"]["list"].get(key)
        if s:
            return key, s
    return None, None


def save_last_task(uid, text, session_key):
    state = _load()
    sid = str(uid)
    if sid in state["users"]:
        state["users"][sid]["_last_task"] = {
            "text": text,
            "session": session_key,
            "ts": int(time.time()),
        }
        _save(state)


def clear_last_task(uid):
    state = _load()
    sid = str(uid)
    if sid in state["users"]:
        state["users"][sid].pop("_last_task", None)
        _save(state)


def get_all_pending_tasks():
    state = _load()
    result = []
    for sid, u in state.get("users", {}).items():
        task = u.get("_last_task")
        if task:
            result.append((int(sid), task))
    return result


def reset_session_counters(uid, key):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and key in u["sessions"]["list"]:
        u["sessions"]["list"][key]["messages"] = 0
        u["sessions"]["list"][key]["tokens"] = 0
        _save(state)


def update_session_tokens(uid, key):
    import logging, time, subprocess, json
    log = logging.getLogger("tg_bot")
    opencode_id = get_session_opencode_id(uid, key)
    if not opencode_id:
        log.warning(f"update_session_tokens: no opencode_id for uid={uid} key={key}")
        return
    try:
        time.sleep(2)
        proc = subprocess.run(
            ["opencode", "export", opencode_id],
            capture_output=True, text=True, timeout=30
        )
        data = json.loads(proc.stdout)
        messages = data.get("messages", [])
        last = messages[-1] if messages else {}
        total = last.get("tokens", {}).get("total", 0)
        state = _load()
        sid = str(uid)
        u = state["users"].get(sid)
        if u and key in u["sessions"]["list"]:
            old = u["sessions"]["list"][key].get("tokens", 0)
            u["sessions"]["list"][key]["tokens"] = total
            _save(state)
            log.info(f"update_session_tokens: uid={uid} key={key} tokens {old} -> {total}")
        else:
            log.warning(f"update_session_tokens: session not found uid={uid} key={key}")
    except Exception as e:
        log.error(f"update_session_tokens: {type(e).__name__}: {e}")


def increment_msg(uid):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u["sessions"]["current"]:
        key = u["sessions"]["current"]
        s = u["sessions"]["list"].get(key)
        if s:
            s["messages"] = s.get("messages", 0) + 1
            _save(state)


def set_user_model(uid, model):
    state = _load()
    sid = str(uid)
    if sid in state["users"]:
        state["users"][sid]["model"] = model
        _save(state)
        return True
    return False


def set_default_model(model):
    state = _load()
    state["default_model"] = model
    _save(state)


def set_limit(uid, limit_type, value):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u.get("limits"):
        key_map = {"msg": "msg", "token": "token", "storage": "storage_mb", "file": "file_count"}
        k = key_map.get(limit_type)
        if k and k in u["limits"]:
            u["limits"][k] = int(value)
            _save(state)
            return True
    return False


def auto_session(uid):
    key, sess = get_current_session(uid)
    if key:
        return key
    return create_session(uid)


def log_unauthorized(uid, username, first_name, text):
    now = int(time.time())
    entry = {
        "uid": uid,
        "username": username or "",
        "first_name": first_name or "",
        "text": (text or "")[:200],
        "time": now,
    }
    if UNAUTHORIZED_FILE.exists():
        data = json.loads(UNAUTHORIZED_FILE.read_text(encoding="utf-8"))
    else:
        data = []
    data.append(entry)
    # Keep last 500
    if len(data) > 500:
        data = data[-500:]
    UNAUTHORIZED_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")


def list_unauthorized():
    if not UNAUTHORIZED_FILE.exists():
        return []
    return json.loads(UNAUTHORIZED_FILE.read_text(encoding="utf-8"))


def set_build_mode(uid, active=True):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u["sessions"]["current"]:
        key = u["sessions"]["current"]
        s = u["sessions"]["list"].get(key)
        if s:
            s["_build_mode"] = active
            _save(state)
            return True
    return False


def get_build_mode(uid):
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if u and u["sessions"]["current"]:
        key = u["sessions"]["current"]
        s = u["sessions"]["list"].get(key)
        if s:
            return s.get("_build_mode", False)
    return False
