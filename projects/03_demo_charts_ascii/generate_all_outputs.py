#!/usr/bin/env python3
"""Pre-generate all ASCII infographics for all available symbols.

Usage:
    python generate_all_outputs.py
    DEMO_OUTPUT_DIR=/path/to/outputs python generate_all_outputs.py
"""
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
FUNDAMENT_DIR = BASE_DIR.parent / "01_fundament_rf" / "data" / "card"

# Default to committed outputs/ for persistence; /tmp for Vercel/runtime
OUTPUT_DIR = Path(os.environ.get("DEMO_OUTPUT_DIR", BASE_DIR / "outputs"))
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
os.environ["DEMO_OUTPUT_DIR"] = str(OUTPUT_DIR)

sys.path.insert(0, str(BASE_DIR))
import charts as ch


def collect_symbols():
    symbols = set()
    for root in (DATA_DIR, FUNDAMENT_DIR):
        if not root.exists():
            continue
        for subdir in root.iterdir():
            if subdir.is_dir() and "_" in subdir.name:
                symbols.add(subdir.name.split("_")[0])
    return sorted(symbols)


def find_obj_id(symbol: str):
    for root in (DATA_DIR, FUNDAMENT_DIR):
        if not root.exists():
            continue
        for subdir in root.iterdir():
            if subdir.is_dir() and subdir.name.startswith(symbol + "_"):
                for f in subdir.glob("*.json"):
                    if not f.name.endswith(("_1D.json", "_RAW.json")):
                        return f.stem
    return None


def main():
    symbols = collect_symbols()
    print(f"Found {len(symbols)} symbols: {', '.join(symbols)}")
    print(f"Output directory: {OUTPUT_DIR}")

    for symbol in symbols:
        obj_id = find_obj_id(symbol)
        if not obj_id:
            print(f"  ⚠️ {symbol}: obj_id not found, skipping")
            continue
        try:
            paths = ch.generate_all(obj_id)
            print(f"  ✅ {symbol}: generated {len(paths)} charts")
        except Exception as e:
            print(f"  ❌ {symbol}: {e}")

    print("\nDone!")


if __name__ == "__main__":
    main()
