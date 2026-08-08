"""API Национального каталога маркированных товаров.

Base:
  Sandbox: https://api.nk.sandbox.crptech.ru
  Production: https://апи.национальный-каталог.рф

Аутентификация: ?apikey=XXX или Authorization: Bearer <token>
"""

from typing import Optional

from crpt.client import HttpClient
from crpt.auth import ApiKeyAuth, TokenAuth
from crpt.types import ApiEnv, BASE_URLS


class NkApiClient:
    """Клиент API Национального каталога (НК)."""

    def __init__(
        self,
        env: ApiEnv = ApiEnv.SANDBOX,
        api_key: Optional[str] = None,
        token: Optional[str] = None,
    ):
        self.base_url = BASE_URLS[env.value]["nk_api"]
        self.api_key_auth = ApiKeyAuth(api_key)
        self.token_auth = TokenAuth(token)
        self._http = HttpClient(self.base_url)

    def _auth_params(self) -> dict:
        return self.api_key_auth.get_query_params()

    def _auth_headers(self) -> dict:
        return self.token_auth.get_headers()

    # ═══════════════════════════════════════════════════════════
    # Карточки товаров
    # ═══════════════════════════════════════════════════════════

    def get_product(self, gtin: str, subaccount: bool = False) -> dict:
        """Получить информацию о собственной карточке товара.

        Эндпоинт: GET /v3/feed-product?apikey=...&gtin={gtin}
        """
        params = self._auth_params()
        params["gtin"] = gtin
        if subaccount:
            params["subaccount"] = "true"
        return self._http.get("/v3/feed-product", params=params)

    def get_product_by_id(self, good_id: int) -> dict:
        """Получить информацию о карточке по good_id.

        Эндпоинт: GET /v3/feed-product?apikey=...&good_id={id}
        """
        params = self._auth_params()
        params["good_id"] = str(good_id)
        return self._http.get("/v3/feed-product", params=params)

    def get_products(self, gtins: list[str]) -> dict:
        """Получить информацию о нескольких карточках.

        Эндпоинт: GET /v3/feed-product?apikey=...&gtins=xxx;yyy
        Максимум 25 GTIN в запросе.
        """
        params = self._auth_params()
        params["gtins"] = ";".join(gtins)
        return self._http.get("/v3/feed-product", params=params)

    def get_public_product(self, gtin: str) -> dict:
        """Получить информацию о публичной карточке.

        Эндпоинт: GET /v3/product?gtin={gtin}
        """
        params = self._auth_params()
        params["gtin"] = gtin
        return self._http.get("/v3/product", params=params)

    def get_short_product(self, gtin: str) -> dict:
        """Получить краткую информацию о карточке.

        Эндпоинт: GET /v3/short-product?apikey=...&gtin={gtin}
        """
        params = self._auth_params()
        params["gtin"] = gtin
        return self._http.get("/v3/short-product", params=params)

    def get_own_products(self, limit: int = 100, page: int = 0) -> dict:
        """Список собственных карточек с краткой информацией.

        Эндпоинт: GET /v3/feed-products?apikey=...&limit={limit}&page={page}
        """
        params = self._auth_params()
        params["limit"] = str(limit)
        params["page"] = str(page)
        return self._http.get("/v3/feed-products", params=params)

    def check_product_changes(self, gtins: list[str]) -> dict:
        """Проверить изменения по карточкам.

        Эндпоинт: GET /v3/product-changes?gtins=xxx;yyy
        """
        params = self._auth_params()
        params["gtins"] = ";".join(gtins)
        return self._http.get("/v3/product-changes", params=params)

    def check_markable(self, gtins: list[str]) -> dict:
        """Проверить принадлежность кодов ТНВЭД к маркируемым товарным группам.

        Эндпоинт: GET /v3/product/markable?gtins=xxx;yyy
        """
        params = self._auth_params()
        params["gtins"] = ";".join(gtins)
        return self._http.get("/v3/product/markable", params=params)

    # ═══════════════════════════════════════════════════════════
    # Создание / редактирование карточек
    # ═══════════════════════════════════════════════════════════

    def create_or_update_product(self, product_data: dict) -> dict:
        """Создать или отредактировать карточку товара.

        Эндпоинт: POST /v3/feed?apikey=...
        """
        return self._http.post("/v3/feed", body=product_data, params=self._auth_params())

    def get_feed_status(self, feed_id: str) -> dict:
        """Проверить статус обработки пакета обновлений.

        Эндпоинт: GET /v3/feed-status?apikey=...&feed_id={id}
        """
        params = self._auth_params()
        params["feed_id"] = feed_id
        return self._http.get("/v3/feed-status", params=params)

    def generate_gtin(self, count: int = 1) -> dict:
        """Сгенерировать код GTIN.

        Эндпоинт: POST /v3/generate-gtin?apikey=...
        """
        return self._http.post("/v3/generate-gtin", body={"count": count}, params=self._auth_params())

    def resize_photo(self, photo_url: str, width: int, height: int) -> dict:
        """Изменить размер фотографии.

        Эндпоинт: POST /v3/resize-photo?apikey=...
        """
        return self._http.post(
            "/v3/resize-photo",
            body={"photo_url": photo_url, "width": width, "height": height},
            params=self._auth_params(),
        )

    def send_to_moderation(self, gtin: str) -> dict:
        """Отправить карточку на модерацию.

        Эндпоинт: POST /v3/moderation?apikey=...
        """
        return self._http.post("/v3/moderation", body={"gtin": gtin}, params=self._auth_params())

    # ═══════════════════════════════════════════════════════════
    # Справочники
    # ═══════════════════════════════════════════════════════════

    def get_categories(self) -> dict:
        """Дерево категорий товаров.

        Эндпоинт: GET /v3/dict/categories?apikey=...
        """
        return self._http.get("/v3/dict/categories", params=self._auth_params())

    def get_attributes(self, category_id: int) -> dict:
        """Перечень атрибутов для категории.

        Эндпоинт: GET /v3/dict/attributes?apikey=...&category_id={id}
        """
        params = self._auth_params()
        params["category_id"] = str(category_id)
        return self._http.get("/v3/dict/attributes", params=params)

    def get_countries(self) -> dict:
        """Справочник стран производства.

        Эндпоинт: GET /v3/dict/countries?apikey=...
        """
        return self._http.get("/v3/dict/countries", params=self._auth_params())

    def get_brands(self, name: Optional[str] = None, limit: int = 100, page: int = 0) -> dict:
        """Справочник товарных знаков.

        Эндпоинт: GET /v3/dict/brands?apikey=...
        """
        params = self._auth_params()
        params["limit"] = str(limit)
        params["page"] = str(page)
        if name:
            params["name"] = name
        return self._http.get("/v3/dict/brands", params=params)

    # ═══════════════════════════════════════════════════════════
    # Разрешительные документы
    # ═══════════════════════════════════════════════════════════

    def check_permit_doc(self, gtin: str, doc_number: str, doc_date: str) -> dict:
        """Проверить наличие разрешительного документа.

        Эндпоинт: GET /v3/permit-doc?apikey=...&gtin={gtin}&number={number}&date={date}
        """
        params = self._auth_params()
        params["gtin"] = gtin
        params["number"] = doc_number
        params["date"] = doc_date
        return self._http.get("/v3/permit-doc", params=params)

    # ═══════════════════════════════════════════════════════════
    # Субаккаунты
    # ═══════════════════════════════════════════════════════════

    def get_subaccounts(self) -> dict:
        """Список субаккаунтов компании.

        Эндпоинт: GET /v3/sub-accounts?apikey=...
        """
        return self._http.get("/v3/sub-accounts", params=self._auth_params())

    def get_accounts_codes(self) -> dict:
        """Получить список компаний и кодов товаров, по которым предоставлен доступ.

        Эндпоинт: GET /v3/accounts-codes?apikey=...
        """
        return self._http.get("/v3/accounts-codes", params=self._auth_params())
