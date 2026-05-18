#!/usr/bin/env python3
"""Export tables from PDF to Excel using camelot-py (no Java needed)."""

import sys
import camelot
import pandas as pd
from pathlib import Path


def pdf_to_excel(pdf_path: str, output_path: str = None, pages: str = "1"):
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"❌ File not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        output_path = pdf.with_suffix(".xlsx")

    print(f"📄 Reading: {pdf.name}")
    print(f"📃 Pages: {pages}")

    tables = camelot.read_pdf(str(pdf), pages=pages, flavor="lattice")

    if len(tables) == 0:
        tables = camelot.read_pdf(str(pdf), pages=pages, flavor="stream")

    if len(tables) == 0:
        print("⚠️  No tables found.")
        sys.exit(1)

    print(f"✅ Found {len(tables)} table(s)")

    with pd.ExcelWriter(output_path) as writer:
        for i, table in enumerate(tables):
            sheet = f"Table_{i+1}" if len(tables) > 1 else "Data"
            table.df.to_excel(writer, sheet_name=sheet, index=False)
            print(f"  → Sheet '{sheet}': {table.df.shape}")

    print(f"\n💾 Saved: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export PDF tables to Excel")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output .xlsx path")
    parser.add_argument("-p", "--pages", default="1", help="Pages (e.g. 1, 1-3, all)")
    args = parser.parse_args()

    pdf_to_excel(args.pdf, args.output, args.pages)
