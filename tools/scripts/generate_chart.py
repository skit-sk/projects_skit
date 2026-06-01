#!/usr/bin/env python3
"""CLI entry point for chart generation.

Usage:
  python3 generate_chart.py --type line --data '{"chart":[...],"summary":{}}' -o chart.png
  python3 generate_chart.py --type bar --data '{"categories":["A","B"],"values":[1,2]}' -o bar.png
  python3 generate_chart.py --type heatmap --data '{"matrix":[[1,0],[0,1]]}' -o heatmap.png
  python3 generate_chart.py --list                    # list available types
  python3 generate_chart.py --test                    # generate test images
  python3 generate_chart.py --test-dir /tmp/charts    # custom output dir
"""

import json
import os
import sys
import argparse


def main():
    parser = argparse.ArgumentParser(description="Generate charts from data")
    parser.add_argument("--type", "-t", help="Chart type (e.g. line, bar, heatmap)")
    parser.add_argument("--data", "-d", help="JSON string with chart data")
    parser.add_argument("--data-file", "-f", help="File with JSON chart data")
    parser.add_argument("--output", "-o", default="/tmp/chart.png", help="Output PNG path")
    parser.add_argument("--uid", type=str, help="TG user ID (sets output dir)")
    parser.add_argument("--list", "-l", action="store_true", help="List available chart types")
    parser.add_argument("--test", action="store_true", help="Generate test images for all types")
    parser.add_argument("--test-dir", default="/tmp/chart_tests", help="Test output directory")
    args = parser.parse_args()

    sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "venv", "lib", "python3.12", "site-packages"))
    import chart_lib

    if args.list:
        for ct in chart_lib.list_types():
            print(ct)
        return

    if args.test:
        results = chart_lib.test_all(args.test_dir)
        ok = sum(1 for v in results.values() if v == "OK")
        fail = sum(1 for v in results.values() if v != "OK")
        print(f"Results: {ok} OK, {fail} FAIL")
        for k, v in results.items():
            status = "✅" if v == "OK" else "❌"
            print(f"  {status} {k}: {v}")
        return

    if not args.type:
        parser.print_help()
        return

    if args.data_file:
        with open(args.data_file) as f:
            data = json.load(f)
    elif args.data:
        data = json.loads(args.data)
    else:
        print("ERROR: provide --data or --data-file", file=sys.stderr)
        sys.exit(1)

    output = args.output
    if args.uid:
        tg_dir = os.path.expanduser(f"~/workspace/projects/07_tg_bot_aiforguest/TG_ALL/TG_{args.uid}")
        os.makedirs(tg_dir, exist_ok=True)
        safe_type = args.type.replace(" ", "_")
        output = os.path.join(tg_dir, f"{safe_type}.png")

    try:
        result = chart_lib.generate(args.type, data, output)
        print(json.dumps({"path": result, "type": args.type}))
    except ValueError as e:
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
