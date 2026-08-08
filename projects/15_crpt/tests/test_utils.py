import pytest
from crpt.utils import parse_datamatrix, parse_receipt_qr, detect_code_type


class TestParseDataMatrix:
    def test_valid_dm(self):
        result = parse_datamatrix("01046300375902232121tZxhYmJdBh")
        assert result is not None
        assert result.gtin == "04630037590223"
        assert result.serial == "21tZxhYmJdBh"

    def test_gs_separator(self):
        result = parse_datamatrix("01046300375902232121tZxhYmJdBh\x1d91ff0d")
        assert result is not None
        assert result.gtin == "04630037590223"

    def test_invalid(self):
        assert parse_datamatrix("hello world") is None
        assert parse_datamatrix("") is None


class TestParseReceipt:
    def test_valid(self):
        r = parse_receipt_qr("t=20231203T2319&s=261.80&fn=7281440701309134&i=10027&fp=3516337491&n=1")
        assert r["t"] == "20231203T2319"
        assert r["s"] == "261.80"
        assert r["fn"] == "7281440701309134"
        assert r["fp"] == "3516337491"


class TestDetectCodeType:
    def test_ean13(self):
        assert detect_code_type("4630037590223") == "ean13"

    def test_datamatrix(self):
        assert detect_code_type("01046300375902232121abc") == "datamatrix"

    def test_qr_receipt(self):
        assert detect_code_type("t=20231203T2319&s=261.80&fn=123") == "qr"

    def test_qr_kiz(self):
        assert detect_code_type("chek.markirovka.nalog.ru/kc/?kiz=RU-430302-AAA") == "qr"
