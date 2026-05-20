import json
import urllib.request


def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except Exception as e:
        return {"error": str(e)}


def get_egrul(inn):
    return _get(f"https://egrul.nalog.ru/search?query={inn}")


def get_bo(inn):
    return _get(f"https://bo.nalog.ru/search?query={inn}")


def get_fssp(inn):
    return _get(f"https://api-ip.fssp.gov.ru/api/v1.0/search?type=1&query={inn}&token=")


def audit_inn(inn):
    egrul = get_egrul(inn)
    bo = get_bo(inn)
    fssp = get_fssp(inn)
    result = {"inn": inn}

    if "error" not in egrul:
        items = egrul.get("items", [])
        if items:
            org = items[0]
            result["name"] = org.get("name", "")
            result["address"] = org.get("address", "")
            result["status"] = org.get("status", "")
            result["okved"] = org.get("okved", "")
            result["registration_date"] = org.get("registration_date", "")
        else:
            result["egrul"] = "not found"
    else:
        result["egrul_error"] = egrul["error"]

    if "error" not in bo:
        result["bo"] = bo.get("items", [])
    else:
        result["bo_error"] = bo["error"]

    if "error" not in fssp:
        result["fssp"] = fssp
    else:
        result["fssp_error"] = fssp["error"]

    return result
