#!/usr/bin/env python3
"""Сборщик цен RouterAI + обновление всех провайдеров в opencode config."""
import re, json, os, time, sys, subprocess
from pathlib import Path


def fetch_page(url: str) -> str:
    result = subprocess.run(
        ["curl", "-s", url,
         "-H", "User-Agent: Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36",
         "-H", "Accept: text/html,application/xhtml+xml",
         "-H", "Accept-Language: ru,en;q=0.9"],
        capture_output=True, text=True, timeout=20
    )
    return result.stdout


OUT_DIR = Path(__file__).resolve().parent / "ai_providers"
OPENCODE_CONFIG = Path.home() / ".config/opencode/opencode.json"


def parse_prices(html: str) -> list[dict]:
    """Extract model id + input/output price + context from HTML."""
    results = []
    # Each model card starts with a link that contains model data
    cards = html.split('data-turbo="false" class="uk-button custom-btn custom-btn_primary model-card__a')
    
    for card in cards[1:]:  # skip first (before first card)
        # Extract model ID: find first "provider/model" pattern that's NOT in URLs/paths
        ids = re.findall(r'([a-z][a-z0-9_.-]+/[a-z][a-z0-9_.-]+)', card, re.IGNORECASE)
        ids = [i for i in ids if not i.startswith('models/')]
        if not ids:
            continue
        model_id = ids[0]

        # Extract input price
        idx_inp = card.find('Входящие токены за 1M:')
        inp_match = re.search(r"c-text'>([\d.]+) ₽", card[idx_inp:idx_inp+100]) if idx_inp >= 0 else None
        inp = float(inp_match.group(1)) if inp_match else None

        # Extract output price
        idx_out = card.find('Исходящие токены за 1M:')
        out_match = re.search(r"c-text'>([\d.]+) ₽", card[idx_out:idx_out+100]) if idx_out >= 0 else None
        out = float(out_match.group(1)) if out_match else None

        # Extract context
        idx_ctx = card.find('Контекст:')
        ctx_match = re.search(r"c-h2'>([\dKM]+)", card[idx_ctx:idx_ctx+100]) if idx_ctx >= 0 else None
        ctx_str = ctx_match.group(1) if ctx_match else None
        ctx = None
        if ctx_str:
            ctx_str = ctx_str.replace('K', '000').replace('M', '000000')
            if ctx_str.isdigit():
                ctx = int(ctx_str)

        if model_id and inp is not None:
            results.append({
                "id": model_id,
                "input_rub": inp,
                "output_rub": out,
                "context": ctx,
            })

    return results


def scrape_all_pages() -> dict:
    """Scrape pages 1-25 and return {model_id: price_data}."""
    all_models = {}
    total_pages = 25

    for page in range(1, total_pages + 1):
        url = f"https://routerai.ru/models?page={page}"
        print(f"📡 Page {page}/{total_pages}...", end=" ", flush=True)
        try:
            html = fetch_page(url)
            models = parse_prices(html)
            for m in models:
                all_models[m["id"]] = m
            print(f"→ {len(models)} models (total: {len(all_models)})")
        except Exception as e:
            print(f"❌ {e}")
        time.sleep(0.5)

    return all_models


def update_routerai_json(prices: dict):
    """Update routerai.json with scraped prices."""
    path = OUT_DIR / "routerai.json"
    if not path.exists():
        print(f"⚠️ {path} not found")
        return

    data = json.loads(path.read_text())
    updated = 0
    for m in data.get("models", []):
        mid = m.get("id", "")
        if mid in prices:
            p = prices[mid]
            m["pricing"] = {"input_rub": p["input_rub"], "output_rub": p["output_rub"]}
            m["context"] = p.get("context")
            updated += 1

    data["pricing_available"] = True
    path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
    print(f"✅ routerai.json: {updated}/{len(prices)} prices updated")


def update_opencode_config():
    """Add all models from aitunnel, routerai, apiyi to opencode config."""
    if not OPENCODE_CONFIG.exists():
        print(f"⚠️ {OPENCODE_CONFIG} not found")
        return

    config = json.loads(OPENCODE_CONFIG.read_text())

    # Map of provider to ai_providers file
    providers_map = {
        "aitunnel": "aitunnel.json",
        "routerai": "routerai.json",
        "apiyi": "apiyi.json",
    }

    for prov_name, prov_file in providers_map.items():
        prov_path = OUT_DIR / prov_file
        if not prov_path.exists():
            continue
        prov_data = json.loads(prov_path.read_text())
        all_models = prov_data.get("models", [])

        if prov_name not in config.get("provider", {}):
            print(f"⚠️ Provider '{prov_name}' not in opencode config")
            continue

        existing = config["provider"][prov_name].get("models", {})

        # Create new models dict preserving existing, adding new ones
        new_models = {}
        for m in all_models:
            mid = m.get("opencode_id" if "opencode_id" in m else "id", m["id"])
            if mid not in existing:
                name = m.get("name", mid)
                new_models[mid] = {"name": name}

        # Merge
        config["provider"][prov_name]["models"] = {**existing, **new_models}
        print(f"✅ {prov_name}: {len(existing)} existing + {len(new_models)} new = {len(existing) + len(new_models)} total")

    OPENCODE_CONFIG.write_text(json.dumps(config, ensure_ascii=False, indent=2))
    print("✅ opencode config updated")


def update_balance_flags():
    """Update aitunnel.json and apiyi.json balance flags."""
    for fname in ["aitunnel.json", "apiyi.json"]:
        path = OUT_DIR / fname
        if not path.exists():
            continue
        data = json.loads(path.read_text())
        data["balance"] = "prepaid"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1))
        print(f"✅ {fname}: balance → prepaid")


if __name__ == "__main__":
    print("=" * 50)
    print("🔍 Scraping RouterAI prices (25 pages)...")
    print("=" * 50)

    prices = scrape_all_pages()
    print(f"\n📊 Total unique models with prices: {len(prices)}")

    print("\n📝 Updating routerai.json...")
    update_routerai_json(prices)

    print("\n📝 Updating opencode config...")
    update_opencode_config()

    print("\n📝 Updating balance flags...")
    update_balance_flags()

    print("\n✅ All done!")
