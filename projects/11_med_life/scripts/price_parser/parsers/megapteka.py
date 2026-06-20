import re
from typing import Optional

from bs4 import BeautifulSoup

from base import BaseParser
from models import PriceResult


class MegaptekaParser(BaseParser):
    source_id = "src_001"
    source_name = "Мегаптека"
    search_url = "https://megapteka.ru/search?q={query}"

    def parse(self, html: str, query: str) -> list[PriceResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []
        cards = soup.select("[class*='product-card'], [class*='ProductCard'], [class*='catalog-card']")
        if not cards:
            cards = soup.select("div[class*='item']", limit=10)

        for card in cards[:5]:
            try:
                title_el = card.select_one("a[class*='title'], a[class*='name'], [class*='product-name'] a")
                price_el = card.select_one("[class*='price'], [class*='Price'], [class*='cost']")
                link_el = title_el or card.select_one("a")

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
                    link = "https://megapteka.ru" + link

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
