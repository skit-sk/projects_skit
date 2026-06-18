#!/usr/bin/env python3
"""Screenshot analytics charts (main chart + indicators) as FHD collage with TG line."""

import os, sys, time, json, urllib.request
from PIL import Image

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


def sync_exchange():
    try:
        req = urllib.request.Request(f"{BASE_URL}/api/sync-all", data=b"", method="POST")
        with urllib.request.urlopen(req, timeout=60):
            pass
    except Exception:
        pass
    # Regenerate TG cache
    try:
        import subprocess
        tg_script = os.path.expanduser("~/workspace/tools/scripts/get_emj_rows.py")
        if os.path.exists(tg_script):
            subprocess.run([sys.executable, tg_script], timeout=60, capture_output=True)
    except Exception:
        pass


def get_objects_list():
    resp = urllib.request.urlopen(f"{BASE_URL}/trade-analytics/api/list", timeout=10)
    return json.loads(resp.read())


def resolve_symbol(symbol_or_number: str, objects: list) -> dict:
    s = symbol_or_number.upper().lstrip("#")
    for obj in objects:
        if not obj.get("has_1d") or not obj.get("has_raw"):
            continue
        name = obj.get("name", "")
        sym = obj.get("symbol", "").upper()
        num = name.split("#")[-1] if "#" in name else ""
        if s == sym or s == num or f"#{s}" == f"#{num}":
            return obj
    return None


def make_collage(input_paths, output_path):
    imgs = [Image.open(p) for p in input_paths]
    max_w = max(im.width for im in imgs)
    total_h = sum(im.height for im in imgs)
    collage = Image.new("RGB", (max_w, total_h), (0, 0, 0))
    y = 0
    for im in imgs:
        x = (max_w - im.width) // 2
        collage.paste(im, (x, y))
        y += im.height
    collage.save(output_path, "PNG", dpi=(144, 144))
    return output_path


def main():
    import argparse
    from playwright.sync_api import sync_playwright

    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", type=str, default=None, help="Comma-separated symbols (ETC,ADA,CAKE)")
    parser.add_argument("--all", action="store_true")
    parser.add_argument("--output-dir", type=str, default=None, help="Single output directory")
    args = parser.parse_args()

    sync_exchange()
    time.sleep(2)

    objects = get_objects_list()
    if args.symbols:
        raw = [s.strip().upper() for s in args.symbols.split(",") if s.strip()]
        targets = []
        for s in raw:
            obj = resolve_symbol(s, objects)
            if obj:
                targets.append(obj)
            else:
                print(f"WARN: symbol '{s}' not found, skipped")
        if not targets:
            print("ERROR: no valid symbols")
            sys.exit(1)
    elif args.all:
        targets = [o for o in objects if o.get("has_1d") and o.get("has_raw")]
        if not targets:
            print("ERROR: no objects with analytics data")
            sys.exit(1)

    if not args.output_dir:
        uids = []
        for name in os.listdir(TG_ALL_DIR):
            if name.startswith("TG_"):
                uids.append(name.replace("TG_", ""))

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True, args=["--no-sandbox", "--disable-setuid-sandbox"])
        page = browser.new_page(viewport={"width": 2560, "height": 1440})

        for obj in targets:
            sym = obj["symbol"]
            url = f"{BASE_URL}/trade-analytics/dashboard/{obj['id']}"
            page.goto(url, wait_until="networkidle")
            time.sleep(3)

            try:
                _emoji_js = open("/tmp/emoji_replace.js").read()
                page.evaluate(_emoji_js)
            except Exception:
                pass

            if args.output_dir:
                out_dirs = [args.output_dir]
            else:
                out_dirs = [os.path.join(TG_ALL_DIR, f"TG_{uid}") for uid in uids]

            tg_el = page.query_selector(".ta-section.block-tg")
            kpi_el = page.query_selector(".ta-section.block-kpi")
            chart_el = page.query_selector(".ta-section.block-chart")
            indic_el = page.query_selector(".ta-section.block-indic")
            if not chart_el or not indic_el:
                print(f"WARN: charts not found for {sym}")
                continue

            for out_dir in out_dirs:
                os.makedirs(out_dir, exist_ok=True)
                tg_path = os.path.join(out_dir, f"{sym}_tg_format.png") if tg_el else None
                kpi_path = os.path.join(out_dir, f"{sym}_kpi.png") if kpi_el else None
                main_path = os.path.join(out_dir, f"{sym}_chart.png")
                indic_path = os.path.join(out_dir, f"{sym}_indicators.png")

                if tg_el: tg_el.screenshot(path=tg_path)
                if kpi_el: kpi_el.screenshot(path=kpi_path)
                chart_el.screenshot(path=main_path)
                indic_el.screenshot(path=indic_path)

                screens = [p for p in [tg_path, kpi_path, main_path, indic_path] if p and os.path.exists(p)]
                if len(screens) >= 2:
                    collage_path = os.path.join(out_dir, f"{sym}_analytics.png")
                    make_collage(screens, collage_path)
                    print(f"✅ Analytics → {collage_path}")
                elif screens:
                    print(f"✅ {sym} → {screens[0]}")

        browser.close()


if __name__ == "__main__":
    main()
