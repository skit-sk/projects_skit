"""Universal OFD API client — supports all auth types and HTTP methods."""

import json
import os
import urllib.request


class OfdApiClient:
    def __init__(self, provider_config: dict, token: str = ""):
        self.base_url = provider_config.get("base_url", "").rstrip("/")
        self.auth_type = provider_config.get("auth_type", "")
        env_token_name = provider_config.get("env_token", "")
        self.token = token or os.environ.get(env_token_name, "")

    def call(self, method_path: str, http_method: str = "GET", params: dict = None):
        if params is None:
            params = {}

        # 1. Build URL with path params and auth
        url, query_params = self._build_url(method_path, params)

        # 2. Prepare request
        body = None
        headers = {}

        if self.auth_type == "bearer_token" and self.token:
            headers["Ofdapitoken"] = self.token

        if http_method in ("POST", "PUT"):
            headers["Content-Type"] = "application/json"
            body = json.dumps(query_params).encode()
        elif http_method == "DELETE":
            body = json.dumps(query_params).encode() if query_params else None

        # Auth as query param (for api_key_query type or as fallback)
        if self.auth_type == "api_key_query" and self.token:
            sep = "&" if "?" in url else "?"
            url = f"{url}{sep}AuthToken={self.token}"

        try:
            req = urllib.request.Request(url, data=body, headers=headers, method=http_method)
            with urllib.request.urlopen(req, timeout=30) as r:
                return json.loads(r.read())
        except urllib.request.HTTPError as e:
            body_text = e.read().decode(errors="replace")[:500]
            return {"error": f"HTTP {e.code}: {e.reason}", "body": body_text, "url": url}
        except (urllib.request.URLError, TimeoutError, OSError) as e:
            return {"error": str(e), "url": url}
        except json.JSONDecodeError as e:
            return {"error": f"JSON parse: {e}", "url": url}

    def _build_url(self, method_path: str, params: dict) -> tuple:
        """Substitute URL params like {INN}, {KKT}, {id} and separate body params."""
        path = method_path.lstrip("/")
        url_params = {}
        body_params = dict(params)

        # Find and replace {param} placeholders in path
        import re
        placeholders = re.findall(r"\{(\w+)\}", path)
        for ph in placeholders:
            val = body_params.pop(ph, None)
            if val is not None:
                path = path.replace("{" + ph + "}", str(val))
                url_params[ph] = val

        # Build full URL
        url = f"{self.base_url}/{path}"

        # For GET/DELETE, put remaining params into query string
        query_parts = []
        qp_names = [k for k in body_params if k != "AuthToken"]
        for k in qp_names:
            v = body_params[k]
            if v is not None and v != "":
                query_parts.append(f"{k}={urllib.request.quote(str(v))}")
        if query_parts:
            url += "?" + "&".join(query_parts)

        # Return remaining body params (for POST/PUT) as the query dict
        remaining = {k: v for k, v in body_params.items() if k not in qp_names and k != "AuthToken"}
        return url, remaining
