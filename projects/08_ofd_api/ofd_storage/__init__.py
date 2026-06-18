"""OFD Storage — file-based JSON storage for abonent data."""
import json, os
from pathlib import Path

DATA_ROOT = Path(__file__).resolve().parent.parent / "data" / "ofd"


class OfdStorage:
    def __init__(self, inn: str):
        self.inn = str(inn)
        self.base = DATA_ROOT / self.inn
        self.items_dir = self.base / "items"
        self.base.mkdir(parents=True, exist_ok=True)
        self.items_dir.mkdir(exist_ok=True)

    # ── Abonent ──
    def save_abonent(self, data: dict):
        with open(self.base / "inn_abonent.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_abonent(self) -> dict:
        p = self.base / "inn_abonent.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    # ── KKT Index ──
    def save_kkt_index(self, data: dict):
        with open(self.base / "inn_kkt_index.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_kkt_index(self) -> dict:
        p = self.base / "inn_kkt_index.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    # ── KKT detail ──
    def save_kkt(self, rnm: str, data: dict):
        safe = rnm.replace("/", "_").replace("\\", "_")
        with open(self.base / f"inn_kkt_{safe}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_kkt(self, rnm: str) -> dict:
        safe = rnm.replace("/", "_").replace("\\", "_")
        p = self.base / f"inn_kkt_{safe}.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    # ── FN shifts ──
    def save_fn(self, fn: str, data: dict):
        with open(self.base / f"fn_{fn}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_fn(self, fn: str) -> dict:
        p = self.base / f"fn_{fn}.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    # ── FN daily ──
    def save_fn_daily(self, fn: str, data: dict):
        with open(self.base / f"fn_{fn}_daily.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def load_fn_daily(self, fn: str) -> dict:
        p = self.base / f"fn_{fn}_daily.json"
        if not p.exists():
            return {}
        return json.loads(p.read_text(encoding="utf-8"))

    # ── Items (receipt products) ──
    def save_items(self, data: dict):
        by_kkt_date = {}
        for r in data.get("receipts", []):
            kkt = r.get("kkt_rnm", "unknown")
            date = r.get("date", "")[:10]
            by_kkt_date.setdefault((kkt, date), []).append(r)
        for (kkt, date), receipts in by_kkt_date.items():
            fname = f"{kkt}_items_{date}.json"
            with open(self.items_dir / fname, "w", encoding="utf-8") as f:
                json.dump({"receipts": receipts}, f, ensure_ascii=False, indent=2)

    def load_items(self, date_from: str = "", date_to: str = "") -> dict:
        all_receipts = []
        for fp in sorted(self.items_dir.glob("*_items_*.json")):
            try:
                date_str = fp.stem.split("_items_")[-1]
            except IndexError:
                continue
            if date_from and date_str < date_from:
                continue
            if date_to and date_str > date_to:
                continue
            data = json.loads(fp.read_text(encoding="utf-8"))
            all_receipts.extend(data.get("receipts", []))
        return {"receipts": all_receipts}

    def save_items_aggregated(self, data: dict, label="items_aggregated"):
        with open(self.items_dir / f"{label}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def save_items_raw(self, data: dict, label="items_raw"):
        with open(self.items_dir / f"{label}.json", "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    # ── List all KKT ──
    def list_kkt_files(self):
        return list(self.base.glob("inn_kkt_*.json"))

    def list_fn_files(self):
        return list(self.base.glob("fn_*.json"))

    # ── Local .env token storage ──
    def save_token(self, token: str):
        """Save token to local .env for this INN."""
        with open(self.base / ".env", "w", encoding="utf-8") as f:
            f.write(f"OFD_TOKEN={token}\n")

    def load_token(self) -> str:
        """Read token from local .env for this INN."""
        p = self.base / ".env"
        if not p.exists():
            return ""
        for line in p.read_text(encoding="utf-8").splitlines():
            if line.startswith("OFD_TOKEN="):
                return line.split("=", 1)[1].strip()
        return ""
