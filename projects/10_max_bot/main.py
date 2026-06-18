import os
import sys
import asyncio
import signal
import logging
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
sys.path.insert(0, str(Path(__file__).resolve().parent / "bot"))

from config import MAX_BOT_TOKEN, MAX_WEBHOOK_URL, LOG_FILE
from session import ensure_super
from max_client import MAXClient
from handler import set_client, dispatch

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    filename=str(LOG_FILE),
    filemode="a",
)
log = logging.getLogger("max_bot")
logging.getLogger("httpx").setLevel(logging.WARNING)

client: MAXClient | None = None
_stop_event = asyncio.Event()


def _signal_handler(signum, frame):
    sig_name = signal.Signals(signum).name
    log.warning("SIGNAL %s (%d) received", sig_name, signum)
    _stop_event.set()


async def _polling_loop():
    global client

    marker = None
    update_types = [
        "message_created", "message_callback",
        "bot_started", "bot_added", "bot_stopped",
    ]

    log.info("Starting polling loop...")
    while not _stop_event.is_set():
        try:
            data = await client.get_updates(
                marker=marker, timeout=30, types=update_types
            )
            updates = data.get("updates", [])
            for update in updates:
                ut = update.get("update_type", "?")
                log.info(f"Update: {ut}")
                asyncio.create_task(dispatch(update))

            new_marker = data.get("marker")
            if new_marker is not None:
                marker = new_marker
        except asyncio.CancelledError:
            break
        except Exception as e:
            log.error(f"Polling error: {e}")
            await asyncio.sleep(5)

    log.info("Polling loop stopped")


async def main():
    global client

    log.info("Starting MAX bot...")
    ensure_super()

    client = MAXClient()
    set_client(client)

    try:
        me = await client.get_me()
        log.info(f"Bot authorized: {me.get('first_name')} (ID: {me.get('user_id')})")
    except Exception as e:
        log.error(f"Auth check failed: {e}")
        await client.close()
        return

    if MAX_WEBHOOK_URL:
        update_types = [
            "message_created", "message_callback",
            "bot_started", "bot_added", "bot_stopped",
        ]
        try:
            result = await client.setup_webhook(
                url=MAX_WEBHOOK_URL,
                secret=None,
                update_types=update_types,
            )
            if result.get("success"):
                log.info(f"Webhook set: {MAX_WEBHOOK_URL}")
            else:
                log.warning(f"Webhook setup result: {result}")
        except Exception as e:
            log.error(f"Webhook setup failed: {e}")
    else:
        log.info("No webhook URL — using Long Polling")

    log.info("MAX bot ready")
    await _polling_loop()

    if MAX_WEBHOOK_URL and client:
        try:
            await client.delete_webhook()
            log.info("Webhook deleted")
        except Exception as e:
            log.warning(f"Webhook delete failed: {e}")

    if client:
        await client.close()
    log.info("MAX bot stopped")


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, _signal_handler)
    signal.signal(signal.SIGINT, _signal_handler)
    asyncio.run(main())
