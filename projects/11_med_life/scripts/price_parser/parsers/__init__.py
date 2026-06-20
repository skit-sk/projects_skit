from parsers.megapteka import MegaptekaParser
from parsers.eapteka import EaptekaParser
from parsers.apteka_ru import AptekaRuParser
from parsers.budzdorov import BudzdorovParser

PARSERS = [
    MegaptekaParser(),
    EaptekaParser(),
    AptekaRuParser(),
    BudzdorovParser(),
]


def get_enabled_parsers():
    return [p for p in PARSERS if p.source_id]
