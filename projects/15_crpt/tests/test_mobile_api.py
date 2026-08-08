import pytest
from crpt.mobile_api import MobileCheckClient
from crpt.types import CodeType


class TestMobileCheckClient:
    def test_init(self):
        client = MobileCheckClient()
        assert client is not None

    def test_check_datamatrix_mock(self, monkeypatch):
        def mock_get(self, path, params=None, headers=None):
            return {"status": 0, "gtin": "04630037590223"}

        monkeypatch.setattr("crpt.client.HttpClient.get", mock_get)

        client = MobileCheckClient()
        result = client.check_datamatrix("01046300375902232121abc")
        assert result["gtin"] == "04630037590223"

    def test_check_ean13_mock(self, monkeypatch):
        def mock_get(self, path, params=None, headers=None):
            assert params["codeType"] == "ean13"
            return {"status": 0}

        monkeypatch.setattr("crpt.client.HttpClient.get", mock_get)

        client = MobileCheckClient()
        result = client.check_ean13("4630037590223")
        assert result["status"] == 0
