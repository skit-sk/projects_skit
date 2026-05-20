#! /usr/bin/env python3
import os
import sys
import atexit
import signal
import asyncio
import logging
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "bot"))
os.chdir(PROJECT_DIR)
os.environ["TG_PROJECT_DIR"] = str(PROJECT_DIR)

import config
from telegram import InputMediaPhoto
from telegram.ext import Application, MessageHandler, filters
from handler import dispatch
from session import get_all_pending_tasks
from send_queue import queue_pop

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(PROJECT_DIR / "bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("tg_bot")

_stop_event: asyncio.Event = None


def _signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    log.warning("SIGNAL %s (%d) received", sig_name, signum)
    global _stop_event
    if _stop_event and not _stop_event.is_set():
        _stop_event.set()


def _atexit_log():
    log.warning("Process exit (atexit)")


async def _queue_worker(app):
    global _stop_event
    while not (_stop_event and _stop_event.is_set()):
        try:
            item = queue_pop(config.SUPER_USER)
            if item:
                files = item.get("files", [])
                caption = item.get("caption", "")

                if files:
                    media = []
                    doc_files = []
                    for path in files:
                        p = Path(path)
                        if not p.exists():
                            continue
                        ext = p.suffix.lower()
                        if ext in (".jpg", ".jpeg", ".png", ".gif"):
                            with open(p, "rb") as f:
                                media.append(InputMediaPhoto(media=f))
                        else:
                            doc_files.append(str(p))

                    if media:
                        if caption:
                            media[0] = InputMediaPhoto(media=media[0].media, caption=caption)
                        await app.bot.send_media_group(chat_id=config.SUPER_USER, media=media)
                        log.info("Queue worker: sent %d media files", len(media))

                    for doc in doc_files:
                        with open(doc, "rb") as f:
                            await app.bot.send_document(
                                chat_id=config.SUPER_USER,
                                document=f,
                                caption=caption if not media else "",
                            )
                            log.info("Queue worker: sent document %s", doc)
                elif caption:
                    await app.bot.send_message(chat_id=config.SUPER_USER, text=caption)
                    log.info("Queue worker: sent text message")
            await asyncio.sleep(5)
        except Exception as e:
            log.error("Queue worker error: %s", e)
            await asyncio.sleep(5)


async def _run_polling(app):
    global _stop_event
    _stop_event = asyncio.Event()
    await app.initialize()
    await app.start()
    await app.updater.start_polling(drop_pending_updates=True)
    asyncio.create_task(_queue_worker(app))
    await _stop_event.wait()
    await app.updater.stop()
    await app.stop()
    await app.shutdown()


def main():
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    atexit.register(_atexit_log)

    log.info("Starting TG bot ...")
    log.info(f"Super user: {config.SUPER_USER}")
    log.info(f"Project dir: {config.PROJECT_DIR}")
    log.info(f"TG_ALL: {config.TG_ALL_DIR}")

    for uid, task in get_all_pending_tasks():
        log.warning("Pending task for %d: %s (session: %s)",
                     uid, task.get("text", "?")[:80], task.get("session", "?"))

    app = Application.builder().token(config.TOKEN).build()

    app.add_handler(MessageHandler(filters.VOICE, dispatch))
    app.add_handler(MessageHandler(filters.Text(), dispatch))
    app.add_handler(MessageHandler(filters.Document(), dispatch))

    async def _on_error(update, context):
        log.error("Handler error: update=%s error=%s",
                   update.update_id if update else "?",
                   context.error)
    app.add_error_handler(_on_error)

    log.info("Bot is polling...")
    try:
        asyncio.run(_run_polling(app))
    except Exception as e:
        log.error("run_polling crashed: %s", e, exc_info=True)
    log.info("Bot stopped.")


if __name__ == "__main__":
    main()
