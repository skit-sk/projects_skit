"""True API — клиент ГИС МТ.

API v3 base: https://markirovka.crpt.ru/api/v3/true-api (production)
API v3 base: https://markirovka.sandbox.crptech.ru/api/v3/true-api (sandbox)

Аутентификация:
  - Публичные методы: без токена
  - Приватные методы: Authorization: Bearer <token>
"""

from typing import Optional

from crpt.client import HttpClient
from crpt.auth import TokenAuth
from crpt.types import ApiEnv, BASE_URLS


class TrueApiClient:
    """Клиент True API ГИС МТ."""

    def __init__(
        self,
        env: ApiEnv = ApiEnv.SANDBOX,
        auth: Optional[TokenAuth] = None,
        api_version: str = "v3",
    ):
        key = f"true_api_{api_version}"
        self.base_url = BASE_URLS[env.value][key]
        self.auth = auth or TokenAuth()
        self._http = HttpClient(self.base_url)

    def _headers(self) -> dict:
        return self.auth.get_headers()

    # ═══════════════════════════════════════════════════════════
    # Публичные методы (без авторизации)
    # ═══════════════════════════════════════════════════════════

    # ── Участники ────────────────────────────────────────────

    def get_participants(self, inn: str) -> dict:
        """Проверка регистрации УОТ по ИНН.

        Эндпоинт: GET /participants?inns={inn}
        Уровень: Level 0 — публичный, без токена.

        Возвращает: статус, товарные группы, роли участника.
        """
        return self._http.get("/participants", params={"inns": inn})

    # ── МОД — места осуществления деятельности ───────────────

    def get_mods_list(
        self,
        inns: Optional[str] = None,
        product_groups: Optional[str] = None,
        limit: int = 100,
        page: int = 0,
    ) -> dict:
        """Список МОД участника.

        Эндпоинт: GET /mods/list
        Уровень: Level 0 — публичный.
        """
        params: dict = {"limit": limit, "page": page}
        if inns:
            params["inns"] = inns
        if product_groups:
            params["productGroups"] = product_groups
        return self._http.get("/mods/list", params=params)

    def get_mods_info(self, pg: list, inn: Optional[str] = None, kpp: Optional[list] = None) -> dict:
        """Статус блокировки МОД (только для пива).

        Эндпоинт: POST /mods/info
        Уровень: Level 0 — публичный.
        """
        body: dict = {"pg": pg}
        if inn:
            body["inn"] = inn
        if kpp:
            body["kpp"] = kpp
        return self._http.post("/mods/info", body=body)

    # ═══════════════════════════════════════════════════════════
    # Аутентификация (Level 2-3)
    # ═══════════════════════════════════════════════════════════

    def auth_key(self) -> dict:
        """Запрос уникальной пары UUID+data для аутентификации.

        Эндпоинт: GET /auth/key
        """
        return self._http.get("/auth/key")

    def auth_sign_in(
        self, uuid: str, data_signed: str, inn: Optional[str] = None
    ) -> dict:
        """Получение ключа сессии.

        Эндпоинт: POST /auth/simpleSignIn

        data_signed — подписанные данные (base64 откреплённая подпись)
        """
        body: dict = {"uuid": uuid, "data": data_signed}
        if inn:
            body["inn"] = inn
        return self._http.post("/auth/simpleSignIn", body=body)

    # ═══════════════════════════════════════════════════════════
    # Коды идентификации (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def cises_short_list(self, cises: list[str]) -> dict:
        """Краткая информация о КИ по списку.

        Эндпоинт: POST /cises/short/list
        """
        return self._http.post("/cises/short/list", body={"cises": cises}, headers=self._headers())

    def cises_info(self, cises: list[str]) -> dict:
        """Подробная информация о КИ по списку.

        Эндпоинт: POST /cises/info
        """
        return self._http.post("/cises/info", body={"cises": cises}, headers=self._headers())

    def cises_history(self, cises: list[str]) -> dict:
        """История движения КИ.

        Эндпоинт: POST /cises/history
        """
        return self._http.post("/cises/history", body={"cises": cises}, headers=self._headers())

    def cises_public_info(self, cises: list[str]) -> dict:
        """Общедоступная информация о КИ (публичный метод).

        Эндпоинт: POST /cises/public-info
        Уровень: Level 0 — без токена.
        """
        return self._http.post("/cises/public-info", body={"cises": cises})

    # ═══════════════════════════════════════════════════════════
    # Товары / продукты (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def product_info(self, gtin: str) -> dict:
        """Информация о товаре по GTIN.

        Эндпоинт: GET /product/info?gtin={gtin}
        """
        return self._http.get("/product/info", params={"gtin": gtin}, headers=self._headers())

    def products_gtin_list(self, inn: Optional[str] = None, product_group: Optional[str] = None) -> dict:
        """Список GTIN товаров УОТ.

        Эндпоинт: GET /products/gtin/list
        """
        params = {}
        if inn:
            params["inn"] = inn
        if product_group:
            params["productGroup"] = product_group
        return self._http.get("/products/gtin/list", params=params, headers=self._headers())

    def product_group_by_gtin(self, gtin: str) -> dict:
        """Код товарной группы по GTIN.

        Эндпоинт: GET /product/group?gtin={gtin}
        """
        return self._http.get("/product/group", params={"gtin": gtin}, headers=self._headers())

    # ═══════════════════════════════════════════════════════════
    # Документы (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def documents_list(
        self,
        limit: int = 100,
        page: int = 0,
        doc_type: Optional[str] = None,
        status: Optional[str] = None,
        date_from: Optional[str] = None,
        date_to: Optional[str] = None,
    ) -> dict:
        """Список загруженных документов.

        Эндпоинт: GET /documents/list
        """
        params: dict = {"limit": limit, "page": page}
        if doc_type:
            params["type"] = doc_type
        if status:
            params["status"] = status
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._http.get("/documents/list", params=params, headers=self._headers())

    def document_info(self, doc_id: str) -> dict:
        """Содержимое документа по ID.

        Эндпоинт: GET /doc/{documentId}/info
        """
        return self._http.get(f"/doc/{doc_id}/info", headers=self._headers())

    def document_cises(self, doc_id: str) -> dict:
        """Список КИ по номеру документа.

        Эндпоинт: GET /doc/{documentId}/cises
        """
        return self._http.get(f"/doc/{doc_id}/cises", headers=self._headers())

    def document_status(self, doc_id: str) -> dict:
        """Статус обработки документа.

        Эндпоинт: GET /document/status?documentId={doc_id}
        """
        return self._http.get("/document/status", params={"documentId": doc_id}, headers=self._headers())

    def document_validate(self, doc_type: str, document_b64: str) -> dict:
        """Предварительная проверка УПД.

        Эндпоинт: POST /document/validate
        """
        return self._http.post(
            "/document/validate",
            body={"documentType": doc_type, "document": document_b64},
            headers=self._headers(),
        )

    # ═══════════════════════════════════════════════════════════
    # Чеки ККТ (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def checks_list(self, limit: int = 100, page: int = 0, date_from: Optional[str] = None, date_to: Optional[str] = None) -> dict:
        """Список загруженных чеков ККТ.

        Эндпоинт: GET /checks/list
        """
        params: dict = {"limit": limit, "page": page}
        if date_from:
            params["dateFrom"] = date_from
        if date_to:
            params["dateTo"] = date_to
        return self._http.get("/checks/list", params=params, headers=self._headers())

    def check_body(self, check_id: str) -> dict:
        """Содержимое чека ККТ.

        Эндпоинт: GET /checks/{checkId}/body
        """
        return self._http.get(f"/checks/{check_id}/body", headers=self._headers())

    # ═══════════════════════════════════════════════════════════
    # Квитанции (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def receipts_document(self, doc_id: str) -> dict:
        """Квитанция по ID документа.

        Эндпоинт: GET /receipts/{documentId}
        """
        return self._http.get(f"/receipts/{doc_id}", headers=self._headers())

    def receipts_check(self, check_id: str) -> dict:
        """Квитанция по ID чека.

        Эндпоинт: GET /receipts/check/{checkId}
        """
        return self._http.get(f"/receipts/check/{check_id}", headers=self._headers())

    # ═══════════════════════════════════════════════════════════
    # Выгрузки данных / Диспенсер (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def dispenser_tasks_create(self, task_type: str, params: dict) -> dict:
        """Создание задания на выгрузку.

        Эндпоинт: POST /dispenser/tasks
        """
        body = {"type": task_type, **params}
        return self._http.post("/dispenser/tasks", body=body, headers=self._headers())

    def dispenser_task_status(self, task_id: str) -> dict:
        """Статус задания на выгрузку.

        Эндпоинт: GET /dispenser/tasks/{taskId}
        """
        return self._http.get(f"/dispenser/tasks/{task_id}", headers=self._headers())

    def dispenser_results(self, task_id: str) -> dict:
        """Результаты выгрузки.

        Эндпоинт: GET /dispenser/results/{taskId}
        """
        return self._http.get(f"/dispenser/results/{task_id}", headers=self._headers())

    def dispenser_download(self, task_id: str) -> dict:
        """Скачать файл выгрузки (ZIP/CSV).

        Эндпоинт: GET /dispenser/results/{taskId}/file
        """
        return self._http.get(f"/dispenser/results/{task_id}/file", headers=self._headers())

    # ═══════════════════════════════════════════════════════════
    # ЭДО Лайт (через True API) (Level 2+)
    # ═══════════════════════════════════════════════════════════

    def edo_abonent_id(self) -> dict:
        """Получение идентификатора абонента в ЭДО Лайт.

        Эндпоинт: GET /edo/abonent
        """
        return self._http.get("/edo/abonent", headers=self._headers())

    def edo_document_zip(self, doc_id: str) -> dict:
        """ZIP-архив документа ЭДО.

        Эндпоинт: GET /edo/document/{documentId}/zip
        """
        return self._http.get(f"/edo/document/{doc_id}/zip", headers=self._headers())
