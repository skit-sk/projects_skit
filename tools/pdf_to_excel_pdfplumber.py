#!/usr/bin/env python3
"""Export tables from PDF to Excel using pdfplumber."""

import sys
import pdfplumber
import pandas as pd
from pathlib import Path


def pdf_to_excel(pdf_path: str, output_path: str = None, pages: str = "1"):
    pdf = Path(pdf_path)
    if not pdf.exists():
        print(f"File not found: {pdf_path}")
        sys.exit(1)

    if output_path is None:
        output_path = pdf.with_suffix(".xlsx")

    page_ranges = []
    for part in pages.split(","):
        if "-" in part:
            a, b = part.split("-")
            page_ranges.extend(range(int(a), int(b) + 1))
        else:
            page_ranges.append(int(part.strip()))

    print(f"Reading: {pdf.name}")
    print(f"Pages: {pages}")

    all_tables = []
    with pdfplumber.open(pdf) as pdf_doc:
        for pnum in page_ranges:
            if pnum > len(pdf_doc.pages):
                continue
            page = pdf_doc.pages[pnum - 1]
            tables = page.extract_tables()
            for t in tables:
                all_tables.append((pnum, t))

    if not all_tables:
        print("No tables found.")
        sys.exit(1)

    print(f"Found {len(all_tables)} table(s)")

    with pd.ExcelWriter(output_path) as writer:
        for i, (pnum, table) in enumerate(all_tables):
            df = pd.DataFrame(table[1:], columns=table[0] if table[0] else None)
            sheet = f"P{pnum}_T{i+1}" if len(all_tables) > 1 else "Data"
            df.to_excel(writer, sheet_name=sheet, index=False)
            print(f"  Sheet '{sheet}' (p.{pnum}): {df.shape}")

    print(f"\nSaved: {output_path}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Export PDF tables to Excel via pdfplumber")
    parser.add_argument("pdf", help="Path to PDF file")
    parser.add_argument("-o", "--output", help="Output .xlsx path")
    parser.add_argument("-p", "--pages", default="1", help="Pages (e.g. 1, 1-3, all)")
    args = parser.parse_args()

    pdf_to_excel(args.pdf, args.output, args.pages)
