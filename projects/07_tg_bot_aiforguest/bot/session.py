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

SESSION_ACTIVE = "ACT"
SESSION_ERROR = "ERR"
SESSION_ORPHAN = "ORN"
SESSION_ARCHIVED = "ARC"
SESSION_DEAD = "DED"


def _load():
    if not STATE_FILE.exists():
        return dict(_EMPTY_SESSION)
    with open(STATE_FILE, encoding="utf-8") as f:
        data = json.load(f)
    _ensure_meta(data)
    return data


def _ensure_meta(state):
    changed = False
    if "session_seq" not in state:
        state["session_seq"] = 0
        changed = True
    if "session_stats" not in state:
        state["session_stats"] = {"total_created": 0, "total_deleted": 0, "active": 0}
        changed = True
    if changed:
        _recalc_stats(state)


def _recalc_stats(state):
    """Пересчитать session_stats и seq для всех сессий."""
    stats = state.setdefault("session_stats", {"total_created": 0, "total_deleted": 0, "active": 0})
    seq = state.get("session_seq", 0)
    active = 0
    for sid, u in state.get("users", {}).items():
        for key, s in u.get("sessions", {}).get("list", {}).items():
            st = s.get("status", SESSION_ACTIVE)
            if s.get("seq", 0) > seq:
                seq = s["seq"]
            if st in (SESSION_ACTIVE, SESSION_ERROR):
                active += 1
    state["session_seq"] = seq
    stats["active"] = active
    # total_created/total_deleted не пересчитываются — они исторические


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

    state["session_seq"] += 1
    state["session_stats"]["total_created"] += 1

    sess = {
        "seq": state["session_seq"],
        "status": SESSION_ACTIVE,
        "name": name,
        "created": ts,
        "messages": 0,
        "model": None,
        "opencode_id": None,
    }
    if str(uid) != str(SUPER_USER):
        sess["agent"] = "tg-reader"
    state["users"][sid]["sessions"]["list"][key] = sess
    _recalc_stats(state)
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
        sess = u["sessions"]["list"].get(key)
        if sess:
            sess["status"] = SESSION_DEAD
        keys = [k for k, v in u["sessions"]["list"].items()
                if v.get("status", SESSION_ACTIVE) in (SESSION_ACTIVE, SESSION_ERROR)]
        u["sessions"]["current"] = keys[-1] if keys else None
        state["session_stats"]["total_deleted"] += 1
        _recalc_stats(state)
        _save(state)
        return True
    return False


def dropsession_by_key(uid, key):
    """Удалить конкретную сессию по ключу."""
    state = _load()
    sid = str(uid)
    u = state["users"].get(sid)
    if not u or key not in u["sessions"]["list"]:
        return False
    u["sessions"]["list"][key]["status"] = SESSION_DEAD
    if u["sessions"]["current"] == key:
        keys = [k for k, v in u["sessions"]["list"].items()
                if v.get("status", SESSION_ACTIVE) in (SESSION_ACTIVE, SESSION_ERROR)]
        u["sessions"]["current"] = keys[-1] if keys else None
    state["session_stats"]["total_deleted"] += 1
    _recalc_stats(state)
    _save(state)
    return True


_RANKS_CACHE: dict | None = None
_RANKS_CACHE_TS: float = 0


def rebuild_ranks(uid=None):
    """Вычислить GID и LID. Кеш 10с."""
    import time as _t
    now = _t.time()
    global _RANKS_CACHE, _RANKS_CACHE_TS
    if _RANKS_CACHE is not None and now - _RANKS_CACHE_TS < 10:
        if uid is not None:
            return {uid: _RANKS_CACHE.get(uid, {})}
        return _RANKS_CACHE

    state = _load()
    result = {}
    for sid, u in state.get("users", {}).items():
        if uid is not None and int(sid) != uid:
            continue
        active = [(k, v) for k, v in u["sessions"]["list"].items()
                  if v.get("status", SESSION_ACTIVE) in (SESSION_ACTIVE, SESSION_ERROR)]
        active.sort(key=lambda x: x[1].get("created", 0))
        all_active = []
        for u2 in state.get("users", {}).values():
            for k2, v2 in u2["sessions"]["list"].items():
                if v2.get("status", SESSION_ACTIVE) in (SESSION_ACTIVE, SESSION_ERROR):
                    all_active.append((k2, v2))
        all_active.sort(key=lambda x: x[1].get("created", 0))

        user_result = {}
        for lid, (key, _) in enumerate(active, 1):
            try:
                gid = next(i for i, (k, _) in enumerate(all_active, 1) if k == key)
            except StopIteration:
                gid = lid
            user_result[key] = {"gid": gid, "lid": lid}
        result[int(sid)] = user_result

    _RANKS_CACHE = result
    _RANKS_CACHE_TS = now
    return result


def resolve_session(uid, query):
    """Найти сессию по gid/lid/имени/ключу.
    Возвращает (key, session_dict) или (None, None)."""
    if not query:
        return None, None

    state = _load()
    ranks = rebuild_ranks(uid)
    user_ranks = ranks.get(uid, {})

    # прямой ключ
    for sid in state.get("users", {}):
        u = state["users"][sid]
        if query in u["sessions"]["list"]:
            return query, u["sessions"]["list"][query]

    super_mode = uid == SUPER_USER

    # цифра → lid (свой) или gid (с префиксом g)
    if query.lstrip("-").isdigit():
        n = int(query)
        # сначала lid среди своих
        for key, r in user_ranks.items():
            if r["lid"] == n:
                u = state["users"].get(str(uid), {})
                if key in u.get("sessions", {}).get("list", {}):
                    return key, u["sessions"]["list"][key]
        # если super, то gid
        if super_mode:
            for sid, u in state.get("users", {}).items():
                for key, s in u.get("sessions", {}).get("list", {}).items():
                    r = rebuild_ranks(int(sid)).get(int(sid), {}).get(key, {})
                    if r.get("gid") == n:
                        return key, s

    # g префикс → gid
    if query.lower().startswith("g") and query[1:].lstrip("-").isdigit():
        n = int(query[1:])
        for sid, u in state.get("users", {}).items():
            for key, s in u.get("sessions", {}).get("list", {}).items():
                r = rebuild_ranks(int(sid)).get(int(sid), {}).get(key, {})
                if r.get("gid") == n:
                    return key, s

    # частичное совпадение по имени
    ql = query.lower()
    for sid, u in state.get("users", {}).items():
        for key, s in u.get("sessions", {}).get("list", {}).items():
            name = s.get("name", "").lower()
            if ql in name:
                return key, s

    return None, None


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


def get_session_full(uid):
    """Возвращает dict со всеми данными сессии для рендеринга футера/статуса."""
    from config import DEFAULT_MODEL
    user = get_user(uid)
    if not user:
        return None

    model = user.get("model") or DEFAULT_MODEL
    role = user.get("role", "normal")
    key, sess = get_current_session(uid)
    fcount, fsize = get_quota(uid)

    # gid / lid
    gid, lid = None, None
    if key:
        ranks = rebuild_ranks(uid)
        user_ranks = ranks.get(uid, {})
        r = user_ranks.get(key, {})
        gid, lid = r.get("gid"), r.get("lid")

    usage = sess.get("usage", {}) or {} if sess else {}
    cost = sess.get("cost", 0) or 0 if sess else 0
    last_msg = sess.get("last_msg", {}) or {} if sess else {}

    result = {
        "uid": uid,
        "name": user.get("name", ""),
        "role": role,
        "model": model,
        "context": _context_limit(model),

        "gid": gid,
        "lid": lid,
        "session_name": sess["name"] if sess else "-",
        "session_key": key,
        "session_created": sess["created"] if sess else 0,
        "session_status": sess.get("status", SESSION_ACTIVE) if sess else SESSION_DEAD,
        "messages": sess["messages"] if sess else 0,
        "tokens": sess.get("tokens", 0) if sess else 0,
        "last_input": last_msg.get("input", 0) or 0,
        "last_output": last_msg.get("output", 0) or 0,
        "cum_input": usage.get("input", 0) or 0,
        "cum_output": usage.get("output", 0) or 0,
        "cost": cost,
        "last_msg": last_msg,
        "usage": usage,

        "storage_used": fsize,
        "file_count": fcount,
    }

    limits = user.get("limits")
    if role == "super" or not limits:
        result["msg_limit"] = None
        result["storage_limit"] = None
        result["file_limit"] = None
    else:
        result["msg_limit"] = limits.get("msg", 50)
        result["storage_limit"] = limits.get("storage_mb", 500) * 1_000_000
        result["file_limit"] = limits.get("file_count", 1000)

    return result


def _context_limit(model: str) -> int:
    MAP = {
        "opus-4.7": 1_000_000, "opus-4.6": 1_000_000, "sonnet-4.6": 1_000_000,
        "opus-4.5": 200_000, "opus-4.1": 200_000, "opus-4": 200_000,
        "sonnet-4.5": 200_000, "sonnet-4": 200_000, "haiku-4": 200_000,
        "haiku": 200_000, "opus": 200_000, "sonnet": 200_000, "claude": 200_000,
        "gpt-5.5": 1_000_000, "gpt-5.4": 1_000_000,
        "gpt-5.3": 1_000_000, "gpt-5.2": 1_000_000, "gpt-5.1": 1_000_000,
        "gpt-5-nano": 128_000, "gpt-5": 400_000, "gpt-4": 128_000,
        "deepseek-v4-flash-free": 1_000_000, "deepseek-v4-flash": 1_000_000,
        "deepseek-v4-pro": 1_000_000, "deepseek-chat": 1_000_000,
        "deepseek-reasoner": 1_000_000, "deepseek": 1_000_000,
        "gemini-3.1-pro": 1_000_000, "gemini-3-pro": 1_000_000,
        "gemini-3": 1_000_000, "gemini-2.5": 1_000_000,
        "gemini-2.0": 1_000_000, "gemini": 1_000_000,
        "kimi-k2.6": 256_000, "kimi-k2.5": 128_000, "kimi": 128_000,
        "qwen3": 131_072, "qwen": 128_000,
        "minimax-m2": 1_000_000, "minimax-m1": 1_000_000, "minimax": 1_000_000,
        "glm-5": 200_000, "glm-4.7": 200_000, "glm-4.6": 200_000,
        "glm-4.5": 128_000, "glm-4": 128_000,
        "nemotron": 128_000, "mistral": 128_000,
    }
    m = model.lower()
    for key, ctx in MAP.items():
        if key in m:
            return ctx
    return 64_000


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
        u["sessions"]["list"][key].pop("usage", None)
        u["sessions"]["list"][key].pop("cost", None)
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
        total = 0
        inp_total = 0
        out_total = 0
        cost = 0.0
        raw = proc.stdout.strip()
        if raw:
            if not raw.endswith("}"):
                raw += "}"
            if raw.startswith("["):
                raw = '{"messages": ' + raw + "}"
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                log.warning(f"update_session_tokens: JSON parse failed, trying lenient")
                import re
                m = re.search(r'"total"\s*:\s*(\d+)', raw)
                if m:
                    total = int(m.group(1))
                else:
                    log.warning(f"update_session_tokens: no total found in export")
                    return
            else:
                # get session-level token info and cost from `info`
                info = data.get("info", {})
                info_tok = info.get("tokens", {}) or {}
                inp_total = info_tok.get("input", 0) or 0
                out_total = info_tok.get("output", 0) or 0
                cost = info.get("cost", 0) or 0.0
                # get last message total from messages
                messages = data.get("messages", [])
                if isinstance(messages, list):
                    for item in reversed(messages):
                        tok_data = item.get("tokens") if isinstance(item, dict) else None
                        if tok_data:
                            if isinstance(tok_data, dict):
                                total = tok_data.get("total", 0) or 0
                            elif isinstance(tok_data, (int, float)):
                                total = int(tok_data)
                            break
        else:
            log.warning(f"update_session_tokens: empty export for {opencode_id}")
            return
        state = _load()
        sid = str(uid)
        u = state["users"].get(sid)
        if u and key in u["sessions"]["list"]:
            sess = u["sessions"]["list"][key]
            old = sess.get("tokens", 0)
            sess["tokens"] = total
            sess["usage"] = {"input": inp_total, "output": out_total}
            sess["cost"] = round(cost, 6)
            _save(state)
            log.info(f"update_session_tokens: uid={uid} key={key} tokens {old}->{total} "
                     f"in={inp_total} out={out_total} cost=${cost}")
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
