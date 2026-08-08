import json
import subprocess
import os
from datetime import datetime
from config import SUPER_USER, DEFAULT_MODEL, WORKSPACE_DIR, TG_ALL_DIR
from session import (
    list_users, get_user, user_exists, add_user, remove_user,
    auto_session, create_session, switch_session, rename_session,
    drop_session, get_current_session, increment_msg, get_quota,
    set_user_model, set_default_model, set_limit, ensure_super,
    get_session_opencode_id, set_session_opencode_id, reset_opencode_id,
    get_session_agent, is_super,
    set_build_mode, get_build_mode,
    save_last_task, clear_last_task, reset_session_counters,
    append_model_history,
    link_platforms, add_platform_link, user_dir, session_run_dir, auto_platform,
)
from security import run_opencode, pre_filter
import monitor as _Mon
from session import list_unauthorized, set_session_tokens
from templates import build_footer, fmt_user_info, fmt_quota, fmt_session_list, _short_model

_all_models_cache = []
_all_models_time = 0


def _get_models(force=False):
    global _all_models_cache, _all_models_time
    import time
    now = time.time()
    if not force and _all_models_cache and now - _all_models_time < 300:
        return _all_models_cache
    try:
        proc = subprocess.run(["opencode", "models"], capture_output=True, text=True, timeout=30)
        _all_models_cache = [m.strip() for m in proc.stdout.strip().split("\n") if m.strip()]
        _all_models_time = now
    except:
        _all_models_cache = []
    return _all_models_cache


def _model_by_number(n_str):
    models = _get_models()
    try:
        idx = int(n_str) - 1
        if 0 <= idx < len(models):
            return models[idx]
    except ValueError:
        pass
    return None


def block(text: str) -> str:
    return f"⚠️ Действие запрещено политикой безопасности.\n{text}"


def _check_user(uid):
    if not user_exists(uid):
        return "❌ Доступ запрещён."
    return None


def cmd_start(uid):
    err = _check_user(uid)
    if err:
        return err
    ensure_super()
    key = auto_session(uid)
    user = get_user(uid)
    sname = get_current_session(uid)
    name = sname[1]["name"] if sname[1] else "unnamed"
    return f"👋 Добро пожаловать, {user.get('name', uid)}!\nАктивна сессия: \"{name}\"\n\nКоманды: /info, /new, /sessions, /models"


def cmd_new(uid, name=None):
    err = _check_user(uid)
    if err:
        return err
    key = create_session(uid, name)
    if key:
        return f"✅ Сессия '{name or '[авто]'}' создана и активирована."
    return "❌ Ошибка создания сессии."


def cmd_sessions(uid):
    err = _check_user(uid)
    if err:
        return err
    return fmt_session_list(uid)


def cmd_switch(uid, key):
    err = _check_user(uid)
    if err:
        return err
    if switch_session(uid, key):
        return f"✅ Переключено на сессию [{key}]"
    return "❌ Сессия не найдена."


def cmd_rename(uid, key, new_name):
    err = _check_user(uid)
    if err:
        return err
    if rename_session(uid, key, new_name):
        return f"✅ Сессия [{key}] переименована в \"{new_name}\""
    return "❌ Сессия не найдена."


def cmd_drop(uid):
    err = _check_user(uid)
    if err:
        return err
    if drop_session(uid):
        return "✅ Сессия удалена."
    return "❌ Нет активной сессии для удаления."


def cmd_info(uid):
    err = _check_user(uid)
    if err:
        return err
    from templates import fmt_user_info
    return fmt_user_info(uid)


def cmd_quota(uid):
    err = _check_user(uid)
    if err:
        return err
    return fmt_quota(uid)


def _get_providers_map():
    all_models = _get_models()
    groups = {}
    for m in all_models:
        prefix = m.split("/")[0] if "/" in m else "system"
        groups.setdefault(prefix, []).append(m)
    sorted_providers = sorted(groups.keys())
    return all_models, groups, sorted_providers


def cmd_models(uid, arg=None):
    err = _check_user(uid)
    if err:
        return err
    all_models, groups, sorted_providers = _get_providers_map()
    if not all_models:
        return "❌ Не удалось получить список моделей."

    total = len(all_models)
    provider_count = len(sorted_providers)

    if not arg or arg == "":
        lines = [f"📋 Провайдеры ({total} моделей):"]
        for num, prov in enumerate(sorted_providers, 1):
            ms = groups[prov]
            lines.append(f"  {num: >3}. 🔹 {prov} ({len(ms)})")
        lines.append("")
        lines.append("/models <номер> — модели провайдера по номеру из списка")
        lines.append("/models <провайдер> — модели провайдера по имени")
        lines.append("/models <строка> — поиск по имени")
        lines.append("/models all — все модели с номерами")
        if is_super(uid):
            lines.append("/setmodel <провайдер> <модель> — назначить модель по провайдеру и модели")
        else:
            lines.append("/request model <имя или номер> — запросить модель")
        return "\n".join(lines)

    if arg == "all":
        lines = [f"📋 Все модели ({total}):"]
        for num, m in enumerate(all_models, 1):
            lines.append(f"  {num: >4}. {m}")
        return "\n".join(lines)

    if arg.isdigit():
        n = int(arg)
        if 1 <= n <= provider_count:
            prov = sorted_providers[n - 1]
            ms = groups[prov]
            start_num = all_models.index(ms[0]) + 1
            lines = [f"📋 {prov} ({len(ms)}):"]
            for i, m in enumerate(ms, start_num):
                lines.append(f"  {i: >4}. {m}")
            return "\n".join(lines)
        page = n
        page_size = 30
        start = (page - 1) * page_size
        batch = all_models[start:start + page_size]
        if not batch:
            return f"❌ Страница не найдена. Всего: {total}"
        total_pages = (total + page_size - 1) // page_size
        lines = [f"📋 Модели ({total}) — стр. {page}/{total_pages}:"]
        for i, m in enumerate(batch, start + 1):
            lines.append(f"  {i: >4}. {m}")
        return "\n".join(lines)

    if arg in groups:
        ms = groups[arg]
        start_num = all_models.index(ms[0]) + 1
        lines = [f"📋 {arg} ({len(ms)}):"]
        for i, m in enumerate(ms, start_num):
            lines.append(f"  {i: >4}. {m}")
        return "\n".join(lines)

    parts = arg.split(maxsplit=1)
    if parts[0] in groups:
        prov = parts[0]
        ms = groups[prov]
        if len(parts) > 1 and parts[1].isdigit():
            n = int(parts[1])
            if 1 <= n <= len(ms):
                return f"📋 {prov} #{n}: {ms[n - 1]}"
            return f"❌ У провайдера {prov} всего {len(ms)} моделей."
        query = parts[1].lower() if len(parts) > 1 else ""
        if query:
            ms = [m for m in ms if query in m.lower()]
        start_num = all_models.index(ms[0]) + 1 if ms else 0
        label = f"📋 {prov} — \"{query}\" ({len(ms)}):" if query else f"📋 {prov} ({len(ms)}):"
        lines = [label]
        for i, m in enumerate(ms[:30], start_num):
            lines.append(f"  {i: >4}. {m}")
        if len(ms) > 30:
            lines.append(f"  ... и ещё {len(ms) - 30}")
        return "\n".join(lines)

    filtered = [m for m in all_models if arg.lower() in m.lower()]
    if not filtered:
        return f"❌ Ничего не найдено по \"{arg}\"."
    lines = [f"📋 Результаты поиска \"{arg}\" ({len(filtered)}):"]
    for i, m in enumerate(filtered[:30], 1):
        num = all_models.index(m) + 1
        lines.append(f"  {num: >4}. {m}")
    if len(filtered) > 30:
        lines.append(f"  ... и ещё {len(filtered) - 30}")
    return "\n".join(lines)


def cmd_request_model(uid, model_name):
    if is_super(uid):
        return "✅ Super может назначить модель через /setmodel."
    if not model_name:
        return "❌ Укажи модель: /request model <имя или номер>\nСписок: /models"
    resolved = _model_by_number(model_name) or model_name
    super_user = get_user(SUPER_USER)
    sname = super_user.get("name", "super") if super_user else "super"
    return (
        f"📩 Запрос на модель отправлен @{sname}\n\n"
        f"Super: /approve-model {uid} {resolved}\n"
        f"Super: /deny {uid}"
    )


def cmd_request_limit(uid, limit_type, value):
    if is_super(uid):
        return "✅ Super может установить лимит через /setlimit."
    if limit_type not in ("msg", "token", "storage", "file"):
        return "❌ Тип: msg, token, storage, file"
    if not value or not value.isdigit():
        return "❌ Укажи число."
    super_user = get_user(SUPER_USER)
    sname = super_user.get("name", "super") if super_user else "super"
    return (
        f"📩 Запрос на лимит {limit_type}={value} отправлен @{sname}\n\n"
        f"Super: /approve {uid} {limit_type} {value}\n"
        f"Super: /deny {uid}"
    )


def _is_session_error(resp=None, err_msg=None) -> bool:
    if err_msg and ("Session not found" in err_msg or "session not found" in err_msg.lower()):
        return True
    if resp and ("Session not found" in resp or "session not found" in resp.lower()):
        return True
    return False


def cmd_message(uid, text):
    err = _check_user(uid)
    if err:
        return None, err, []

    user = get_user(uid)
    if not user:
        return None, "❌ Пользователь не найден.", []

    if not is_super(uid):
        limits = user.get("limits")
        if limits:
            key, sess = get_current_session(uid)
            msgs = sess["messages"] if sess else 0
            if msgs >= limits.get("msg", 50):
                return None, "❌ Лимит сообщений исчерпан. Обратитесь к администратору.", []

            fcount, fsize = get_quota(uid)
            storage_mb = limits.get("storage_mb", 500)
            if fsize >= storage_mb * 1_000_000:
                return None, "❌ Лимит хранилища исчерпан. Очистите файлы (/clean) или обратитесь к администратору.", []
            file_limit = limits.get("file_count", 1000)
            if fcount >= file_limit:
                return None, "❌ Лимит количества файлов исчерпан.", []

        blocked, reason = pre_filter(uid, text)
        if blocked:
            return None, f"⚠️ Действие запрещено политикой безопасности.\nПричина: {reason}", []

    model = user.get("model")
    if not model and not is_super(uid):
        model = DEFAULT_MODEL

    key, sess = get_current_session(uid)
    if not key:
        key = auto_session(uid)

    opencode_id = get_session_opencode_id(uid, key) if sess else None

    if is_super(uid):
        u = get_user(uid)
        cd = u.get("_cwd") if u else None
        plat = auto_platform(uid)
        wd = cd or session_run_dir(uid, plat)
    else:
        plat = auto_platform(uid)
        wd = session_run_dir(uid, plat)
    wd.mkdir(parents=True, exist_ok=True)

    before = set(wd.rglob("*.[pj][np]g"))

    sname = sess["name"] if sess else key
    title = sname if not opencode_id else None
    if is_super(uid) and get_build_mode(uid):
        agent = None
        agent_label = "build"
    elif not is_super(uid):
        has_session = bool(opencode_id)
        agent = get_session_agent(uid, key) or (None if not has_session else "tg-reader")
        agent_label = agent or "tg-reader"
    else:
        agent = get_session_agent(uid, key) or "plan"
        agent_label = agent

    save_last_task(uid, text, key)

    # save session token baseline before this run
    from session import get_session_full
    sd = get_session_full(uid)
    _Mon.set_offset(
        uid, sd["tokens"],
        inp=sd["cum_input"], out=sd["cum_output"], cost=sd["cost"]
    )

    try:
        resp, parsed_sid, json_lines, err_msg = run_opencode(
            uid, text, opencode_id=opencode_id, model=model, work_dir=wd,
            title=title, agent=agent
        )
        # Auto-retry: if session expired, reset and try again
        if _is_session_error(resp, err_msg):
            reset_opencode_id(uid, key)
            key, sess = get_current_session(uid)
            opencode_id = get_session_opencode_id(uid, key) if sess else None
            if not opencode_id:
                auto_session(uid)
                key, sess = get_current_session(uid)
            sname = sess["name"] if sess else key
            title = sname if not opencode_id else None
            retry_agent = None if not opencode_id else agent
            resp, parsed_sid, json_lines, err_msg = run_opencode(
                uid, text, opencode_id=opencode_id, model=model, work_dir=wd,
                title=title, agent=retry_agent
            )
    finally:
        clear_last_task(uid)

    if err_msg or _is_session_error(resp, None):
        return None, resp or err_msg, [], agent_label

    if parsed_sid and parsed_sid != opencode_id:
        set_session_opencode_id(uid, key, parsed_sid)
        reset_session_counters(uid, key)

    increment_msg(uid)

    live = _Mon.get_final(uid)
    offset = _Mon._offsets.get(uid, 0)
    delta = max(0, live - offset)
    if live:
        set_session_tokens(uid, key, live)

    try:
        from session import _load, _save, _transaction
        with _transaction():
            _sd = _load()
            _sid = str(uid)
            if _sid in _sd["users"] and key in _sd["users"][_sid]["sessions"]["list"]:
                _s = _sd["users"][_sid]["sessions"]["list"][key]
                estimated_input = max(len(text) // 4, 1)
                if delta <= estimated_input:
                    estimated_input = max(delta // 2, 1) if delta > 1 else delta
                    output = delta - estimated_input
                else:
                    output = max(0, delta - estimated_input)
                COST_IN = 0.27 / 1_000_000
                COST_OUT = 1.10 / 1_000_000
                cost_in = round(estimated_input * COST_IN, 4)
                cost_out = round(output * COST_OUT, 4)
                _s["last_msg"] = {"input": estimated_input, "output": output, "cost_in": cost_in, "cost_out": cost_out}
                _usage = _s.setdefault("usage", {"input": 0, "output": 0, "cost_in": 0, "cost_out": 0})
                _usage["input"] += estimated_input
                _usage["output"] += output
                _usage["cost_in"] = round(_usage.get("cost_in", 0) + cost_in, 4)
                _usage["cost_out"] = round(_usage.get("cost_out", 0) + cost_out, 4)
                _s["cost"] = round(_usage.get("cost_in", 0) + _usage.get("cost_out", 0), 4)
                _save(_sd)
    except Exception:
        pass

    after = set(wd.rglob("*.[pj][np]g"))
    new_images = [str(p) for p in (after - before)][:3]
    return resp, None, new_images, agent_label


def cmd_cd(uid, target=None):
    if not is_super(uid):
        return "❌ Только super."
    u = get_user(uid)
    if u is None:
        return "❌ Пользователь не найден."
    state = u
    if not target:
        current = state.get("_cwd", str(WORKSPACE_DIR))
        return f"📁 Текущая директория: {current}"
    if target == "workspace":
        new_dir = str(WORKSPACE_DIR)
    elif target == "tg":
        new_dir = str(user_dir(uid, "tg"))
    else:
        p = target if target.startswith("/") else str(WORKSPACE_DIR / target)
        if not os.path.isdir(p):
            return f"❌ Директория не существует: {p}"
        new_dir = p
    from session import _load, _save, _transaction
    with _transaction():
        state_data = _load()
        sid = str(uid)
        if sid in state_data["users"]:
            state_data["users"][sid]["_cwd"] = new_dir
            _save(state_data)
    return f"✅ Директория: {new_dir}"


def cmd_users(uid):
    if not is_super(uid):
        return "❌ Только super."
    users = list_users()
    lines = ["📋 Пользователи:"]
    for sid, u in users.items():
        role = u.get("role", "normal")
        model = _short_model(u.get("model") or DEFAULT_MODEL)
        limits = u.get("limits")
        lim_str = ""
        if limits:
            lim_str = f" msg:{limits.get('msg','-')} tok:{limits.get('token','-')} str:{limits.get('storage_mb','-')}MB"
        fcount, fsize = get_quota(int(sid))
        from templates import _fmt_size
        lines.append(f"  [{role}] {u.get('name', '?')} ({sid}) {model} {lim_str} 💾{_fmt_size(fsize)} 📄{fcount}")
    return "\n".join(lines)


def _fetch_tg_name(uid_int):
    from config import TOKEN
    import urllib.request, json
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/getChat?chat_id={uid_int}"
        resp = urllib.request.urlopen(url, timeout=10)
        data = json.loads(resp.read())
        if data.get("ok"):
            result = data["result"]
            name = result.get("first_name", "")
            if result.get("last_name"):
                name += f" {result['last_name']}"
            return name.strip() or None
    except Exception:
        pass
    return None


def cmd_adduser(uid, user_id, name=None):
    if not is_super(uid):
        return "❌ Только super."
    try:
        uid_int = int(user_id)
    except:
        return "❌ ID должен быть числом."
    if user_exists(uid_int):
        return "❌ Пользователь уже существует."
    if not name:
        name = _fetch_tg_name(uid_int)
        if not name:
            return "❌ Укажи имя или ID не найден: /adduser <id> <name>"
    add_user(uid_int, name)
    return f"✅ Пользователь {name} ({uid_int}) добавлен.\nНастрой лимиты: /setlimit {uid_int} msg 100\n  /setlimit {uid_int} token 1000000\n  /setlimit {uid_int} storage 500\n  /setmodel {uid_int} {DEFAULT_MODEL}"


def cmd_removeuser(uid, user_id):
    if not is_super(uid):
        return "❌ Только super."
    try:
        uid_int = int(user_id)
    except:
        return "❌ ID должен быть числом."
    remove_user(uid_int)
    return f"✅ Пользователь {uid_int} удалён."


def cmd_link(uid, args):
    if not args:
        return "❌ /link usr_xxxxxxx tg <id> [max <id>]\n/link tg <id>  или  /link max <id>"

    if args[0].startswith("usr_") and is_super(uid):
        internal_uid = args[0]
        if len(args) < 3:
            return "❌ /link usr_xxxxxxx tg <id> [max <id>]"
        err_parts = []
        for i in range(1, len(args), 2):
            if i + 1 >= len(args):
                break
            platform = args[i].lower()
            if platform not in ("tg", "max"):
                err_parts.append(f"❌ Неизвестная платформа: {platform}")
                continue
            try:
                pid = int(args[i + 1])
            except ValueError:
                err_parts.append(f"❌ Неверный id: {args[i+1]}")
                continue
            err = add_platform_link(internal_uid, platform, pid)
            if err:
                err_parts.append(err)
            else:
                err_parts.append(f"✅ {internal_uid} {platform} -> {pid}")
        return "\n".join(err_parts)

    if len(args) == 2:
        platform = args[0].lower()
        platform_id = args[1]
        try:
            pid = int(platform_id)
        except ValueError:
            return "❌ ID должен быть числом."
        if platform == "tg":
            err = link_platforms(pid, uid, caller_uid=uid)
        elif platform == "max":
            err = link_platforms(uid, pid, caller_uid=uid)
        else:
            return f"❌ Неизвестная платформа: {platform}. Используй tg или max."
        if err:
            return err
        return f"✅ Привязан {platform}:{pid} к вашему аккаунту."

    return "❌ Неверный формат."


def cmd_userinfo(uid, target_id=None):
    if not is_super(uid):
        return "❌ Только super."
    if not target_id:
        return "❌ Укажи ID: /userinfo <id>"
    try:
        tid = int(target_id)
    except:
        return "❌ ID должен быть числом."
    return fmt_user_info(tid, as_super=True)


def cmd_view(uid, target_id, session_key):
    if not is_super(uid):
        return "❌ Только super."
    try:
        tid = int(target_id)
    except:
        return "❌ ID должен быть числом."
    user = get_user(tid)
    if not user:
        return "❌ Пользователь не найден."
    sess = user["sessions"]["list"].get(session_key)
    if not sess:
        return "❌ Сессия не найдена."
    cmd = ["opencode", "export", session_key]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=15)
        data = proc.stdout.strip()[:3000] or "(пусто)"
    except:
        data = "(не удалось загрузить)"
    return f"📖 Сессия [{session_key}] ({sess.get('name')}):\n{data}"


def _resolve_provider_model(provider, model):
    all_models, groups, sorted_providers = _get_providers_map()
    if provider.isdigit():
        idx = int(provider) - 1
        if 0 <= idx < len(sorted_providers):
            prov_name = sorted_providers[idx]
        else:
            return None, f"❌ Провайдер #{provider} не найден. Всего: {len(sorted_providers)}"
    else:
        prov_name = provider
        if prov_name not in groups:
            return None, f"❌ Провайдер \"{provider}\" не найден."
    ms = groups[prov_name]
    if model.isdigit():
        midx = int(model) - 1
        if 0 <= midx < len(ms):
            return ms[midx], None
        return None, f"❌ У провайдера {prov_name} всего {len(ms)} моделей."
    matches = [m for m in ms if model.lower() in m.lower()]
    if not matches:
        return None, f"❌ У провайдера {prov_name} нет модели по запросу \"{model}\"."
    return matches[0], None


def _find_model_anywhere(model_query: str) -> tuple[str | None, str | None]:
    """Search model across ALL providers by name or number."""
    all_models, groups, _ = _get_providers_map()
    if model_query.isdigit():
        idx = int(model_query) - 1
        if 0 <= idx < len(all_models):
            return all_models[idx], None
        return None, f"❌ Модель #{model_query} не найдена. Всего: {len(all_models)}"
    # 1. Exact match (full model ID)
    if model_query in all_models:
        return model_query, None
    # 2. Ends-with match (e.g. "deepseek-v4-flash" → ".../deepseek-v4-flash")
    exact_matches = [m for m in all_models if m.endswith(f"/{model_query}") or m == model_query]
    if not exact_matches:
        exact_matches = [m for m in all_models if m.endswith(model_query)]
    if len(exact_matches) == 1:
        return exact_matches[0], None
    if len(exact_matches) > 1:
        # Prefer opencode-go, then opencode, then others
        priority = [m for m in exact_matches if m.startswith("opencode-go/") or m.startswith("opencode/")]
        if priority:
            return priority[0], None
        return exact_matches[0], None
    # 3. Partial match
    matches = []
    for prov_name, ms in groups.items():
        for m in ms:
            if model_query.lower() in m.lower():
                matches.append(m)
    if len(matches) == 1:
        return matches[0], None
    if len(matches) > 1:
        return None, f"❌ Найдено несколько моделей по запросу \"{model_query}\":\n" + "\n".join(f"  {m}" for m in matches[:10])
    return None, f"❌ Модель \"{model_query}\" не найдена."


def _resolve_model_arg(model_arg: str) -> str | None:
    """Parse model arg: 'provider/model' or just 'model' (search all)."""
    if "/" in model_arg:
        parts = model_arg.split("/", 1)
        resolved, err = _resolve_provider_model(parts[0], parts[1])
        if err:
            # Try full match as model ID
            all_models, _, _ = _get_providers_map()
            if model_arg in all_models:
                return model_arg
            return None
        return resolved
    resolved, err = _find_model_anywhere(model_arg)
    return resolved if not err else None


def cmd_setmodel(uid, target, model_str):
    """Установить модель для пользователя.
    
    Форматы:
      /setmodel <uid> <provider/model> [msg_limit]
      /setmodel <uid> <model_name> [msg_limit]
      /setmodel <uid> <model_number> [msg_limit]
      /setmodel default <model>
    """
    if not is_super(uid):
        return "❌ Только super."
    if not model_str:
        return "❌ /setmodel <uid> <модель> [лимит]\n   /setmodel default <модель>"

    parts = model_str.split()
    model_query = parts[0]
    msg_limit = int(parts[1]) if len(parts) > 1 and parts[1].isdigit() else None

    if "/" in model_query:
        provider, model = model_query.split("/", 1)
        resolved, err = _resolve_provider_model(provider, model)
    else:
        resolved, err = _find_model_anywhere(model_query)

    if err:
        return err
    if not resolved:
        return "❌ Модель не найдена."

    if target == "default":
        set_default_model(resolved)
        return f"✅ Модель по умолчанию: {resolved}"
    try:
        tid = int(target)
    except:
        return "❌ ID должен быть числом."
    if not user_exists(tid):
        return "❌ Пользователь не найден."

    set_user_model(tid, resolved)
    append_model_history(tid, resolved, uid)
    reply = f"✅ Модель для {tid}: {resolved}"
    if msg_limit is not None:
        set_limit(tid, "msg", msg_limit)
        reply += f"\n📩 Лимит сообщений: {msg_limit}"
    return reply


def cmd_setlimit(uid, target_id, limit_type, value):
    if not is_super(uid):
        return "❌ Только super."
    if limit_type not in ("msg", "token", "storage", "file"):
        return "❌ Тип: msg, token, storage, file"
    if not value or not value.isdigit():
        return "❌ Укажи число."
    try:
        tid = int(target_id)
    except:
        return "❌ ID должен быть числом."
    if set_limit(tid, limit_type, int(value)):
        return f"✅ Лимит {limit_type}={value} для {tid}"
    return "❌ Пользователь не найден."


def cmd_approve_model(uid, target_id, model):
    if not is_super(uid):
        return "❌ Только super."
    try:
        tid = int(target_id)
    except:
        return "❌ ID должен быть числом."
    model = _resolve_model_arg(model)
    if model is None:
        return "❌ Модель не найдена."
    if set_user_model(tid, model):
        append_model_history(tid, model, uid)
        return f"✅ Запрос одобрен. Модель для {tid}: {model}"
    return "❌ Пользователь не найден."


def cmd_approve(uid, target_id, limit_type, value):
    if not is_super(uid):
        return "❌ Только super."
    if limit_type not in ("msg", "token", "storage", "file"):
        return "❌ Тип: msg, token, storage, file"
    if not value or not value.isdigit():
        return "❌ Укажи число."
    try:
        tid = int(target_id)
    except:
        return "❌ ID должен быть числом."
    if set_limit(tid, limit_type, int(value)):
        return f"✅ Запрос одобрен. Лимит {limit_type}={value} для {tid}"
    return "❌ Пользователь не найден."


def cmd_deny(uid, target_id):
    if not is_super(uid):
        return "❌ Только super."
    return f"❌ Запрос для {target_id} отклонён."


def cmd_build(uid):
    if not is_super(uid):
        return "❌ Только super."
    err = _check_user(uid)
    if err:
        return err
    if set_build_mode(uid, True):
        return "✅ Build mode включён для следующего сообщения. После ответа — автоматически вернусь в plan."
    return "❌ Не удалось включить build mode."


def cmd_plan(uid):
    if not is_super(uid):
        return "❌ Только super."
    err = _check_user(uid)
    if err:
        return err
    if set_build_mode(uid, False):
        return "✅ Plan mode активен."
    return "❌ Не удалось переключить в plan."


def cmd_broadcast(uid, message):
    if not is_super(uid):
        return "❌ Только super."
    if not message:
        return "❌ Укажи текст: /broadcast <сообщение>"
    from config import TOKEN
    import urllib.request, json
    users = list_users()
    sent = 0
    failed = 0
    for sid in users:
        try:
            data = json.dumps({"chat_id": int(sid), "text": f"📢 Рассылка:\n\n{message}"}).encode()
            req = urllib.request.Request(
                f"https://api.telegram.org/bot{TOKEN}/sendMessage",
                data=data,
                headers={"Content-Type": "application/json"}
            )
            urllib.request.urlopen(req, timeout=10)
            sent += 1
        except:
            failed += 1
    return f"✅ Рассылка завершена.\nОтправлено: {sent}\nОшибок: {failed}"


def cmd_sandbox(uid, target_id=None):
    if not is_super(uid):
        return "❌ Только super."
    from templates import _fmt_size
    if target_id:
        try:
            tid = int(target_id)
        except:
            return "❌ ID должен быть числом."
        fcount, fsize = get_quota(tid)
        user = get_user(tid)
        u = user_dir(tid, "tg")
        log = u / "sandbox.log"
        log_content = ""
        if log.exists():
            log_content = log.read_text(errors="replace")[-2000:]
        return (
            f"🏖 Песочница TG_{tid}:\n"
            f"💾 {_fmt_size(fsize)} · 📄 {fcount} файлов\n\n"
            f"📋 Лог нарушений:\n{log_content or '(чисто)'}"
        )
    return "🏖 Песочницы:\n" + "\n".join(
        f"  TG_{sid}: {_fmt_size(get_quota(int(sid))[1])}"
        for sid in list_users()
    )


def cmd_unauthorized(uid):
    if not is_super(uid):
        return "❌ Только super."
    entries = list_unauthorized()
    if not entries:
        return "✅ Нет записей о несанкционированных попытках."
    from datetime import datetime
    lines = [f"🚫 Несанкционированные попытки ({len(entries)}):"]
    for e in entries[-20:]:
        ts = datetime.fromtimestamp(e["time"]).strftime("%d.%m %H:%M")
        uname = e.get("username") or e.get("first_name") or "?"
        text = e.get("text", "")[:40]
        lines.append(f"  [{ts}] {e['uid']} @{uname}: \"{text}\"")
    if len(entries) > 20:
        lines.append(f"  ... и ещё {len(entries) - 20}")
    return "\n".join(lines)


def cmd_shutdown(uid):
    if not is_super(uid):
        return "❌ Только super."
    return "🛑 SHUTDOWN"  # signal for main.py


def cmd_sysinfo(uid):
    if not is_super(uid):
        return "❌ Только super."
    try:
        from system_info import get_system_status
        return get_system_status()
    except Exception as e:
        return f"❌ Ошибка: {e}"


COMMANDS = [
    ("🧠 Сессия", [
        ("/start", "all", "Продолжить или создать сессию"),
        ("/new [имя]", "all", "Создать новую сессию (автоимя если без имени)"),
        ("/sessions", "all", "Список своих сессий"),
        ("/switch <key>", "all", "Переключиться на другую сессию"),
        ("/rename <key> <имя>", "all", "Переименовать сессию"),
        ("/drop", "all", "Удалить активную сессию"),
        ("/dropsession <key>", "all", "Удалить сессию по ключу"),
        ("/purge", "all", "Удалить все сессии кроме активной"),
    ]),
    ("📊 Инфо", [
        ("/menu", "all", "Показать это меню"),
        ("/info", "all", "Статистика: лимиты, модель, сессия, квоты"),
        ("/quota", "all", "Квота хранилища и файлы"),
        ("/files", "all", "Список файлов в uploads"),
        ("/rm <name>", "all", "Удалить файл из uploads"),
        ("/clean", "all", "Очистить uploads"),
        ("/format", "all", "Форматы текста (Markdown, HTML, спойлер)"),
        ("/sysinfo", "all", "Системная информация (CPU, MEM, диски)"),
        ("/status mode <compact|normal|full|auto>", "all", "Режим монитора статуса"),
    ]),
    ("🤖 Модели", [
        ("/models [строка|N|провайдер|all]", "all", "Список/поиск/провайдеры моделей"),
        ("/request model <имя>", "normal", "Запросить модель у super"),
        ("/request limit <тип> <n>", "normal", "Запросить лимит (msg/token/storage/file)"),
        ("/setmodel <id|default> <модель|номер>", "super", "Назначить модель"),
        ("/approve-model <id> <модель>", "super", "Одобрить запрос модели"),
        ("/deny <id>", "super", "Отклонить запрос"),
    ]),
    ("👥 Пользователи", [
        ("/users", "super", "Все пользователи и их лимиты"),
        ("/adduser <id> <name>", "super", "Добавить пользователя"),
        ("/removeuser <id>", "super", "Удалить пользователя"),
        ("/userinfo <id>", "super", "Информация о пользователе"),
        ("/view <id> session <key>", "super", "Читать сессию пользователя"),
        ("/setlimit <id> <тип> <n>", "super", "Установить лимит"),
        ("/approve <id> <тип> <n>", "super", "Одобрить запрос лимита"),
    ]),
    ("📈 Торговля", [
        ("/emj_positions", "super", "Эмодзи-строки позиций Bitget"),
        ("/sc_positions", "super", "Скриншот таблицы позиций Bitget"),
        ("/sc_analytics", "super", "Скриншот графиков аналитики [symbol] [all]"),
        ("/sc_graphs", "super", "Скриншот всех графиков (graphics/all)"),
        ("/positions", "super", "Риск-сводка: маржа, P&L, экспозиция"),
        ("/positions --image", "super", "Риск-сводка как PNG (Rich)"),
        ("/ws_ob <SYMBOL> [depth] [aggr]", "super", "Стакан (пример: /ws_ob BTC 50 1)"),
        ("/wgc <SYMBOL>", "super", "Коллаж виджетов 1d+4h+1h"),
        ("/sc <SYMBOL> [tf] [range]", "super", "TradingView скриншот"),
        ("/wg <SYMBOL> [tf] [range]", "super", "Widget скриншот"),
    ]),
    ("🔍 Аудит", [
        ("/audit_ip <IP>", "super", "Быстрый аудит IP (top-50 портов)"),
        ("/audit_ip --deep <IP>", "super", "Глубокий аудит (top-50 → top-1000 → 65535 + CVE)"),
        ("/audit_inn <INN>", "super", "Аудит ИНН: ЕГРЮЛ, банкротства"),
    ]),
    ("📟 ОФД-Я", [
        ("/ofd_kkt", "super", "Список касс ККТ"),
        ("/ofd_inn [INN]", "super", "ИНН организации по токену"),
        ("/ofd_receipts <fn> <date> [items]", "super", "Чеки за сутки по ФН"),
        ("/ofd_shift <fn>", "super", "Список смен по ФН"),
        ("/ofd_stat <fn>", "super", "Статистика документов по ФН"),
        ("/ofd_orgs", "super", "Сохранённые организации"),
    ]),
    ("🛠 Админ", [
        ("/stop", "super", "Остановить активный процесс"),
        ("/restart", "super", "Перезапустить бота"),
        ("/task_stats", "super", "Статистика выполнения задач"),
        ("/task_errors", "super", "Ошибки задач"),
        ("/cd [dir]", "super", "Сменить рабочую директорию"),
        ("/broadcast <текст>", "super", "Рассылка всем пользователям"),
        ("/sandbox [id]", "super", "Логи нарушений песочницы"),
        ("/unauthorized", "super", "Попытки входа без регистрации"),
        ("/build", "super", "Build mode"),
        ("/plan", "super", "Plan mode"),
    ]),
]


DANGEROUS_COMMANDS = [
    "/shutdown",
]


def cmd_menu(uid):
    from session import get_user
    user = get_user(uid)
    role = user.get("role", "normal") if user else "normal"
    lines = [f"📋 Команды бота (роль: {role}):\n"]
    for section_name, section_cmds in COMMANDS:
        lines.append(f"\n{section_name}")
        for cmd, access, desc in section_cmds:
            if access == "super" and role != "super":
                continue
            lines.append(f"  {cmd:30s} — {desc}")
    if role == "super" and DANGEROUS_COMMANDS:
        lines.append("")
        lines.append("  ⚠️  ────  ОСТОРОЖНО  ────  ⚠️")
        for cmd in DANGEROUS_COMMANDS:
            lines.append(f"  {cmd:>30s}")
    lines.append("")
    lines.append("Любой другой текст → opencode (AI-ассистент)")
    return "\n".join(lines)


def cmd_files(uid):
    err = _check_user(uid)
    if err:
        return err
    from templates import _fmt_size
    u = user_dir(uid, "tg") / "uploads"
    if not u.exists():
        return "📂 (пусто)"
    files = sorted(u.iterdir(), key=lambda p: p.stat().st_mtime, reverse=True)
    if not files:
        return "📂 (пусто)"
    lines = [f"📂 Файлы ({len(files)}):"]
    for f in files[:20]:
        sz = _fmt_size(f.stat().st_size)
        from datetime import datetime
        mt = datetime.fromtimestamp(f.stat().st_mtime).strftime("%d.%m %H:%M")
        lines.append(f"  {f.name}  {sz}  {mt}")
    if len(files) > 20:
        lines.append(f"  ... и ещё {len(files) - 20}")
    return "\n".join(lines)


def cmd_rm(uid, filename):
    err = _check_user(uid)
    if err:
        return err
    path = user_dir(uid, "tg") / "uploads" / filename
    if not path.exists() or not path.is_file():
        return "❌ Файл не найден."
    path.unlink()
    return f"✅ Файл {filename} удалён."


def cmd_purge(uid):
    err = _check_user(uid)
    if err:
        return err
    from session import _load, _save, _transaction
    with _transaction():
        state = _load()
        sid = str(uid)
        u = state["users"].get(sid)
        if not u:
            return "❌ Пользователь не найден."
        current = u["sessions"]["current"]
        all_sessions = u["sessions"]["list"]
        kept = {k: v for k, v in all_sessions.items() if k == current}
        removed = len(all_sessions) - len(kept)
        if removed == 0:
            return "✅ Нет сессий для удаления."
        u["sessions"]["list"] = kept
        _save(state)
    name = kept[current]["name"] if kept and current else "-"
    return f"✅ Удалено {removed} сессий. Активная: \"{name}\""


def cmd_dropsession(uid, key):
    err = _check_user(uid)
    if err:
        return err
    from session import _load, _save, _transaction
    with _transaction():
        state = _load()
        sid = str(uid)
        u = state["users"].get(sid)
        if not u or key not in u["sessions"]["list"]:
            return "❌ Сессия не найдена."
        if key == u["sessions"]["current"]:
            return "❌ Нельзя удалить активную сессию. Используй /drop."
        name = u["sessions"]["list"][key]["name"]
        del u["sessions"]["list"][key]
        _save(state)
    return f"✅ Сессия \"{name}\" [{key}] удалена."


def cmd_clean(uid):
    err = _check_user(uid)
    if err:
        return err
    import shutil
    u = user_dir(uid, "tg") / "uploads"
    if u.exists():
        count = sum(1 for f in u.iterdir() if f.is_file())
        shutil.rmtree(u)
        u.mkdir(exist_ok=True)
        return f"✅ uploads/ очищен. Удалено {count} файлов."
    return "✅ (уже пусто)"
