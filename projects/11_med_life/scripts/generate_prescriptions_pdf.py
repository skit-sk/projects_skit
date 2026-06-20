#!/usr/bin/env python3
"""
Генерация отчёта «Препараты и цены» для пациента.
Данные динамически: examination entry + price_tracker + drug_reference.
Опция --send для отправки через MAX bot.

Использование:
    python scripts/generate_prescriptions_pdf.py
    python scripts/generate_prescriptions_pdf.py --send
    python scripts/generate_prescriptions_pdf.py --uid usr_8e498be --entry 2026-06-17_001
"""

import argparse
import asyncio
import json
import os
import sys
from datetime import date
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]

DEFAULT_UID = "usr_8e498be"
DEFAULT_ENTRY = "2026-06-17_001"
MAX_PROJECT = PROJECT_ROOT.parent / "10_max_bot"
MAX_USER_ID = 3309222


def load_json(path: Path):
    with open(path) as f:
        return json.load(f)


def gather_data(uid: str, entry_prefix: str) -> list[dict]:
    obj_dir = PROJECT_ROOT / "data" / "objects" / uid / "entries"
    entries = sorted(obj_dir.glob(f"{entry_prefix}_*.json"))
    if not entries:
        print(f"[ERROR] No entry found for {uid}/{entry_prefix}")
        sys.exit(1)

    entry = load_json(entries[0])
    if entry.get("domain") != "examination":
        print(f"[ERROR] Entry {entries[0].name} is not examination")
        sys.exit(1)

    # load drug index
    drug_index = load_json(PROJECT_ROOT / "data" / "drug_reference" / "index.json")
    drug_map = {d["drug_id"]: d for d in drug_index}

    rows = []
    for p in entry.get("data", {}).get("prescriptions", []):
        d = p.get("dose", {})
        r = p.get("regimen", {})
        drug_id = p.get("drug_id")

        inn = ""
        if drug_id and drug_id in drug_map:
            inn = drug_map[drug_id].get("generic", "")

        # load prices from price_tracker
        prices = {}
        if drug_id:
            pt_path = PROJECT_ROOT / "data" / "price_tracker" / f"{drug_id}.json"
            if pt_path.exists():
                pt = load_json(pt_path)
                for src_id, src_data in pt.get("prices", {}).items():
                    src_name = src_data.get("source_name", src_id)
                    pg = src_data.get("price_group", {})
                    median = pg.get("median")
                    prices[src_name] = f"{median:,.0f} ₽".replace(",", " ") if median else "—"

        # collect all source names across all rows
        regimen_parts = []
        if r.get("time"):
            regimen_parts.append(r["time"])
        if r.get("frequency"):
            regimen_parts.append(r["frequency"])
        if r.get("duration"):
            regimen_parts.append(r["duration"])

        rows.append({
            "drug": p["drug"],
            "dose": d.get("text", ""),
            "route": p.get("route", ""),
            "regimen": " × ".join(regimen_parts) if regimen_parts else "",
            "inn": inn,
            "prices": prices,
        })

    return rows


def get_all_sources(rows: list[dict]) -> list[str]:
    seen = []
    for r in rows:
        for s in r["prices"]:
            if s not in seen:
                seen.append(s)
    return seen


def generate_md(rows: list[dict], sources: list[str]) -> str:
    today = date.today()
    lines = [
        "# Препараты и цены",
        "",
        f"**Пациент:** {DEFAULT_UID} | **Дата:** 2026-06-17 | **Сформировано:** {today}",
        "",
        f"| Препарат | Доза | Route | Режим | {' | '.join(sources)} | МНН |",
        f"|{'|'.join('---' for _ in range(5 + len(sources)))}|",
    ]

    for p in rows:
        row = [
            f"**{p['drug']}**",
            p["dose"],
            p["route"],
            p["regimen"],
            *[p["prices"].get(s, "—") for s in sources],
            p["inn"],
        ]
        lines.append(f"| {' | '.join(row)} |")

    lines += [
        "",
        "---",
        f"_Цены указаны на {today}. Данные получены из открытых источников._",
    ]
    return "\n".join(lines)


def generate_pdf(rows: list[dict], sources: list[str], pdf_path: Path):
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    FONT_DIR = "/usr/share/fonts/truetype/dejavu/"

    # column widths in mm (landscape A4 ~277mm usable)
    col_widths = [35, 32, 10, 55]
    for _ in sources:
        col_widths.append(22)
    col_widths.append(50)

    pdf = FPDF(orientation="L", unit="mm", format="A4")
    pdf.add_page()
    pdf.add_font("DejaVu", "", FONT_DIR + "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", FONT_DIR + "DejaVuSans-Bold.ttf")

    today = date.today()

    pdf.set_font("DejaVu", "B", 12)
    pdf.cell(0, 10, "Препараты и цены", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 7)
    pdf.cell(0, 5, f"Пациент: {DEFAULT_UID}  |  2026-06-17  |  Сформировано: {today}", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    h_style = FontFace(family="DejaVu", emphasis="B", size_pt=6, color=(255, 255, 255), fill_color=(60, 60, 60))

    headers = ["Препарат", "Доза", "Route", "Режим", *sources, "МНН"]

    pdf.set_font("DejaVu", "", 6)
    with pdf.table(
        col_widths=col_widths,
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=h_style,
        line_height=3.5,
        repeat_headings=1,
        cell_fill_color=(240, 240, 240),
        cell_fill_mode="ROWS",
    ) as table:
        row = table.row()
        for h in headers:
            row.cell(h)

        for p in rows:
            row = table.row()
            row.cell(p["drug"])
            row.cell(p["dose"])
            row.cell(p["route"])
            row.cell(p["regimen"])
            for s in sources:
                row.cell(p["prices"].get(s, "—"))
            row.cell(p["inn"])

    pdf.ln(3)
    pdf.set_font("DejaVu", "", 6)
    pdf.set_text_color(120, 120, 120)
    pdf.cell(0, 5, f"Цены указаны на {today}. Данные получены из открытых источников.", new_x="LMARGIN", new_y="NEXT")

    pdf.output(str(pdf_path))
    print(f"  PDF: {pdf_path}")


async def send_via_maxbot(file_paths: list[Path]):
    sys.path.insert(0, str(MAX_PROJECT))
    try:
        from max_client import MAXClient
    except ImportError:
        print("  [WARN] max_client.py not found, skip send")
        return

    client = MAXClient()
    try:
        for fp in file_paths:
            print(f"  Sending {fp.name} to user {MAX_USER_ID}...")
            result = await client.send_file(
                user_id=MAX_USER_ID,
                file_path=str(fp),
                caption=f"Отчёт: {fp.stem}",
            )
            print(f"  [{'OK' if result else 'FAIL'}] {fp.name}")
    finally:
        await client.close()


def main():
    parser = argparse.ArgumentParser(description="Generate prescription price report (MD + PDF)")
    parser.add_argument("--uid", default=DEFAULT_UID, help="Patient object_id")
    parser.add_argument("--entry", default=DEFAULT_ENTRY, help="Entry prefix (YYYY-MM-DD_NNN)")
    parser.add_argument("--send", action="store_true", help="Send files via MAX bot")
    args = parser.parse_args()

    rows = gather_data(args.uid, args.entry)
    sources = get_all_sources(rows)

    user_dir = PROJECT_ROOT / "data" / "user" / "users" / args.uid
    os.makedirs(user_dir, exist_ok=True)

    md_path = user_dir / "prescriptions_prices.md"
    pdf_path = user_dir / "prescriptions_prices.pdf"

    md_content = generate_md(rows, sources)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD: {md_path}")

    generate_pdf(rows, sources, pdf_path)

    print(f"\n  Reports: {user_dir}")

    if args.send:
        asyncio.run(send_via_maxbot([md_path, pdf_path]))

    print("  Done.")


if __name__ == "__main__":
    main()
