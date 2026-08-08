"""Утилиты: парсинг DataMatrix, GS1, QR-чеков."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class DataMatrixInfo:
    """Распарсенный DataMatrix код маркировки."""
    gtin: str
    serial: str
    raw: str

    @property
    def sgtin(self) -> str:
        return f"{self.gtin}{self.serial}"


def parse_datamatrix(code: str) -> Optional[DataMatrixInfo]:
    """Парсинг DataMatrix кода формата GS1.

    Пример: 01046300375902232121tZxhYmJdBh<GS>91ff0d<GS>92...
    """
    code = code.strip()
    gtin_match = re.search(r"01(\d{14})", code)
    serial_match = re.search(r"21([!-~]+)", code)
    if gtin_match and serial_match:
        return DataMatrixInfo(gtin=gtin_match.group(1), serial=serial_match.group(1), raw=code)
    return None


def parse_receipt_qr(code: str) -> dict[str, str]:
    """Парсинг QR-строки чека."""
    params = {}
    for part in code.split("&"):
        if "=" in part:
            k, v = part.split("=", 1)
            params[k] = v
    return params


def detect_code_type(code: str) -> str:
    """Автоопределение типа кода."""
    code = code.strip()
    if len(code) == 13 and code.isdigit():
        return "ean13"
    if code.startswith("t=") and "&s=" in code:
        return "qr"
    if re.search(r"01\d{14}", code):
        return "datamatrix"
    if code.startswith("chek.") or "markirovka" in code or "kiz=" in code:
        return "qr"
    return "datamatrix"
