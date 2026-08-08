import pytest
from crpt.types import ApiEnv, BASE_URLS, PRODUCT_GROUPS


class TestTypes:
    def test_base_urls_have_all_environments(self):
        assert ApiEnv.PRODUCTION.value in BASE_URLS
        assert ApiEnv.SANDBOX.value in BASE_URLS

    def test_true_api_urls(self):
        sandbox = BASE_URLS[ApiEnv.SANDBOX.value]
        assert "sandbox" in sandbox["true_api_v3"]
        production = BASE_URLS[ApiEnv.PRODUCTION.value]
        assert "sandbox" not in production["true_api_v3"]

    def test_product_groups(self):
        assert PRODUCT_GROUPS["shoes"] == "Обувные товары"
        assert PRODUCT_GROUPS["milk"] == "Молочная продукция"
        assert PRODUCT_GROUPS["water"] == "Упакованная вода"


class TestAuth:
    def test_api_key_auth(self):
        from crpt.auth import ApiKeyAuth

        auth = ApiKeyAuth("test-key-123")
        params = auth.get_query_params()
        assert params["apikey"] == "test-key-123"

    def test_token_auth(self):
        from crpt.auth import TokenAuth

        auth = TokenAuth("bearer-token")
        headers = auth.get_headers()
        assert headers["Authorization"] == "Bearer bearer-token"

    def test_no_auth(self):
        from crpt.auth import TokenAuth

        auth = TokenAuth()
        assert auth.get_headers() == {}
