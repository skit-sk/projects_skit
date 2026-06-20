import random
import time
from abc import ABC, abstractmethod
from typing import Optional

import requests
from bs4 import BeautifulSoup

from config import USER_AGENTS, REQUEST_TIMEOUT, REQUEST_DELAY
from models import PriceResult


class BaseParser(ABC):
    source_id: str = ""
    source_name: str = ""
    search_url: str = ""

    def _get_headers(self) -> dict:
        return {
            "User-Agent": random.choice(USER_AGENTS),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "ru-RU,ru;q=0.9,en;q=0.8",
        }

    def _fetch(self, url: str) -> Optional[str]:
        try:
            resp = requests.get(url, headers=self._get_headers(), timeout=REQUEST_TIMEOUT)
            resp.raise_for_status()
            time.sleep(REQUEST_DELAY)
            return resp.text
        except requests.RequestException as e:
            print(f"  [WARN] {self.source_name}: {e}")
            return None

    @abstractmethod
    def parse(self, html: str, query: str) -> list[PriceResult]:
        ...

    def search(self, drug_name: str, dose_form: str = "") -> list[PriceResult]:
        query = f"{drug_name} {dose_form}".strip()
        url = self.search_url.format(query=query)
        print(f"  Searching {self.source_name}: {url}")
        html = self._fetch(url)
        if not html:
            return []
        return self.parse(html, drug_name)
