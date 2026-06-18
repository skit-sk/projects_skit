import asyncio
import logging
import time
import os
import sys
import re
from datetime import datetime
from pathlib import Path

_HANDLER_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(_HANDLER_DIR))
sys.path.insert(0, str(_HANDLER_DIR / "bot"))

from config import SUPER_USER, TG_ALL_DIR, ALL_USERS_DIR, WORKSPACE_DIR, VENV_PYTHON

sys.path.insert(0, str(WORKSPACE_DIR / "projects" / "08_ofd_api" / "bot_ofd"))
sys.path.insert(0, str(WORKSPACE_DIR / "tools" / "scripts"))

from commands import *
from session import (
    ensure_super, get_user, user_exists, get_quota,
    get_current_session, log_unauthorized,
    resolve_uid, is_super,
    link_platforms, add_platform_link, user_dir,
)
from security import pre_filter
import monitor as _Monitor
import task_state
import task_control
import task_stats
from templates import build_footer
from screenshot_browser import (
    parse_request as parse_request_regular,
    take_screenshot as take_screenshot_regular,
)
from screenshot_widget import (
    parse_request as parse_request_widget,
    take_screenshot as take_screenshot_widget,
)
import screenshot_widget
from collage import make_collage
from kb_commands import cmd_save, cmd_bookmarks, cmd_search, cmd_tags, cmd_kb_stats

log = logging.getLogger("max_bot")

MAX_MESSAGE_LIMIT = 4000

_client = None
_pending_tasks: dict = {}

def set_client(client):
    global _client
    _client = client


async def send_message(uid, text, format="markdown", keyboard=None):
    if _client is None:
        log.error("MAXClient not set")
        return
    try:
        await _client.send_message(uid, text, format=format, keyboard=keyboard)
    except Exception as e:
        log.error(f"send_message error (uid={uid}): {e}")


async def send_image(uid, image_path, caption=None):
    if _client is None:
        log.error("MAXClient not set")
        return None
    try:
        return await _client.send_image(uid, image_path, caption=caption)
    except Exception as e:
        log.error(f"send_image error (uid={uid}): {e}")
        return None


async def send_file(uid, file_path, caption=None):
    if _client is None:
        return None
    try:
        return await _client.send_file(uid, file_path, caption=caption)
    except Exception as e:
        log.error(f"send_file error (uid={uid}): {e}")
        return None


async def dispatch(update: dict):
    update_type = update.get("update_type")

    if update_type == "message_created":
        await _handle_message_created(update)
    elif update_type == "message_callback":
        await _handle_callback(update)
    elif update_type == "bot_started":
        await _handle_bot_started(update)
    elif update_type == "bot_added":
        await _handle_bot_added(update)
    elif update_type == "bot_stopped":
        log.info(f"Bot stopped by user {update.get('user', {}).get('user_id')}")
    else:
        log.debug(f"Unhandled update type: {update_type}")


async def _handle_bot_started(update: dict):
    user = update.get("user", {})
    uid = user.get("user_id")
    if not uid:
        return
    ensure_super()
    resolved = resolve_uid(uid)
    if not resolved:
        log_unauthorized(uid, user.get("first_name", ""), user.get("username", ""))
        await send_message(
            uid,
            f"❌ Доступ запрещён.\nВаш ID: `{uid}`\nОбратитесь к администратору для добавления в белый список.",
        )
        return

    create_session(resolved)
    await send_message(
        uid,
        f"👋 Добро пожаловать, {user.get('first_name', '')}!\n"
        f"Используй /menu для списка команд или просто напиши сообщение.",
    )


async def _handle_bot_added(update: dict):
    user = update.get("user", {})
    uid = user.get("user_id")
    chat_id = update.get("chat_id")
    if uid and chat_id:
        log.info(f"Bot added to chat {chat_id} by user {uid}")


async def _handle_callback(update: dict):
    callback_id = update.get("callback_id")
    data = update.get("data", "")
    uid = update.get("user", {}).get("user_id")

    if not uid or not resolve_uid(uid):
        return

    if _client:
        await _client.answer_callback(callback_id, "✅")


async def _handle_message_created(update: dict):
    ensure_super()

    message = update.get("message", {})
    body = message.get("body", {})
    text = (body or {}).get("text", "").strip()
    sender = message.get("sender", {})
    uid = sender.get("user_id") if sender else None

    if not uid:
        log.warning("No user_id in message_created")
        return

    resolved = resolve_uid(uid)
    if not resolved:
        log_unauthorized(uid, sender.get("first_name", ""), sender.get("username", ""), text[:100])
        await send_message(
            uid,
            f"❌ Доступ запрещён.\n"
            f"Ваш ID: `{uid}`\n"
            f"Обратитесь к администратору для добавления в белый список.",
        )
        return

    if not text:
        attachments = (body or {}).get("attachments", [])
        if attachments:
            text = "[вложение]"
        else:
            return

    await _route_command(uid, text)


async def _route_command(uid: int, text: str):
    parts = text.split()
    cmd = parts[0].lower() if parts else ""
    args = parts[1:] if len(parts) > 1 else []

    if cmd in ("/start", "/new", "/sessions", "/switch", "/rename",
               "/drop", "/info", "/quota", "/files", "/rm",
               "/clean", "/purge", "/dropsession", "/menu",
               "/models", "/request", "/cd", "/users",
               "/adduser", "/removeuser", "/userinfo", "/view",
               "/setmodel", "/setlimit", "/approve", "/approve-model",
               "/deny", "/broadcast", "/sandbox", "/build",
               "/plan", "/format", "/unauthorized", "/shutdown",
               "/sysinfo", "/stop", "/link"):
        reply = _run_sync_cmd(cmd, uid, args)
        if reply:
            await send_message(uid, reply)
        return

    screenshot_cmds = {"/sc", "/wg", "/wgc", "/sc_positions",
                       "/sc_analytics", "/sc_graphs",
                       "/emj_positions", "/positions",
                       "/ws_ob"}

    if cmd in screenshot_cmds:
        await _handle_screenshot_cmd(uid, cmd, text)
        return

    if cmd == "/task_stats" or cmd == "/task_errors":
        reply = task_stats.cmd_task_stats(uid, args[0] if args else None) if cmd == "/task_stats" else task_stats.cmd_task_errors(uid)
        await send_message(uid, reply or "Нет данных")
        return

    if cmd == "/save":
        reply = cmd_save(uid, args)
        await send_message(uid, reply or "Готово")
        return

    if cmd in ("/bookmarks", "/search", "/tags", "/kb_stats"):
        if cmd == "/bookmarks":
            reply = cmd_bookmarks(uid, args)
        elif cmd == "/search":
            reply = cmd_search(uid, " ".join(args))
        elif cmd == "/tags":
            reply = cmd_tags(uid, args[0] if args else None)
        else:
            reply = cmd_kb_stats(uid)
        await send_message(uid, reply or "Нет данных")
        return

    await _handle_message(uid, text)


def _run_sync_cmd(cmd: str, uid: int, args: list) -> str | None:
    handler_map = {
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
        "/models": lambda: cmd_models(uid, " ".join(args) if args else None),
        "/request": lambda: _handle_request(uid, args),
        "/cd": lambda: cmd_cd(uid, args[0] if args else None) if is_super(uid) else "❌ Только super.",
        "/users": lambda: cmd_users(uid) if is_super(uid) else "❌ Только super.",
        "/adduser": lambda: cmd_adduser(uid, args[0], " ".join(args[1:]) if len(args) >= 2 else None),
        "/removeuser": lambda: cmd_removeuser(uid, args[0]) if args else "❌ /removeuser <id>",
        "/userinfo": lambda: cmd_userinfo(uid, args[0] if args else None),
        "/view": lambda: cmd_view(uid, args[0] if args else None, args[1] if len(args) > 1 else None),
        "/setmodel": lambda: cmd_setmodel(uid, args),
        "/setlimit": lambda: cmd_setlimit(uid, args[0], args[1], args[2]) if len(args) >= 3 else "❌ /setlimit <id> <msg|token|storage|file> <value>",
        "/approve": lambda: cmd_approve(uid, args[0], args[1], args[2]) if len(args) >= 3 else "❌ /approve <id> <msg|token|storage|file> <value>",
        "/approve-model": lambda: cmd_approve_model(uid, args[0], " ".join(args[1:])) if len(args) >= 2 else "❌ /approve-model <id> <model>",
        "/deny": lambda: cmd_deny(uid, args[0]) if args else "❌ /deny <id>",
        "/broadcast": lambda: cmd_broadcast(uid, " ".join(args)) if is_super(uid) else "❌ Только super.",
        "/sandbox": lambda: cmd_sandbox(uid, args[0] if args else None),
        "/build": lambda: cmd_build(uid),
        "/plan": lambda: cmd_plan(uid),
        "/unauthorized": lambda: cmd_unauthorized(uid),
        "/link": lambda: cmd_link(uid, args),
        "/sysinfo": lambda: cmd_sysinfo(uid),
        "/stop": lambda: "❌ /stop не поддерживается в MAX (используйте системный kill)",
        "/shutdown": lambda: _handle_shutdown(uid),
        "/format": lambda: "форматирование не поддерживается в MAX",
    }
    handler = handler_map.get(cmd)
    if handler:
        return handler()
    return None


async def _handle_screenshot_cmd(uid: int, cmd: str, text: str):
    if cmd == "/wgc":
        await _handle_widget_collage(uid, text)
        return

    if cmd == "/sc_positions":
        await _handle_run_script_and_send(
            uid, "screenshot_positions.py", "positions_table.png", "📸 Позиции",
            output_dir_flag="--output-dir"
        )
        return
    if cmd == "/sc_analytics":
        parts = text.split()
        user_path = user_dir(uid, "max")
        user_path.mkdir(parents=True, exist_ok=True)
        if len(parts) >= 2:
            symbol = parts[1].upper()
            await _handle_run_script_and_send(
                uid, "screenshot_analytics.py", f"{symbol}_analytics.png",
                f"📸 {symbol}", extra_args=["--symbols", symbol], timeout=180,
                output_dir_flag="--output-dir"
            )
        else:
            await send_message(uid, "🔄 📸 Аналитика всех символов...")
            script = WORKSPACE_DIR / "tools" / "scripts" / "screenshot_analytics.py"
            cmd = [VENV_PYTHON, str(script), "--output-dir", str(user_path), "--all"]
            proc_env = {**os.environ, "PYTHONUNBUFFERED": "1"}
            proc = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                env=proc_env,
            )
            await asyncio.wait_for(proc.wait(), timeout=180)
            t0 = time.time()
            emj_path = user_path / "positions_emj_rows.txt"
            emj_rows = {}
            if emj_path.exists():
                for line in emj_path.read_text(encoding="utf-8").split("\n"):
                    line = line.strip()
                    for png in user_path.glob("*_analytics.png"):
                        sym = png.stem.replace("_analytics", "").upper()
                        if f"🚏{sym}" in line:
                            emj_rows[sym] = line
            sent_count = 0
            for png in sorted(user_path.glob("*_analytics.png")):
                sym = png.stem.replace("_analytics", "").upper()
                caption = f"📊 {sym}"
                if sym in emj_rows:
                    caption += f"\n{emj_rows[sym]}"
                ok = await send_image(uid, str(png), caption=caption)
                if ok is not None:
                    sent_count += 1
                await asyncio.sleep(1)
            elapsed = int((time.time() - t0) * 1000)
            ts = datetime.now().strftime("%H:%M:%S")
            await send_message(uid, f"✅ Отправлено {sent_count} | {ts} | {elapsed}ms")
        return
    if cmd == "/sc_graphs":
        parts = text.split()
        user_path = user_dir(uid, "max")
        if len(parts) >= 2:
            symbol = parts[1].upper()
            await _handle_run_script_and_send(
                uid, "screenshot_card.py", f"{symbol.lower()}_graph.png",
                f"📊 {symbol}",
                extra_args=["--symbol", symbol],
                output_dir_flag="--output-dir"
            )
            fname = f"{symbol.lower()}_graph.png"
        else:
            await _handle_run_script_and_send(
                uid, "screenshot_graphs.py", "graphs_all.png", "📸 Графики",
                output_dir_flag="--output-dir"
            )
            fname = "graphs_all.png"
        fpath = user_path / fname
        if fpath.exists():
            await send_file(uid, str(fpath), caption=f"{fname} original")
        return
    if cmd == "/ws_ob":
        await _handle_ws_ob(uid, text)
        return
    if cmd == "/emj_positions":
        await _handle_emj_positions(uid)
        return
    if cmd == "/positions":
        if "--image" in text:
            await _handle_positions_image(uid)
        else:
            await _handle_positions(uid)
        return

    use_widget = cmd == "/wg"
    parse_fn = parse_request_widget if use_widget else parse_request_regular

    text_for_parse = f"{'wg' if use_widget else 'sc'} {' '.join(text.split()[1:])}".upper()
    symbol, tf, rv, err = parse_fn(text_for_parse)
    if err:
        await send_message(uid, err)
        return
    if not symbol:
        await send_message(uid, f"❌ {cmd} <SYMBOL> [tf] [range]\nПример: {cmd} BTCUSDT")
        return

    label = "Widget" if use_widget else "TradingView"
    await send_message(uid, f"📸 Делаю скриншот {label} {symbol}...")
    fn = take_screenshot_widget if use_widget else take_screenshot_regular
    path, err = await fn(symbol, tf, str(user_dir(uid, "max")), rv)
    if err:
        await send_message(uid, f"❌ {err}")
        return
    await send_image(uid, path, caption=f"📊 {label} {symbol}")
    log.info(f"Screenshot sent: {symbol} {tf} rv={rv}")


async def _handle_widget_collage(uid: int, text: str):
    parts = text.split()
    if len(parts) < 2:
        await send_message(uid, "❌ /wgc <SYMBOL>\nПример: /wgc BTCUSDT")
        return

    symbol_raw = parts[1].upper()
    if ":" not in symbol_raw:
        symbol_raw = f"BITGET:{symbol_raw}"

    tfs = ["1d", "4h", "1h"]
    await send_message(uid, f"📸 Делаю коллаж {symbol_raw} (1d+4h+1h)...")

    u_dir = user_dir(uid, "max")
    u_dir.mkdir(parents=True, exist_ok=True)
    t0 = time.time()

    screenshots = []
    for tf in tfs:
        path, err = await take_screenshot_widget(
            symbol_raw, screenshot_widget.TF_MAP[tf], str(u_dir)
        )
        if err:
            await send_message(uid, f"❌ {symbol_raw} {tf}: {err}")
            return
        screenshots.append(path)

    safe = symbol_raw.lower().replace(":", "_")
    collage_path = os.path.join(str(u_dir), f"collage_{safe}.png")
    make_collage(screenshots, collage_path)

    elapsed = int((time.time() - t0) * 1000)
    ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
    caption = f"📊 {symbol_raw} (1d · 4h · 1h) | {ts} | {elapsed}ms"

    ok = await send_image(uid, collage_path, caption=caption)
    if ok is not None:
        log.info(f"Collage sent: {collage_path} ({elapsed}ms)")
    else:
        log.error(f"Collage send failed: {collage_path}")


async def _handle_emj_positions(uid: int):
    try:
        output_dir = str(user_dir(uid, "max"))
        proc = await asyncio.create_subprocess_exec(
            VENV_PYTHON, str(WORKSPACE_DIR / "tools" / "scripts" / "get_emj_rows.py"),
            "--output-dir", output_dir,
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        await asyncio.wait_for(proc.communicate(), timeout=30)

        txt_path = Path(output_dir) / "positions_emj_rows.txt"
        if not txt_path.exists():
            await send_message(uid, "❌ Нет данных по позициям")
            return

        text = txt_path.read_text(encoding="utf-8").strip()
        await send_message(uid, text, format="markdown")

    except Exception as e:
        await send_message(uid, f"❌ Ошибка: {e}")


async def _handle_positions(uid: int):
    try:
        proc = await asyncio.create_subprocess_exec(
            VENV_PYTHON, str(WORKSPACE_DIR / "tools" / "scripts" / "positions_summary.py"),
            stdout=asyncio.subprocess.PIPE, stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=30)
        text = stdout.decode().strip()
        if text:
            await send_message(uid, text, format="markdown")
        else:
            await send_message(uid, "❌ Нет данных по позициям")
    except Exception as e:
        await send_message(uid, f"❌ Ошибка: {e}")


async def _handle_run_script_and_send(
    uid: int, script_name: str, image_name: str | None,
    label: str, extra_args: list[str] | None = None,
    timeout: int = 120, output_dir_flag: str | None = None
):
    script = WORKSPACE_DIR / "tools" / "scripts" / script_name
    if not script.exists():
        await send_message(uid, f"❌ Скрипт не найден: {script}")
        return
    user_path = user_dir(uid, "max")
    user_path.mkdir(parents=True, exist_ok=True)
    await send_message(uid, f"🔄 {label}...")
    t0 = time.time()
    try:
        cmd = [VENV_PYTHON, str(script)]
        if output_dir_flag:
            cmd.extend([output_dir_flag, str(user_path)])
        if extra_args:
            cmd.extend(extra_args)
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )
        stdout, stderr = await asyncio.wait_for(proc.communicate(), timeout=timeout)
        elapsed = int((time.time() - t0) * 1000)
        ts = datetime.now().strftime("%d.%m.%y %H:%M:%S")
        if proc.returncode != 0:
            err = (stderr.decode()[:200] or stdout.decode()[:200])
            await send_message(uid, f"❌ Ошибка: {err}")
            return
        if image_name:
            img_path = user_path / image_name
            if img_path.exists():
                emj_line = ""
                emj_path = user_path / "positions_emj_rows.txt"
                if emj_path.exists() and " " in label:
                    sym = label.split(" ", 1)[1].split(" ")[0].upper()
                    if len(sym) <= 10:
                        for line in emj_path.read_text(encoding="utf-8").strip().split("\n"):
                            if f"🚏{sym}" in line:
                                emj_line = line.strip()
                                break
                caption = f"{emj_line}\n| {ts} | {elapsed}ms" if emj_line else f"{label} | {ts} | {elapsed}ms"
                ok = await send_image(uid, str(img_path), caption=caption)
                if ok is not None:
                    log.info(f"Image sent: {img_path} ({elapsed}ms)")
                else:
                    await send_message(uid, f"✅ {label} не отправлен (ошибка API)")
            else:
                await send_message(uid, f"✅ {label} сохранён, файл: {image_name}")
        # image_name=None — скрипт сам вывел результат, не дублируем
    except asyncio.TimeoutError:
        await send_message(uid, f"⏱ Превышено время ({timeout}с)")
    except Exception as e:
        await send_message(uid, f"❌ Ошибка: {e}")


async def _handle_positions_image(uid: int):
    import httpx
    t0 = time.time()
    await send_message(uid, "🔄 📊 Сводка позиций...")
    try:
        async with httpx.AsyncClient(base_url="http://localhost:5000", timeout=httpx.Timeout(15.0)) as _hclient:
            resp = await _hclient.get("/account-api/api/computed")
            data = resp.json()
            if "error" in data:
                await send_message(uid, f"❌ {data['error']}")
                return
            positions = data.get("positions", [])
            totals = data.get("totals", {})
            fill_counts = data.get("fill_counts", {})

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

        from rich.console import Console
        from formatters.screenshot import async_render_rich_to_png
        from rich.table import Table

        console = Console(record=True, width=100)
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
        img_path = f"/tmp/positions_risk_{int(time.time())}.png"
        result = await async_render_rich_to_png(console, img_path)

        if result:
            user_path = user_dir(uid, "max")
            user_path.mkdir(parents=True, exist_ok=True)
            final_path = user_path / "positions_table.png"
            import shutil
            shutil.copy(result, str(final_path))
            elapsed = int((time.time() - t0) * 1000)
            ts = datetime.now().strftime("%H:%M:%S")
            ok = await send_image(uid, str(final_path), caption=f"📊 Positions | {ts} | {elapsed}ms")
            if ok is not None:
                log.info(f"Positions image sent ({elapsed}ms)")
            else:
                await send_message(uid, f"✅ Таблица сохранена, но не отправлена")
        else:
            await send_message(uid, "❌ Не удалось отрисовать таблицу")

    except Exception as e:
        await send_message(uid, f"❌ Ошибка: {e}")


async def _handle_ws_ob(uid: int, text: str):
    parts = text.split()
    args = parts[1:] if len(parts) > 1 else []
    want_image = "--image" in args
    clean_args = [a for a in args if a != "--image"]

    if not clean_args:
        await send_message(uid, "❌ /ws_ob <SYMBOL> [depth] [aggr] [--image]\nПример: /ws_ob BTC 50 1")
        return

    symbol = clean_args[0].upper()
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

    await send_message(uid, f"📊 Получаю стакан {symbol}...")

    from formatters.orderbook import fetch_aggregated_ob_ws
    data = await fetch_aggregated_ob_ws(symbol, depth, bucket_size)
    if not data:
        await send_message(uid, f"❌ Нет данных стакана для {symbol}")
        return

    asks = data.get("asks", [])
    bids = data.get("bids", [])
    if not asks or not bids:
        await send_message(uid, f"❌ Нет данных стакана для {symbol}")
        return

    t0 = time.time()

    if want_image:
        from rich.console import Console
        from formatters.screenshot import async_render_rich_to_png
        from rich.table import Table

        req_bs = data.get("requested_bucket_size", bucket_size)
        actual_bs = data.get("bucket_size", bucket_size)
        actual_a = len(asks)
        actual_b = len(bids)
        table_title = f"📊 Order Book {symbol}"
        if actual_bs:
            table_title += f" (aggr: {actual_bs} USDT"
            if actual_bs != req_bs:
                table_title += f" req: {req_bs}"
            table_title += f", depth: {actual_a}:{actual_b}/{depth})"
        else:
            table_title += f" (depth: {actual_a}:{actual_b}/{depth})"

        console = Console(record=True, width=120)
        tbl = Table(title=table_title, width=120)
        tbl.add_column("Bid Price", style="green", justify="right")
        tbl.add_column("Bid Vol", style="green", justify="right")
        tbl.add_column("|", justify="center", width=1)
        tbl.add_column("B/A", justify="center", width=8)
        tbl.add_column("│", justify="center", width=1)
        tbl.add_column("Ask Price", style="bright_red", justify="right")
        tbl.add_column("Ask Vol", style="bright_red", justify="right")

        max_rows = max(len(asks), len(bids))

        bids_display = list(reversed(bids))
        asks_display = asks

        for i in range(max_rows):
            b = bids_display[i] if i < len(bids_display) else ["", ""]
            a = asks_display[i] if i < len(asks_display) else ["", ""]
            bv = float(b[1]) if b[1] and b[1] != '-' else 0
            av = float(a[1]) if a[1] and a[1] != '-' else 0

            ba = bv / av if av > 0 else (99 if bv > 0 else 1)
            ba_colored = f"[green]↑{ba:.1f}x[/]" if ba > 1.2 else f"[red]↓{ba:.1f}x[/]" if ba < 0.8 else f"[dim]{ba:.1f}x[/]"

            bp = str(b[0]) if b[0] and b[0] != '-' else ""
            bv_s = str(b[1]) if b[1] else ""
            ap = str(a[0]) if a[0] and a[0] != '-' else ""
            av_s = str(a[1]) if a[1] else ""

            tbl.add_row(bp, bv_s, "|", ba_colored, "│", ap, av_s)

        if asks and bids and asks[0] and bids[0]:
            try:
                sp = float(asks[0][0]) - float(bids[0][0])
                sp_pct = sp / float(bids[0][0]) * 100
                tbl.add_section()
                tbl.add_row("", "", "", f"[dim]Spread {sp:.2f} ({sp_pct:.3f}%)[/]", "", "", "")
            except (ValueError, IndexError):
                pass

        total_bid_vol = sum(float(b[1]) for b in bids if b[1] and b[1] != '-')
        total_ask_vol = sum(float(a[1]) for a in asks if a[1] and a[1] != '-')
        ba_total = total_bid_vol / total_ask_vol if total_ask_vol else 99
        ba_total_text = f"[green]↑{ba_total:.1f}x[/]" if ba_total > 1.2 else f"[red]↓{ba_total:.1f}x[/]" if ba_total < 0.8 else f"[dim]{ba_total:.1f}x[/]"
        tbl.add_section()
        tbl.add_row(f"TOTAL: {total_bid_vol:.4f}", "", "|", ba_total_text, "│", f"TOTAL: {total_ask_vol:.4f}", "", style="bold")

        console.print(tbl)
        img_path = f"/tmp/ob_{symbol}_{int(time.time())}.png"
        result = await async_render_rich_to_png(console, img_path, title=table_title)

        if result:
            user_path = user_dir(uid, "max")
            user_path.mkdir(parents=True, exist_ok=True)
            import shutil
            final_path = user_path / f"ob_{symbol.lower()}.png"
            shutil.copy(result, str(final_path))
            elapsed = int((time.time() - t0) * 1000)
            ts = datetime.now().strftime("%H:%M:%S")
            ok = await send_image(uid, str(final_path), caption=f"📊 {symbol} Order Book | {ts} | {elapsed}ms")
            if ok is not None:
                log.info(f"OB image sent ({elapsed}ms)")
        else:
            from formatters.positions_risk import format_order_book
            text = format_order_book(symbol, asks, bids, bucket_size)
            await send_message(uid, f"{text}\n\n{symbol}")
    else:
        from formatters.positions_risk import format_order_book
        actual_bs = data.get("bucket_size", bucket_size)
        actual_asks = len(asks)
        actual_bids = len(bids)
        text = format_order_book(symbol, asks, bids, actual_bs)
        await send_message(uid, f"{text}\n\n{symbol} | asks: {actual_asks} bids: {actual_bids} depth: {depth}")


async def _handle_request(uid, args):
    if not args:
        return "❌ /request <текст>"
    return "Запрос принят."


async def _handle_shutdown(uid):
    if uid != SUPER_USER:
        return "❌ Только super."
    log.warning(f"Shutdown requested by {uid}")
    loop = asyncio.get_event_loop()
    loop.call_later(1, os._exit, 0)
    return "🔄 Завершение работы..."


async def _handle_message(uid: int, text: str):
    blocked, reason = pre_filter(uid, text)
    if blocked:
        await send_message(uid, f"❌ Блокировка: {reason}")
        return

    ok, msg = await task_control.acquire(uid, "opencode")
    if not ok:
        await send_message(uid, msg)
        return

    task_id = task_state.task_create(uid, "M01")
    task_state.task_start(task_id)
    _pending_tasks[uid] = task_id
    t0 = time.time()

    try:
        response, error, new_images, agent_label = cmd_message(uid, text)
        elapsed = int((time.time() - t0) * 1000)

        if error:
            await send_message(uid, f"❌ {error[:1000]}")
            task_state.task_fail(task_id, error)
            return

        if response:
            chunks = _chunk_text(response, MAX_MESSAGE_LIMIT)
            for chunk in chunks:
                await send_message(uid, chunk)

        if new_images:
            for img in new_images:
                if os.path.exists(img):
                    await send_image(uid, img)

        elapsed_fmt = f"{elapsed}ms"
        task_state.task_complete(task_id)
        log.info(f"AI response sent (uid={uid}) elapsed={elapsed_fmt}")

    except Exception as e:
        log.error(f"_handle_message error (uid={uid}): {e}", exc_info=True)
        await send_message(uid, f"❌ Внутренняя ошибка: {str(e)[:500]}")
        task_state.task_fail(task_id, str(e)[:200])
    finally:
        task_control.release(uid, "opencode")
        _pending_tasks.pop(uid, None)


def _chunk_text(text: str, limit: int) -> list[str]:
    if len(text) <= limit:
        return [text]
    chunks = []
    while text:
        if len(text) <= limit:
            chunks.append(text)
            break
        split_at = text.rfind("\n", 0, limit)
        if split_at == -1:
            split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        chunks.append(text[:split_at])
        text = text[split_at:].strip()
    return chunks
