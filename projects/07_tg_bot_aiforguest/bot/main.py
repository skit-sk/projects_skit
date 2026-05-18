#!/usr/bin/env python3
import os
import sys
import atexit
import signal
import logging
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_DIR / "bot"))
os.chdir(PROJECT_DIR)
os.environ["TG_PROJECT_DIR"] = str(PROJECT_DIR)

import config
from telegram.ext import Application, MessageHandler, filters
from handler import dispatch
from session import get_all_pending_tasks

logging.basicConfig(
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    level=logging.INFO,
    handlers=[
        logging.FileHandler(PROJECT_DIR / "bot.log"),
        logging.StreamHandler(),
    ],
)
log = logging.getLogger("tg_bot")


def _signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    log.warning("SIGNAL %s (%d) received", sig_name, signum)


def _atexit_log():
    log.warning("Process exit (atexit)")


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
        app.run_polling(drop_pending_updates=True)
    except Exception as e:
        log.error("run_polling crashed: %s", e, exc_info=True)
    log.info("Bot stopped. Reason: check above")


if __name__ == "__main__":
    main()
