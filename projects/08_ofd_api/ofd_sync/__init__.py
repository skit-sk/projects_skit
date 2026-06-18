"""OFD Sync Engine — собирает данные от провайдера в JSON-сторадж."""
import time
from datetime import datetime, timedelta

from ofd_storage import OfdStorage


def sync_abonent(inn: str, provider: dict, token: str,
                 period_from: str, period_to: str,
                 storage: OfdStorage):
    """Основной sync: INN → TP → KKT → FN → shifts → daily."""
    from bot_ofd.yandex_ofd import YandexOfdClient
    client = YandexOfdClient(token=token)

    # 2. TradePoints — returns {"trade_points": {"id": {...}, ...}}
    tp_raw = client.trade_points()
    tp_dict = {}
    if isinstance(tp_raw, dict):
        tp_dict = tp_raw.get("trade_points", tp_raw.get("items", {}))
    elif isinstance(tp_raw, list):
        tp_dict = {str(i): t for i, t in enumerate(tp_raw)} if tp_raw else {}
    if not isinstance(tp_dict, dict):
        tp_dict = {}

    kkt_index_data = {"inn": inn, "kkt_list": []}
    all_kkt = []

    # 3. For each TP → KKT
    for tp_id, tp_info in tp_dict.items():
        if not isinstance(tp_info, dict):
            continue
        tp_id_str = tp_id
        kkt_raw = client.call("v1/KKTbyTradePoint", {"TP": int(tp_id) if str(tp_id).isdigit() else tp_id})

        # Parse KKT list — returns {"kkt": {"fn": {...}, ...}}
        kkt_dict = {}
        if isinstance(kkt_raw, dict):
            kkt_dict = kkt_raw.get("kkt", kkt_raw.get("items", {}))

        if isinstance(kkt_dict, dict):
            for fn_key, kkt_info in kkt_dict.items():
                if not isinstance(kkt_info, dict):
                    continue
                rnm = kkt_info.get("register_number_kkt") or kkt_info.get("kktregid") or kkt_info.get("rnm", "")
                fn = kkt_info.get("factory_number_fn") or kkt_info.get("fn") or fn_key
                kkt_name = kkt_info.get("name") or rnm or "ККТ"

                if not rnm:
                    continue
                all_kkt.append({
                    "rnm": rnm,
                    "kkt_name": kkt_name,
                    "fn": fn,
                    "tp": {"id": tp_id_str, "name": tp_info.get("name", "")},
                    "provider": provider.get("id", "yandex_ofd"),
                })

    # 4. Save abonent + kkt_index
    existing = storage.load_abonent()
    abonent = existing if existing else {
        "inn": inn, "provider": provider, "kkt_summary": [],
    }
    abonent["last_sync"] = datetime.now().isoformat()

    for k in all_kkt:
        # Get FN details
        fn_totals = {"shifts": 0, "receipts": {"total": 0, "cash": 0, "card": 0, "return": 0},
                     "sums": {"total": 0, "cash": 0, "card": 0, "return": 0}, "errors": 0}

        # Sync shifts for this FN — call with date range
        if k["fn"] and len(k["fn"]) >= 10:
            try:
                shifts_raw = client.call("v1/KKTShift", {
                    "fiscalDriveNumber": k["fn"],
                    "startDate": period_from,
                    "endDate": period_to,
                })
                shift_list = shifts_raw.get("shifts", []) if isinstance(shifts_raw, dict) else []
                sync_fn_shifts(k["fn"], k["rnm"], shift_list, client, storage, provider)
                fn_data = storage.load_fn(k["fn"])
                fn_totals = _aggregate_shifts(fn_data.get("shifts", []))

                # Sync items for each FN+date
                try:
                    dates_set = set()
                    for s in shift_list:
                        od = (s.get("openDateTime") or s.get("open_date", ""))[:10]
                        if od and od >= period_from and od <= period_to:
                            dates_set.add(od)
                    for d in dates_set:
                        sync_fn_items(k["fn"], k["rnm"], d, client, storage)
                except Exception:
                    pass
            except Exception:
                pass

        kkt_entry = {
            "rnm": k["rnm"],
            "kkt_name": k["kkt_name"],
            "tp": k["tp"],
            "provider": provider.get("id"),
            "fn_current": k["fn"],
            "totals": fn_totals,
        }
        abonent["kkt_summary"].append(kkt_entry)

        # KKT detail
        kkt_detail = {
            "rnm": k["rnm"],
            "kkt_name": k["kkt_name"],
            "provider": provider.get("id"),
            "totals": fn_totals,
        }
        storage.save_kkt(k["rnm"], kkt_detail)

        # KKT index
        kkt_index_data["kkt_list"].append({
            "rnm": k["rnm"],
            "kkt_name": k["kkt_name"],
            "tp": k["tp"],
            "provider": provider.get("id"),
            "fn_history": [{"fn": k["fn"], "provider": provider.get("id"), "from": period_from, "to": period_to,
                           "status": "active", "totals": fn_totals}],
            "totals": fn_totals,
        })

    storage.save_abonent(abonent)
    storage.save_kkt_index(kkt_index_data)
    return {"ok": True, "kkt_count": len(all_kkt)}


def sync_fn_shifts(fn: str, rnm: str, shifts: list, client, storage: OfdStorage, provider: dict):
    """Sync shifts for one FN — merges with existing data by shift_number."""
    existing = storage.load_fn(fn)
    fn_data = existing if existing else {
        "fn": fn, "rnm": rnm, "provider": provider.get("id"), "shifts": [],
    }
    # Index existing shifts by shift_number for dedup
    seen = {s["shift_number"] for s in fn_data.get("shifts", []) if s.get("shift_number")}
    daily_agg = {}

    for s in shifts:
        shift_num = s.get("shiftNumber") or s.get("shift_number") or 0
        open_date_str = s.get("openDateTime", s.get("open_date", ""))
        close_date_str = s.get("closeDateTime", s.get("close_date", ""))
        date_key = open_date_str[:10] if len(open_date_str) >= 10 else ""

        receipt_count = int(s.get("receiptCount", 0))
        total_sum_penny = float(s.get("totalSum", 0) or 0)
        cash_sum_penny = float(s.get("cashTotalSum", 0) or 0)
        card_sum_penny = float(s.get("ecashTotalSum", 0) or 0)
        return_sum_penny = total_sum_penny - cash_sum_penny - card_sum_penny

        # Proportional receipt count by payment type
        if total_sum_penny > 0:
            cash_receipts = round(receipt_count * cash_sum_penny / total_sum_penny)
            card_receipts = round(receipt_count * card_sum_penny / total_sum_penny)
            return_receipts = receipt_count - cash_receipts - card_receipts
        else:
            cash_receipts = card_receipts = return_receipts = 0

        shift_entry = {
            "shift_number": shift_num,
            "open_date": open_date_str,
            "close_date": close_date_str,
            "receipt_count": receipt_count,
            "cash_receipts": cash_receipts,
            "card_receipts": card_receipts,
            "return_receipts": return_receipts,
            "total_sum": round(total_sum_penny / 100, 2),
            "cash_sum": round(cash_sum_penny / 100, 2),
            "card_sum": round(card_sum_penny / 100, 2),
            "return_sum": round(return_sum_penny / 100, 2),
        }

        if shift_num not in seen:
            fn_data["shifts"].append(shift_entry)
            seen.add(shift_num)

        # Aggregate by date for daily file
        if date_key:
            if date_key not in daily_agg:
                daily_agg[date_key] = {"cash": 0, "card": 0, "return": 0, "cash_sum": 0, "card_sum": 0, "return_sum": 0}
            daily_agg[date_key]["cash"] += cash_receipts
            daily_agg[date_key]["card"] += card_receipts
            daily_agg[date_key]["return"] += return_receipts
            daily_agg[date_key]["cash_sum"] += round(cash_sum_penny / 100, 2)
            daily_agg[date_key]["card_sum"] += round(card_sum_penny / 100, 2)
            daily_agg[date_key]["return_sum"] += round(return_sum_penny / 100, 2)

    storage.save_fn(fn, fn_data)
    # Save daily aggregates
    fn_daily = {"fn": fn, "rnm": rnm, "daily": []}
    for d in sorted(daily_agg.keys()):
        fn_daily["daily"].append({"date": d, **daily_agg[d]})
    storage.save_fn_daily(fn, fn_daily)


def _aggregate_shifts(shifts: list) -> dict:
    """Aggregate shifts into totals with proportional receipt counts."""
    totals = {"shifts": len(shifts),
              "receipts": {"total": 0, "cash": 0, "card": 0, "return": 0},
              "sums": {"total": 0, "cash": 0, "card": 0, "return": 0}, "errors": 0}
    for s in shifts:
        if not isinstance(s, dict):
            continue
        rc = int(s.get("receiptCount", 0))
        ts = float(s.get("totalSum", 0) or 0)
        cash_s = float(s.get("cashTotalSum", 0) or 0)
        card_s = float(s.get("ecashTotalSum", 0) or 0)
        ret_s = ts - cash_s - card_s

        totals["receipts"]["total"] += rc
        # Proportional distribution
        if ts > 0:
            totals["receipts"]["cash"] += round(rc * cash_s / ts)
            totals["receipts"]["card"] += round(rc * card_s / ts)
            totals["receipts"]["return"] += round(rc * ret_s / ts)
        totals["sums"]["total"] += round(ts / 100, 2)
        totals["sums"]["cash"] += round(cash_s / 100, 2)
        totals["sums"]["card"] += round(card_s / 100, 2)
        totals["sums"]["return"] += round(ret_s / 100, 2)
    return totals


def sync_fn_items(fn: str, rnm: str, date_str: str, client, storage):
    """Fetch receipt items for one FN+date and save to items JSON."""
    result = client.call("v1/documents", {"fiscalDriveNumber": fn, "date": date_str})
    items_list = result.get("items", []) if isinstance(result, dict) else []
    if not items_list:
        return

    existing = storage.load_items()
    receipts = existing.get("receipts", [])

    for doc in items_list:
        if not isinstance(doc, dict):
            continue
        products = doc.get("items", [])
        if not products or not isinstance(products, list):
            continue
        # Filter out non-product lines
        real_products = [p for p in products if isinstance(p, dict) and p.get("price", 0) > 0]
        if not real_products:
            continue
        receipts.append({
            "date": date_str,
            "kkt_rnm": rnm,
            "fn": fn,
            "shift_number": doc.get("shiftNumber", 0),
            "fiscal_doc_number": doc.get("fiscalDocumentNumber", 0),
            "fiscal_sign": doc.get("fiscalSign", 0),
            "total_sum": round(float(doc.get("totalSum", 0) or 0) / 100, 2),
            "cash_sum": round(float(doc.get("cashTotalSum", 0) or 0) / 100, 2),
            "card_sum": round(float(doc.get("ecashTotalSum", 0) or 0) / 100, 2),
            "products": [{
                "name": p.get("name", ""),
                "quantity": float(p.get("quantity", 1)),
                "price": round(float(p.get("price", 0) or 0) / 100, 2),
                "sum": round(float(p.get("sum", 0) or 0) / 100, 2),
            } for p in real_products],
        })

    existing["receipts"] = receipts
    existing["count"] = len(receipts)
    storage.save_items(existing)
