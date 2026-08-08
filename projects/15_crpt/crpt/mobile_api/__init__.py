"""Mobile API — публичная проверка кодов без авторизации.

Base: https://mobile.api.crpt.ru/mobile/check
Не требует токенов/ключей. Работает через эмуляцию мобильного приложения.
"""

from typing import Union

from crpt.client import HttpClient
from crpt.types import BASE_URLS, ApiEnv


MOBILE_UA = (
    "Platform: iOS 17.2; AppVersion: 4.47.0; AppVersionCode: 7630; Device: iPhone 14 Pro;"
)


class MobileCheckClient:
    """Клиент публичной проверки кодов через mobile API."""

    def __init__(self, env: ApiEnv = ApiEnv.SANDBOX):
        base = BASE_URLS[env.value]["mobile"]
        self._http = HttpClient(
            base,
            headers={
                "User-Agent": MOBILE_UA,
                "Accept": "application/json",
            },
        )

    # ── GET методы ──────────────────────────────────────────

    def check_datamatrix(self, code: str) -> dict:
        """Проверка DataMatrix кода маркировки.

        Эндпоинт: GET /mobile/check?code=...&codeType=datamatrix

        Пример: 01046300375902232121tZxhYmJdBh
        """
        return self._http.get("/mobile/check", params={"code": code, "codeType": "datamatrix"})

    def check_ean13(self, code: str) -> dict:
        """Проверка штрихкода EAN-13.

        Эндпоинт: GET /mobile/check?code=...&codeType=ean13

        Пример: 4630037590223
        """
        return self._http.get("/mobile/check", params={"code": code, "codeType": "ean13"})

    def check_qr(self, code: str) -> dict:
        """Проверка QR-кода чека.

        Эндпоинт: GET /mobile/check?code=...&codeType=qr
        """
        return self._http.get("/mobile/check", params={"code": code, "codeType": "qr"})

    # ── POST методы ─────────────────────────────────────────

    def check_receipt(self, receipt_str: str) -> dict:
        """Проверка чека по реквизитной строке.

        Эндпоинт: POST /mobile/check
        Тело: {"code": "t=20231203T2319&s=261.80&fn=...&i=10027&fp=...&n=1", "codeType": "qr"}
        """
        return self._http.post(
            "/mobile/check",
            body={"code": receipt_str, "codeType": "qr"},
            headers={"Content-Type": "application/json"},
        )

    # ── Универсальный метод ─────────────────────────────────

    def check(self, code: str, code_type: str = "datamatrix") -> dict:
        """Универсальная проверка любого кода.

        Эндпоинт: GET /mobile/check?code=...&codeType=...

        Допустимые code_type: datamatrix, ean13, qr
        """
        return self._http.get("/mobile/check", params={"code": code, "codeType": code_type})
