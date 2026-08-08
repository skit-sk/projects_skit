"""Базовый HTTP клиент с retry и логированием."""

import json
import logging
import time
from typing import Optional, Any
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

logger = logging.getLogger("crpt")


class HttpClient:
    """Синхронный HTTP клиент на urllib (без внешних зависимостей)."""

    def __init__(self, base_url: str, timeout: int = 30, headers: Optional[dict] = None):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self.default_headers = headers or {}
        self.default_headers.setdefault("Accept", "application/json")

    def _build_url(self, path: str, params: Optional[dict] = None) -> str:
        url = f"{self.base_url}{path}"
        if params:
            qs = urlencode({k: v for k, v in params.items() if v is not None})
            if qs:
                url = f"{url}?{qs}"
        return url

    def _request(
        self,
        method: str,
        path: str,
        params: Optional[dict] = None,
        body: Optional[dict] = None,
        headers: Optional[dict] = None,
    ) -> dict:
        url = self._build_url(path, params)
        all_headers = {**self.default_headers, **(headers or {})}

        data_bytes = None
        if body is not None:
            data_bytes = json.dumps(body).encode("utf-8")
            all_headers["Content-Type"] = "application/json"

        req = Request(url, data=data_bytes, method=method)
        for k, v in all_headers.items():
            req.add_header(k, v)

        start = time.monotonic()
        try:
            resp = urlopen(req, timeout=self.timeout)
            elapsed = (time.monotonic() - start) * 1000
            raw = resp.read().decode("utf-8")
            logger.info("[%s %s] %d %.0fms", method, path, resp.status, elapsed)
            if not raw:
                return {}
            return json.loads(raw)
        except HTTPError as e:
            body_raw = e.read().decode("utf-8", errors="replace")
            logger.error("[%s %s] %d — %s", method, path, e.code, body_raw[:500])
            try:
                return json.loads(body_raw)
            except json.JSONDecodeError:
                raise RuntimeError(f"HTTP {e.code}: {body_raw[:500]}")
        except URLError as e:
            logger.error("[%s %s] URLError: %s", method, path, e.reason)
            raise RuntimeError(f"Connection error: {e.reason}")
        except Exception as e:
            logger.error("[%s %s] Error: %s", method, path, e)
            raise

    def get(self, path: str, params: Optional[dict] = None, headers: Optional[dict] = None) -> dict:
        return self._request("GET", path, params=params, headers=headers)

    def post(
        self, path: str, body: Optional[dict] = None, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> dict:
        return self._request("POST", path, params=params, body=body, headers=headers)

    def delete(
        self, path: str, body: Optional[dict] = None, params: Optional[dict] = None, headers: Optional[dict] = None
    ) -> dict:
        return self._request("DELETE", path, params=params, body=body, headers=headers)
