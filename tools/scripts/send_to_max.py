#!/usr/bin/env python3
"""Generic file/image sender to MAX bot.

Usage:
    python3 send_to_max.py <file_path> [user_id] [caption]

Examples:
    python3 send_to_max.py /tmp/photo.png
    python3 send_to_max.py /tmp/photo.png 3309222 "Caption text"
    python3 send_to_max.py /tmp/doc.pdf "" "My report"
"""
import asyncio
import os
import sys
from pathlib import Path

MAX_BOT_DIR = (
    Path(__file__).resolve().parent.parent.parent
    / "projects" / "10_max_bot"
)
sys.path.insert(0, str(MAX_BOT_DIR))

from max_client import MAXClient  # noqa: E402
from config import MAX_BOT_TOKEN, SUPER_USER  # noqa: E402

IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}


def main():
    if len(sys.argv) < 2:
        print("Usage: send_to_max.py <file_path> [user_id] [caption]")
        sys.exit(1)
    file_path = Path(sys.argv[1])
    if not file_path.exists():
        print(f"NO_FILE: {file_path}")
        sys.exit(2)
    user_id = (
        int(sys.argv[2]) if len(sys.argv) > 2 and sys.argv[2] else SUPER_USER
    )
    size_kb = file_path.stat().st_size // 1024
    if len(sys.argv) > 3 and sys.argv[3]:
        caption = sys.argv[3]
    else:
        caption = f"📎 {file_path.name} — {size_kb} KB"
    try:
        asyncio.run(_send(user_id, file_path, caption))
    except Exception as e:
        print(f"ERROR: {type(e).__name__}: {e}")
        sys.exit(3)


async def _send(user_id, path, caption):
    client = MAXClient(token=MAX_BOT_TOKEN)
    try:
        if path.suffix.lower() in IMAGE_EXTS:
            result = await client.send_image(
                user_id=user_id, image_path=path, caption=caption
            )
        else:
            result = await client.send_file(
                user_id=user_id, file_path=path, caption=caption
            )
        if result is None:
            print("SEND_FAILED")
            return
        msg = result.get("message", {})
        body = msg.get("body", {})
        att = body.get("attachments", [{}])[0].get("payload", {})
        print(f"OK: mid={body.get('mid')} photo_id={att.get('photo_id')} url={att.get('url')}")
    finally:
        await client.close()


if __name__ == "__main__":
    main()
