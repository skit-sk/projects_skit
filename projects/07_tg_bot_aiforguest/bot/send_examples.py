#!/usr/bin/env python3
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from config import TOKEN
from telegram import Bot

IMAGES_DIR = Path("/tmp/opencode/tool_images")

TOOL_LABELS = {
    "grap_": "Grapheteria",
    "sim_": "Sim",
    "skillpad": "Skillpad",
    "codelegate": "Codelegate",
    "agno_": "Agno",
    "clawx_": "ClawX",
}

async def main():
    bot = Bot(token=TOKEN)
    chat_id = 248207602

    for img_path in sorted(IMAGES_DIR.iterdir()):
        if img_path.suffix not in (".png", ".gif"):
            continue
        label = "Example"
        for prefix, name in TOOL_LABELS.items():
            if img_path.name.startswith(prefix):
                label = name
                break
        with open(img_path, "rb") as f:
            await bot.send_photo(chat_id=chat_id, photo=f, caption=f"📸 {label}")
        print(f"Sent {img_path.name}")

if __name__ == "__main__":
    asyncio.run(main())
