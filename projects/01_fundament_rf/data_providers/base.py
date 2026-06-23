import time
import json
import hashlib
from abc import ABC, abstractmethod
from typing import Optional, Any
from pathlib import Path


class CacheEntry:
    def __init__(self, data: Any, ttl: float = 300.0):
        self.data = data
        self.expires_at = time.time() + ttl

    @property
    def expired(self) -> bool:
        return time.time() > self.expires_at


class BaseProvider(ABC):
    RETRY_DELAYS = [0.5, 1.0, 2.0]

    def __init__(self, retries: int = 3, timeout: int = 15, cache_ttl: float = 300.0):
        self.retries = retries
        self.timeout = timeout
        self.cache_ttl = cache_ttl
        self._cache: dict[str, CacheEntry] = {}

    @abstractmethod
    def fetch(self, *args, **kwargs) -> Any:
        pass

    def _cache_key(self, *args, **kwargs) -> str:
        raw = json.dumps({"args": args, "kwargs": kwargs}, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()[:32]

    def _cached(self, key: str) -> Optional[Any]:
        entry = self._cache.get(key)
        if entry and not entry.expired:
            return entry.data
        return None

    def _store_cache(self, key: str, data: Any):
        self._cache[key] = CacheEntry(data, self.cache_ttl)

    def _fetch_with_retry(self, url: str, **req_kwargs) -> dict:
        import requests
        last_error = None
        for attempt in range(self.retries):
            try:
                resp = requests.get(url, timeout=self.timeout, **req_kwargs)
                if resp.status_code == 200:
                    return resp.json()
            except Exception as e:
                last_error = e
                if attempt < self.retries - 1:
                    time.sleep(self.RETRY_DELAYS[min(attempt, len(self.RETRY_DELAYS) - 1)])
        raise RuntimeError(f"Fetch failed after {self.retries} attempts: {last_error}")

    def clear_cache(self):
        self._cache.clear()
