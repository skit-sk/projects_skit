import pytest
from crpt.models import Participant, CiseInfo, ProductInfo, AuthKey


class TestModels:
    def test_participant(self):
        p = Participant(inn="1234567890", is_registered=True)
        assert p.inn == "1234567890"
        assert p.is_registered is True

    def test_cise_info_defaults(self):
        c = CiseInfo(cis="01046300375902232121abc")
        assert c.cis == "01046300375902232121abc"
        assert c.status == ""
        assert c.childs == []

    def test_product_info(self):
        p = ProductInfo(gtin="04630037590223", name="Test Product")
        assert p.gtin == "04630037590223"
        assert p.name == "Test Product"

    def test_auth_key(self):
        ak = AuthKey(uuid="abc-123", data="random-data")
        assert ak.uuid == "abc-123"
        assert ak.data == "random-data"

    def test_participant_list_fields(self):
        p = Participant(inn="0", is_registered=False, productGroups=["shoes", "lp"])
        assert "shoes" in p.productGroups
        assert "lp" in p.productGroups
