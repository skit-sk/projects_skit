import os
import sys
import asyncio
import logging
import time
import subprocess
import re
import signal
from datetime import datetime
from pathlib import Path
import numpy as np
from config import SUPER_USER, TG_ALL_DIR, WORKSPACE_DIR, VENV_PYTHON
sys.path.insert(0, str(WORKSPACE_DIR / "projects" / "08_ofd_api" / "bot_ofd"))
from commands import *
from session import ensure_super, get_user, user_exists, get_quota, get_current_session, log_unauthorized, user_dir as sud
from security import pre_filter, cancel_process, _active_processes
import monitor as _Monitor
import task_state
import task_control
import task_stats
from templates import _fmt_size, _fmt_tokens
from templates import build_footer, _fmt_size, _fmt_tokens
from telegram import InputMediaPhoto
from send_queue import queue_pop, queue_add
from screenshot_browser import parse_request as parse_request_regular, take_screenshot as take_screenshot_regular, TF_LABEL
from screenshot_widget import parse_request as parse_request_widget, take_screenshot as take_screenshot_widget
import screenshot_widget
from collage import make_collage
import ip_audit
from voice import transcribe_voice
from youtube_transcribe import transcribe_youtube
from rutube_transcribe import transcribe_rutube
import kb_commands
import kb_analyzer
from sync import sync_exchange

log = logging.getLogger("tg_bot")

WORKSPACE = WORKSPACE_DIR
SCRIPTS_DIR = WORKSPACE / "tools" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

def _try_parse_tradingview_url(url: str):
    """Извлечь symbol + timeframe из TradingView URL."""
    import re as _re
    from urllib.parse import unquote
    symbol = None
    interval = None
    range_val = None

    m = _re.search(r'symbol=([A-Za-z0-9%:]+)', url)
    if m:
        raw = unquote(m.group(1)).upper()
        if ":" not in raw:
            raw = f"BITGET:{raw}"
        symbol = raw

    m = _re.search(r'interval=(\w+)', url)
    if m:
        interval = m.group(1)

    m = _re.search(r'range=(\w+)', url)
    if m:
        range_val = m.group(1)

    return symbol, interval, range_val


def _kill_process_group(proc_pid):
    """Kill a spawned process's PID directly (not its process group).
    Safe to call after process exits — handles ESRCH gracefully.
    """
    import errno
    if proc_pid is None or proc_pid <= 1:
        return
    import time
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.kill(proc_pid, sig)
            if sig == signal.SIGTERM:
                time.sleep(0.5)
        except OSError as e:
            if e.errno == errno.ESRCH:
                break  # process already gone
            if e.errno == errno.EPERM:
                break  # no permission (already reaped)


# sync_exchange() moved to sync.py


async def _handle_task_stats(update, uid, text):
    """Обработчик /task_stats и /task_errors."""
    import json
    from security import is_super
    state_file = os.path.join(WORKSPACE, "projects", "07_tg_bot_aiforguest", "TG_ALL", "task_state.json")
    if not os.path.exists(state_file):
        await _reply(update, "❌ Файл статистики не найден", uid)
        return
    try:
        with open(state_file, "r") as f:
            data = json.load(f)
    except Exception as e:
        await _reply(update, f"❌ Ошибка чтения stats: {e}", uid)
        return

    cmd = text.split()[0].lower()
    need_errors = cmd == "/task_errors"
    role = "super" if is_super(uid) else "user"

    targets, depth, err = task_stats.parse_args(uid, text, role)
    if err:
        await _reply(update, err, uid)
        return

    try:
        if need_errors:
            report = task_stats.errors_run(data, targets, depth)
        else:
            report = task_stats.stats_run(data, targets, depth)
        if len(report) > 3800:
            report = report[:3500] + "\n\n... (обрезано)"
        await _reply(update, report, uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка формирования отчёта: {e}", uid)


async def _handle_emj_positions(update, uid):
    import time as _time
    t0 = _time.time()
    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        status_msg = await update.message.reply_text(
            "⚡ Sync из кэша\n📊 Получаю строки позиций..." if cached
            else f"✅ Sync: {sync_count} карт\n📊 Получаю строки позиций..."
        )
    else:
        status_msg = await update.message.reply_text(
            f"⚠️ Sync: {sync_err}\n📊 Строки устаревших данных..."
        )

    script = SCRIPTS_DIR / "get_emj_rows.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    user_dir = sud(uid)
    proc = None
    try:
        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                [sys.executable, str(script), "--output-dir", str(user_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
        stdout, stderr = await asyncio.wait_for(
            loop.run_in_executor(None, proc.communicate), timeout=30
        )
        elapsed = int((_time.time() - t0) * 1000)
        
        if proc.returncode != 0:
            err_txt = stderr.decode()[:200] or f"(пустой stderr, stdout: {stdout.decode()[:200]})"
            await status_msg.edit_text(f"❌ Ошибка скрипта (rc={proc.returncode}): {err_txt}")
            return

        txt_path = user_dir / "positions_emj_rows.txt"
        if txt_path.exists():
            txt = txt_path.read_text(encoding="utf-8")
            ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
            header = f"📊 Bitget Positions | {ts} | {elapsed}ms\n\n"
            if len(txt) + len(header) > 3800:
                txt = txt[:3500] + "\n\n... (обрезано)"
            await status_msg.edit_text(f"{header}{txt}")
        else:
            await status_msg.edit_text("✅ Файл сохранён, но не найден для отправки")
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (30с)")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_sc_positions(update, uid):
    import time as _time
    t0 = _time.time()
    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg, force=True)
    if sync_ok:
        await status_msg.edit_text(f"✅ Sync: {sync_count} карт обновлено\n📸 Делаю скриншот позиций...")
    else:
        await status_msg.edit_text(
            f"⚠️ Sync не удался: {sync_err}\n📸 Скриншот устаревших данных..."
        )

    script = SCRIPTS_DIR / "screenshot_positions.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
        stdout, stderr = await asyncio.wait_for(
            loop.run_in_executor(None, proc.communicate), timeout=60
        )
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err = (stderr.decode()[:200] or stdout.decode()[:200])
            await status_msg.edit_text(f"❌ Ошибка скриншота: {err}")
            return

        user_dir = sud(uid)
        img_path = user_dir / "positions_table.png"
        if img_path.exists():
            ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
            await status_msg.delete()
            with open(img_path, "rb") as f:
                await update.message.reply_photo(
                    photo=f,
                    caption=f"📊 Bitget Positions | {ts} | {elapsed}ms"
                )
        else:
            await status_msg.edit_text("✅ Скриншот сохранён, но файл не найден")
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (60с)")
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_sc_analytics(update, uid, args):
    import time as _time
    import json, urllib.request
    t0 = _time.time()

    if not args:
        help_text = (
            "📸 **/sc_analytics** — скриншоты графиков аналитики\n\n"
            "**Ключи:**\n"
            "  `/sc_analytics <symbol>` — символ или номер (ETC, 11)\n"
            "  `/sc_analytics all` — все доступные символы\n\n"
            "**Примеры:**\n"
            "  `/sc_analytics ETC`\n"
            "  `/sc_analytics 3` — DOT #3\n"
            "  `/sc_analytics all`"
        )
        await update.message.reply_text(help_text)
        return

    target = args[0]

    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        status_msg = await update.message.reply_text(
            "⚡ Sync из кэша\n📸 Делаю скриншот аналитики..." if cached
            else f"✅ Sync: {sync_count} карт\n📸 Делаю скриншот аналитики..."
        )
    else:
        status_msg = await update.message.reply_text(
            f"⚠️ Sync: {sync_err}\n📸 Скриншот устаревших данных..."
        )

    script = SCRIPTS_DIR / "screenshot_analytics.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        # Parse symbols: space or comma separated
        raw_symbols = []
        for a in args:
            for part in a.split(","):
                s = part.strip().upper()
                if s:
                    raw_symbols.append(s)

        is_all = len(raw_symbols) == 1 and raw_symbols[0] == "ALL"

        if is_all:
            cmd_args = [sys.executable, str(script), "--all"]
        else:
            cmd_args = [sys.executable, str(script), "--symbols", ",".join(raw_symbols)]

        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                cmd_args,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
        stdout, stderr = await asyncio.wait_for(
            loop.run_in_executor(None, proc.communicate), timeout=120
        )
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err = (stderr.decode()[:200] or stdout.decode()[:200])
            await status_msg.edit_text(f"❌ Ошибка скриншота: {err}")
            return
        user_dir = sud(uid)

        def _tg_line(ticker: str) -> str:
            tg_path = user_dir / "positions_emj_rows.txt"
            if not tg_path.exists():
                return ""
            txt = tg_path.read_text(encoding="utf-8")
            for line in txt.split("\n"):
                if f"🚏{ticker.upper()}" in line:
                    return line.strip()
            return ""

        ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
        await status_msg.delete()

        # Determine which symbols to send
        send_symbols = raw_symbols if not is_all else []
        if is_all or not send_symbols:
            import json, urllib.request as _req
            try:
                list_resp = _req.urlopen("http://localhost:5000/trade-analytics/api/list", timeout=5)
                all_objs = json.loads(list_resp.read())
                send_symbols = [o["symbol"] for o in all_objs if o.get("has_1d") and o.get("has_raw")]
            except Exception:
                send_symbols = []

        for sym in send_symbols:
            coll_path = user_dir / f"{sym}_analytics.png"
            if coll_path.exists():
                tg = _tg_line(sym)
                cap = (tg + "\n\n" if tg else "") + f"📊 Analytics {sym} | {ts} | {elapsed}ms"
                with open(coll_path, "rb") as f:
                    await update.message.reply_photo(photo=f, caption=cap)
                await asyncio.sleep(0.5)
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (120с)")
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_sc_graphs(update, uid):
    import json as _json
    import time as _time
    import httpx
    t0 = _time.time()
    log.info(f"sc_graphs: start uid={uid}")
    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        if cached:
            await status_msg.edit_text("⚡ Sync из кэша\n📊 Генерирую графики...")
        else:
            await status_msg.edit_text(f"✅ Sync: {sync_count} карт\n📊 Генерирую графики...")
    else:
        await status_msg.edit_text(f"⚠️ Sync: {sync_err}\n📊 Графики устаревших данных...")

    script = SCRIPTS_DIR / "generate_graphs.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        log.info("sc_graphs: about to create_subprocess_exec")
        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                [VENV_PYTHON, str(script), "--uid", str(uid)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
        log.info(f"sc_graphs: proc started pid={proc.pid}")
        stdout, stderr = await asyncio.wait_for(
            loop.run_in_executor(None, proc.communicate), timeout=180
        )
        log.info(f"sc_graphs: subprocess done rc={proc.returncode} stdout={len(stdout)}b stderr={len(stderr)}b")

        if proc.returncode != 0:
            err = (stderr.decode()[:300] or stdout.decode()[:200])
            log.error(f"sc_graphs: subprocess failed rc={proc.returncode} stderr={err!r}")
            await status_msg.edit_text(f"❌ Ошибка генерации графиков: {err}")
            return

        raw = stdout.decode().strip()
        result = _json.loads(raw) if raw else {"files": []}
        files = result.get("files", [])
        log.info(f"sc_graphs: parsed files={len(files)} total={result.get('total_ms')}")

        if not files:
            await status_msg.edit_text("❌ Нет данных для графиков.")
            return

        # Build position map for TG row lines
        pos_map = {}
        try:
            async with httpx.AsyncClient(base_url="http://localhost:5000", timeout=httpx.Timeout(10)) as _hc:
                _r = await _hc.get("/account-api/api/computed")
                for _p in _r.json().get("positions", []):
                    pos_map[_p["ticker"]] = _p
        except Exception:
            pass

        def _make_tg_row(p):
            if not p:
                return ""
            n = p.get("number", "?")
            sym = p.get("ticker", "?")
            price = float(p.get("current_price", 0))
            ed = p.get("open_date", "")
            days = p.get("days_open", 0)
            vol = float(p.get("margin_size", 0))
            pp = float(p.get("pl_percent", 0))
            pu = float(p.get("unrealized_pl", 0))
            res = "🟢" if pu >= 0 else "🔴"
            lev = float(p.get("leverage", 10))
            return f"🏗️{n} 🚏{sym} 🧾{price:.4f} 📆{ed} 🕒{days}дн 🧱{vol:.4f} 🫧{pp:+.2f} 🪙{pu:+.4f} 📦{res} ⬆️{lev:.0f}x"

        await status_msg.delete()
        total = result.get("total_ms", 0)
        sent = 0
        for f in files:
            path = f.get("path", "")
            symbol = f.get("symbol", "?")
            date_str = f.get("date", "")
            ms = f.get("ms", 0)
            if not os.path.isfile(path):
                log.warning(f"sc_graphs: file missing {path}")
                continue
            log.info(f"sc_graphs: sending {symbol} from {path} size={os.path.getsize(path)}b")
            _pos = pos_map.get(symbol)
            _tg_line = _make_tg_row(_pos)
            try:
                with open(path, "rb") as fp:
                    if _tg_line:
                        caption = f"{_tg_line}\n🔄 📊 {symbol} | {date_str} | {ms}ms"
                    else:
                        caption = f"📊 {symbol} | {date_str} | {ms}ms"
                    await update.message.reply_photo(photo=fp, caption=caption)
                sent += 1
                await asyncio.sleep(0.5)
            except Exception as e:
                log.warning("send_graph photo failed: %s", e)

        if sent == 0:
            await update.message.reply_text(f"❌ Графики не сгенерированы (total: {total}ms)")
    except _json.JSONDecodeError:
        await status_msg.edit_text("❌ Ошибка парсинга результата скрипта.")
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (3 мин)")
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_chart(update, uid, args):
    import json as _json
    import time as _time
    t0 = _time.time()

    _ALL_TYPES = [
        "line", "bar", "boxplot", "violin", "bubble", "scatter",
        "histogram", "density", "heatmap", "correlogram", "pie",
        "circular_bar", "radar", "lollipop", "histogram2d",
        "dendrogram", "network", "parallel_coords", "ridgeline",
        "stream", "treemap", "venn", "wordcloud", "scatter3d",
        "scatter_matrix", "grouped_bar", "stacked_bar",
    ]

    if not args:
        lines = ["📊 **Chart Generator**\n", "Команды:\n"]
        for ct in _ALL_TYPES:
            lines.append(f"  `/chart {ct}` — {ct}")
        lines.append("\n  `/chart all` — все 27 типов на реальных данных")
        await _reply(update, "\n".join(lines), uid)
        return

    chart_type = args[0].lower()

    is_all = chart_type == "all"
    target_types = _ALL_TYPES if is_all else [chart_type]

    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        if cached:
            prefix = "⚡ Sync из кэша"
        else:
            prefix = f"✅ Sync: {sync_count} карт"
        if is_all:
            await status_msg.edit_text(f"{prefix}\n📊 Генерирую {len(target_types)} графиков...")
        else:
            await status_msg.edit_text(f"{prefix}\n📊 Генерирую {chart_type}...")
    else:
        if is_all:
            await status_msg.edit_text(f"⚠️ Sync: {sync_err}\n📊 Графики устаревших данных...")
        else:
            await status_msg.edit_text(f"⚠️ Sync: {sync_err}\n📊 График устаревших данных...")

    script = SCRIPTS_DIR / "generate_chart.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    import urllib.request
    import re as _re

    objects = []
    try:
        list_resp = urllib.request.urlopen("http://localhost:5000/graphics/all", timeout=10)
        html = list_resp.read().decode()
        ids = _re.findall(r'data-id="([^"]+)"', html)
        symbols = _re.findall(r'data-symbol="([^"]+)"', html)
        seen = set()
        for i in range(len(ids)):
            if ids[i] not in seen:
                seen.add(ids[i])
                objects.append({"id": ids[i], "symbol": symbols[i] if i < len(symbols) else "?"})
    except Exception as e:
        if not is_all:
            await status_msg.edit_text(f"❌ Ошибка загрузки данных: {e}")
            return
        objects = []

    charts_data = []
    for obj in objects:
        try:
            cr = urllib.request.urlopen(f"http://localhost:5000/graphics/chart/{obj['id']}", timeout=15)
            charts_data.append(json.loads(cr.read()))
        except Exception:
            pass

    def _cd(idx=0):
        return charts_data[idx] if charts_data else {"chart": [], "summary": {}}

    def _clamp(val, lo, hi):
        return max(lo, min(hi, val))

    def _build_data(ct: str) -> dict:
        d = {"title": f"Test {ct}"}

        if ct == "line":
            cd = _cd(0)
            d.update({"chart": cd.get("chart", []), "summary": cd.get("summary", {})})

        elif ct == "bar":
            vals = [c.get("summary", {}).get("total_deviation_percent", 0) for c in charts_data]
            syms = [o["symbol"] for o in objects[:len(vals)]]
            d.update({"categories": syms, "values": vals, "ylabel": "PnL %"})

        elif ct == "grouped_bar":
            np.random.seed(42)
            grps = ["W1", "W2", "W3"]
            sgs = [o["symbol"] for o in objects[:4]]
            vals = [[np.random.rand() * 10 - 3 for _ in sgs] for _ in grps]
            d.update({"groups": grps, "subgroups": sgs, "values": vals})

        elif ct == "stacked_bar":
            cats = [o["symbol"] for o in objects[:5]]
            grps = ["PnL", "Fees", "Volume"]
            np.random.seed(42)
            vals = [[np.random.rand() * 5 for _ in grps] for _ in cats]
            d.update({"categories": cats, "groups": grps, "values": vals})

        elif ct in ("boxplot", "violin"):
            grps = {}
            for i, o in enumerate(objects[:5]):
                pts = charts_data[i].get("chart", [])
                grps[o["symbol"]] = [p.get("deviation_percent", 0) for p in pts if p.get("deviation_percent") is not None]
            d.update({"groups": grps, "ylabel": "Deviation %"})

        elif ct == "bubble":
            xs, ys, ss, lbs = [], [], [], []
            for i, o in enumerate(objects[:10]):
                s = charts_data[i].get("summary", {})
                xs.append(s.get("leverage", 10))
                ys.append(s.get("total_deviation_percent", 0))
                ss.append(float(s.get("current_price", 100)))
                lbs.append(o["symbol"])
            d.update({"x": xs, "y": ys, "size": ss, "labels": lbs, "xlabel": "Leverage", "ylabel": "PnL %"})

        elif ct == "scatter":
            xs, ys = [], []
            for i in range(min(len(objects), len(charts_data))):
                s = charts_data[i].get("summary", {})
                xs.append(float(s.get("entry_price", 0)))
                ys.append(float(s.get("current_price", 0)))
            d.update({"x": xs, "y": ys, "xlabel": "Entry Price", "ylabel": "Current Price"})

        elif ct == "histogram":
            vals = []
            for cd in charts_data:
                for p in cd.get("chart", []):
                    v = p.get("deviation_percent")
                    if v is not None:
                        vals.append(v)
            d.update({"values": vals, "bins": 25, "xlabel": "Deviation %"})

        elif ct == "density":
            grps = {}
            for i, o in enumerate(objects[:5]):
                pts = charts_data[i].get("chart", [])
                vals = [p.get("deviation_percent") for p in pts if p.get("deviation_percent") is not None]
                if vals:
                    grps[o["symbol"]] = vals
            d.update({"groups": grps, "xlabel": "Deviation %"})

        elif ct in ("heatmap", "correlogram"):
            n = min(len(objects), 7)
            if n < 2:
                n = 2
            mat = [[0.0] * n for _ in range(n)]
            labs = [o["symbol"] for o in objects[:n]]
            for i in range(n):
                for j in range(n):
                    if i == j:
                        mat[i][j] = 1.0
                    elif i < len(charts_data) and j < len(charts_data):
                        pi = [p.get("deviation_percent", 0) or 0 for p in charts_data[i].get("chart", [])]
                        pj = [p.get("deviation_percent", 0) or 0 for p in charts_data[j].get("chart", [])]
                        min_len = min(len(pi), len(pj))
                        if min_len > 2:
                            mat[i][j] = float(np.corrcoef(pi[:min_len], pj[:min_len])[0, 1])
            d.update({"matrix": mat, "row_labels": labs, "col_labels": labs, "cmap": "RdBu_r"})

        elif ct == "pie":
            vals = []
            labs = []
            for i, o in enumerate(objects[:6]):
                s = charts_data[i].get("summary", {})
                v = abs(float(s.get("total_deviation_usdt", 0) or 0))
                if v:
                    vals.append(v)
                    labs.append(o["symbol"])
            if not vals:
                vals, labs = [25, 25, 25, 25], ["A", "B", "C", "D"]
            d.update({"labels": labs, "values": vals, "donut": True})

        elif ct == "circular_bar":
            vals = [charts_data[i].get("summary", {}).get("total_deviation_percent", 0) or 0 for i in range(min(len(objects), len(charts_data)))]
            syms = [o["symbol"] for o in objects[:len(vals)]]
            d.update({"labels": syms, "values": vals})

        elif ct == "radar":
            cats = ["PnL", "Dp", "Dn", "Lev", "Days"]
            series = []
            for i, o in enumerate(objects[:3]):
                s = charts_data[i].get("summary", {})
                st = charts_data[i].get("stats", {})
                lv = float(s.get("leverage", 1))
                vals = [
                    _clamp(float(s.get("total_deviation_percent", 0) or 0), -30, 30) / 30 * 100,
                    _clamp(float(st.get("dp", 0)), 0, 50) / 50 * 100,
                    _clamp(float(st.get("dn", 0)), 0, 50) / 50 * 100,
                    _clamp(lv, 1, 20) / 20 * 100,
                    _clamp(float(s.get("entry_time", 0) or 0), 0, 365) / 365 * 100,
                ]
                series.append({"name": o["symbol"], "values": vals})
            d.update({"categories": cats, "series": series})

        elif ct == "lollipop":
            vals = [charts_data[i].get("summary", {}).get("total_deviation_percent", 0) or 0 for i in range(min(len(objects), len(charts_data)))]
            syms = [o["symbol"] for o in objects[:len(vals)]]
            d.update({"categories": syms, "values": vals, "ylabel": "PnL %"})

        elif ct == "histogram2d":
            xs, ys = [], []
            for cd in charts_data:
                for p in cd.get("chart", []):
                    dv = p.get("deviation_percent")
                    if dv is not None:
                        xs.append(dv)
                        ys.append(abs(dv) * 2 + np.random.rand() * 2)
            d.update({"x": xs[:200], "y": ys[:200], "kind": "hexbin", "xlabel": "Deviation %", "ylabel": "Volume"})

        elif ct == "dendrogram":
            n = min(len(objects), 8)
            mat = []
            for i in range(n):
                pts = charts_data[i].get("chart", [])
                means = [p.get("deviation_percent", 0) or 0 for p in pts[:5]]
                while len(means) < 5:
                    means.append(0)
                mat.append(means[:5])
            labs = [o["symbol"] for o in objects[:n]]
            d.update({"matrix": mat, "labels": labs})

        elif ct == "network":
            nodes = [o["symbol"] for o in objects[:8]]
            edges = []
            for i in range(len(nodes)):
                for j in range(i + 1, len(nodes)):
                    if i < len(charts_data) and j < len(charts_data):
                        pi = [p.get("deviation_percent", 0) or 0 for p in charts_data[i].get("chart", [])]
                        pj = [p.get("deviation_percent", 0) or 0 for p in charts_data[j].get("chart", [])]
                        ml = min(len(pi), len(pj))
                        if ml > 2:
                            corr = float(np.corrcoef(pi[:ml], pj[:ml])[0, 1])
                            if abs(corr) > 0.5:
                                edges.append((nodes[i], nodes[j]))
            d.update({"nodes": nodes, "edges": edges or [(nodes[0], nodes[1])]})

        elif ct == "parallel_coords":
            cols = ["Entry", "Current", "PnL%", "Lev"]
            vals = []
            for i in range(min(len(objects), len(charts_data))):
                s = charts_data[i].get("summary", {})
                vals.append([
                    float(s.get("entry_price", 0) or 0),
                    float(s.get("current_price", 0) or 0),
                    float(s.get("total_deviation_percent", 0) or 0),
                    float(s.get("leverage", 1) or 1),
                ])
            d.update({"categories": cols, "values": vals})

        elif ct == "ridgeline":
            grps = {}
            for i, o in enumerate(objects[:5]):
                pts = charts_data[i].get("chart", [])
                vals = [p.get("deviation_percent", 0) for p in pts if p.get("deviation_percent") is not None]
                if vals:
                    grps[o["symbol"]] = vals
            d.update({"groups": grps, "xlabel": "Deviation %", "gap": 0.3})

        elif ct == "stream":
            n_pts = min(20, min([len(cd.get("chart", [])) for cd in charts_data[:4]] or [5]))
            x = list(range(n_pts))
            layers = []
            labs = []
            for i, o in enumerate(objects[:4]):
                pts = charts_data[i].get("chart", [])
                vals = [p.get("deviation_percent", 0) or 0 for p in pts[:n_pts]]
                if len(vals) < n_pts:
                    vals += [0] * (n_pts - len(vals))
                layers.append(vals)
                labs.append(o["symbol"])
            d.update({"x": x, "layers": layers, "labels": labs, "xlabel": "Day", "ylabel": "Deviation %"})

        elif ct == "treemap":
            labs = [o["symbol"] for o in objects[:8]]
            sizes = []
            for i in range(min(len(objects), len(charts_data))):
                v = abs(float(charts_data[i].get("summary", {}).get("total_deviation_usdt", 0) or 0))
                sizes.append(max(v, 0.1))
            d.update({"labels": labs, "sizes": sizes})

        elif ct == "venn":
            from random import sample
            symbols = [o["symbol"] for o in objects[:3]]
            n10 = max(len(objects) // 3, 1)
            d.update({"sets": (n10, n10, n10 // 2), "labels": symbols})

        elif ct == "wordcloud":
            words = " ".join([o["symbol"] for o in objects] +
                             [f"{o['symbol']} chart analysis price entry" for o in objects])
            d.update({"text": words, "max_words": 40})

        elif ct == "scatter3d":
            xs, ys, zs = [], [], []
            for i in range(min(len(objects), len(charts_data))):
                s = charts_data[i].get("summary", {})
                xs.append(float(s.get("entry_price", 0) or 0))
                ys.append(float(s.get("current_price", 0) or 0))
                zs.append(float(s.get("leverage", 1) or 1))
            d.update({"x": xs, "y": ys, "z": zs})

        elif ct == "scatter_matrix":
            cols = ["Entry", "Current", "PnL%", "Lev"]
            vals = []
            for i in range(min(len(objects), len(charts_data))):
                s = charts_data[i].get("summary", {})
                vals.append([
                    float(s.get("entry_price", 0) or 0),
                    float(s.get("current_price", 0) or 0),
                    float(s.get("total_deviation_percent", 0) or 0),
                    float(s.get("leverage", 1) or 1),
                ])
            d.update({"columns": cols, "values": vals})

        return d

    user_dir = sud(uid)
    user_dir.mkdir(parents=True, exist_ok=True)

    sys.path.insert(0, str(SCRIPTS_DIR))
    import chart_lib

    generated = []
    failed = 0
    for ct in target_types:
        try:
            data = _build_data(ct)
            out_path = str(user_dir / f"ch_{ct}.png")
            chart_lib.generate(ct, data, out_path)
            generated.append((ct, out_path))
        except Exception as e:
            log.warning("chart %s failed: %s", ct, e)
            failed += 1

    if not generated:
        await status_msg.edit_text("❌ Не удалось сгенерировать ни одного графика.")
        return

    elapsed_ms = int((_time.time() - t0) * 1000)
    ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
    await status_msg.delete()

    for ct, path in generated:
        try:
            with open(path, "rb") as fp:
                await update.message.reply_photo(
                    photo=fp,
                    caption=f"📊 {ct} | {ts} | {elapsed_ms}ms",
                )
            await asyncio.sleep(0.3)
        except Exception as e:
            log.warning("send chart %s failed: %s", ct, e)

    summary = f"✅ Отправлено {len(generated)}/{len(target_types)} графиков"
    if failed:
        summary += f" ({failed} ошибок)"
    await update.message.reply_text(summary)


async def _handle_positions(update, uid):
    import time as _time
    t0 = _time.time()
    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        status_msg = await update.message.reply_text(
            "⚡ Sync из кэша\n📊 Получаю сводку..." if cached
            else f"✅ Sync: {sync_count} карт\n📊 Получаю сводку..."
        )
    else:
        status_msg = await update.message.reply_text(
            f"⚠️ Sync: {sync_err}\n📊 Сводка устаревших данных..."
        )

    script = SCRIPTS_DIR / "get_emj_rows.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    user_dir = sud(uid)
    proc = None
    try:
        loop = asyncio.get_event_loop()
        proc = await loop.run_in_executor(
            None,
            lambda: subprocess.Popen(
                [sys.executable, str(script), "--output-dir", str(user_dir)],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
            )
        )
        stdout, stderr = await asyncio.wait_for(
            loop.run_in_executor(None, proc.communicate), timeout=60
        )
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err_text = stderr.decode()[:200] or f"(пустой stderr, stdout: {stdout.decode()[:200]})"
            await status_msg.edit_text(f"❌ Ошибка скрипта (rc={proc.returncode}): {err_text}")
            return

        txt_path = user_dir / "positions_risk.txt"
        if txt_path.exists():
            text = txt_path.read_text(encoding="utf-8")
            if len(text) > 3800:
                text = text[:3500] + "\n\n... (обрезано)"
            await status_msg.edit_text(f"{text}\n\n📊 Positions | {elapsed}ms")
        else:
            await status_msg.edit_text("✅ Сводка saved, но файл не найден")
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (60с)")
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_positions_image(update, uid):
    import time as _time
    import httpx
    t0 = _time.time()
    status_msg = await update.message.reply_text("🔄 Синхронизирую с Bitget...")
    log.info(f"positions_image: start uid={uid}")

    sync_ok, sync_count, sync_err, cached = await sync_exchange(status_msg)
    if sync_ok:
        if cached:
            await status_msg.edit_text("⚡ Sync из кэша\n📊 Готовлю скриншот сводки...")
        else:
            await status_msg.edit_text(f"✅ Sync: {sync_count} карт\n📊 Готовлю скриншот сводки...")
    else:
        await status_msg.edit_text(f"⚠️ Sync: {sync_err}\n📊 Готовлю скриншот устаревших данных...")

    try:
        async with httpx.AsyncClient(base_url="http://localhost:5000", timeout=httpx.Timeout(15.0)) as _hclient:
            resp = await _hclient.get("/account-api/api/computed")
            data = resp.json()
            log.info(f"positions_image: computed loaded n={len(data.get('positions', []))}")

            if "error" in data:
                await status_msg.edit_text(f"❌ {data['error']}")
                return

            positions = data.get("positions", [])
            totals = data.get("totals", {})
            fill_counts = data.get("fill_counts", {})
            order_counts = data.get("order_counts", {})

            balance = 0.0
            try:
                bresp = await _hclient.get("/account-api/api/balance", timeout=httpx.Timeout(5.0))
                bdata = bresp.json()
                for item in bdata.get("futures", []):
                    if item.get("margin_coin") == "USDT":
                        balance = float(item.get("available", 0))
                        break
                if not balance:
                    for item in bdata.get("spot", []):
                        if item.get("coin") == "USDT":
                            balance = float(item.get("available", 0))
                            break
            except Exception:
                pass
            log.info(f"positions_image: balance={balance}")
        
        from formatters.positions_risk import format_risk_summary
        from rich.console import Console
        from formatters.screenshot import async_render_rich_to_png
        
        # Build Rich Table with record=True
        console = Console(record=True, width=100)
        from rich.table import Table
        table = Table(title=f"📊 Risk Summary (Balance: {balance:.2f} USDT)", width=100)
        table.add_column("Ticker", style="bold", no_wrap=True)
        table.add_column("Side", no_wrap=True)
        table.add_column("Margin", justify="right")
        table.add_column("Bal%", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("Exp%", justify="right")
        table.add_column("ROE%", justify="right")
        table.add_column("Mgn%", justify="right")
        table.add_column("LiqΔ%", justify="right")
        table.add_column("Cnt", justify="right")
        table.add_column("Lev", justify="right")
        
        sum_mgn_pct = 0.0
        for pos in positions:
            margin = float(pos.get("margin_size", 0))
            pl = float(pos.get("unrealized_pl", 0))
            bal_pct = float(pos.get("bal_pct", 0))
            mgn_pct = float(pos.get("mgn_pct", 0))
            exp_pct = float(pos.get("ror", 0))
            roe = float(pos.get("roe", 0))
            liq_d = float(pos.get("liq_delta", 0))
            side = "L" if pos.get("hold_side") == "long" else "S"
            sum_mgn_pct += mgn_pct
            
            _abs = abs(roe)
            if _abs > 100:
                _lvl = "bright"
            elif _abs > 50:
                _lvl = "mid"
            else:
                _lvl = "dim"
            row_style = {"bright": "on #00cc44", "mid": "on #00882e", "dim": "on #004418"}[_lvl] if pl >= 0 else {"bright": "on #cc3333", "mid": "on #882222", "dim": "on #441111"}[_lvl]
            _sym = pos.get("symbol", "?")
            _cnt = fill_counts.get(_sym, 0)
            table.add_row(_sym, side, f"{margin:.2f}",
                         f"{bal_pct:.2f}", f"{pl:+.2f}", f"{exp_pct:.2f}",
                         f"{roe:+.1f}", f"{mgn_pct:.2f}", f"{liq_d:.1f}",
                         str(_cnt), f"{int(pos.get('leverage', 0))}x",
                         style=row_style)
        
        table.add_section()
        total_margin_f = totals.get('total_margin', 0)
        total_pl_f = totals.get('total_pl', 0)
        total_roe = (total_pl_f / total_margin_f * 100) if total_margin_f else 0
        total_bal_pct = (total_margin_f / balance * 100) if balance else 0
        total_exp_pct = (total_pl_f / balance * 100) if balance else 0
        _total_cnt = sum(fill_counts.values())
        table.add_row("TOTAL", "", f"{total_margin_f:.2f}",
                     f"{total_bal_pct:.2f}", f"{total_pl_f:+.2f}", f"{total_exp_pct:.2f}",
                     f"{total_roe:+.1f}", f"{sum_mgn_pct:.2f}", "", str(_total_cnt), "")
        
        console.print(table)
        img_path = f"/tmp/positions_risk_{int(_time.time())}.png"
        log.info(f"positions_image: starting render path={img_path}")
        result = await async_render_rich_to_png(console, img_path)
        log.info(f"positions_image: rendered {'ok' if result else 'fail'} size={os.path.getsize(img_path) if result else 0}")
        
        if result:
            await status_msg.delete()
            with open(result, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"📊 Positions | {int((_time.time()-t0)*1000)}ms")
        else:
            # Fallback to text
            text = format_risk_summary(positions, balance, fill_counts, order_counts, totals)
            await status_msg.edit_text(f"{text}\n\n📊 Positions | {int((_time.time()-t0)*1000)}ms" if len(text) < 3500 else "❌ Ошибка создания изображения")
        log.info(f"positions_image: done total={int((_time.time()-t0)*1000)}ms")
    
    except Exception as e:
        await status_msg.edit_text(f"❌ Ошибка: {e}")


def _normalize_symbol(raw: str) -> str | None:
    """Привести символ к формату TICKERUSDT."""
    s = raw.strip().upper()
    if s.endswith("USDT"):
        return s
    if s.isalpha() and len(s) <= 10:
        return f"{s}USDT"
    return None


async def _handle_ws_ob(update, uid, args):
    import time as _time
    t0 = _time.time()
    
    # Parse --image flag
    want_image = "--image" in args
    clean_args = [a for a in args if a != "--image"]
    
    if not clean_args:
        status_msg = await update.message.reply_text("❌ Укажи символ. Пример: /ws_ob BTC")
        return
    
    symbol = _normalize_symbol(clean_args[0])
    if not symbol:
        status_msg = await update.message.reply_text(f"❌ Некорректный символ: {clean_args[0]}")
        return
    
    # Parse depth and aggregation
    depth = 15
    bucket_size = 0
    VALID_DEPTHS = (5, 15, 50, 100)
    VALID_AGGR = (0.05, 0.5, 1, 10, 50, 100, 1000)
    
    if len(clean_args) > 1:
        try:
            d = int(clean_args[1])
            if d in VALID_DEPTHS:
                depth = d
        except ValueError:
            pass
    
    if len(clean_args) > 2:
        try:
            bs = float(clean_args[2])
            if bs in VALID_AGGR:
                bucket_size = bs
        except ValueError:
            pass
    
    status_msg = await update.message.reply_text("📊 Получаю стакан...")
    
    # Fetch OB (aggregated if bucket_size > 0)
    from formatters.orderbook import fetch_aggregated_ob
    data = fetch_aggregated_ob(symbol, depth, bucket_size)
    
    if not data:
        await status_msg.edit_text(f"❌ Нет данных стакана для {symbol}")
        return
    
    elapsed = int((_time.time() - t0) * 1000)
    asks = data.get("asks", [])
    bids = data.get("bids", [])
    
    if not asks or not bids:
        await status_msg.edit_text(f"❌ Нет данных стакана для {symbol}")
        return
    
    from formatters.positions_risk import format_order_book
    from rich.console import Console
    from io import StringIO
    
    if want_image:
        # Rich → HTML → PNG → send photo
        from formatters.screenshot import async_render_rich_to_png
        
        table_title = f"📊 Order Book {symbol}"
        if bucket_size:
            table_title += f" (aggr: {bucket_size} USDT, depth: {depth})"
        
        console = Console(record=True, width=100)
        from rich.table import Table
        tbl = Table(title=table_title, width=100)
        tbl.add_column("Bid Price", style="green", justify="right")
        tbl.add_column("Bid Vol", style="green", justify="right")
        tbl.add_column("│")
        tbl.add_column("Ask Price", style="red", justify="right")
        tbl.add_column("Ask Vol", style="red", justify="right")
        
        max_rows = max(len(asks), len(bids))
        for i in range(max_rows):
            b = bids[i] if i < len(bids) else ["", ""]
            a = asks[i] if i < len(asks) else ["", ""]
            tbl.add_row(str(b[0]) if b[0] else "", str(b[1]) if b[1] else "", "│",
                       str(a[0]) if a[0] else "", str(a[1]) if a[1] else "")
        
        # Spread
        if asks and bids and asks[0] and bids[0]:
            def _fp(val):
                if isinstance(val, str) and "–" in val:
                    return float(val.split("–")[0])
                return float(val)
            try:
                sp = _fp(asks[0][0]) - _fp(bids[0][0])
                sp_pct = sp / _fp(bids[0][0]) * 100
                tbl.add_section()
                tbl.add_row("", "", f"Spread: {sp:.2f} ({sp_pct:.3f}%)", "", "")
            except (ValueError, IndexError):
                pass
        
        console.print(tbl)
        img_path = f"/tmp/ob_{symbol}_{int(_time.time())}.png"
        result = await async_render_rich_to_png(console, img_path, title=table_title)
        
        if result:
            await status_msg.delete()
            with open(result, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"{symbol} | {elapsed}ms")
        else:
            # Fallback to text
            text = format_order_book(symbol, asks, bids, bucket_size)
            await status_msg.edit_text(f"{text}\n\n{symbol} | {elapsed}ms")
    else:
        text = format_order_book(symbol, asks, bids, bucket_size)
        full = f"{text}\n\n{symbol} | {elapsed}ms"
        if len(full) > 3800:
            full = full[:3500] + "\n\n... (обрезано)"
        await status_msg.edit_text(full)


def _save_message_record(uid: int, text: str, forward_data: dict):
    """Сохранить структурированную запись сообщения в messages.ndjson."""
    try:
        import json
        from datetime import datetime
        from pathlib import Path

        resolved = str(uid)
        state = None
        try:
            from session import _load
            state = _load()
        except Exception:
            pass
        if state:
            for k, v in state.get("users", {}).items():
                links = v.get("platform_links", {})
                for platform, ids in links.items():
                    if uid in ids:
                        resolved = k
                        break

        analytics = Path(WORKSPACE_DIR) / "ALL_USERS" / resolved / "analytics"
        analytics.mkdir(parents=True, exist_ok=True)

        record = {
            "id": f"msg_{uid}_{int(datetime.now().timestamp()*1000)}",
            "ts": datetime.now().isoformat(),
            "uid": uid,
            "text": text[:500] if text else "",
            "type": _classify_text(text),
            "symbols": _extract_symbols(text),
            "urls": _extract_urls(text),
            "is_forward": bool(forward_data),
        }
        if forward_data:
            record["forward"] = forward_data

        out = analytics / "messages.ndjson"
        with open(out, "a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    except Exception:
        pass


def _classify_text(text: str) -> str:
    if not text:
        return "empty"
    if text.startswith("/"):
        return "command"
    if re.search(r'youtube\.com/watch|youtu\.be/', text):
        return "youtube"
    if re.search(r'github\.com/\w+/\w+', text):
        return "github"
    low = text.lower()
    if any(kw in low for kw in ('bitget', 'long', 'short', 'сигнал', 'midasflow', 'авто-сигнал', 'entry')):
        return "trading_signal"
    if re.search(r'https?://', text):
        return "url"
    return "ai_query" if len(text) > 10 else "text"


def _extract_symbols(text: str) -> list:
    raw = re.findall(r'\b([A-Z]{2,10}(?:USDT|USD|BTC|ETH)|#?[A-Z]{2,10})\b', text)
    seen = set()
    result = []
    for s in raw:
        s = s.lstrip("#").upper()
        if s not in seen and len(s) >= 2:
            seen.add(s)
            result.append(s)
    return result[:10]


def _extract_urls(text: str) -> list:
    return re.findall(r'https?://\S+', text)[:5]


async def _reply(update, text, uid, agent=None, parse_mode=None, fmt_style="link", live_tok=0, show_footer=False):
    if show_footer:
        try:
            last_cost = 0
            try:
                from session import get_session_full
                sd = get_session_full(uid)
                if sd:
                    last_cost = sd.get("last_msg", {}).get("cost", 0) or 0
            except Exception:
                pass
            footer = build_footer(uid, agent=agent, parse_mode=parse_mode, fmt_style=fmt_style, live_tok=live_tok, last_cost=last_cost)
        except Exception:
            footer = ""
    else:
        footer = ""
    parts = text.split("\n━━━\n", 1)
    if len(parts) >= 2 and parts[1].strip():
        full = text
    else:
        full = f"{text}\n\n━━━\n\n{footer}" if footer else text
    chat_id = update.effective_chat.id
    kwargs = {"parse_mode": parse_mode} if parse_mode else {}
    if len(full) <= 4000:
        try:
            await update.effective_chat.send_message(full, **kwargs)
        except Exception as e:
            log.error(f"_reply: {e}")
            kwargs.pop("parse_mode", None)
            try:
                await update.effective_chat.send_message(f"✅ Ответ получен, но слишком длинный для Telegram.\n\n{footer}", **kwargs)
            except Exception as e:
                log.warning(f"_reply fallback failed: {e}")
        return
    body = text if not footer else parts[0]
    lines = body.split("\n")
    chunks = []
    buf = ""
    for line in lines:
        cand = f"{buf}\n{line}" if buf else line
        if len(cand) > 3500:
            if buf:
                chunks.append(buf)
            buf = line
        else:
            buf = cand
    if buf:
        chunks.append(buf)
    total = len(chunks)
    for i, chunk in enumerate(chunks):
        if i < total - 1:
            await update.effective_chat.send_message(f"{chunk}\n\n({i+1}/{total})", **kwargs)
        else:
            await update.effective_chat.send_message(f"{chunk}\n\n{footer}", **kwargs)


async def dispatch(update, context):
    user = update.effective_user
    uid = user.id
    msg = update.message
    text = msg.text.strip() if msg and msg.text else ""
    doc = msg.document if msg else None

    # Capture forward metadata (safe getattr for older python-telegram-bot)
    fwd_info = ""
    forward_data = {}
    if msg:
        fwd = getattr(msg, 'forward_origin', None) or getattr(msg, 'forward_from', None)
        fwd_chat = getattr(msg, 'forward_from_chat', None)
        fwd_sender = getattr(msg, 'forward_sender_name', None)
        fwd_date = getattr(msg, 'forward_date', None)
        auto_fwd = getattr(msg, 'is_automatic_forward', None)

        if fwd and hasattr(fwd, 'id'):
            fwd_info = f" fwd_user={fwd.id}"
            name = getattr(fwd, 'full_name', '') or getattr(fwd, 'first_name', '') or ''
            forward_data = {"type": "user", "from_id": fwd.id, "from_name": str(name)}
        elif fwd_chat:
            title = getattr(fwd_chat, 'title', '') or ''
            cid = getattr(fwd_chat, 'id', '')
            fwd_info = f" fwd_chat={title}({cid})"
            forward_data = {"type": "chat", "from_chat_id": cid, "from_chat_title": str(title)}
        elif fwd_sender:
            fwd_info = f" fwd_sender={fwd_sender}"
            forward_data = {"type": "sender", "sender_name": str(fwd_sender)}
        if fwd_date:
            try:
                forward_data["forward_date"] = fwd_date.isoformat()
            except Exception:
                pass
        if auto_fwd:
            forward_data["auto"] = True

    log.info(f"Dispatch: uid={uid}{fwd_info} text={text[:50] if text else '(no text)'}")

    # Save structured message
    _save_message_record(uid, text, forward_data)

    if not user_exists(uid):
        u = update.effective_user
        log_unauthorized(uid, u.username, u.first_name, text)
        await _reply(update, "❌ Доступ запрещён.", uid)
        return

    ensure_super()

    # check send queue
    item = queue_pop(uid)
    if item:
        try:
            media = []
            for path in item["files"]:
                p = Path(path)
                if p.exists():
                    with open(p, "rb") as f:
                        media.append(InputMediaPhoto(media=f))
            if media:
                caption = item.get("caption", "")
                if caption and media:
                    media[0] = InputMediaPhoto(media=media[0].media, caption=caption)
                await update.message.reply_media_group(media=media)
        except Exception as e:
            log.warning(f"send_queue error: {e}")

    voice = update.message.voice if update.message else None

    if voice:
        await _handle_voice(update, context, uid)
        return


    if doc:
        await _handle_file(update, context, uid, doc)
        return

    if not text:
        await _reply(update, "❌ Пустое сообщение.", uid)
        return

    symbol, tf, rv, err = parse_request_regular(text)
    if err:
        await _reply(update, err, uid)
        return
    if symbol:
        await _handle_screenshot(update, context, uid, symbol, tf, rv, use_widget=False)
        return

    symbol, tf, rv, err = parse_request_widget(text)
    if err:
        await _reply(update, err, uid)
        return
    if symbol:
        await _handle_screenshot(update, context, uid, symbol, tf, rv, use_widget=True)
        return

    parts = text.split()
    cmd = parts[0].lower()
    args = parts[1:] if len(parts) > 1 else []

    if cmd in ("/sc", "/wg") and is_super(uid):
        use_widget = cmd == "/wg"
        args_upper = [a.upper() if i == 0 else a for i, a in enumerate(args)]
        text_for_parse = f"{'wg' if use_widget else 'sc'} {' '.join(args_upper)}"
        fn = parse_request_widget if use_widget else parse_request_regular
        symbol, tf, rv, err = fn(text_for_parse)
        if err:
            await _reply(update, err, uid)
        elif symbol:
            await _handle_screenshot(update, context, uid, symbol, tf, rv, use_widget=use_widget)
        return

    handlers = {
        "/start": lambda: cmd_start(uid),
        "/new": lambda: cmd_new(uid, " ".join(args) if args else None),
        "/sessions": lambda: cmd_sessions(uid),
        "/switch": lambda: cmd_switch(uid, args[0]) if args else "❌ Укажи ключ сессии.",
        "/rename": lambda: cmd_rename(uid, args[0], " ".join(args[1:])) if len(args) >= 2 else "❌ /rename <key> <name>",
        "/drop": lambda: cmd_drop(uid),
        "/info": lambda: cmd_info(uid),
        "/quota": lambda: cmd_quota(uid),
        "/files": lambda: cmd_files(uid),
        "/rm": lambda: cmd_rm(uid, args[0]) if args else "❌ /rm <filename>",
        "/clean": lambda: cmd_clean(uid),
        "/purge": lambda: cmd_purge(uid),
        "/dropsession": lambda: cmd_dropsession(uid, args[0]) if args else "❌ /dropsession <key>",
        "/menu": lambda: cmd_menu(uid),
        "/models": lambda: _call_models(uid, " ".join(args) if args else None),
        "/request": lambda: _handle_request(uid, args),
        "/cd": lambda: cmd_cd(uid, args[0] if args else None) if is_super(uid) else "❌ Только super.",
        "/users": lambda: cmd_users(uid) if is_super(uid) else "❌ Только super.",
        "/adduser": lambda: cmd_adduser(uid, args[0], " ".join(args[1:]) if len(args) >= 2 else None),
        "/removeuser": lambda: cmd_removeuser(uid, args[0]) if args else "❌ /removeuser <id>",
        "/userinfo": lambda: cmd_userinfo(uid, args[0] if args else None),
        "/view": lambda: _handle_view(uid, args),
        "/setmodel": lambda: _handle_setmodel(uid, args),
        "/setlimit": lambda: cmd_setlimit(uid, args[0], args[1], args[2]) if len(args) >= 3 else "❌ /setlimit <id> <msg|token|storage|file> <value>",
        "/approve": lambda: cmd_approve(uid, args[0], args[1], args[2]) if len(args) >= 3 else "❌ /approve <id> <msg|token|storage|file> <value>",
        "/approve-model": lambda: cmd_approve_model(uid, args[0], " ".join(args[1:])) if len(args) >= 2 else "❌ /approve-model <id> <model>",
        "/deny": lambda: cmd_deny(uid, args[0]) if args else "❌ /deny <id>",
        "/broadcast": lambda: cmd_broadcast(uid, " ".join(args)) if is_super(uid) else "❌ Только super.",
        "/sandbox": lambda: cmd_sandbox(uid, args[0] if args else None),
        "/build": lambda: cmd_build(uid),
        "/plan": lambda: cmd_plan(uid),
        "/format": lambda: "обработка в dispatch",
        "/link": lambda: cmd_link(uid, args),
        "/unauthorized": lambda: cmd_unauthorized(uid),
        "/shutdown": lambda: _handle_shutdown(uid),
        "/sysinfo": lambda: cmd_sysinfo(uid),
        "/stop": lambda: _handle_stop(uid),
    }

    if cmd == "/build":
        reply = cmd_build(uid)
        if reply:
            await _reply(update, reply, uid, agent="build")
        return

    if cmd == "/plan":
        reply = cmd_plan(uid)
        if reply:
            await _reply(update, reply, uid, agent="plan")
        return

    if cmd == "/emj_positions":
        await _handle_emj_positions(update, uid)
        return

    if cmd == "/sc_positions":
        await _handle_sc_positions(update, uid)
        return

    if cmd == "/sc_analytics":
        await _handle_sc_analytics(update, uid, args)
        return

    if cmd == "/sc_graphs":
        await _handle_sc_graphs(update, uid)
        return

    if cmd == "/positions":
        if "--image" in args:
            await _handle_positions_image(update, uid)
        else:
            await _handle_positions(update, uid)
        return

    if cmd == "/ws_ob":
        await _handle_ws_ob(update, uid, args)
        return

    if cmd == "/wgc":
        await _handle_widget_collage(update, context, uid, text)
        return

    if cmd == "/audit_ip":
        await _handle_audit(update, uid, text)
        return

    if cmd in ("/task_stats", "/task_errors"):
        await _handle_task_stats(update, uid, text)
        return

    if cmd in ("/ofd_kkt", "/ofd_receipts", "/ofd_inn", "/ofd_shift",
               "/ofd_stat", "/ofd_orgs", "/ofd_receipts"):
        await _handle_ofd(update, uid, text)
        return
    if cmd == "/audit_inn":
        await _handle_audit_inn(update, uid, text)
        return

    if cmd == "/restart":
        await _handle_restart(update, uid)
        return

    if cmd == "/metrics":
        await _handle_metrics(update, uid, args)
        return

    if cmd == "/task":
        await _handle_task_report(update, uid, args)
        return

    if cmd == "/status":
        args = text.split()[1:] if len(text.split()) > 1 else []
        if args and args[0] == "mode" and len(args) >= 2:
            mode = args[1].lower()
            if mode in ("compact", "normal", "full", "auto"):
                _Monitor.set_status_mode(uid, mode)
                await _reply(update, f"✅ Режим статуса: {mode}", uid)
            else:
                await _reply(update, "❌ Режимы: compact, normal, full, auto", uid)
        else:
            await _reply(update, "❌ /status mode <compact|normal|full|auto>", uid)
        return

    if cmd == "/format":
        body = (
            "Спойлер: скрытый текст\n"
            "Моноширинный: код\n"
            "Жирный: важное\n"
            "Обычный: полный текст"
        )
        for label, pm, fs in [
            ("MarkdownV2 — ссылка", "MarkdownV2", "link"),
            ("MarkdownV2 — спойлер", "MarkdownV2", "spoiler"),
            ("MarkdownV2 — моно", "MarkdownV2", "mono"),
            ("HTML — ссылка", "HTML", "link"),
            ("HTML — спойлер", "HTML", "spoiler"),
            ("HTML — моно", "HTML", "mono"),
        ]:
            await _reply(update, f"📌 {label}\n\n{body}", uid, parse_mode=pm, fmt_style=fs)
        return

    if cmd == "/save":
        reply = await asyncio.to_thread(kb_commands.cmd_save, uid, args)
        if reply:
            await _reply(update, reply, uid, parse_mode="MarkdownV2")
        return

    if cmd == "/bookmarks":
        reply = await asyncio.to_thread(kb_commands.cmd_bookmarks, uid, args)
        if reply:
            await _reply(update, reply, uid)
        return

    if cmd == "/search":
        reply = await asyncio.to_thread(kb_commands.cmd_search, uid, args)
        if reply:
            await _reply(update, reply, uid)
        return

    if cmd == "/tags":
        reply = await asyncio.to_thread(kb_commands.cmd_tags, uid, args)
        if reply:
            await _reply(update, reply, uid)
        return

    if cmd == "/kb_stats":
        reply = await asyncio.to_thread(kb_commands.cmd_kb_stats, uid)
        if reply:
            await _reply(update, reply, uid)
        return

    if cmd == "/chart" and is_super(uid):
        await _handle_chart(update, uid, args)
        return

    handler = handlers.get(cmd)
    if handler:
        reply = await asyncio.to_thread(handler)
        if reply:
            await _reply(update, reply, uid)
        return

    url_match = re.search(r'(https?://[^\s<>"\'()]+)', text)
    if url_match:
        url = url_match.group(0)
        url_lower = url.lower()

        if any(d in url_lower for d in ["youtube.com", "youtu.be"]):
            await _handle_youtube(update, uid, text)
            return

        if "rutube.ru" in url_lower:
            await _handle_rutube(update, uid, url)
            return

        reply = await asyncio.to_thread(kb_commands.cmd_save, uid, [url])
        if reply:
            await _reply(update, reply, uid, parse_mode="MarkdownV2")
        return

    await _handle_message(uid, text, update)


async def _handle_message(uid, text, update):
    user = get_user(uid)
    if not user:
        await _reply(update, "❌ Пользователь не найден.", uid)
        return

    if not is_super(uid):
        limits = user.get("limits")
        if limits:
            key, sess = get_current_session(uid)
            msgs = sess["messages"] if sess else 0
            if msgs >= limits.get("msg", 50):
                await _reply(update, "❌ Лимит сообщений исчерпан. Обратитесь к администратору.", uid)
                return
            fcount, fsize = get_quota(uid)
            if fsize >= limits.get("storage_mb", 500) * 1_000_000:
                await _reply(update, "❌ Лимит хранилища исчерпан.", uid)
                return
            if fcount >= limits.get("file_count", 1000):
                await _reply(update, "❌ Лимит количества файлов исчерпан.", uid)
                return

        blocked, reason = pre_filter(uid, text)
        if blocked:
            await _reply(update, f"⚠️ Действие запрещено политикой безопасности.\nПричина: {reason}", uid)
            return

    proc = _active_processes.get(uid)
    if proc and proc.returncode is None:
        await _reply(update, "⏳ Предыдущий запрос ещё выполняется. Дождитесь ответа.", uid)
        return

    log.info("_handle_message: cmd_message thread start")
    loop = asyncio.get_event_loop()
    start_ts = time.time()

    # Acquire opencode lock
    ok, msg = await task_control.acquire(uid, text)
    if not ok:
        await _reply(update, msg, uid)
        return

    # Create task
    current_task_id = task_state.task_create(uid, text)
    task_state.task_start(current_task_id)

    status_msg = None
    _cached_footer = ""
    # Set offset BEFORE thread starts so 🔤 shows correct delta
    _k, _s = get_current_session(uid)
    _initial_tok = _s.get("tokens", 0) if _s else 0
    _Monitor.set_offset(uid, _initial_tok)
    try:
        from metrics import mark_task_start
        mark_task_start(uid, current_task_id, text, task_state._cmd_code(text))
    except Exception:
        pass

    _edit_count = 0
    _result_sent = False
    thread_task = loop.run_in_executor(None, cmd_message, uid, text)

    # Watchdog — принудительная отправка результата в TG, если основной цикл не смог
    async def _watchdog_send():
        nonlocal _result_sent
        try:
            r = await asyncio.shield(thread_task)
        except Exception as e:
            log.error(f"watchdog: task error {e}")
            if not _result_sent:
                await _reply(update, f"❌ Ошибка выполнения: {e}", uid)
            return
        if _result_sent:
            return
        log.info("watchdog: sending result (main loop missed it)")
        _result_sent = True
        resp, err, new_images = r[0], r[1], r[2]
        agent_label = r[3] if len(r) >= 4 else None
        if err:
            await _reply(update, f"❌ {err}", uid)
        elif resp:
            if new_images:
                full = f"{resp}\n\n━━━\n\n{_Monitor.status_block4(uid, agent=agent_label, live_tok=_Monitor.get_delta(uid))}"
                if len(full) <= 1000:
                    media = []
                    for i, img_path in enumerate(new_images):
                        with open(img_path, "rb") as f:
                            media.append(InputMediaPhoto(media=f, caption=full if i == 0 else None))
                    await update.message.reply_media_group(media=media)
                else:
                    await _reply(update, resp, uid, agent=agent_label, live_tok=_Monitor.get_delta(uid), show_footer=True)
                    media = []
                    for img_path in new_images:
                        with open(img_path, "rb") as f:
                            media.append(InputMediaPhoto(media=f))
                    await update.message.reply_media_group(media=media)
            else:
                await _reply(update, resp, uid, agent=agent_label, live_tok=_Monitor.get_delta(uid), show_footer=True)
        task_control.release(uid, text)

    asyncio.create_task(_watchdog_send())
    result = None

    while True:
        elapsed = int(time.time() - start_ts)
        try:
            result = await asyncio.wait_for(asyncio.shield(thread_task), timeout=3)
            break
        except asyncio.TimeoutError:
            elapsed = int(time.time() - start_ts)
            block1 = await _Monitor.status_block1(uid, elapsed)

            # Check if process died unexpectedly
            if elapsed > 10:
                from security import _active_processes as _aprocs
                _aproc = _aprocs.get(uid)
                if _aproc and _aproc.returncode is not None:
                    log.warning(f"Process died unexpectedly (rc={_aproc.returncode}) for uid={uid}")
                    cancel_process(uid)
                    task_state.task_fail(current_task_id, f"process died rc={_aproc.returncode}")
                    task_control.release(uid, text)
                    if status_msg:
                        try:
                            await status_msg.edit_text("💀 Process died unexpectedly")
                        except Exception:
                            pass
                    result = (None, f"💀 Процесс завершился (rc={_aproc.returncode})", [], None)
                    break

            block2 = await _Monitor.status_block2(uid, current_task_id, elapsed)
            block3 = await _Monitor.status_block3()
            if elapsed % 10 < 3:
                _cached_footer = _Monitor.status_block4(uid, live_tok=0)
            block4 = _cached_footer

            lines = block1[:]
            lines.extend(block2)
            if block3:
                lines.extend(["", *block3])
                from system_info import get_uptime as _gup
                lines.append(f"⏱ Uptime: {_gup()}")
            if block4:
                lines.extend(["", "━━━", "", block4])
            if elapsed >= 300:
                wait_counter = (elapsed // 30) * 30
                lines.extend(["", f"⏳ Ожидание ответа от модели: {wait_counter}с",
                              "/stop => Отменить"])
            text = "\n".join(lines)
            if len(text) > 3800:
                text = text[:3500] + "\n\n... (truncated)"

            if status_msg is None or _edit_count >= 80:
                if status_msg:
                    try:
                        await asyncio.wait_for(status_msg.delete(), timeout=2)
                    except Exception:
                        pass
                try:
                    status_msg = await asyncio.wait_for(
                        update.message.reply_text(text), timeout=5
                    )
                    _edit_count = 0
                except asyncio.TimeoutError:
                    log.warning("status reply_text timeout — retrying")
                    continue
            else:
                try:
                    await asyncio.wait_for(status_msg.edit_text(text), timeout=2)
                    _edit_count += 1
                except (asyncio.TimeoutError, Exception) as e:
                    log.warning(f"status edit error: {e}")
                    try:
                        await asyncio.wait_for(status_msg.delete(), timeout=2)
                    except Exception:
                        pass
                    try:
                        status_msg = await asyncio.wait_for(
                            update.message.reply_text(text), timeout=5
                        )
                        _edit_count = 0
                    except asyncio.TimeoutError:
                        log.warning("status reply_text timeout — retrying")
                        continue

    try:
        log.info("_handle_message: cmd_message returned")

        _delta_tok = _Monitor.get_delta(uid)

        if _result_sent:
            log.warning("_handle_message: result already sent by watchdog")
            return

        if result is None or not isinstance(result, (list, tuple)):
            log.warning("_handle_message: empty result — no response from agent")
            result = (None, "✅ Готово.", [], None)

        if len(result) == 4:
            resp, err, new_images, agent_label = result
        else:
            resp, err, new_images = result
            agent_label = None

        if err:
            log.info("_handle_message: replying with error")
            _result_sent = True
            await _reply(update, err, uid, agent=agent_label, live_tok=_delta_tok, show_footer=True)
            log.info("_handle_message: error reply done")
        elif resp:
            log.info("_handle_message: replying with response")
            _result_sent = True
            if new_images:
                footer = _Monitor.status_block4(uid, agent=agent_label, live_tok=_delta_tok)
                full = f"{resp}\n\n━━━\n\n{footer}"
                if len(full) <= 1000:
                    media = []
                    for i, img_path in enumerate(new_images):
                        with open(img_path, "rb") as f:
                            if i == 0:
                                media.append(InputMediaPhoto(media=f, caption=full))
                            else:
                                media.append(InputMediaPhoto(media=f))
                    await update.message.reply_media_group(media=media)
                else:
                    await _reply(update, resp, uid, agent=agent_label, live_tok=_delta_tok, show_footer=True)
                    media = []
                    for img_path in new_images:
                        with open(img_path, "rb") as f:
                            media.append(InputMediaPhoto(media=f))
                    await update.message.reply_media_group(media=media)
            else:
                await _reply(update, resp, uid, agent=agent_label, live_tok=_delta_tok, show_footer=True)
        if resp:
            log.info("📨 FINAL:\n%s", resp[:500])
        elif err:
            log.info("📨 FINAL ERR:\n%s", err[:500])

        # task complete + release
        elapsed_ms = task_state.task_complete(current_task_id) or 0
        task_control.release(uid, text)

        # completion summary
        try:
            from metrics import mark_task_end, read_task_samples, build_metrics_block
            from templates import _fmt_tokens as _ft
            _cost_val = _Monitor._cost_finals.get(uid, 0.0)
            mark_task_end(uid, current_task_id, elapsed_ms, _delta_tok, _cost_val)

            sec = elapsed_ms // 1000
            elapsed_str = f"{sec // 60}м {sec % 60}с" if sec >= 60 else f"{sec}с"
            inp = _Monitor._input_finals.get(uid, 0)
            out = _Monitor._output_finals.get(uid, 0)
            total_tok = inp + out or 1
            cost_in = _cost_val * (inp / total_tok)
            cost_out = _cost_val * (out / total_tok)

            lines = [f"━━━ ✅ Задача выполнена ━━━", ""]
            lines.append(f"📋 {cmd_label[:120] if 'cmd_label' in dir() else text[:120]}")
            lines.append(f"🤖 {agent_label or 'opencode-go'} · ⏱ {elapsed_str} · 💲{_cost_val:.4f}")
            lines.append("")

            mdata = read_task_samples(current_task_id)
            if mdata and len(mdata) >= 2:
                lines.extend(build_metrics_block(mdata))
                lines.append("")

            lines.append(f"🔤 +{_ft(_delta_tok)}💲{_cost_val:.4f} · ⏱ {elapsed_str}")
            lines.append(f"↙ {_ft(inp)}💲{cost_in:.4f} · ↗ {_ft(out)}💲{cost_out:.4f}")

            summary = "\n".join(lines)
            await asyncio.wait_for(update.message.reply_text(summary), timeout=5)
        except Exception as e:
            log.warning(f"completion summary error: {e}")
            try:
                await asyncio.wait_for(update.message.reply_text(
                    f"━━━ ✅ Задача выполнена ━━━\n\n"
                    f"📋 {text[:120]}\n"
                    f"⏱ {elapsed_str} · 💲{_cost_val:.4f}\n\n"
                    f"📊 Подробный отчёт недоступен (metrics: {e})"
                ), timeout=5)
            except Exception:
                pass
    except Exception as e:
        log.error(f"_handle_message: reply failed: {e}")
        if not _result_sent:
            try:
                await asyncio.wait_for(
                    update.message.reply_text("✅ Готово (ошибка форматирования)."),
                    timeout=5
                )
            except Exception:
                pass
    finally:
        task_state.task_complete(current_task_id)
        task_control.release(uid, text)

    if status_msg:
        try:
            await asyncio.wait_for(status_msg.delete(), timeout=3)
        except Exception as e:
            log.warning(f"status delete error: {e}")


async def _handle_screenshot(update, context, uid, symbol, tf, range_val="", use_widget=False):
    import time as _time
    t0 = _time.time()
    label = "Widget" if use_widget else "TradingView dark"
    rng = f" range={range_val}" if range_val else ""
    status_msg = await update.message.reply_text(f"📸 Делаю скриншот {symbol} {tf} ({label}){rng}...")

    user_dir = sud(uid)
    user_dir.mkdir(parents=True, exist_ok=True)

    log.info(f"_handle_screenshot: symbol={symbol} tf={tf} range={range_val or '-'} uid={uid} widget={use_widget}")
    fn = take_screenshot_widget if use_widget else take_screenshot_regular
    path, err = await fn(symbol, tf, str(user_dir), range_val)

    if err:
        log.error(f"_handle_screenshot failed: {err}")
        await status_msg.edit_text(f"❌ Ошибка скриншота: {err}")
        return

    elapsed = int((_time.time() - t0) * 1000)
    ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
    log.info(f"_handle_screenshot: ready to send {path}")
    tf_label = TF_LABEL.get(tf, tf)
    await status_msg.delete()
    try:
        with open(path, "rb") as f:
            await update.message.reply_photo(
                photo=f,
                caption=f"📊 {symbol} ({tf_label}) | {ts} | {elapsed}ms"
            )
        log.info(f"_handle_screenshot: photo sent OK")
    except Exception as e:
        log.error(f"_handle_screenshot reply_photo: {e}")
        await update.message.reply_text(f"✅ Скриншот сохранён, но не отправлен: {e}", uid)


async def _handle_widget_collage(update, context, uid, text):
    parts = text.split()
    if len(parts) < 2:
        await _reply(update, "❌ /wgc <SYMBOL>\nПример: /wgc BTCUSDT", uid)
        return

    symbol_raw = parts[1].upper()
    if ":" not in symbol_raw:
        symbol_raw = f"BITGET:{symbol_raw}"

    tfs = ["1d", "4h", "1h"]
    await _reply(update, f"📸 Делаю коллаж {symbol_raw} (1d+4h+1h)...", uid)

    user_dir = sud(uid)
    user_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    screenshots = []
    for tf in tfs:
        path, err = await take_screenshot_widget(symbol_raw, screenshot_widget.TF_MAP[tf], str(user_dir))
        if err:
            await _reply(update, f"❌ {symbol_raw} {tf}: {err}", uid)
            return
        screenshots.append(path)

    safe = symbol_raw.lower().replace(":", "_")
    collage_path = os.path.join(str(user_dir), f"collage_{safe}.png")
    make_collage(screenshots, collage_path)

    elapsed = int((time.time() - t0) * 1000)
    ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")

    with open(collage_path, "rb") as f:
        await update.message.reply_photo(
            photo=f,
            caption=f"📊 {symbol_raw} (1d · 4h · 1h) | {ts} | {elapsed}ms"
        )

    log.info(f"Collage sent: {collage_path} ({elapsed}ms)")


async def _handle_ofd(update, uid, text):
    from yandex_ofd import YandexOfdClient
    import json
    parts = text.split()
    cmd = parts[0].lower() if parts else ""

    try:
        client = YandexOfdClient()
    except Exception as e:
        await _reply(update, f"❌ OFD client error: {e}", uid)
        return

    try:
        if cmd == "/ofd_kkt":
            data = client.kkt_list()
            await _reply(update, f"📟 **ККТ:**\n{json.dumps(data, indent=2, ensure_ascii=False)[:3500]}", uid)
        elif cmd == "/ofd_inn":
            inn = parts[1] if len(parts) > 1 else "010500776503"
            data = client.inn(inn)
            await _reply(update, f"🔍 **ИНН {inn}:**\n{json.dumps(data, indent=2, ensure_ascii=False)[:3500]}", uid)
        elif cmd == "/ofd_receipts":
            fn = parts[1] if len(parts) > 1 else ""
            date = parts[2] if len(parts) > 2 else ""
            with_items = "items" in parts
            if not fn or not date:
                await _reply(update, "❌ /ofd_receipts <fn> <date> [items]", uid)
                return
            data = client.get_daily_receipts(fn, date, with_items=with_items)
            text = json.dumps(data, indent=2, ensure_ascii=False)[:3500]
            await _reply(update, f"📋 **Чеки {date}:**\n{text}", uid)
        elif cmd == "/ofd_shift":
            fn = parts[1] if len(parts) > 1 else ""
            if not fn:
                await _reply(update, "❌ /ofd_shift <fn>", uid)
                return
            data = client.shifts(fn)
            await _reply(update, f"📊 **Смены:**\n{json.dumps(data, indent=2, ensure_ascii=False)[:3500]}", uid)
        elif cmd == "/ofd_stat":
            fn = parts[1] if len(parts) > 1 else ""
            if not fn:
                await _reply(update, "❌ /ofd_stat <fn>", uid)
                return
            data = client.get_doc_count(fn)
            await _reply(update, f"📈 **Статистика:**\n{json.dumps(data, indent=2, ensure_ascii=False)[:3500]}", uid)
        elif cmd == "/ofd_orgs":
            import glob, json
            orgs = []
            for p in glob.glob("TG_ALL/tg_ofd/orgs/*.json"):
                orgs.append(json.load(open(p)))
            text = "\n".join(f"🏢 {o.get('name','?')} ({o.get('inn','?')})" for o in orgs)
            await _reply(update, f"**Организации:**\n{text}" if text else "❌ нет организаций", uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка OFD: {e}", uid)


async def _handle_audit(update, uid, text):
    from ip_audit import (
        scan_stage1, scan_stage2, scan_stage3_ports, scan_stage3_vuln,
        whois_lookup, geo_lookup, shodan_lookup, ping_host,
        fmt_beauty_stage, fmt_full_md, fmt_third_party,
        resolve_hostname,
    )
    import time

    def _is_ip(s):
        parts = s.split(".")
        return len(parts) == 4 and all(p.isdigit() for p in parts)

    parts = text.split()
    deep = "--deep" in parts
    raw = next((p for p in parts if not p.startswith("/") and p != "--deep"), "")

    if not raw:
        await _reply(update, "❌ Укажи IP или домен.\n  /audit_ip 8.8.8.8\n  /audit_ip google.com\n  /audit_ip --deep 8.8.8.8", uid)
        return

    if _is_ip(raw):
        ip = raw
        hostname = None
    else:
        hostname = raw.lower()
        ip, err = resolve_hostname(hostname)
        if err:
            await _reply(update, f"❌ {err}", uid)
            return

    status = await update.message.reply_text(f"🔍 Сканирую {hostname or ip}...")

    alive = await ping_host(ip)

    whois, geo, shodan = await asyncio.gather(
        asyncio.to_thread(whois_lookup, ip),
        asyncio.to_thread(geo_lookup, ip),
        shodan_lookup(ip),
    )

    if not deep:
        s1 = await scan_stage1(ip)
        report = fmt_beauty_stage(ip, "Top-50 сканирование", s1, whois, hostname=hostname)
        third = fmt_third_party(ip, geo, shodan, hostname=hostname)
        if third:
            report += f"\n{third}"
        report += "\n💡 **Полный аудит:** `/audit_ip --deep <...>`"
        await status.edit_text(report[:4000])
        return

    t0 = time.time()
    stages = []

    await status.edit_text(f"🔍 Stage 1 — Top-50 портов {hostname or ip}...")
    s1 = await scan_stage1(ip)
    t1 = time.time()
    stages.append(("Stage 1 (top-50)", s1))

    await status.edit_text(f"🔍 Stage 2 — Top-1000 + версии {hostname or ip}...")
    s2 = await scan_stage2(ip)
    t2 = time.time()
    stages.append(("Stage 2 (top-1000)", s2))

    await status.edit_text(f"🔍 Stage 3 — Все порты + CVE {hostname or ip}...")
    s3p, s3v = await asyncio.gather(
        scan_stage3_ports(ip), scan_stage3_vuln(ip)
    )
    t3 = time.time()
    stages.append(("Stage 3 (all 65535)", s3p))

    timings = [t1 - t0, t2 - t1, t3 - t2]
    report = fmt_full_md(ip, stages, whois, s3v, timings, ping=alive, hostname=hostname)
    third = fmt_third_party(ip, geo, shodan, hostname=hostname)
    if third:
        report += f"\n\n{third}"
    await status.edit_text(report[:4000])


async def _handle_audit_inn(update, uid, text):
    from audit_inn import audit_inn
    parts = text.split()
    inn = parts[1] if len(parts) > 1 else "010500776503"
    await _reply(update, f"🔍 Аудит ИНН {inn}...", uid)
    try:
        data = audit_inn(inn)
        lines = [f"━━━ ✅ Аудит ИНН {inn} ━━━\n"]

        valid = data.get("valid", "")
        if valid and valid.startswith("⛔"):
            lines.append(f"{valid}")
            await _reply(update, "\n".join(lines), uid)
            return

        lines.append(f"{valid} **{data['egrul'].get('name', '?')}**")
        short = data["egrul"].get("short", "")
        if short:
            lines[1] = f"{valid} **{data['egrul']['name']}** ({short})"
        head = data["egrul"].get("head", "")
        if head:
            lines.append(f"👤 {head}")
        lines.append(f"🆔 {data['egrul'].get('ogrn', '?')} · 📅 {data['egrul'].get('reg_date', '?')}")
        addr = data["egrul"].get("address", "")
        if addr:
            lines.append(f"🏠 {addr}")
        kpp = data["egrul"].get("kpp", "")
        if kpp:
            lines.append(f"📊 КПП: {kpp}")
        lines.append("")

        # Service statuses
        lines.append("📊 Статусы источников:")
        egrul_st = data["egrul"]["status"]
        egrul_note = "название, адрес, руководитель, КПП"
        if data["egrul"].get("name"):
            egrul_note = f"найден: {data['egrul']['name'][:50]}"
        lines.append(f"{egrul_st} ЕГРЮЛ — {egrul_note}")

        fssp = data.get("fssp", {})
        if fssp:
            f_note = fssp.get("note", "")[:100]
            lines.append(f"{fssp['status']} ФССП — {f_note}")

        bankr = data.get("bankruptcy", {})
        if bankr:
            b_note = bankr.get("note", "")[:100]
            cases = bankr.get("bankruptcies", [])
            if cases:
                b_note = f"найдено {len(cases)} дел"
            lines.append(f"{bankr['status']} Банкротства — {b_note}")

        await _reply(update, "\n".join(lines), uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка аудита: {e}", uid)


async def _handle_task_report(update, uid, args):
    if not args:
        await _reply(update, "❌ Укажи task_id\nПример: /task 248207602-XOCX-M01-171", uid)
        return
    task_id = args[0]
    try:
        from metrics import read_task_samples, build_metrics_block
        from templates import _fmt_tokens as _ft
        mdata = read_task_samples(task_id)
        if not mdata:
            await _reply(update, f"❌ Задача {task_id} не найдена в metrics.log", uid)
            return
        block1 = f"━━━ ✅ Задача выполнена ━━━\n\n📋 {task_id}"
        if len(mdata) >= 2:
            metrics_lines = build_metrics_block(mdata)
            block2 = "\n\n━━━ 📊 Метрики задачи ━━━\n\n" + "\n".join(metrics_lines)
        else:
            block2 = ""
        # ищем task_end маркер для токенов и времени
        import json
        end_entry = None
        with open("/tmp/opencode/metrics.log") as f:
            for line in f:
                try:
                    e = json.loads(line)
                except Exception:
                    continue
                if e.get("_type") == "task_end" and e.get("task_id") == task_id:
                    end_entry = e
        if end_entry:
            sec = (end_entry.get("elapsed_ms", 0) or 0) // 1000
            elapsed_str = f"{sec // 60}м {sec % 60}с" if sec >= 60 else f"{sec}с"
            dt = end_entry.get("delta_tok", 0)
            c = end_entry.get("cost", 0.0)
            block3 = f"\n\n━━━ 📊 Токены и время ━━━\n\n⏱ {elapsed_str} · 🔤 +{_ft(dt)}💲{c:.4f}"
        else:
            block3 = ""
        await _reply(update, block1 + block2 + block3, uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка: {e}", uid)


async def _handle_metrics(update, uid, args):
    import json, os
    from pathlib import Path

    log_path = Path("/tmp/opencode/metrics.log")
    if not log_path.exists():
        await _reply(update, "❌ metrics.log не найден. Запусти метрики.", uid)
        return

    # парсим временной диапазон
    default_minutes = 3
    if args:
        try:
            raw = args[0].lower()
            if raw.endswith("h"):
                default_minutes = int(raw[:-1]) * 60
            elif raw.endswith("m"):
                default_minutes = int(raw[:-1])
            else:
                default_minutes = int(raw)
        except ValueError:
            pass
    want_points = default_minutes * 60 // 3

    lines = log_path.read_text().strip().split("\n")
    points = [json.loads(l) for l in lines[-want_points:] if l.strip()]
    if len(points) < 2:
        await _reply(update, "❌ Недостаточно точек для графика.", uid)
        return

    await _reply(update, f"📊 Строю график ({len(points)} точек)...", uid)

    try:
        import plotly.graph_objects as go
        from plotly.subplots import make_subplots

        ts = [p["ts"] for p in points]
        cpu = [p["cpu"] for p in points]
        mem_u = [p["mem"]["u"] for p in points]
        mem_f = [p["mem"]["f"] for p in points]
        mem_c = [p["mem"]["c"] for p in points]
        proc = [p["proc"] for p in points]
        load = [p["load"][0] for p in points]

        fig = make_subplots(
            rows=4, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.06,
            subplot_titles=("CPU (%)", "Memory (MB)", "Processes", "Load Avg"),
        )

        fig.add_trace(go.Scatter(x=ts, y=cpu, name="CPU", line=dict(color="#ff6b6b")), row=1, col=1)
        fig.add_trace(go.Scatter(x=ts, y=mem_u, name="Used", line=dict(color="#ffa726")), row=2, col=1)
        fig.add_trace(go.Scatter(x=ts, y=mem_f, name="Free", line=dict(color="#66bb6a")), row=2, col=1)
        fig.add_trace(go.Scatter(x=ts, y=mem_c, name="Cache", line=dict(color="#42a5f5")), row=2, col=1)
        fig.add_trace(go.Scatter(x=ts, y=proc, name="Procs", line=dict(color="#ab47bc")), row=3, col=1)
        fig.add_trace(go.Scatter(x=ts, y=load, name="Load 1m", line=dict(color="#ef5350")), row=4, col=1)

        fig.update_layout(
            height=600, margin=dict(l=20, r=20, t=30, b=20),
            template="plotly_dark", showlegend=False,
            paper_bgcolor="#1a1a2e", plot_bgcolor="#1a1a2e"
        )
        fig.update_xaxes(showticklabels=False, row=1, col=1)
        fig.update_xaxes(showticklabels=False, row=2, col=1)
        fig.update_xaxes(showticklabels=False, row=3, col=1)
        fig.update_xaxes(row=4, col=1)

        img_path = f"/tmp/metrics_{int(time.time())}.png"
        fig.write_image(img_path, width=800, height=600, scale=1)

        with open(img_path, "rb") as f:
            from datetime import datetime
            caption = f"📊 Метрики ({len(points)} точек | {default_minutes}мин)"
            await update.message.reply_photo(photo=f, caption=caption)

        os.unlink(img_path)

    except ImportError as e:
        await _reply(update, f"❌ plotly не установлен: {e}", uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка графика: {e}", uid)


async def _handle_youtube(update, uid, url):
    t0 = time.time()
    await _reply(update, "🎬 Загружаю и транскрибирую видео...", uid)
    try:
        text = await asyncio.to_thread(transcribe_youtube, url)
        elapsed_ms = int((time.time() - t0) * 1000)
        if text and text != "(пусто)":
            title = _yt_title(url)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = [
                f"🎬 **{title}**",
                f"🔗 {url}",
                "",
                "📝 Транскрипция",
                "🌐 ru",
                "",
                "━━━",
                f"🕐 {now}",
                f"⏱ {elapsed_ms:,}ms",
                f"⚙ локальный Whisper (CPU)",
                "  ├─ download+convert",
                "  ├─ whisper asr",
                f"  └─ chars:{len(text):,}",
                "",
            ]
            if len(text) > 2800:
                txt_path = f"/tmp/transcript_{int(time.time())}.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                header.append(f"📄 Полный текст ({len(text)} символов) — отправлен файлом")
                await update.message.reply_text("\n".join(header))
                await update.message.reply_document(open(txt_path, "rb"))
            else:
                header.append(text)
                await update.message.reply_text("\n".join(header))
        else:
            await _reply(update, "❌ Не удалось распознать речь.", uid)
    except subprocess.TimeoutExpired:
        await _reply(update, "⏱ Превышено время ожидания (5 мин).", uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка: {e}", uid)


def _yt_title(url: str) -> str:
    try:
        res = subprocess.run(["yt-dlp", "--get-title", url],
                             capture_output=True, text=True, timeout=30)
        return (res.stdout.strip() or "Untitled")[:80]
    except Exception:
        return "Untitled"


async def _handle_rutube(update, uid, url):
    t0 = time.time()
    await _reply(update, "🎬 Загружаю и транскрибирую Rutube...", uid)
    try:
        text = await asyncio.to_thread(transcribe_rutube, url)
        elapsed_ms = int((time.time() - t0) * 1000)
        if text and text != "(пусто)":
            title = _yt_title(url)
            now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            header = [
                f"🎬 **{title}**",
                f"🔗 {url}",
                "",
                "📝 Транскрипция",
                "🌐 ru",
                "",
                "━━━",
                f"🕐 {now}",
                f"⏱ {elapsed_ms:,}ms",
                f"⚙ локальный Whisper (CPU)",
                "  ├─ download+convert",
                "  ├─ whisper asr",
                f"  └─ chars:{len(text):,}",
                "",
            ]
            if len(text) > 2800:
                txt_path = f"/tmp/transcript_{int(time.time())}.txt"
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write(text)
                header.append(f"📄 Полный текст ({len(text)} символов) — отправлен файлом")
                await update.message.reply_text("\n".join(header))
                await update.message.reply_document(open(txt_path, "rb"))
            else:
                header.append(text)
                await update.message.reply_text("\n".join(header))
        else:
            await _reply(update, "❌ Не удалось распознать речь.", uid)
    except subprocess.TimeoutExpired:
        await _reply(update, "⏱ Превышено время ожидания (5 мин).", uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка: {e}", uid)


async def _handle_voice(update, context, uid):
    duration = update.message.voice.duration
    await _reply(update, f"🎤 Распознаю голосовое ({duration}c)...", uid)

    try:
        text = await transcribe_voice(update, context)
    except Exception as e:
        log.error(f"Voice transcription error: {e}")
        await _reply(update, f"❌ Ошибка распознавания: {e}\n\nПроверьте: /sysinfo", uid)
        return

    if not text:
        await _reply(update, "❌ Не удалось распознать речь.", uid)
        return

    await _reply(update, f"📝 Распознано: «{text}»", uid)
    await _handle_message(uid, text, update)


async def _handle_file(update, context, uid, doc):
    if not get_user(uid):
        await _reply(update, "❌ Доступ запрещён.", uid)
        return

    if not is_super(uid):
        user = get_user(uid)
        limits = user.get("limits") if user else {}
        if limits:
            fcount, fsize = get_quota(uid)
            file_size = doc.file_size or 0
            if fcount >= limits.get("file_count", 1000):
                await _reply(update, f"❌ Лимит файлов ({limits['file_count']}) исчерпан.", uid)
                return
            if fsize + file_size > limits.get("storage_mb", 500) * 1_000_000:
                await _reply(update,
                    f"❌ Превышение квоты хранилища "
                    f"({_fmt_size(fsize + file_size)} > {limits['storage_mb']}MB)", uid)
                return

    upload_dir = sud(uid) / "uploads"
    upload_dir.mkdir(parents=True, exist_ok=True)

    try:
        tg_file = await context.bot.get_file(doc.file_id)
        fname = doc.file_name or f"file_{datetime.now().strftime('%H%M%S')}"
        local_path = upload_dir / fname
        await tg_file.download_to_drive(str(local_path))
        await _reply(update,
            f"✅ Файл {fname} загружен.\n"
            f"Теперь отправь запрос в opencode, "
            f"например: \"извлеки таблицы из {fname} на страницах 1-3\"", uid)
    except Exception as e:
        await _reply(update, f"❌ Ошибка загрузки: {e}", uid)


def _handle_request(uid, args):
    if len(args) < 2:
        return "❌ /request <model|limit> <value>"
    if args[0] == "model":
        return cmd_request_model(uid, " ".join(args[1:]))
    if args[0] == "limit":
        if len(args) < 3:
            return "❌ /request limit <msg|token|storage|file> <count>"
        return cmd_request_limit(uid, args[1], args[2])
    return "❌ /request model <name>  или  /request limit <msg|token|storage|file> <count>"


def _handle_view(uid, args):
    if len(args) < 3 or args[1] != "session":
        return "❌ /view <id> session <key>"
    return cmd_view(uid, args[0], args[2])


def _handle_shutdown(uid):
    result = cmd_shutdown(uid)
    if result == "🛑 SHUTDOWN":
        import os
        os._exit(0)
    return result


def _handle_stop(uid):
    """Принудительная остановка текущего процесса opencode."""
    import logging
    log = logging.getLogger("tg_bot")
    if uid not in _active_processes:
        return "⏹ Нет активного процесса для остановки."
    cancel_process(uid)
    log.warning("Process stopped by /stop for uid=%s", uid)
    return "⏹ Процесс остановлен. Можно отправить новый запрос."


async def _handle_restart(update, uid):
    from task_state import task_create, task_start

    if not is_super(uid):
        await _reply(update, "❌ Только super.", uid)
        return

    tid = task_create(uid, "🔄 Bot restart — завершение сессии...")
    task_start(tid)

    status = await update.message.reply_text(
        "🔄 **Bot restart...**\n\n"
        "⏱ Через 3 секунды бот перезапустится\n"
        "┣ Очистка старых задач — ✅\n"
        "┣ Сохранение состояния — ✅\n"
        "┗ Отчёт после перезапуска — ⏳\n\n"
        "━━━\n"
        "После рестарта отправь `/menu` для проверки"
    )

    await asyncio.sleep(2)

    import subprocess, os
    script = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "tg_bot.sh")
    subprocess.Popen(["bash", script, "restart"],
                     stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    await asyncio.sleep(1)
    try:
        await status.edit_text(
            "🔄 **Бот перезапускается...**\n\n"
            "⏱ Через 2-3с новый процесс встанет на polling\n"
            "📋 После запуска — `/menu`"
        )
    except Exception:
        pass


def _call_models(uid, arg):
    return cmd_models(uid, arg)


def _handle_setmodel(uid, args):
    if not is_super(uid):
        return "❌ Только super."
    if len(args) < 2:
        return "❌ /setmodel <uid> <модель> [лимит]\n   /setmodel default <модель>"
    if args[0] == "default":
        return cmd_setmodel(uid, "default", " ".join(args[1:]))
    return cmd_setmodel(uid, args[0], " ".join(args[1:]))




