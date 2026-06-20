#!/usr/bin/env python3
"""Build ranvik.json from https://api.ranvik.ru/server/pricing"""
import json, sys
from pathlib import Path

API_URL = "https://api.ranvik.ru/server/pricing"
OUT_DIR = Path(__file__).resolve().parent / "ai_providers"
OUT_FILE = OUT_DIR / "ranvik.json"

MODALITY_MAP = {
    "text": "llm",
    "image": "image_gen",
    "video": "video_gen",
    "audio": "audio",
    "embedding": "embedding",
    "object3d": "object3d",
}


def extract_price(prices, unit):
    """Return first price_rub for given unit, or None."""
    for p in prices:
        if p["unit"] == unit:
            return p["price_rub"]
    return None


def build_model(m):
    prices = m.get("prices", [])
    modality = m.get("modality", "text")
    mtype = MODALITY_MAP.get(modality, "llm")

    pricing = {}
    if mtype == "llm":
        inp = extract_price(prices, "input_token")
        out = extract_price(prices, "output_token")
        if inp is not None:
            pricing["input_rub"] = inp
        if out is not None:
            pricing["output_rub"] = out
    elif mtype == "image_gen":
        per_img = extract_price(prices, "image")
        if per_img is not None:
            pricing["per_image"] = per_img
    elif mtype == "video_gen":
        per_sec = extract_price(prices, "second")
        if per_sec is not None:
            pricing["per_second"] = per_sec
    elif mtype == "audio":
        per_sec = extract_price(prices, "second")
        per_min = extract_price(prices, "minute")
        if per_sec is not None:
            pricing["per_second"] = per_sec
        elif per_min is not None:
            pricing["per_minute"] = per_min
        else:
            per_char = extract_price(prices, "character")
            if per_char is not None:
                pricing["per_character"] = per_char
            else:
                per_req = extract_price(prices, "request")
                if per_req is not None:
                    pricing["per_request"] = per_req
    elif mtype == "embedding":
        inp = extract_price(prices, "input_token")
        if inp is not None:
            pricing["input_rub"] = inp
    elif mtype == "object3d":
        per_req = extract_price(prices, "request")
        if per_req is not None:
            pricing["per_request"] = per_req

    return {
        "id": m["id"],
        "name": m.get("display_name", m["id"]),
        "vendor": m.get("vendor", ""),
        "modality": modality,
        "type": mtype,
        "pricing": pricing if pricing else None,
        "context": m.get("context_window"),
        "max_output": m.get("max_output"),
        "is_deprecated": m.get("is_deprecated", False),
        "capabilities": m.get("capabilities", []),
    }


def fetch():
    import subprocess
    result = subprocess.run(
        ["curl", "-s", API_URL,
         "-H", "User-Agent: build_ranvik/1.0"],
        capture_output=True, text=True, timeout=30,
    )
    if result.returncode != 0:
        print(f"❌ curl failed: {result.stderr}")
        sys.exit(1)
    return json.loads(result.stdout)


def build(data):
    models = [build_model(m) for m in data["data"]]
    deprecated = [m for m in models if m["is_deprecated"]]
    active = [m for m in models if not m["is_deprecated"]]

    # Count vendors
    vendors = sorted(set(m.get("vendor", "") for m in active))
    by_type = {}
    for m in active:
        t = m["type"]
        by_type[t] = by_type.get(t, 0) + 1

    out = {
        "provider": "ranvik",
        "label": "Ranvik API",
        "homepage": "https://api.ranvik.ru",
        "api_endpoint": API_URL,
        "balance": "unknown",
        "updated": __import__("datetime").datetime.now().isoformat()[:10],
        "opencode_prefix": "ranvik/",
        "models_count": len(active),
        "total_models": len(models),
        "deprecated_count": len(deprecated),
        "vendors": len(vendors),
        "vendor_list": vendors,
        "by_type": by_type,
        "usd_to_rub": data.get("usd_to_rub"),
        "pricing_unit": "RUB per unit",
        "models": active,
    }
    return out


def save(out):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=1)
    print(f"✅ ranvik.json: {out['models_count']} active models, {out['vendors']} vendors")


if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--local":
        with open(sys.argv[2]) as f:
            data = json.load(f)
    else:
        print(f"📡 Fetching {API_URL}...")
        data = fetch()

    out = build(data)
    save(out)
    print(f"   by type: {out['by_type']}")
