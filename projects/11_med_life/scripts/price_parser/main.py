#!/usr/bin/env python3
"""
Price Parser — поиск цен на препараты в аптечных маркетплейсах.

Использование:
    python main.py search "Триттико"
    python main.py search "Триттико" --save
    python main.py batch
"""

import argparse
import json
import os
import sys
from datetime import date
from typing import Optional

from rich.console import Console
from rich.table import Table

from config import SOURCES
from models import PriceResult, PriceGroup, SourceEntry
from parsers import get_enabled_parsers

console = Console()
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
PRICE_TRACKER_DIR = os.path.join(PROJECT_ROOT, "data", "price_tracker")
DRUG_REF_DIR = os.path.join(PROJECT_ROOT, "data", "drug_reference")


def load_drug_index() -> list[dict]:
    path = os.path.join(DRUG_REF_DIR, "index.json")
    if not os.path.exists(path):
        return []
    with open(path) as f:
        return json.load(f)


def save_price_file(drug_id: str, drug_name: str, results: dict[str, SourceEntry]):
    path = os.path.join(PRICE_TRACKER_DIR, f"{drug_id}.json")
    existing = {"drug_id": drug_id, "drug_name": drug_name, "last_updated": str(date.today()), "prices": {}, "history": []}

    if os.path.exists(path):
        with open(path) as f:
            existing = json.load(f)

    prices = {}
    for src_id, entry in results.items():
        prices[src_id] = {
            "source_name": entry.source_name,
            "dose_form": entry.dose_form,
            "price_group": {
                "min": entry.price_group.min,
                "median": entry.price_group.median,
                "max": entry.price_group.max,
            },
            "url": entry.url,
            "availability": entry.availability,
            "last_checked": str(date.today()),
        }

    existing["prices"].update(prices)
    existing["last_updated"] = str(date.today())
    existing.setdefault("history", []).append({
        "date": str(date.today()),
        "entries": list(prices.keys()),
    })

    with open(path, "w", encoding="utf-8") as f:
        json.dump(existing, f, ensure_ascii=False, indent=2)
    console.print(f"[green]Saved:[/green] {path}")


def group_results(results: list[PriceResult]) -> dict[str, SourceEntry]:
    grouped: dict[str, list[PriceResult]] = {}
    for r in results:
        grouped.setdefault(r.source_id, []).append(r)

    entries = {}
    for src_id, items in grouped.items():
        pg = PriceGroup.from_results(items)
        first = items[0]
        entries[src_id] = SourceEntry(
            source_name=first.source_name,
            dose_form=first.dose_form,
            price_group=pg,
            url=first.url,
            availability=first.availability,
            last_checked=str(date.today()),
        )
    return entries


def format_results_table(results: list[PriceResult]):
    table = Table(title="Price Results")
    table.add_column("Source", style="cyan")
    table.add_column("Drug")
    table.add_column("Dose Form")
    table.add_column("Price", justify="right", style="green")
    table.add_column("URL")

    for r in results:
        table.add_row(r.source_name, r.drug_name, r.dose_form, f"{r.amount:.2f} ₽", r.url)

    console.print(table)

    grouped = group_results(results)
    if len(grouped) > 1:
        table2 = Table(title="Price Groups by Source")
        table2.add_column("Source", style="cyan")
        table2.add_column("Min", justify="right")
        table2.add_column("Median", justify="right")
        table2.add_column("Max", justify="right")
        for src_id, entry in grouped.items():
            pg = entry.price_group
            table2.add_row(entry.source_name, f"{pg.min:.2f}", f"{pg.median:.2f}", f"{pg.max:.2f}")
        console.print(table2)


def cmd_search(drug_name: str, dose_form: str = "", save: bool = False):
    console.print(f"[bold]Searching prices for:[/bold] {drug_name} {dose_form}".strip())

    all_results: list[PriceResult] = []
    parsers = get_enabled_parsers()

    if not parsers:
        console.print("[red]No parsers available[/red]")
        return

    for parser in parsers:
        results = parser.search(drug_name, dose_form)
        all_results.extend(results)
        if results:
            amounts = [r.amount for r in results]
            avg = sum(amounts) / len(amounts)
            console.print(f"  → {parser.source_name}: {len(results)} results, avg {avg:.2f} ₽")
        else:
            console.print(f"  → {parser.source_name}: [yellow]no results[/yellow]")

    if not all_results:
        console.print("[red]No prices found[/red]")
        return

    format_results_table(all_results)

    if save:
        grouped = group_results(all_results)
        drug_id = _resolve_drug_id(drug_name)
        if drug_id:
            save_price_file(drug_id, drug_name, grouped)
        else:
            console.print("[yellow]drug_id not found in index, saved by name[/yellow]")
            save_price_file(f"_{drug_name.lower().replace(' ', '_')}", drug_name, grouped)


def _resolve_drug_id(drug_name: str) -> Optional[str]:
    index = load_drug_index()
    for item in index:
        if item["name"].lower() == drug_name.lower():
            return item["drug_id"]
    return None


def cmd_batch():
    index = load_drug_index()
    if not index:
        console.print("[red]Drug index not found. Run from project root.[/red]")
        return

    console.print(f"[bold]Batch search for {len(index)} drugs[/bold]")
    for item in index:
        if item.get("needs_clarification"):
            console.print(f"[yellow]Skipping {item['name']} (needs clarification)[/yellow]")
            continue
        drug_name = item["name"]
        console.print(f"\n[bold]=== {drug_name} ===[/bold]")
        cmd_search(drug_name, "", save=True)


def main():
    parser = argparse.ArgumentParser(description="Price Parser — поиск цен на препараты")
    sub = parser.add_subparsers(dest="command")

    search_p = sub.add_parser("search", help="Поиск цен по названию препарата")
    search_p.add_argument("drug", help="Название препарата")
    search_p.add_argument("--form", "-f", default="", help="Форма выпуска (необязательно)")
    search_p.add_argument("--save", "-s", action="store_true", help="Сохранить результаты в price_tracker")

    batch_p = sub.add_parser("batch", help="Поиск по всем препаратам из drug_reference/index.json")

    args = parser.parse_args()

    if args.command == "search":
        cmd_search(args.drug, args.form, args.save)
    elif args.command == "batch":
        cmd_batch()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
