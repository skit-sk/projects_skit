import json, os, urllib.request


class YandexOfdClient:
    def __init__(self, token=None):
        self.token = token or os.environ.get("OFD_API_TOKEN", "")
        self.base = "https://api.ofd-ya.ru/ofdapi"

    def call(self, method, params=None):
        url = f"{self.base}/{method.lstrip('/')}"
        body = json.dumps(params or {}).encode()
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={
                    "Ofdapitoken": self.token,
                    "Content-Type": "application/json",
                },
                method="POST",
            )
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.request.HTTPError as e:
            return {"error": f"HTTP {e.code}: {e.reason}", "url": url}
        except (urllib.request.URLError, TimeoutError, OSError) as e:
            return {"error": str(e), "url": url}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse error: {e}", "url": url}

    def inn(self, inn):
        return self.call("v1/inn", {"inn": inn})

    def kkt_list(self):
        return self.call("v1/KKT")

    def check_fn(self, fn):
        return self.call("v1/Check_FN", {"fiscalDriveNumber": fn})

    def trade_points(self):
        return self.call("v1/TradePoint")

    def tp(self):
        return self.call("v1/TP")

    def kkt_by_trade_point(self, tp_id):
        return self.call("v1/KKTbyTradePoint", {"tradePointId": tp_id})

    def documents(self, fn, date, time_start=None, time_end=None):
        params = {"fiscalDriveNumber": fn, "date": date}
        if time_start:
            params["timeStart"] = time_start
        if time_end:
            params["timeEnd"] = time_end
        return self.call("v1/documents", params)

    def get_daily_receipts(self, fn, date, with_items=False):
        resp = self.documents(fn, date)
        if with_items:
            return resp
        total = sum(d.get("totalSum", 0) or 0 for d in resp.get("items", []))
        return {
            "count": resp.get("count", 0),
            "total_sum": total / 100,
            "date": date,
        }

    def get_doc_count(self, fn, date=None):
        params = {"fiscalDriveNumber": fn}
        if date:
            params["date"] = date
        return self.call("v1/getDocCount", params)

    def shifts(self, fn):
        return self.call("v1/KKTShift", {"fiscalDriveNumber": fn})

    def documents_shift(self, fn, shift):
        return self.call("v1/documentsShift", {"fiscalDriveNumber": fn, "shiftNumber": shift})

    def close_shift_report(self, fn, shift):
        return self.call("v1/closeShiftReport", {"fiscalDriveNumber": fn, "shiftNumber": shift})

    def cheque_link(self, fn, fd, fp):
        return self.call("v1/getChequeLink", {
            "fiscalDriveNumber": fn,
            "fiscalDocumentNumber": fd,
            "fiscalSign": fp,
        })

    def get_fiscal_doc(self, fn, fd, fp):
        return self.call("v1/getFiscalDoc", {
            "fiscalDriveNumber": fn,
            "fiscalDocumentNumber": fd,
            "fiscalSign": fp,
        })

    def get_fiscal_report(self, fn):
        return self.call("v1/getFiscalReport", {"fiscalDriveNumber": fn})

    def get_crpt_ticket(self, fn, fd, fp):
        return self.call("v1/getCrptTicket", {
            "fiscalDriveNumber": fn,
            "fiscalDocumentNumber": fd,
            "fiscalSign": fp,
        })
