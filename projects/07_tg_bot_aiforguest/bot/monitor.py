import asyncio
import json
import os
import subprocess
import time as _time
from collections import defaultdict
from templates import _fmt_tokens, _fmt_size, _short_model
from session import _context_limit
from system_info import get_uptime

_log = None


def _log_init():
    global _log
    if _log is None:
        import logging
        _log = logging.getLogger("tg_bot")


_processes: dict[int, subprocess.Popen] = {}
_starts: dict[int, float] = {}
_tokens: dict[int, int] = {}
_offsets: dict[int, int] = {}
_finals: dict[int, int] = {}
_deltas: dict[int, int] = {}
_actives: dict[int, dict] = {}
_input_tokens: dict[int, int] = {}
_output_tokens: dict[int, int] = {}
_cost: dict[int, float] = {}
_input_offsets: dict[int, int] = {}
_output_offsets: dict[int, int] = {}
_cost_offsets: dict[int, float] = {}
_input_finals: dict[int, int] = {}
_output_finals: dict[int, int] = {}
_cost_finals: dict[int, float] = {}


# ── State API ──

def register(uid: int, proc: subprocess.Popen):
    _processes[uid] = proc
    _starts[uid] = _time.time()


def set_offset(uid: int, offset: int, inp=0, out=0, cost=0.0):
    _offsets[uid] = offset
    _input_offsets[uid] = inp
    _output_offsets[uid] = out
    _cost_offsets[uid] = cost


def update_tokens(uid: int, value: int, inp=0, out=0, cost=0.0):
    if value > _tokens.get(uid, 0):
        _tokens[uid] = value
    if inp > _input_tokens.get(uid, 0):
        _input_tokens[uid] = inp
    if out > _output_tokens.get(uid, 0):
        _output_tokens[uid] = out
    if cost > _cost.get(uid, 0):
        _cost[uid] = cost


def finalize(uid: int):
    tok = _tokens.get(uid, 0)
    off = _offsets.get(uid, 0)
    _finals[uid] = tok
    _deltas[uid] = max(0, tok - off)
    _input_finals[uid] = max(0, _input_tokens.get(uid, 0) - _input_offsets.get(uid, 0))
    _output_finals[uid] = max(0, _output_tokens.get(uid, 0) - _output_offsets.get(uid, 0))
    _cost_finals[uid] = max(0.0, _cost.get(uid, 0.0) - _cost_offsets.get(uid, 0.0))


def get_final(uid: int) -> int:
    return _finals.get(uid, 0)


def get_delta(uid: int) -> int:
    return _deltas.get(uid, 0)


def get_session_usage(uid: int, sess: dict | None) -> dict:
    if not sess:
        return {"total": 0, "input": 0, "output": 0, "cost": 0.0}
    usage = sess.get("usage", {}) or {}
    cost = sess.get("cost", 0) or 0
    return {
        "total": sess.get("tokens", 0) or 0,
        "input": usage.get("input", 0) or 0,
        "output": usage.get("output", 0) or 0,
        "cost": cost,
    }


def cleanup(uid: int):
    _processes.pop(uid, None)
    _starts.pop(uid, None)
    _tokens.pop(uid, None)
    _offsets.pop(uid, None)
    # keep _finals for get_final()
    _deltas.pop(uid, None)
    _actives.pop(uid, None)
    _input_tokens.pop(uid, None)
    _output_tokens.pop(uid, None)
    _cost.pop(uid, None)
    _input_offsets.pop(uid, None)
    _output_offsets.pop(uid, None)
    _cost_offsets.pop(uid, None)
    _input_finals.pop(uid, None)
    _output_finals.pop(uid, None)
    _cost_finals.pop(uid, None)


def is_active(uid: int) -> bool:
    proc = _processes.get(uid)
    return proc is not None and proc.returncode is None


def get_process(uid: int) -> subprocess.Popen | None:
    return _processes.get(uid)


# ── Imports from templates ──
# _fmt_tokens, _fmt_size, _short_model, _context_hint

_user_status_mode: dict[int, str] = {}  # "auto" | "compact" | "normal" | "full"
_user_name_cache: dict[int, str] = {}


def set_status_mode(uid: int, mode: str):
    if mode in ("auto", "compact", "normal", "full"):
        _user_status_mode[uid] = mode


def get_status_mode(uid: int) -> str:
    return _user_status_mode.get(uid, "auto")


# cache for task state (refresh every 10s)
_TASK_CACHE_DATA = None
_TASK_CACHE_TS = 0
_TASK_CACHE_SUMMARY = {"ok": 0, "running": 0, "skip": 0, "fail": 0}


def get_task_data(force=False):
    """Загрузить task_state.json с кешем на 10с"""
    global _TASK_CACHE_DATA, _TASK_CACHE_TS, _TASK_CACHE_SUMMARY
    import time as _t
    now = _t.time()
    if not force and _TASK_CACHE_DATA is not None and now - _TASK_CACHE_TS < 10:
        return _TASK_CACHE_DATA, _TASK_CACHE_SUMMARY

    try:
        from task_state import _load, cleanup_stale
        data = _load()
        data = cleanup_stale(data, max_age=300, save=False)
    except Exception:
        data = {"tasks": {}}

    _TASK_CACHE_DATA = data
    _TASK_CACHE_TS = now

    summary = {"ok": 0, "running": 0, "skip": 0, "fail": 0}
    for tid, task in data.get("tasks", {}).items():
        s = task.get("status", "")
        if s == "completed":
            summary["ok"] += 1
        elif s in ("running", "queued"):
            summary["running"] += 1
        elif s == "failed":
            summary["fail"] += 1
        else:
            summary["skip"] += 1

    _TASK_CACHE_SUMMARY = summary
    return data, summary


# ── Metrics log reader ──

_METRICS_CACHE: list[dict] = []
_METRICS_TS: float = 0


def _read_metrics_log(n: int = 2) -> list[dict]:
    global _METRICS_CACHE, _METRICS_TS
    now = _time.time()
    if now - _METRICS_TS < 2:
        return _METRICS_CACHE[-n:] if _METRICS_CACHE else []
    _METRICS_TS = now
    try:
        log = "/tmp/opencode/metrics.log"
        if not os.path.exists(log):
            return []
        with open(log) as f:
            raw = f.read().strip().split("\n")
        points = []
        for line in raw:
            try:
                entry = json.loads(line)
                if "_type" not in entry:
                    points.append(entry)
            except json.JSONDecodeError:
                continue
        _METRICS_CACHE = points
        return points[-n:] if points else []
    except Exception:
        return []


# ── DISK / NET max speed trackers (updated from metrics.log) ──

_DISK_PREV = {"max_read": 0, "max_write": 0}
_NET_PREV = {"max_rx": 0, "max_tx": 0}


def _fmt_speed(v):
    v = int(v)
    if v >= 1_000_000_000:
        return f"{v/1_000_000_000:.1f}G"
    if v >= 1_000_000:
        return f"{v/1_000_000:.0f}M"
    if v >= 1000:
        return f"{v/1000:.0f}K"
    return str(v)


async def status_block1(uid: int, elapsed: int) -> list:
    pts = _read_metrics_log(2)
    if not pts:
        return [f"⏳ {elapsed//60:02d}:{elapsed%60:02d} · ⏎ Waiting for metrics..."]

    p = pts[-1]
    cpu = p.get("cpu", 0)
    mem_u = p.get("mem", {}).get("u", 0)
    dsk = p.get("dsk", {})
    net = p.get("net", {})

    # скорости из дельты между 2 точками
    if len(pts) >= 2 and pts[-1]["ts"] - pts[-2]["ts"] > 1:
        dt = pts[-1]["ts"] - pts[-2]["ts"]
        dsk_r_spd = (pts[-1]["dsk"]["rt"] - pts[-2]["dsk"]["rt"]) / dt
        dsk_w_spd = (pts[-1]["dsk"]["wt"] - pts[-2]["dsk"]["wt"]) / dt
        net_rx_spd = (pts[-1]["net"]["rx"] - pts[-2]["net"]["rx"]) / dt
        net_tx_spd = (pts[-1]["net"]["tx"] - pts[-2]["net"]["tx"]) / dt
    else:
        dsk_r_spd = dsk_w_spd = net_rx_spd = net_tx_spd = 0

    from session import get_session_full
    sd = get_session_full(uid)

    lines = []
    line1 = (
        f"⏳ {elapsed//60:02d}:{elapsed%60:02d} · ⚡ {cpu:.1f}% · 🧠 {mem_u}MB"
        f" · 💾 R:{_fmt_speed(dsk.get('rt',0))} W:{_fmt_speed(dsk.get('wt',0))}"
        f" · 🌐 RX:{_fmt_speed(net.get('rx',0))} TX:{_fmt_speed(net.get('tx',0))}"
    )
    lines.append(line1)

    dsk_r_mx = _DISK_PREV.get("max_read", 0)
    dsk_w_mx = _DISK_PREV.get("max_write", 0)
    net_rx_mx = _NET_PREV.get("max_rx", 0)
    net_tx_mx = _NET_PREV.get("max_tx", 0)
    if dsk_r_spd > dsk_r_mx:
        _DISK_PREV["max_read"] = dsk_r_spd
        dsk_r_mx = dsk_r_spd
    if dsk_w_spd > dsk_w_mx:
        _DISK_PREV["max_write"] = dsk_w_spd
        dsk_w_mx = dsk_w_spd
    if net_rx_spd > net_rx_mx:
        _NET_PREV["max_rx"] = net_rx_spd
        net_rx_mx = net_rx_spd
    if net_tx_spd > net_tx_mx:
        _NET_PREV["max_tx"] = net_tx_spd
        net_tx_mx = net_tx_spd

    line2 = (
        f"💿 Rmax:{_fmt_speed(dsk_r_mx)}/s Wmax:{_fmt_speed(dsk_w_mx)}/s"
        f" · 📡 RXmax:{_fmt_speed(net_rx_mx)}/s TXmax:{_fmt_speed(net_tx_mx)}/s"
    )
    lines.append(line2)

    sess_tok = sd["tokens"] if sd else 0
    from templates import _fmt_tokens as _ft
    cost_avg = 0.000000685
    tok_cost = round(cpu * cost_avg, 4)
    sess_cost = round(sess_tok * cost_avg, 4)
    line3 = (
        f"↙ 0💲0.00 · ↗ {_ft(int(cpu))}💲{tok_cost:.2f}"
        f" · 🔤 +{_ft(int(cpu))}💲{tok_cost:.2f}"
        f" · 📊 {_ft(sess_tok)}💲{sess_cost:.2f}"
    )
    lines.append(line3)

    return lines


async def status_block3() -> list:
    pts = _read_metrics_log(1)
    if not pts or "top" not in pts[0]:
        t5 = await top5()  # fallback
        if not t5:
            return []
        return ["📊 Top 5 proc:"] + t5

    top_data = pts[0]["top"]
    if not top_data:
        return []

    c_len = max(len(e[0]) for e in top_data) + 2
    head_name = "NAME"
    header = f"  {head_name:{c_len}s} {'CPU':>7s} {'MEM':>6s} {'CNT':>4s} {'ELAPSED':>8s}"
    rows = []
    for comm, cpu, mem, cnt, etime in top_data:
        mm, ss = divmod(etime, 60)
        hh, mm = divmod(mm, 60)
        t_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"
        rows.append(f"  {comm:{c_len}s} {cpu:6.1f}% {mem:5d}MB {cnt:4d} {t_str:>8s}")
    return ["📊 Top 5 proc:", header] + rows


async def top5() -> list:
    """Fallback: если metrics.log нет top-данных."""
    try:
        rproc = await asyncio.create_subprocess_exec(
            "ps", "-eo", "comm=,%cpu=,%mem=,rss=,etimes=", "--no-headers",
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE
        )
        stdout, _ = await asyncio.wait_for(rproc.communicate(), timeout=5)
        rows = stdout.decode().strip().split("\n")
    except Exception:
        return []

    groups = {}
    for row in rows:
        parts = row.strip().split()
        if len(parts) < 5:
            continue
        comm = parts[0][:20]
        try:
            cpu = float(parts[1])
            rss_kb = int(parts[3])
            mem_mb = rss_kb // 1024
            etime = int(parts[4])
        except (ValueError, IndexError):
            continue
        g = groups.setdefault(comm, {"cpu": 0.0, "mem_mb": 0, "count": 0, "max_etime": 0})
        g["cpu"] += cpu
        g["mem_mb"] += mem_mb
        g["count"] += 1
        if etime > g["max_etime"]:
            g["max_etime"] = etime

    sorted_g = sorted(groups.items(), key=lambda x: x[1]["cpu"], reverse=True)[:5]
    if not sorted_g:
        return []

    c_len = max(max(len(comm) for comm, _ in sorted_g), 4) + 2
    head = f"  {'NAME':{c_len}s} {'CPU':>7s} {'MEM':>6s} {'CNT':>4s} {'ELAPSED':>8s}"
    rows = []
    for comm, g in sorted_g:
        mm, ss = divmod(g["max_etime"], 60)
        hh, mm = divmod(mm, 60)
        t_str = f"{hh:02d}:{mm:02d}:{ss:02d}" if hh else f"{mm:02d}:{ss:02d}"
        rows.append(f"  {comm:{c_len}s} {g['cpu']:6.1f}% {g['mem_mb']:5d}MB {g['count']:4d} {t_str:>8s}")
    return [head] + rows


def _resolve_mode(uid: int, elapsed: int) -> str:
    mode = get_status_mode(uid)
    if mode == "auto":
        if elapsed < 10:
            return "compact"
        elif elapsed < 50:
            return "normal"
        else:
            return "full"
    return mode


def _task_id_short(task_id: str) -> str:
    parts = task_id.split("-")
    if len(parts) >= 4:
        return f"{parts[1]}-{parts[2]}-{parts[3]}"
    return task_id


def _task_label(task_id: str, task_data: dict | None) -> str:
    if task_data:
        cmd = task_data.get("cmd", "")
        return cmd[:50] if cmd else ""
    return ""


def _session_age(uid: int) -> str:
    try:
        from session import get_session_full
        sd = get_session_full(uid)
        created = sd.get("session_created") if sd else None
        if not created:
            return "—"
        secs = int(_time.time() - created)
        d, secs = divmod(secs, 86400)
        h, m = divmod(secs, 3600)
        return f"{d}d {h:02d}h" if d else f"{h:02d}h{m:02d}m"
    except Exception:
        return "—"


async def status_block2(uid: int, task_id: str | None, elapsed: int,
                         avg_ms: int | None = None) -> list:
    if not task_id:
        return []

    mode = _resolve_mode(uid, elapsed)
    task_data, ts = get_task_data()

    tid_short = _task_id_short(task_id)
    task_info = task_data.get("tasks", {}).get(task_id, {})
    cmd_label = _task_label(task_id, task_info)

    pct = min(elapsed / 300 * 100, 99) if elapsed < 300 else 99
    bar_len = 10
    filled = int(pct / 100 * bar_len)
    bar = "█" * filled + "░" * (bar_len - filled)

    avg_str = f"avg {avg_ms//1000}s" if avg_ms else "avg —"

    lines = []
    lines.append(f"[{cmd_label}]" if cmd_label else "[—]")
    lines.append(f"  {tid_short}")
    lines.append(f"  [{ts['ok']}/{ts['ok']+ts['running']+ts['fail']+ts['skip']}] ✅{ts['ok']} 🔄{ts['running']} ❌{ts['fail']}")

    if mode == "compact":
        lines.append(f"  ⏱ {avg_str} · {elapsed}s")
        lines.append(f"  {bar} {int(pct)}%  {_compact_stat(ts)}")
    else:
        lines.append(f"  ⏱ {avg_str} · {elapsed}s")

        if mode == "normal":
            lines.append(f"  {bar} {int(pct)}%  {_compact_stat(ts)}")
            lines.append(f"  ⏱ {_session_age(uid)}")

        elif mode == "full":
            from datetime import datetime
            now = datetime.now().strftime("%d.%m.%y")
            lines.append(f"  {bar} {int(pct)}%")
            from datetime import datetime
            now = datetime.now().strftime("%d.%m.%y")
            lines.append(f"  📋 {cmd_label[:50]}  [🗓 {now}]")
            lines.append(f"  ✅ {ts['ok']}  🔄 {ts['running']}  ⏭ {ts['skip']}  ❌ {ts['fail']}  ⏱ {_session_age(uid)}")
            lines.append("")

            from task_state import get_user_name
            all_tasks = task_data.get("tasks", {})
            sorted_tasks = sorted(
                all_tasks.items(),
                key=lambda x: x[1].get("created_ms", 0), reverse=True
            )
            shown = 0
            for tid2, t2 in sorted_tasks:
                if shown >= 4:
                    break
                st = t2.get("status", "")
                emoji = {"completed": "✅", "running": "🔄",
                         "queued": "🔄", "failed": "❌"}.get(st, "⏭")
                uname = _user_name_cache.get(t2.get("uid", 0)) or get_user_name(t2.get("uid", 0))
                _user_name_cache[t2.get("uid", 0)] = uname
                label2 = t2.get("cmd", "")[:50]
                gnum = tid2.split("-")[3] if len(tid2.split("-")) >= 4 else "?"
                ctime = datetime.fromtimestamp(
                    t2.get("created_ms", 0) / 1000
                ).strftime("%d.%m.%y")
                start_ms = t2.get("start_ms")
                elapsed_ms = t2.get("elapsed_ms")
                dur = "--:--"
                start_str = "--:--"
                end_str = "--:--"
                if start_ms:
                    start_str = datetime.fromtimestamp(
                        start_ms / 1000
                    ).strftime("%H:%M:%S")
                if elapsed_ms and start_ms:
                    end_sec = (start_ms + elapsed_ms) / 1000
                    end_str = datetime.fromtimestamp(end_sec).strftime("%H:%M:%S")
                    m, s = divmod(elapsed_ms // 1000, 60)
                    dur = f"{m:02d}:{s:02d}"
                elif st == "running":
                    end_str = "..."
                lines.append(f"  {emoji} [{gnum}] [{uname}] {label2}  [🗓 {ctime}]")
                lines.append(f"  └─ {start_str} → {end_str}  [🕛 {dur}]")
                shown += 1
        else:
            lines.append(f"  ✅ {ts['ok']}  🔄 {ts['running']}  ⏭ {ts['skip']}  ❌ {ts['fail']}  ⏱ {uptime}")

    return lines


def _compact_stat(ts: dict) -> str:
    return f"✅{ts['ok']} 🔄{ts['running']} ❌{ts['fail']}"


def status_block4(uid: int, agent=None, live_tok=0) -> str:
    """Footer — делегирует build_footer"""
    from templates import build_footer
    last_cost = max(0.0, _cost.get(uid, 0.0) - _cost_offsets.get(uid, 0.0))
    return build_footer(uid, agent=agent, live_tok=live_tok, last_cost=last_cost)

    msgs = sess["messages"] if sess else 0
    if user.get("role") == "super":
        msg_part = f"{msgs}/-"
        storage_part = f"{_fmt_size(fsize)}/-"
        file_part = f"{fcount}/-"
    else:
        limits = user.get("limits")
        msg_limit = limits.get("msg", 50) if limits else 50
        storage_mb = limits.get("storage_mb", 500) if limits else 500
        file_limit = limits.get("file_count", 1000) if limits else 1000
        msg_part = f"{msgs}/{msg_limit}"
        storage_part = f"{_fmt_size(fsize)}/{_fmt_size(storage_mb * 1_000_000)}"
        file_part = f"{fcount}/{file_limit}"

    return (
        f"🤖 {short}\n"
        f"{ctx_line}\n"
        f"💬 {msg_part} · 📁 {sname}\n"
        f"💾 {storage_part} · 📄 {file_part}"
    )
