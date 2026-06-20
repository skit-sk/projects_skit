from dataclasses import dataclass, field
from typing import Optional


@dataclass
class PriceResult:
    drug_name: str
    dose_form: str
    amount: float
    source_id: str
    source_name: str
    availability: str = "in_stock"
    url: str = ""
    currency: str = "RUB"
    preliminary: bool = True


@dataclass
class PriceGroup:
    min: float
    median: float
    max: float

    @classmethod
    def from_results(cls, results: list[PriceResult]) -> "PriceGroup":
        prices = sorted(r.amount for r in results)
        n = len(prices)
        if n == 0:
            return cls(min=0, median=0, max=0)
        return cls(
            min=prices[0],
            median=prices[n // 2],
            max=prices[-1],
        )


@dataclass
class SourceEntry:
    source_name: str
    dose_form: str
    price_group: PriceGroup
    url: str
    availability: str
    last_checked: str
