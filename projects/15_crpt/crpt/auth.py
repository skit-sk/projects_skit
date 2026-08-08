"""Базовая аутентификация: API Key, динамический токен, КЭП."""

import os
from typing import Optional, Callable

from crpt.types import ApiEnv, BASE_URLS


class AuthProvider:
    """Базовый провайдер аутентификации."""

    def get_headers(self) -> dict[str, str]:
        return {}

    def get_query_params(self) -> dict[str, str]:
        return {}


class ApiKeyAuth(AuthProvider):
    """Аутентификация через API Key (Национальный каталог)."""

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or os.environ.get("NK_API_KEY", "")

    def get_query_params(self) -> dict[str, str]:
        if self.api_key:
            return {"apikey": self.api_key}
        return {}

    def get_headers(self) -> dict[str, str]:
        return {}


class TokenAuth(AuthProvider):
    """Аутентификация через Bearer-токен (True API)."""

    def __init__(self, token: Optional[str] = None):
        self._token = token

    @property
    def token(self) -> Optional[str]:
        return self._token

    @token.setter
    def token(self, value: str):
        self._token = value

    def get_headers(self) -> dict[str, str]:
        if self._token:
            return {"Authorization": f"Bearer {self._token}"}
        return {}


class DynamicTokenAuth(TokenAuth):
    """Динамический токен через omsConnection — без КЭП."""

    def __init__(
        self,
        oms_connection: Optional[str] = None,
        env: ApiEnv = ApiEnv.SANDBOX,
        signer: Optional[Callable[[str], str]] = None,
    ):
        super().__init__()
        self.oms_connection = oms_connection or os.environ.get("CRPT_OMS_CONNECTION", "")
        self.env = env
        self.signer = signer
        self._auth_key: Optional[dict] = None

    def _get_base_url(self) -> str:
        env_str = self.env.value
        return BASE_URLS[env_str]["true_api_v3"]

    async def authenticate(self, client) -> Optional[str]:
        """Выполнить авторизацию и получить токен.

        Алгоритм:
        1. GET /auth/key → {uuid, data}
        2. Подписать data (нужен signer callback)
        3. POST /auth/simpleSignIn → token
        """
        import httpx

        base = self._get_base_url()

        async with httpx.AsyncClient(timeout=30) as http:
            r_key = await http.get(f"{base}/auth/key")
            r_key.raise_for_status()
            key_data = r_key.json()
            uuid_val = key_data["uuid"]
            data_val = key_data["data"]

            if not self.signer:
                raise RuntimeError(
                    "Для динамического токена нужен signer callback: "
                    "функция, подписывающая data строку и возвращающая base64-подпись"
                )

            signed = self.signer(data_val)

            r_token = await http.post(
                f"{base}/auth/simpleSignIn",
                json={
                    "uuid": uuid_val,
                    "data": signed,
                },
            )
            if r_token.status_code != 200:
                raise RuntimeError(f"Auth failed: {r_token.status_code} {r_token.text}")

            token_resp = r_token.json()
            self._token = token_resp.get("token") or token_resp.get("uuidToken")
            return self._token

    def authenticate_sync(self, client) -> Optional[str]:
        import httpx

        base = self._get_base_url()
        r_key = httpx.get(f"{base}/auth/key", timeout=30)
        r_key.raise_for_status()
        key_data = r_key.json()
        uuid_val = key_data["uuid"]
        data_val = key_data["data"]

        if not self.signer:
            raise RuntimeError(
                "Для динамического токена нужен signer callback"
            )

        signed = self.signer(data_val)
        r_token = httpx.post(
            f"{base}/auth/simpleSignIn",
            json={"uuid": uuid_val, "data": signed},
            timeout=30,
        )
        if r_token.status_code != 200:
            raise RuntimeError(f"Auth failed: {r_token.status_code} {r_token.text}")

        token_resp = r_token.json()
        self._token = token_resp.get("token") or token_resp.get("uuidToken")
        return self._token


class KEPAuth(TokenAuth):
    """Аутентификация через КЭП (ГОСТ-подпись) — на будущее."""

    def __init__(self, cert_path: Optional[str] = None, env: ApiEnv = ApiEnv.SANDBOX):
        super().__init__()
        self.cert_path = cert_path or os.environ.get("CRPT_CERT_PATH", "")
        self.env = env
        self._gost: Optional[object] = None

    def _get_base_url(self) -> str:
        env_str = self.env.value
        return BASE_URLS[env_str]["true_api_v3"]

    async def authenticate(self, client) -> Optional[str]:
        raise NotImplementedError(
            "КЭП-аутентификация будет реализована при наличии сертификата. "
            "Пока используйте DynamicTokenAuth (без КЭП) или ApiKeyAuth (Национальный каталог)."
        )
