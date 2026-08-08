"""Типы и константы ГИС МТ."""

from enum import Enum


class ApiEnv(str, Enum):
    PRODUCTION = "production"
    SANDBOX = "sandbox"


class CodeType(str, Enum):
    DATAMATRIX = "datamatrix"
    EAN13 = "ean13"
    QR = "qr"


# Базовые URL
BASE_URLS: dict[str, dict[str, str]] = {
    ApiEnv.PRODUCTION: {
        "true_api_v3": "https://markirovka.crpt.ru/api/v3/true-api",
        "true_api_v4": "https://markirovka.crpt.ru/api/v4/true-api",
        "nk_api": "https://апи.национальный-каталог.рф",
        "edo": "https://edo-gismt.crpt.ru",
        "mobile": "https://mobile.api.crpt.ru",
    },
    ApiEnv.SANDBOX: {
        "true_api_v3": "https://markirovka.sandbox.crptech.ru/api/v3/true-api",
        "true_api_v4": "https://markirovka.sandbox.crptech.ru/api/v4/true-api",
        "nk_api": "https://api.nk.sandbox.crptech.ru",
        "edo": "https://edo-gismt.sandbox.crptech.ru",
        "mobile": "https://mobile.api.crpt.ru",
    },
}

# Коды товарных групп
PRODUCT_GROUPS: dict[str, str] = {
    "lp": "Лёгкая промышленность",
    "shoes": "Обувные товары",
    "tobacco": "Табачная продукция",
    "perfumery": "Духи и туалетная вода",
    "tires": "Шины и покрышки",
    "water": "Упакованная вода",
    "milk": "Молочная продукция",
    "beer": "Пиво и слабоалкогольные напитки",
    "meat": "Мясные изделия",
    "bicycle": "Велосипеды",
    "wheelchairs": "Кресла-коляски",
    "otp": "Отопительные приборы",
    "electronics": "Радиоэлектронная продукция",
    "seafood": "Морепродукты",
    "vegetable_oils": "Растительные масла",
    "canned": "Консервированная продукция",
    "pet_food": "Корма для животных",
    "cosmetics": "Косметика и бытовая химия",
    "motor_oil": "Моторные масла",
    "fiber_optic": "Оптоволокно",
    "pipes": "Полимерные трубы",
    "building_materials": "Строительные материалы",
    "antiseptics": "Антисептики и дезинфицирующие средства",
    "toys": "Игры и игрушки для детей",
    "photography": "Фотокамеры",
    "sweets": "Сладости и кондитерские изделия",
    "juice": "Соковая продукция и безалкогольные напитки",
    "non_alcohol_beer": "Безалкогольное пиво",
    "tobacco_alternative": "Альтернативная табачная продукция",
    "nicotine": "Никотиносодержащая продукция",
    "cable": "Кабельно-проводниковая продукция",
    "printed": "Печатная продукция",
    "pyro": "Пиротехника и огнетушащее оборудование",
    "fur": "Натуральный мех",
}
