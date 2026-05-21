import json
import os
import subprocess
import urllib.request
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent


def _post(url, data):
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode(),
            headers={"Content-Type": "application/json", "User-Agent": "Mozilla/5.0"}
        )
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection failed: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def _get(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {"error": f"HTTP {e.code}: {e.reason}"}
    except urllib.error.URLError as e:
        return {"error": f"Connection failed: {e.reason}"}
    except Exception as e:
        return {"error": str(e)}


def validate_inn(inn: str) -> str | None:
    if not inn:
        return "⛔ пустой ИНН"
    if not inn.isdigit():
        return "⛔ ИНН должен содержать только цифры"
    if len(inn) == 10:
        return None  # ЮЛ
    if len(inn) == 12:
        return None  # ИП
    return "⛔ ИНН: 10 цифр (ЮЛ) или 12 цифр (ИП)"


def inn_type(inn: str) -> str:
    return "🏢 ЮЛ" if len(inn) == 10 else "👤 ИП" if len(inn) == 12 else "?"


# ── EGRUL ──

EGRUL_OK = "✅"
EGRUL_ERR = "❌"


def fetch_egrul(inn: str) -> dict:
    try:
        resp = _post("https://egrul.nalog.ru/", {
            "query": inn, "page": "1",
            "searchType": "exact", "region": "", "citizenship": ""
        })
        if "error" in resp:
            return {"status": EGRUL_ERR, "note": resp["error"]}
        token = resp.get("t", "")
        if not token:
            return {"status": EGRUL_ERR, "note": "EGRUL token not received"}
        result = _get(f"https://egrul.nalog.ru/search-result/{token}")
        if "error" in result:
            return {"status": EGRUL_ERR, "note": result["error"]}
        rows = result.get("rows", [])
        if not rows:
            return {"status": EGRUL_ERR, "note": "По ИНН ничего не найдено"}
        row = rows[0]
        return {
            "status": EGRUL_OK,
            "name": row.get("n", ""),
            "short": row.get("c", ""),
            "head": row.get("g", ""),
            "address": row.get("rn", ""),
            "kpp": row.get("p", ""),
            "ogrn": row.get("o", ""),
            "reg_date": row.get("r", ""),
            "kind": "fl" if row.get("k") == "fl" else "ul",
        }
    except Exception as e:
        return {"status": EGRUL_ERR, "note": f"EGRUL error: {e}"}


# ── FSSP (через Playwright) ──

FSSP_OK = "✅"
FSSP_ERR = "❌"
FSSP_SKIP = "⏭"


def fetch_fssp(inn: str, timeout: int = 30) -> dict:
    script = SCRIPT_DIR / "audit_fssp.py"
    if not script.exists():
        return {"status": FSSP_SKIP, "note": "скрипт audit_fssp.py не найден"}
    pw_script = SCRIPT_DIR.parent.parent.parent / "tools" / "playwright" / "bin" / "playwright.sh"
    if not pw_script.exists():
        return {"status": FSSP_SKIP, "note": "playwright.sh не найден"}
    try:
        result = subprocess.run(
            [str(pw_script), str(script), inn],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return {"status": FSSP_ERR, "note": result.stderr.strip()[:200]}
        data = json.loads(result.stdout.strip())
        return data
    except subprocess.TimeoutExpired:
        return {"status": FSSP_ERR, "note": "таймаут 30с"}
    except json.JSONDecodeError as e:
        return {"status": FSSP_ERR, "note": f"parse error: {e}"}
    except Exception as e:
        return {"status": FSSP_ERR, "note": str(e)}


# ── Банкротства (через CloakBrowser) ──

BANKR_OK = "✅"
BANKR_ERR = "❌"
BANKR_SKIP = "⏭"


def fetch_bankruptcy(inn: str, timeout: int = 45) -> dict:
    script = SCRIPT_DIR / "audit_bankruptcy.py"
    if not script.exists():
        return {"status": BANKR_SKIP, "note": "скрипт audit_bankruptcy.py не найден"}
    cb_script = SCRIPT_DIR.parent.parent.parent / "tools" / "cloakbrowser" / "bin" / "cloakbrowser.sh"
    if not cb_script.exists():
        return {"status": BANKR_SKIP, "note": "cloakbrowser.sh не найден"}
    try:
        result = subprocess.run(
            [str(cb_script), str(script), inn],
            capture_output=True, text=True, timeout=timeout
        )
        if result.returncode != 0:
            return {"status": BANKR_ERR, "note": result.stderr.strip()[:200]}
        data = json.loads(result.stdout.strip())
        return data
    except subprocess.TimeoutExpired:
        return {"status": BANKR_ERR, "note": "таймаут 45с"}
    except json.JSONDecodeError as e:
        return {"status": BANKR_ERR, "note": f"parse error: {e}"}
    except Exception as e:
        return {"status": BANKR_ERR, "note": str(e)}


# ── audit_inn ──

def audit_inn(inn: str) -> dict:
    err = validate_inn(inn)
    if err:
        return {"inn": inn, "valid": err}

    result = {
        "inn": inn,
        "valid": inn_type(inn),
        "egrul": fetch_egrul(inn),
        "fssp": None,
        "bankruptcy": None,
    }

    # FSSP и банкротства — через browser (только если EGRUL нашёл)
    if result["egrul"].get("status") == EGRUL_OK:
        result["fssp"] = fetch_fssp(inn)
        result["bankruptcy"] = fetch_bankruptcy(inn)
    else:
        result["fssp"] = {"status": FSSP_SKIP, "note": "EGRUL не ответил"}
        result["bankruptcy"] = {"status": BANKR_SKIP, "note": "EGRUL не ответил"}

    return result
