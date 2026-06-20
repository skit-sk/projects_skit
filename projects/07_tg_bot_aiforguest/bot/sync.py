import os
import time
import asyncio
import urllib.request
import json as _json
import logging

_LAST_SYNC_TS = 0.0
_SYNC_TTL = 60.0
log = logging.getLogger("sync")


async def sync_exchange(status_msg=None, force: bool = False) -> tuple:
    """POST /api/sync-all with 60s cache.

    Returns: (sync_ok: bool, sync_count: int, sync_err: str, cached: bool)
    """
    global _LAST_SYNC_TS
    now = time.time()
    age = now - _LAST_SYNC_TS
    if not force and age < _SYNC_TTL and _LAST_SYNC_TS > 0:
        log.info(f"sync: cache hit (age {age:.1f}s < {_SYNC_TTL}s)")
        return True, 0, "", True

    sync_ok = True
    sync_count = 0
    sync_err = ""
    try:
        base_url = os.environ.get("FLASK_BASE_URL", "http://localhost:5000")
        req = urllib.request.Request(base_url + "/api/sync-all", method="POST",
                                     headers={"Content-Type": "application/json"})
        loop = asyncio.get_event_loop()
        resp_body = await loop.run_in_executor(
            None,
            lambda: urllib.request.urlopen(req, timeout=60).read(),
        )
        j = _json.loads(resp_body)
        if isinstance(j, dict):
            sync_count = j.get("count", 0)
            if not j.get("ok", True):
                sync_ok = False
                errors = j.get("errors", [])
                def _fmt_err(r):
                    if "error" in r:
                        return r["error"]
                    failed = [f"{k}={v}" for k, v in r.get("steps", {}).items()
                              if not v.startswith("ok")]
                    return "; ".join(failed) if failed else "unknown"
                sync_err = "; ".join(_fmt_err(e) for e in errors[:3])
        _LAST_SYNC_TS = time.time()
        log.info(f"sync: ok={sync_ok} count={sync_count} age={age:.1f}s errors={sync_err[:100] if sync_err else 'none'}")
    except Exception as e:
        sync_ok = False
        sync_err = str(e)[:200]
        log.warning(f"sync: failed: {sync_err}")

    return sync_ok, sync_count, sync_err, False
