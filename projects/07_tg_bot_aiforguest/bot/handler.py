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
from commands import *
from session import ensure_super, get_user, user_exists, get_quota, get_current_session, log_unauthorized
from security import pre_filter, cancel_process, get_process_info, get_top5, _active_processes
from templates import build_footer, _fmt_size, _fmt_tokens
from telegram import InputMediaPhoto
from send_queue import queue_pop
from screenshot_browser import parse_request as parse_request_regular, take_screenshot as take_screenshot_regular, TF_LABEL
from screenshot_widget import parse_request as parse_request_widget, take_screenshot as take_screenshot_widget
from voice import transcribe_voice
from youtube_transcribe import transcribe_youtube

log = logging.getLogger("tg_bot")

WORKSPACE = WORKSPACE_DIR
SCRIPTS_DIR = WORKSPACE / "tools" / "scripts"

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
            await status_msg.edit_text(f"❌ Ошибка: {stderr.decode()[:200]}")
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


async def _reply(update, text, uid, agent=None, parse_mode=None, fmt_style="link", live_tok=0):
    try:
        footer = build_footer(uid, agent=agent, parse_mode=parse_mode, fmt_style=fmt_style, live_tok=live_tok)
    except Exception:
        footer = ""
    parts = text.split("\n━━━\n", 1)
    if len(parts) >= 2 and parts[1].strip():
        body, custom_footer = parts
        full = text
    else:
        body = parts[0]
        full = f"{text}\n\n━━━\n\n{footer}"
    if len(full) <= 4000:
        kwargs = {"parse_mode": parse_mode} if parse_mode else {}
        try:
            await update.message.reply_text(full, **kwargs)
        except Exception as e:
            log.error(f"_reply: {e}")
            kwargs.pop("parse_mode", None)
            try:
                await update.message.reply_text(f"✅ Ответ получен, но слишком длинный для Telegram.\n\n{footer}", **kwargs)
            except Exception as e:
                log.warning(f"_reply fallback failed: {e}")
        return
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
    kwargs = {"parse_mode": parse_mode} if parse_mode else {}
    for i, chunk in enumerate(chunks):
        if i < total - 1:
            await update.message.reply_text(f"{chunk}\n\n({i+1}/{total})", **kwargs)
        else:
            await update.message.reply_text(f"{chunk}\n\n{footer}", **kwargs)


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

    status_msg = None
    thread_task = loop.run_in_executor(None, cmd_message, uid, text)

    while True:
        elapsed = int(time.time() - start_ts)
        if elapsed > 300:
            cancel_process(uid)
            try:
                if status_msg:
                    await status_msg.edit_text(
                        "⏱ Превышено время ожидания (300с).\n"
                        "Попробуйте переключить модель через /setmodel"
                    )
            except Exception:
                pass
            result = (None, "⏱ Превышено время ожидания (300с). Попробуйте переключить модель через /setmodel", [], None)
            break
        try:
            result = await asyncio.wait_for(asyncio.shield(thread_task), timeout=3)
            break
        except asyncio.TimeoutError:
            elapsed = int(time.time() - start_ts)
            info = get_process_info(uid)
            key, sess = get_current_session(uid)
            sess = sess or {}
            sess_tok = sess.get("tokens", 0) or 0
            live_tok = info["tokens"] if info else 0
            show_tok = max(sess_tok, live_tok)

            if True:
                if info:
                    line0 = (
                        f"⏳ {info['time']} · ⚡ {info['cpu']:.1f}% · 🧠 {info['mem_mb']}MB"
                        f" · 🔤 +{_fmt_tokens(live_tok)} · 📊 {_fmt_tokens(show_tok)}"
                    )
                else:
                    line0 = f"⏳ {elapsed//60:02d}:{elapsed%60:02d} · 📊 {_fmt_tokens(sess_tok)} · ⏎ Saving..."
                lines = [line0]
                if info:
                    top5 = get_top5()
                    if top5:
                        lines.append("📊 Top 5 proc:")
                        for line in top5:
                            lines.append(line)
                footer = build_footer(uid, live_tok=live_tok)
                if footer:
                    lines.extend(["", "━━━", "", footer])
                text = "\n".join(lines)
                if status_msg is None:
                    status_msg = await update.message.reply_text(text)
                else:
                    try:
                        await status_msg.edit_text(text)
                    except Exception as e:
                        log.warning(f"status edit error: {e}")

    if status_msg:
        try:
            await status_msg.delete()
        except Exception as e:
            log.warning(f"status delete error: {e}")

    try:
        log.info("_handle_message: cmd_message returned")
        
        # Get session tokens after opencode finished
        _key, _sess = get_current_session(uid)
        _final_tok = _sess.get("tokens", 0) if _sess else 0
        
        if len(result) == 4:
            resp, err, new_images, agent_label = result
        else:
            resp, err, new_images = result
            agent_label = None

        if err:
            log.info("_handle_message: replying with error")
            await _reply(update, err, uid, agent=agent_label, live_tok=_final_tok)
            log.info("_handle_message: error reply done")
        elif resp:
            log.info("_handle_message: replying with response")
            if new_images:
                footer = build_footer(uid, agent=agent_label, live_tok=_final_tok)
                full = f"{resp}\n\n━━━\n\n{footer}"
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
                    await _reply(update, resp, uid, agent=agent_label, live_tok=_final_tok)
                    media = []
                    for img_path in new_images:
                        with open(img_path, "rb") as f:
                            media.append(InputMediaPhoto(media=f))
                    await update.message.reply_media_group(media=media)
            else:
                await _reply(update, resp, uid, agent=agent_label, live_tok=_final_tok)
            log.info("_handle_message: response reply done")
    except Exception as e:
        log.error(f"_handle_message: reply failed: {e}")
        try:
            await update.message.reply_text("✅ Готово (ошибка форматирования).")
        except Exception:
            pass


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




