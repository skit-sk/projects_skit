#!/usr/bin/env python3
"""
Верификатор собранных .epf (1С 8.3) — проверяет, что патчи применились.

Использование:
    python3 verify_epf.py <epf1.epf> <epf2.epf> [остатки.xml]

    Если передан XML остатков — дополнительно прогоняет его через parse_stocks.py.

Что проверяет:
  1. Сигнатуру контейнера 1С 8.3 (\\xff\\xff\\xff\\x7f)
  2. Распаковывает через v8unpack -E во временный каталог
  3. Проверяет наличие ключевых функций/процедур/атрибутов:
     - epf1 (выгрузка):
         * ЗаписатьСправочникКонтрагентов
         * ПолучитьДанныеКонтрагентов
         * ТаблицаКонтрагентов
         * "Код" в ЗаписатьСправочникТиповЦен (исправление бага)
         * ИЕРАРХИЯ в запросе номенклатуры
     - epf2 (загрузчик):
         * ПолучитьСоответствиеКодовЦен
         * Повторная обработка группы (Шаг 1.5)
         * ВисящиеГруппы
         * 6 новых видов цен: 2 Монтажники, 3 Колонка, 4 Колонка,
           5 Розничная, Закупочная+5, Розничная +10%
  4. Опционально: парсит XML остатков (если передан)
"""
import sys
import os
import re
import json
import shutil
import subprocess
import tempfile
import time
from pathlib import Path


# Ожидаемые признаки для каждой обработки
EPF1_CHECKS = [
    ("ЗаписатьСправочникКонтрагентов",  "процедура записи контрагентов"),
    ("ПолучитьДанныеКонтрагентов",      "функция получения контрагентов"),
    ("ТаблицаКонтрагентов",             "переменная таблицы контрагентов"),
    ('"Код", Строка(Строка.Код)',       "атрибут Код в типах цен (исправление)"),
    ("ИЕРАРХИЯ",                        "иерархическая сортировка"),
    ("ЗаписатьСправочникНоменклатуры",  "процедура записи номенклатуры"),
    ("Себестоимость",                   "выгрузка себестоимости"),
]

EPF2_CHECKS = [
    ("ПолучитьСоответствиеКодовЦен",    "функция маппинга кодов цен (fallback)"),
    ("СоответствиеКодовИНаименованийЦен", "v1.76: парсинг (Код → Наименование)"),
    ("МассивВидовЦен",                  "v1.76: массив видов цен для цикла"),
    ("ВнутриСправочникТипыЦен",         "v1.76: флаг секции типов цен"),
    ("ВнутриЭлементаТипаЦен",           "v1.76: флаг элемента типа цен"),
    ("СоответствиеGUIDИНаименованийЦен", "v1.76: связка GUID→наименование"),
    ("КодДляПоиска = КодИзXML",         "v1.76: логика префикса УТ"),
    ("ВисящиеГруппы",                   "v1.75: счётчик висящих групп"),
    ("СоздатьГруппуНоменклатуры",       "функция создания групп"),
    ("СоздатьНоменклатуруНаСервере",    "основная функция создания"),
    ("ВводОстатков",                    "документ ввода остатков"),
    ("УстановкаЦен",                    "документ установки цен"),
    ("Стратегия \"идентичные наименования\"", "v1.76: стратегия"),
    ("КэшСуществующейНоменклатуры",     "v1.78: кеш существующей номенклатуры"),
    ("КэшЕдиниц",                       "v1.78: кеш единиц измерения"),
    ("КэшВидовНоменклатуры",            "v1.78: кеш видов номенклатуры"),
    ("КэшСтавокНДС",                    "v1.78: кеш ставок НДС"),
    ("НачатьТранзакцию",                "v1.78: батчевая транзакция"),
    ("ЗафиксироватьТранзакцию",         "v1.78: фиксация транзакции"),
    ("РазмерБатча = 500",               "v1.78: размер батча"),
    ("ПолучитьСтавкуНДСИзКеша",         "v1.78: оптимизированная ставка НДС"),
    ("Состояние(\"Создание номенклатуры\"", "v1.78: прогресс-бар"),
    ("КэшВидовЦен",                     "v1.79: кеш видов цен (СоздатьУстановкуЦен)"),
    ("СформироватьОтчетОЗагрузке",      "v1.79: функция сводного отчёта"),
    ("LOAD_REPORT_",                    "v1.79: шаблон имени файла отчёта"),
    ("СтатНоменклатураСоздано",         "v1.79: статистика номенклатуры"),
    ("СтатОстаткиСтрок",                "v1.79: статистика остатков"),
    ("СтатЦеныСтрок",                   "v1.79: статистика цен"),
    ("СтатXMLИмяФайла",                 "v1.79: имя XML в отчёте"),
]

EPF1_8_SIGNATURE = b"\xff\xff\xff\x7f"


def die(msg, code=1):
    print(f"!!! {msg}", file=sys.stderr)
    sys.exit(code)


def find_files(root, suffix):
    """Найти все файлы с указанным суффиксом под root."""
    return [str(p) for p in Path(root).rglob(f"*{suffix}") if p.is_file()]


def find_bsl_files(root):
    """Все .bsl файлы (модули объектов и форм)."""
    return find_files(root, ".bsl")


def find_json_files(root):
    return find_files(root, ".json")


def check_signature(epf_path):
    """Сигнатура 1С 8.3 = \\xff\\xff\\xff\\x7f в первых 4 байтах."""
    with open(epf_path, "rb") as f:
        head = f.read(4)
    return head == EPF1_8_SIGNATURE, head


def find_v8unpack():
    """Путь к v8unpack. Приоритет: venv/bin/v8unpack > PATH."""
    # Проверим venv от workspace
    candidates = [
        "/home/user_aioc/workspace/venv/bin/v8unpack",
        shutil.which("v8unpack"),
    ]
    for c in candidates:
        if c and os.path.isfile(c):
            return c
    return None


def unpack_epf(epf_path, dest_dir, v8unpack_bin):
    """Распаковать .epf через v8unpack -E. Возвращает (ok, stderr)."""
    try:
        result = subprocess.run(
            [v8unpack_bin, "-E", epf_path, dest_dir],
            capture_output=True, text=True, timeout=60
        )
        if result.returncode != 0:
            return False, result.stderr
        return True, ""
    except subprocess.TimeoutExpired:
        return False, "timeout"
    except Exception as e:
        return False, str(e)


def search_in_bsl(bsl_files, pattern):
    """Найти pattern (substring) в .bsl файлах. Возвращает список (file, count)."""
    hits = []
    for fp in bsl_files:
        try:
            with open(fp, "r", encoding="utf-8-sig") as f:
                content = f.read()
            cnt = content.count(pattern)
            if cnt > 0:
                hits.append((fp, cnt))
        except Exception:
            pass
    return hits


def parse_external_data_processor(json_files):
    """Найти и распарсить ExternalDataProcessor.json, вернуть dict или None."""
    for fp in json_files:
        if "ExternalDataProcessor.json" in fp:
            try:
                with open(fp, "r", encoding="utf-8-sig") as f:
                    return json.load(f), fp
            except Exception:
                return None, fp
    return None, None


def parse_metadata(json_files):
    """Найти Form/*.json файлы, вернуть список имён элементов формы (если есть)."""
    forms = []
    for fp in json_files:
        if "/Form/" in fp and fp.endswith(".json"):
            try:
                with open(fp, "r", encoding="utf-8-sig") as f:
                    data = json.load(f)
                if isinstance(data, dict) and "title" in data:
                    forms.append((fp, data.get("title", {})))
            except Exception:
                pass
    return forms


def run_parse_stocks(xml_path, work_dir):
    """Запустить parse_stocks.py (если найден) на xml. Возвращает (ok, summary)."""
    parser = os.path.join(os.path.dirname(os.path.abspath(__file__)), "parse_stocks.py")
    if not os.path.isfile(parser):
        return False, f"parse_stocks.py не найден рядом: {parser}"
    try:
        result = subprocess.run(
            [sys.executable, parser, xml_path],
            capture_output=True, text=True, timeout=120
        )
        if result.returncode != 0:
            return False, result.stderr or result.stdout
        # Возьмём последние 5 строк как summary
        lines = [l for l in result.stdout.split("\n") if l.strip()]
        return True, "\n".join(lines[-5:])
    except subprocess.TimeoutExpired:
        return False, "parse_stocks.py: timeout"
    except Exception as e:
        return False, str(e)


def verify_epf(epf_path, checks, work_subdir, v8unpack_bin):
    """Проверить один .epf. Возвращает dict с результатами."""
    results = {
        "path": epf_path,
        "name": os.path.basename(epf_path),
        "size": os.path.getsize(epf_path),
        "signature_ok": False,
        "signature_hex": "",
        "unpack_ok": False,
        "metadata": {},
        "checks": [],   # список (label, ok, details)
        "summary": {"passed": 0, "failed": 0, "skipped": 0},
    }

    # 1. Сигнатура
    sig_ok, head = check_signature(epf_path)
    results["signature_ok"] = sig_ok
    results["signature_hex"] = head.hex(" ")

    # 2. Распаковка
    dest = os.path.join(work_subdir, "unpack")
    os.makedirs(dest, exist_ok=True)
    ok, err = unpack_epf(epf_path, dest, v8unpack_bin)
    results["unpack_ok"] = ok
    if not ok:
        results["checks"].append(("Распаковка через v8unpack", False, err[:200]))
        results["summary"]["failed"] += 1
        return results

    # 3. Метаданные
    json_files = find_json_files(dest)
    edp, edp_path = parse_external_data_processor(json_files)
    if edp:
        results["metadata"] = {
            "name":  edp.get("name", "?"),
            "name2": (edp.get("name2") or {}).get("ru", "?"),
            "uuid":  edp.get("uuid", "?"),
        }

    # 4. Проверки по паттернам
    bsl_files = find_bsl_files(dest)
    all_bsl_content = ""
    for fp in bsl_files:
        try:
            with open(fp, "r", encoding="utf-8-sig") as f:
                all_bsl_content += "\n" + f.read()
        except Exception:
            pass

    for pattern, label in checks:
        cnt = all_bsl_content.count(pattern)
        ok = cnt > 0
        results["checks"].append((label, ok, f"{cnt} вхождений" if ok else "не найдено"))
        if ok:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1

    return results


def print_section(title):
    print()
    print("=" * 72)
    print(f"  {title}")
    print("=" * 72)


def print_results(results):
    name = results["name"]
    print(f"  Файл:        {name}")
    print(f"  Путь:        {results['path']}")
    print(f"  Размер:      {results['size']:,} байт ({results['size']/1024:.1f} КБ)")
    sig_mark = "OK" if results["signature_ok"] else "FAIL"
    print(f"  Сигнатура:   {sig_mark}  ({results['signature_hex']})")
    unp_mark = "OK" if results["unpack_ok"] else "FAIL"
    print(f"  Распаковка:  {unp_mark}")
    md = results["metadata"]
    if md:
        print(f"  Имя:         {md.get('name','?')}")
        print(f"  Синоним:     {md.get('name2','?')}")
        print(f"  UUID:        {md.get('uuid','?')}")
    print()
    print(f"  Проверки паттернов ({results['summary']['passed']} ✓ / {results['summary']['failed']} ✗):")
    for label, ok, details in results["checks"]:
        mark = "✓" if ok else "✗"
        print(f"    [{mark}] {label}  ({details})")


def main():
    if len(sys.argv) < 3:
        print("Использование:")
        print("  python3 verify_epf.py <epf1.epf> <epf2.epf> [остатки.xml]")
        print()
        print("Аргументы:")
        print("  epf1.epf     — выгрузка из УТ 10.3 (должна быть первой)")
        print("  epf2.epf     — загрузчик в УТ 11.5 (должна быть второй)")
        print("  остатки.xml  — (опц.) XML остатков для дополнительной проверки")
        sys.exit(1)

    epf1 = sys.argv[1]
    epf2 = sys.argv[2]
    xml_path = sys.argv[3] if len(sys.argv) > 3 else None

    if not os.path.isfile(epf1):
        die(f"Файл не найден: {epf1}")
    if not os.path.isfile(epf2):
        die(f"Файл не найден: {epf2}")
    if xml_path and not os.path.isfile(xml_path):
        die(f"XML не найден: {xml_path}")

    v8unpack_bin = find_v8unpack()
    if not v8unpack_bin:
        die("v8unpack не найден. Установите: pip install v8unpack")

    work_dir = tempfile.mkdtemp(prefix="verify_epf_")
    print(f"Рабочая папка: {work_dir}")
    print(f"v8unpack:      {v8unpack_bin}")

    t0 = time.time()
    r1 = verify_epf(epf1, EPF1_CHECKS, os.path.join(work_dir, "epf1"), v8unpack_bin)
    r2 = verify_epf(epf2, EPF2_CHECKS, os.path.join(work_dir, "epf2"), v8unpack_bin)
    dt = time.time() - t0

    print_section("EPF #1 (выгрузка из УТ 10.3)")
    print_results(r1)
    print_section("EPF #2 (загрузчик в УТ 11.5)")
    print_results(r2)

    if xml_path:
        print_section("ПАРСЕР XML ОСТАТКОВ")
        ok, summary = run_parse_stocks(xml_path, work_dir)
        mark = "OK" if ok else "FAIL"
        print(f"  Файл:    {xml_path}")
        print(f"  Статус:  {mark}")
        if ok:
            print(f"  Итог (последние 5 строк):")
            for line in summary.split("\n"):
                print(f"    {line}")
        else:
            print(f"  Ошибка:  {summary[:300]}")

    print_section("ИТОГ")
    total_passed = r1["summary"]["passed"] + r2["summary"]["passed"]
    total_failed = r1["summary"]["failed"] + r2["summary"]["failed"]
    print(f"  Всего проверок:  {total_passed + total_failed}")
    print(f"  Пройдено:        {total_passed} ✓")
    print(f"  Провалено:       {total_failed} ✗")
    print(f"  Время:           {dt:.2f} сек")

    if total_failed == 0:
        print()
        print("  ✅ Все патчи применились. Можно открывать в 1С.")
    else:
        print()
        print("  ❌ Есть провалы. См. детали выше.")

    # Очистка временного каталога
    try:
        shutil.rmtree(work_dir)
    except Exception:
        pass

    sys.exit(0 if total_failed == 0 else 2)


if __name__ == "__main__":
    main()
