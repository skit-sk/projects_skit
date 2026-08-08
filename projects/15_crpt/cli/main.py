"""CLI интерфейс CRPT.

Использование:
    python -m cli.main check <code>              # Проверка кода
    python -m cli.main participant <inn>         # Проверка УОТ
    python -m cli.main product <gtin>            # Инфо о товаре
    python -m cli.main history <cis1,cis2>       # История КИ
    python -m cli.main docs                      # Документы
    python -m cli.main env                       # Инфо об окружении
"""

import argparse
import json
import os
import sys

from dotenv import load_dotenv

load_dotenv()


def cmd_check(args):
    from crpt.mobile_api import MobileCheckClient

    client = MobileCheckClient()
    code = args.code
    ct = args.type or "datamatrix"

    if ct == "receipt":
        result = client.check_receipt(code)
    else:
        result = client.check(code, ct)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_participant(args):
    from crpt.true_api import TrueApiClient

    client = TrueApiClient()
    result = client.get_participants(args.inn)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_mods(args):
    from crpt.true_api import TrueApiClient

    client = TrueApiClient()
    result = client.get_mods_list(inns=args.inn, limit=args.limit)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_product(args):
    token = os.environ.get("CRPT_TOKEN", "")
    from crpt.true_api import TrueApiClient
    from crpt.auth import TokenAuth

    client = TrueApiClient(auth=TokenAuth(token)) if token else TrueApiClient()
    result = client.product_info(args.gtin)
    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_cises(args):
    token = os.environ.get("CRPT_TOKEN", "")
    from crpt.true_api import TrueApiClient
    from crpt.auth import TokenAuth

    cises = [c.strip() for c in args.cises.split(",") if c.strip()]
    client = TrueApiClient(auth=TokenAuth(token)) if token else TrueApiClient()

    if args.history:
        result = client.cises_history(cises)
    elif args.public:
        result = client.cises_public_info(cises)
    else:
        result = client.cises_info(cises) if token else client.cises_public_info(cises)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_documents(args):
    token = os.environ.get("CRPT_TOKEN", "")
    from crpt.true_api import TrueApiClient
    from crpt.auth import TokenAuth

    client = TrueApiClient(auth=TokenAuth(token))

    if args.id:
        if args.cises:
            result = client.document_cises(args.id)
        else:
            result = client.document_info(args.id)
    else:
        result = client.documents_list(limit=args.limit)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_nk(args):
    api_key = os.environ.get("NK_API_KEY", "")
    from crpt.nk_api import NkApiClient

    client = NkApiClient(api_key=api_key)

    if args.gtin:
        result = client.get_product(args.gtin)
    elif args.categories:
        result = client.get_categories()
    elif args.brands:
        result = client.get_brands()
    elif args.countries:
        result = client.get_countries()
    else:
        result = client.get_own_products(limit=args.limit)

    print(json.dumps(result, indent=2, ensure_ascii=False))


def cmd_env(args):
    from crpt.types import BASE_URLS

    print("=== CRPT Environment ===\n")
    for env_name, urls in BASE_URLS.items():
        label = "PRODUCTION" if "production" in env_name else "SANDBOX"
        print(f"[{label}]")
        for k, v in urls.items():
            print(f"  {k}: {v}")
        print()

    print("=== Auth Config ===")
    print(f"  NK_API_KEY: {'✓ set' if os.environ.get('NK_API_KEY') else '✗ not set'}")
    print(f"  CRPT_OMS_CONNECTION: {'✓ set' if os.environ.get('CRPT_OMS_CONNECTION') else '✗ not set'}")
    print(f"  CRPT_TOKEN: {'✓ set' if os.environ.get('CRPT_TOKEN') else '✗ not set'}")


def main():
    parser = argparse.ArgumentParser(description="CRPT — Честный Знак CLI")
    sub = parser.add_subparsers(dest="command")

    # check
    p_check = sub.add_parser("check", help="Проверка кода маркировки")
    p_check.add_argument("code", help="Код (DataMatrix / EAN-13 / QR / receipt-string)")
    p_check.add_argument("-t", "--type", choices=["datamatrix", "ean13", "qr", "receipt"], default="datamatrix")
    p_check.set_defaults(func=cmd_check)

    # participant
    p_part = sub.add_parser("participant", help="Проверка участника по ИНН")
    p_part.add_argument("inn")
    p_part.set_defaults(func=cmd_participant)

    # mods
    p_mods = sub.add_parser("mods", help="Список МОД")
    p_mods.add_argument("--inn", default=None)
    p_mods.add_argument("--limit", type=int, default=100)
    p_mods.set_defaults(func=cmd_mods)

    # product
    p_prod = sub.add_parser("product", help="Информация о товаре по GTIN")
    p_prod.add_argument("gtin")
    p_prod.set_defaults(func=cmd_product)

    # cises
    p_cis = sub.add_parser("cises", help="Информация о кодах идентификации")
    p_cis.add_argument("cises", help="КИ через запятую")
    p_cis.add_argument("--history", action="store_true", help="История движения")
    p_cis.add_argument("--public", action="store_true", help="Только публичная информация")
    p_cis.set_defaults(func=cmd_cises)

    # documents
    p_doc = sub.add_parser("docs", help="Документы")
    p_doc.add_argument("--id", help="ID документа")
    p_doc.add_argument("--cises", action="store_true", help="Список КИ документа")
    p_doc.add_argument("--limit", type=int, default=100)
    p_doc.set_defaults(func=cmd_documents)

    # nk
    p_nk = sub.add_parser("nk", help="Национальный каталог")
    p_nk.add_argument("--gtin", help="GTIN товара")
    p_nk.add_argument("--categories", action="store_true", help="Дерево категорий")
    p_nk.add_argument("--brands", action="store_true", help="Справочник брендов")
    p_nk.add_argument("--countries", action="store_true", help="Справочник стран")
    p_nk.add_argument("--limit", type=int, default=100)
    p_nk.set_defaults(func=cmd_nk)

    # env
    p_env = sub.add_parser("env", help="Информация об окружении")
    p_env.set_defaults(func=cmd_env)

    args = parser.parse_args()
    if not args.command:
        parser.print_help()
        sys.exit(1)

    args.func(args)


if __name__ == "__main__":
    main()
