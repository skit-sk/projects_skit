#!/usr/bin/env python3
"""Screenshot the /graphics/all page (all charts) at FHD resolution."""

import os, sys, time, argparse

parser = argparse.ArgumentParser()
parser.add_argument("--output-dir", type=str, default=None, help="Single output directory")
args, _ = parser.parse_known_args()

_font_conf = "/tmp/fonts/fonts.conf"
if os.path.isfile(_font_conf):
    os.environ["FONTCONFIG_FILE"] = _font_conf

TG_PROJECT = os.path.expanduser("~/workspace/projects/07_tg_bot_aiforguest")
TG_ALL_DIR = os.path.join(TG_PROJECT, "TG_ALL")
BASE_URL = "http://localhost:5000"

os.environ["PLAYWRIGHT_BROWSERS_PATH"] = os.path.expanduser("~/workspace/tools/playwright/browsers")
_old_pw = os.path.expanduser("~/workspace/tools/browser-temp/browsers")
if not os.path.isdir(os.path.expanduser("~/workspace/tools/playwright/browsers")) and os.path.isdir(_old_pw):
    os.environ["PLAYWRIGHT_BROWSERS_PATH"] = _old_pw

pango_libs = os.path.expanduser("~/workspace/tools/playwright/lib")
if not os.path.isdir(pango_libs):
    pango_libs = os.path.expanduser("~/workspace/tools/browser-temp/pango_libs/usr/lib/x86_64-linux-gnu")
if os.path.isdir(pango_libs):
    ld_path = os.environ.get("LD_LIBRARY_PATH", "")
    if pango_libs not in ld_path:
        os.environ["LD_LIBRARY_PATH"] = f"{pango_libs}:{ld_path}" if ld_path else pango_libs


def main():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page(viewport={"width": 2560, "height": 1440})

        page.goto(f"{BASE_URL}/graphics/all", wait_until="networkidle")
        time.sleep(5)

        try:
            page.wait_for_selector("canvas", timeout=15000)
            page.evaluate("() => { document.querySelectorAll('canvas').forEach(c => { if (c.getContext) c.getContext('2d'); }); }")
        except Exception:
            pass
        time.sleep(3)

        # Replace emoji with Twemoji SVG
        try:
            _emoji_js = open("/tmp/emoji_replace.js").read()
            page.evaluate(_emoji_js)
        except Exception:
            pass

        page.screenshot(path="/tmp/graphs_full.png", full_page=True)
        from PIL import Image
        header = page.query_selector("h2")
        if header:
            box = header.bounding_box()
            if box:
                img = Image.open("/tmp/graphs_full.png")
                cropped = img.crop((0, box["y"], img.width, img.height))
                cropped.save("/tmp/graphs_clip.png", dpi=(144, 144))
            else:
                page.screenshot(path="/tmp/graphs_clip.png")
        else:
            page.screenshot(path="/tmp/graphs_clip.png")

        if args.output_dir:
            dirs = [args.output_dir]
        else:
            dirs = [os.path.join(TG_ALL_DIR, f"TG_{name.replace('TG_', '')}")
                    for name in os.listdir(TG_ALL_DIR) if name.startswith("TG_")]
            if not dirs:
                print("No TG users found in", TG_ALL_DIR)

        import shutil
        for d in dirs:
            os.makedirs(d, exist_ok=True)
            out = os.path.join(d, "graphs_all.png")
            shutil.copy("/tmp/graphs_clip.png", out)
            print(f"✅ Graphs → {out}")

        browser.close()


if __name__ == "__main__":
    main()
