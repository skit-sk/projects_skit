import os
import sys
import asyncio
import logging
import time
import subprocess
import signal
from datetime import datetime
from pathlib import Path
from config import SUPER_USER, TG_ALL_DIR, WORKSPACE_DIR
sys.path.insert(0, str(WORKSPACE_DIR / "projects" / "08_ofd_api" / "bot_ofd"))
from commands import *
from session import ensure_super, get_user, user_exists, get_quota, get_current_session, log_unauthorized
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

log = logging.getLogger("tg_bot")

WORKSPACE = WORKSPACE_DIR
SCRIPTS_DIR = WORKSPACE / "tools" / "scripts"
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

def _kill_process_group(proc_pid):
    """Kill the process group of a spawned process (not other users' processes).
    
    Uses os.killpg on the stored PID (which is the PGID when using os.setpgrp).
    Safe to call after process exits — handles ESRCH gracefully.
    """
    import errno
    if proc_pid is None or proc_pid <= 1:
        return
    import time
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try:
            os.killpg(proc_pid, sig)
            if sig == signal.SIGTERM:
                time.sleep(0.5)
        except OSError as e:
            if e.errno == errno.ESRCH:
                break  # all processes in group are gone
            if e.errno == errno.EPERM:
                break  # no permission (already reaped)


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


async def _handle_tg_positions(update, uid):
    import time as _time
    t0 = _time.time()
    status_msg = await update.message.reply_text("📊 Получаю строки позиций...")
    script = SCRIPTS_DIR / "get_tg_rows.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err_txt = stderr.decode()[:200] or f"(пустой stderr, stdout: {stdout.decode()[:200]})"
            await status_msg.edit_text(f"❌ Ошибка скрипта (rc={proc.returncode}): {err_txt}")
            return

        user_dir = TG_ALL_DIR / f"TG_{uid}"
        txt_path = user_dir / "positions_tg_rows.txt"
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
    status_msg = await update.message.reply_text("📸 Делаю скриншот позиций...")

    script = SCRIPTS_DIR / "screenshot_positions.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err = (stderr.decode()[:200] or stdout.decode()[:200])
            await status_msg.edit_text(f"❌ Ошибка скриншота: {err}")
            return

        user_dir = TG_ALL_DIR / f"TG_{uid}"
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
    target = args[0] if args else "all"

    status_msg = await update.message.reply_text("📸 Делаю скриншот аналитики...")

    script = SCRIPTS_DIR / "screenshot_analytics.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        is_all = target.lower() == "all"
        cmd_args = [sys.executable, str(script), "--all"] if is_all else [sys.executable, str(script), "--symbol", target]
        proc = await asyncio.create_subprocess_exec(
            *cmd_args,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=120)
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err = (stderr.decode()[:200] or stdout.decode()[:200])
            await status_msg.edit_text(f"❌ Ошибка скриншота: {err}")
            return

        user_dir = TG_ALL_DIR / f"TG_{uid}"

        ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
        caption_base = f"📊 Analytics | {ts} | {elapsed}ms"
        await status_msg.delete()

        if is_all:
            # Collect all screenshots from the API list
            import json, urllib.request as _req
            try:
                list_resp = _req.urlopen("http://localhost:5000/trade-analytics/api/list", timeout=5)
                obj_list = json.loads(list_resp.read())
            except Exception:
                obj_list = []
            media = []
            for obj in obj_list:
                if not obj.get("has_1d") or not obj.get("has_raw"):
                    continue
                sym = obj["symbol"]
                mp = user_dir / f"{sym}_main_chart.png"
                ip = user_dir / f"{sym}_indicators.png"
                if mp.exists():
                    with open(mp, "rb") as f:
                        media.append(InputMediaPhoto(media=f, caption=f"{caption_base} {sym}"))
                if ip.exists():
                    with open(ip, "rb") as f:
                        media.append(InputMediaPhoto(media=f))
            if media:
                # TG limit: 10 media per group
                for i in range(0, len(media), 10):
                    await update.message.reply_media_group(media=media[i:i+10])
            else:
                await update.message.reply_text("❌ Скриншоты не созданы")
        else:
            sym_upper = target.upper()
            main_path = user_dir / f"{sym_upper}_main_chart.png"
            indic_path = user_dir / f"{sym_upper}_indicators.png"
            caption = f"📊 Analytics {sym_upper} | {ts} | {elapsed}ms"
            media = []
            if main_path.exists():
                with open(main_path, "rb") as f:
                    media.append(InputMediaPhoto(media=f, caption=caption))
            if indic_path.exists():
                with open(indic_path, "rb") as f:
                    media.append(InputMediaPhoto(media=f))
            if media:
                await update.message.reply_media_group(media=media)
            else:
                await update.message.reply_text("❌ Скриншоты не созданы")
    except asyncio.TimeoutError:
        await status_msg.edit_text("⏱ Превышено время ожидания (120с)")
    except Exception as e:
        try:
            await status_msg.edit_text(f"❌ Ошибка: {e}")
        except Exception:
            pass
    finally:
        _kill_process_group(proc.pid if proc else None)


async def _handle_positions(update, uid):
    import time as _time, subprocess
    t0 = _time.time()
    status_msg = await update.message.reply_text("📊 Получаю сводку...")

    script = SCRIPTS_DIR / "get_tg_rows.py"
    if not script.exists():
        await status_msg.edit_text(f"❌ Скрипт не найден: {script}")
        return

    proc = None
    try:
        proc = await asyncio.create_subprocess_exec(
            sys.executable, str(script),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            preexec_fn=os.setpgrp
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=60)
        elapsed = int((_time.time() - t0) * 1000)

        if proc.returncode != 0:
            err_text = stderr.decode()[:200] or f"(пустой stderr, stdout: {stdout.decode()[:200]})"
            await status_msg.edit_text(f"❌ Ошибка скрипта (rc={proc.returncode}): {err_text}")
            return

        user_dir = TG_ALL_DIR / f"TG_{uid}"
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
    import json, urllib.request
    t0 = _time.time()
    status_msg = await update.message.reply_text("📊 Готовлю скриншот сводки...")

    try:
        # Sync exchange first
        try:
            req = urllib.request.Request(
                "http://localhost:5000/api/sync-all",
                data=b"",
                method="POST"
            )
            urllib.request.urlopen(req, timeout=30)
        except Exception:
            pass

        # Получить данные с API
        resp = urllib.request.urlopen(f"http://localhost:5000/account-api/api/computed", timeout=10)
        data = json.loads(resp.read())
        
        if "error" in data:
            await status_msg.edit_text(f"❌ {data['error']}")
            return
        
        positions = data.get("positions", [])
        totals = data.get("totals", {})
        fill_counts = data.get("fill_counts", {})
        order_counts = data.get("order_counts", {})
        
        # Balance
        balance = 0.0
        try:
            bresp = urllib.request.urlopen(f"http://localhost:5000/account-api/api/balance", timeout=5)
            bdata = json.loads(bresp.read())
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
        
        from formatters.positions_risk import format_risk_summary
        from rich.console import Console
        from formatters.screenshot import render_rich_to_png
        
        # Build Rich Table with record=True
        console = Console(record=True, width=100)
        from rich.table import Table
        table = Table(title=f"📊 Risk Summary (Balance: {balance:.2f} USDT)", width=100)
        table.add_column("Ticker", style="bold", no_wrap=True)
        table.add_column("Cnt", justify="right")
        table.add_column("Side", no_wrap=True)
        table.add_column("Margin", justify="right")
        table.add_column("Bal%", justify="right")
        table.add_column("Exp%", justify="right")
        table.add_column("P&L", justify="right")
        table.add_column("ROE%", justify="right")
        table.add_column("Lev", justify="right")
        table.add_column("LiqΔ%", justify="right")
        
        total_margin = 0.0
        total_pl = 0.0
        for pos in positions:
            margin = float(pos.get("margin_size", 0))
            pl = float(pos.get("unrealized_pl", 0))
            lev = float(pos.get("leverage", 0))
            total_margin += margin
            total_pl += pl
            bal_pct = (margin / balance * 100) if balance else 0
            exp_pct = (margin * lev / balance * 100) if balance else 0
            roe = (pl / margin * 100) if margin else 0
            open_p = float(pos.get("open_price_avg", 0))
            liq_p = float(pos.get("liquidation_price", 0))
            liq_d = abs((open_p - liq_p) / open_p * 100) if open_p and liq_p else 0
            side = "🟢 LONG" if pos.get("hold_side") == "long" else "🔴 SHORT"
            
            table.add_row(pos.get("symbol","?"), str(fill_counts.get(pos.get("symbol",""), 0)),
                         side, f"{margin:.6f}", f"{bal_pct:.2f}", f"{exp_pct:.2f}",
                         f"{pl:+.6f}", f"{'🔮' if roe>=100 else '💚' if roe>=30 else '🟢' if roe>=5 else '⚪' if roe>=-5 else '⚠️' if roe>=-30 else '🔶' if roe>=-100 else '🛑'}{roe:+.1f}",
                         f"{int(lev)}x", f"{liq_d:.1f}")
        
        table.add_section()
        total_margin_f = totals.get('total_margin', total_margin)
        total_pl_f = totals.get('total_pl', total_pl)
        total_roe = (total_pl_f / total_margin_f * 100) if total_margin_f else 0
        total_bal_pct = (total_margin_f / balance * 100) if balance else 0
        table.add_row("TOTAL", str(len(positions)), "", f"{total_margin_f:.6f}",
                     f"{total_bal_pct:.2f}", "",
                     f"{total_pl_f:+.6f}", f"{total_roe:+.1f}", "", "")
        
        console.print(table)
        img_path = f"/tmp/positions_risk_{int(_time.time())}.png"
        result = render_rich_to_png(console, img_path)
        
        if result:
            await status_msg.delete()
            with open(result, "rb") as f:
                await update.message.reply_photo(photo=f, caption=f"📊 Positions | {int((_time.time()-t0)*1000)}ms")
        else:
            # Fallback to text
            text = format_risk_summary(positions, balance, fill_counts, order_counts, totals)
            await status_msg.edit_text(f"{text}\n\n📊 Positions | {int((_time.time()-t0)*1000)}ms" if len(text) < 3500 else "❌ Ошибка создания изображения")
    
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
        from formatters.screenshot import render_rich_to_png
        
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
        result = render_rich_to_png(console, img_path, title=table_title)
        
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
    log.info(f"Dispatch: uid={uid} text={update.message.text[:50] if update.message and update.message.text else '(no text)'}")
    text = update.message.text.strip() if update.message and update.message.text else ""
    doc = update.message.document if update.message else None

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

    if text and any(d in text.lower() for d in ["youtube.com", "youtu.be", "ytube"]):
        await _handle_youtube(update, uid, text)
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

    if cmd == "/tg_positions":
        await _handle_tg_positions(update, uid)
        return

    if cmd == "/sc_positions":
        await _handle_sc_positions(update, uid)
        return

    if cmd == "/sc_analytics":
        await _handle_sc_analytics(update, uid, args)
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

    handler = handlers.get(cmd)
    if handler:
        reply = await asyncio.to_thread(handler)
        if reply:
            await _reply(update, reply, uid)
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
    from session import get_current_session
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

        if len(result) == 4:
            resp, err, new_images, agent_label = result
        else:
            resp, err, new_images = result
            agent_label = None

        if err:
            log.info("_handle_message: replying with error")
            await _reply(update, err, uid, agent=agent_label, live_tok=_delta_tok, show_footer=True)
            log.info("_handle_message: error reply done")
            _result_sent = True
        elif resp:
            log.info("_handle_message: replying with response")
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
            log.info("_handle_message: response reply done")
            _result_sent = True
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

    user_dir = TG_ALL_DIR / f"TG_{uid}"
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

    user_dir = TG_ALL_DIR / f"TG_{uid}"
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
    await _reply(update, "🎬 Загружаю и транскрибирую видео...", uid)
    try:
        text = await asyncio.to_thread(transcribe_youtube, url)
        if text and text != "(пусто)":
            await update.message.reply_text(f"📝 Транскрипция:\n\n{text}")
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

    upload_dir = TG_ALL_DIR / f"TG_{uid}" / "uploads"
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
        return "❌ /setmodel <провайдер> <модель>\n   /setmodel default <провайдер> <модель>\n   /setmodel <uid> <провайдер> <модель>"
    if len(args) == 2:
        return cmd_setmodel(uid, str(uid), args[0], args[1])
    if args[0] == "default" or (args[0].isdigit() and user_exists(int(args[0]))):
        return cmd_setmodel(uid, args[0], args[1], args[2])
    return cmd_setmodel(uid, str(uid), args[0], args[1])




