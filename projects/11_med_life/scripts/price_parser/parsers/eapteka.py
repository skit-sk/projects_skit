import re

from bs4 import BeautifulSoup

from base import BaseParser
from models import PriceResult


class EaptekaParser(BaseParser):
    source_id = "src_002"
    source_name = "eApteka"
    search_url = "https://eapteka.ru/search/?q={query}"

    def parse(self, html: str, query: str) -> list[PriceResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        items = soup.select("[class*='product'], [class*='Product'], [class*='catalog-item']")
        if not items:
            items = soup.select("div[class*='card']", limit=10)

        for item in items[:5]:
            try:
                title_el = item.select_one("a[class*='title'], a[class*='name'], [class*='product-name']")
                price_el = item.select_one("[class*='price'], [class*='Price'], [class*='current-price']")
                link_el = title_el or item.select_one("a")

                if not title_el or not price_el:
                    continue

                title = title_el.get_text(strip=True)
                price_text = price_el.get_text(strip=True)
                price_match = re.search(r"([\d\s,.]+)", price_text.replace("\u00a0", " "))
                if not price_match:
                    continue

                amount = float(price_match.group(1).replace(" ", "").replace(",", "."))
                link = link_el.get("href", "") if link_el else ""
                if link and not link.startswith("http"):
                    link = "https://eapteka.ru" + link

                dose_form = title.replace(query.split()[0] if query else "", "").strip(" ,-")

                results.append(PriceResult(
                    drug_name=query,
                    dose_form=dose_form,
                    amount=amount,
                    source_id=self.source_id,
                    source_name=self.source_name,
                    url=link,
                ))
            except (AttributeError, ValueError, TypeError):
                continue

        return results
