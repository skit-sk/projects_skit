import re
import unicodedata
from typing import Optional

from bs4 import BeautifulSoup

from base import BaseParser
from models import PriceResult

CYRILLIC_TO_LATIN = {
    "а": "a", "б": "b", "в": "v", "г": "g", "д": "d",
    "е": "e", "ё": "e", "ж": "zh", "з": "z", "и": "i",
    "й": "y", "к": "k", "л": "l", "м": "m", "н": "n",
    "о": "o", "п": "p", "р": "r", "с": "s", "т": "t",
    "у": "u", "ф": "f", "х": "kh", "ц": "ts", "ч": "ch",
    "ш": "sh", "щ": "shch", "ъ": "", "ы": "y", "ь": "",
    "э": "e", "ю": "yu", "я": "ya",
}


def transliterate(text: str) -> str:
    text = text.lower().strip()
    result = []
    for ch in text:
        if ch in CYRILLIC_TO_LATIN:
            result.append(CYRILLIC_TO_LATIN[ch])
        else:
            result.append(ch)
    return "".join(result)


class BudzdorovParser(BaseParser):
    source_id = "src_012"
    source_name = "Будь Здоров"
    search_url = "https://saratov.budzdorov.ru/forms/{slug}"

    def search(self, drug_name: str, dose_form: str = "") -> list[PriceResult]:
        slug = transliterate(drug_name)
        url = self.search_url.format(slug=slug)
        print(f"  Searching {self.source_name}: {url}")
        html = self._fetch(url)
        if not html:
            return []
        return self.parse(html, drug_name)

    def parse(self, html: str, query: str) -> list[PriceResult]:
        soup = BeautifulSoup(html, "lxml")
        results = []

        products = self._find_products(soup)
        for prod in products:
            try:
                parsed = self._parse_product(prod, query)
                if parsed:
                    results.append(parsed)
            except (AttributeError, ValueError, TypeError):
                continue

        return results

    def _find_products(self, soup: BeautifulSoup) -> list:
        candidates = soup.select(
            "[class*='product-card'], [class*='productCard'], [class*='ProductCard'], "
            "[class*='catalog-card'], [class*='catalogItem'], [class*='item'], "
            "[class*='card'], article[class*='product']"
        )
        if candidates:
            return candidates[:10]

        # fallback: find divs containing both a title link and a price
        for tag in ["div", "li", "article"]:
            for el in soup.find_all(tag, class_=True):
                text = el.get_text(strip=True)
                if any(kw in text for kw in ["Руб", "₽", "руб"]) and len(text) < 600:
                    candidates.append(el)
        return candidates[:10]

    def _parse_product(self, el, query: str) -> Optional[PriceResult]:
        title_el = el.select_one(
            "a[class*='title'], a[class*='name'], [class*='product-name'] a, "
            "[class*='card-title'] a, h2 a, h3 a, a[class*='link']"
        )
        price_el = el.select_one(
            "[class*='price'], [class*='Price'], [class*='cost'], "
            "[class*='current-price'], [class*='discount-price'], "
            "span[class*='rub'], [class*='b-price']"
        )

        title = ""
        if title_el:
            title = title_el.get_text(strip=True)
        elif not title_el:
            possible = el.select_one("a") or el.find("a")
            if possible:
                title = possible.get_text(strip=True)

        price_text = ""
        if price_el:
            price_text = price_el.get_text(strip=True)
        else:
            match = re.search(r"(\d[\d\s]*)\s*(?:Руб|₽|руб)", el.get_text())
            if match:
                price_text = match.group(0)

        if not price_text:
            return None

        price_match = re.search(r"([\d\s,.]+)", price_text.replace("\u00a0", " ").replace("&nbsp;", " "))
        if not price_match:
            return None

        amount = float(price_match.group(1).replace(" ", "").replace(",", ".").replace("\u2009", ""))
        link_el = title_el or el.select_one("a")
        link = link_el.get("href", "") if link_el else ""
        if link and not link.startswith("http"):
            link = "https://saratov.budzdorov.ru" + link

        dose_form = title.replace(query, "").strip(" ,-–") if title else query

        availability = "in_stock"
        avail_text = el.get_text().lower()
        if "нет в наличии" in avail_text or "отсутствует" in avail_text:
            availability = "out_of_stock"

        return PriceResult(
            drug_name=query,
            dose_form=dose_form,
            amount=amount,
            source_id=self.source_id,
            source_name=self.source_name,
            url=link,
            availability=availability,
        )
