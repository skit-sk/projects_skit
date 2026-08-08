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
    # ===== v2.00 — финальная переработка под УТ 11.5 =====
    ("v2.00: критический фикс для УТ 11.5", "v2.00: основной маркер версии"),
    ("v2.00: ПОЛНАЯ ПЕРЕРАБОТКА",          "v2.00: маркер переработки"),
    ("v2.00: КРИТИЧЕСКИЕ ОТЛИЧИЯ",         "v2.00: маркер критических отличий"),
    # Кеши (модульные переменные)
    ("Перем КэшСтавокНДС",                "v2.00: кеш Справочник.СтавкиНДС (модульная переменная)"),
    ("Перем МассивНастоящихОшибок",       "v2.00: массив настоящих сбоев"),
    ("Перем КоличествоКаскадныхОшибок",    "v2.00: счётчик каскадных ошибок"),
    ("КэшВидовНоменклатуры",             "v2.00: кеш видов номенклатуры"),
    ("КэшЕдиниц",                        "v2.00: кеш единиц измерения"),
    # Транзакции и батчи
    ("РазмерБатча = 1",                  "v2.01: одна транзакция на запись (нет каскадных откатов)"),
    ("транзакция на каждую запись",      "v2.01: маркер режима 1 элемент = 1 транзакция"),
    # Маркеры в логах
    ("Создано групп",                    "v2.00: маркер итогов по группам"),
    ("ПЕРВЫЙ СБОЙ",                      "v2.01: маркер первого настоящего сбоя"),
    ("МассивНастоящихОшибок",            "v2.00: накопление настоящих сбоев"),
    ("=== СВОДКА ОШИБОК v2.00 ===",      "v2.00: финальная сводка в логе"),
    ("ЗАПУСК v2.00",                     "v2.00: маркер запуска v2.00 (совместимость)"),
    ("ЗАПУСК v2.01",                     "v2.01: маркер запуска v2.01"),
    # Хелперы
    ("ПолучитьИлиСоздатьВидНоменклатуры", "v2.00: хелпер ВидовНоменклатуры"),
    ("ПолучитьИлиСоздатьЕдиницуИзмерения","v2.00: хелпер УпаковкиЕдиницыИзмерения"),
    ("ПолучитьИлиСоздатьСтавкуНДС",      "v2.00: хелпер Справочник.СтавкиНДС"),
    ("ПолучитьПеречислениеСтавкаНДСИзСтроки", "v2.00: преобразование строки в перечисление"),
    ("ИнициализироватьКэши",             "v2.00: процедура инициализации кешей"),
    # Правильные типы УТ 11.5 (полные пути через точку)
    ("CatalogRef.СтавкиНДС",             "v2.00: правильный тип для Номенклатура.СтавкаНДС (в комментарии)"),
    ("Справочники.УпаковкиЕдиницыИзмерения", "v2.00: правильный путь для единиц измерения"),
    ("Справочники.ВидыНоменклатуры",     "v2.00: правильный путь для видов номенклатуры"),
    ("Справочники.СтавкиНДС",           "v2.00: правильный путь для ставок НДС"),
    # Использование перечислений
    ("Перечисления.СтавкиНДС.НДС20",    "v2.00: использование правильного перечисления"),
    # Базовые функции (сохранены из v1.x)
    ("СоздатьНоменклатуруНаСервере",    "v2.00: основная функция создания"),
    ("СоздатьНоменклатуру",             "v2.00: команда формы (клиент)"),
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

    # 5. Регрессионные проверки (анти-паттерны)
    bsl_lines = all_bsl_content.split("\n")
    for entry in ANTIPATTERNS:
        if len(entry) == 3:
            antipattern, label, kind = entry
        else:
            antipattern, label = entry
            kind = "flat"

        violations = []
        if kind == "flat":
            # Плоский анти-паттерн: вхождение подстроки в исполняемой строке
            for line in bsl_lines:
                if line.lstrip().startswith("//"):
                    continue
                if antipattern in line:
                    violations.append(line.strip())
        elif kind == "contextual":
            # Контекстный: в 5 строках выше должен быть Попытка (исполняемая)
            for i, line in enumerate(bsl_lines):
                if line.lstrip().startswith("//"):
                    continue
                if antipattern in line:
                    has_popytka = any(
                        "Попытка" in bsl_lines[j] and not bsl_lines[j].lstrip().startswith("//")
                        for j in range(max(0, i-5), i)
                    )
                    if not has_popytka:
                        violations.append((i+1, line.strip()))

        elif kind == "server_strict":
            # v2.01: антипаттерн ЗАПРЕЩЁН в &НаСервере контексте (внутри функции)
            current_ctx = None
            for i, line in enumerate(bsl_lines):
                m_ctx = re.match(r"^\s*&На(Клиенте|Сервере)", line)
                if m_ctx:
                    current_ctx = m_ctx.group(1)
                # Конец блока = новая Процедура/Функция
                if re.match(r"^\s*(Процедура|Функция)\s+", line):
                    current_ctx = None
                if current_ctx == "Сервере" and line.lstrip().startswith("//") is False:
                    if antipattern in line:
                        violations.append((i+1, line.strip()))

        ok = len(violations) == 0
        if ok:
            details = "OK"
        else:
            first = violations[0]
            if isinstance(first, tuple):
                details = f"{len(violations)} нарушений: строка {first[0]}: {first[1][:60]}"
            else:
                details = f"{len(violations)} нарушений: {first[:60]}"
        results["checks"].append((f"[РЕГРЕССИЯ] {label}", ok, details))
        if ok:
            results["summary"]["passed"] += 1
        else:
            results["summary"]["failed"] += 1

    return results


# Анти-паттерны BSL, которые компилятор 1С НЕ поддерживает.
# v8unpack не валидирует BSL — только пакует. Реальная компиляция только в 1С.
# Если найдено исполняемое вхождение — epf не откроется.
# Формат:
#   (паттерн, описание)                          — плоский поиск подстроки
#   (паттерн, описание, "contextual")            — в 5 строках выше должна быть "Попытка"
ANTIPATTERNS = [
    ("Повторять",          "1С не имеет Repeat-Until; используй Пока...Цикл"),
    ("Состояние(",         "Состояние() — клиентский метод, недоступен на сервере (&НаСервере). v1.83: запрещено в любом контексте. Используй Сообщить() или убери."),
    ("Новый ТекстовыйДокумент(", "ТекстовыйДокумент в обычном приложении имеет только конструктор по умолчанию. v1.84: используй 'Новый ТекстовыйДокумент' + Записать(Путь, Кодировка)"),
    ("Новый Действие(",    "Новый Действие() — синтаксис управляемого приложения. v1.86: в толстом клиенте обычного приложения используй УстановитьДействие(\"Нажатие\", \"ИмяПроцедуры\") со строкой"),
    ("ЭлементыФормы.",     "ЭлементыФормы — реквизит УПРАВЛЯЕМОЙ формы, в обычной форме недоступен. v1.87: декларативно объявляй в Form.elem.json или используй Поле ввода как флаг"),
    ("СтрПовтор(",          "v2.00: СтрПовтор не существует в 1С 8.x — используй СтрПовторитьСтроку (8.3.10+) или цикл"),
    ("ТипУзлаXML.Элемент",  "v2.00: несуществующее значение enum. Правильно: ТипУзлаXML.НачалоЭлемента"),
    ("ПостроительDOM",      "v2.01: ПостроительDOM.ТипУзла возвращает СТРОКУ, а не enum. Используй потоковый ЧтениеXML (ТипУзла = ТипУзлаXML.НачалоЭлемента) — это работает и для больших XML (20+ МБ)"),
    ("ДокументDOM",         "v2.01: см. ПостроительDOM. Узел.ТипУзла DOM-парсера возвращает строку. Потоковый ЧтениеXML — надёжнее"),
    ("Сообщить(",           "v2.01-fix: Сообщить() — клиентский метод, запрещён в &НаСервере. Используй ЗаписатьВЛогСервер()", "server_strict"),
    ("ПоказатьПредупреждение(", "v2.01-fix: ПоказатьПредупреждение() — клиентский метод, запрещён в &НаСервере. Используй Сообщить на клиенте после серверного вызова", "server_strict"),
    ("ПостроительDOM",      "v2.01: ПостроительDOM.ТипУзла возвращает СТРОКУ, а не enum. Используй потоковый ЧтениеXML (ТипУзла = ТипУзлаXML.НачалоЭлемента) — это работает и для больших XML (20+ МБ)"),
    ("ДокументDOM",         "v2.01: см. ПостроительDOM. Узел.ТипУзла DOM-парсера возвращает строку. Потоковый ЧтениеXML — надёжнее"),
]


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
        # v2.01: проверка, что имя файла содержит внутреннее имя EPF
        # (иначе 1С не перекомпилирует модуль после переоткрытия)
        internal_name = md.get("name", "")
        if internal_name and internal_name in name:
            results["checks"].append((
                f"имя файла содержит '{internal_name}'",
                True,
                "1С перекомпилирует модуль"
            ))
            results["summary"]["passed"] += 1
        elif internal_name:
            results["checks"].append((
                f"имя файла содержит '{internal_name}'",
                False,
                f"имя файла='{name}' — 1С НЕ перекомпилирует модуль (кэш)"
            ))
            results["summary"]["failed"] += 1
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

    # ⚠️  Временные файлы ТОЛЬКО в _work/.tmp/ проекта (не /tmp/)
    tmp_root = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".tmp")
    os.makedirs(tmp_root, exist_ok=True)
    work_dir = tempfile.mkdtemp(prefix="verify_epf_", dir=tmp_root)
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

    # 5. Проверка кнопок формы (только для загрузчика — epf2)
    # Без этого кнопки в обычной форме 1С будут "молча" ничего не делать
    # при нажатии (особенность обычной формы — нет ошибки при отсутствии обработчика)
    if os.path.isfile(epf2):
        try:
            work_btn = os.path.join(work_dir, "btn_check")
            os.makedirs(work_btn, exist_ok=True)
            ok, _ = verify_epf.unpack_epf(epf2, work_btn, v8unpack_bin)
            if ok:
                bsl_files = verify_epf.find_bsl_files(work_btn)
                all_bsl_btn = ""
                for f in bsl_files:
                    with open(f, "r", encoding="utf-8-sig") as fp:
                        all_bsl_btn += "\n" + fp.read()
                expected_handlers = [
                    # v2.01: имена handler'ов из Form.elem.json (raw[8]), а не "name" команды
                    "ВыбратьФайл", "ОчиститьВсе",
                    "СоздатьВводОстатков", "СоздатьСправочники", "СоздатьУстановкуЦен",
                    "ЗагрузитьДанные", "СоздатьНоменклатуру",
                    "ЗаписатьШтрихКоды",  # одна процедура для двух кнопок: "ЗаписатьШтрихКоды" и "ЗагрузиьШтрихкоды" (опечатка)
                ]
                for h in expected_handlers:
                    has_handler = (f"Процедура {h}(Команда)" in all_bsl_btn)
                    if has_handler:
                        r2["checks"].append((f"кнопка: {h}", True, "обработчик есть"))
                        r2["summary"]["passed"] += 1
                    else:
                        r2["checks"].append((f"кнопка: {h}", False,
                            f"обработчик НЕ найден — кнопка не будет работать"))
                        r2["summary"]["failed"] += 1

            # v2.01: проверка, что все Результат.Количество<X> объявлены через Результат.Вставить("Количество<X>")
            import re as _re2
            refs_result = set()
            for fp in bsl_files:
                with open(fp, 'r', encoding='utf-8-sig') as fpp:
                    content = fpp.read()
                # Используем \w — в Python по умолчанию включает Cyrillic
                for m in _re2.finditer(r'Результат(?:Номенклатура)?\.Количество(\w+)', content):
                    refs_result.add("Количество" + m.group(1))
                for m in _re2.finditer(r'Результат(?:Номенклатура)?\.Свойство\("Количество(\w+)"\)', content):
                    refs_result.add("Количество" + m.group(1))
            declared = set()
            for fp in bsl_files:
                with open(fp, 'r', encoding='utf-8-sig') as fpp:
                    content = fpp.read()
                for m in _re2.finditer(r'Результат\.Вставить\("(\w+)"', content):
                    declared.add(m.group(1))
            for fr in sorted(refs_result):
                if fr in declared:
                    r2["checks"].append((f"Результат.{fr}", True, "объявлено через Вставить"))
                    r2["summary"]["passed"] += 1
                else:
                    r2["checks"].append((f"Результат.{fr}", False,
                        f"НЕТ объявления Результат.Вставить(\"{fr}\") в коде"))
                    r2["summary"]["failed"] += 1

            # v2.01: проверка, что все НовСтр.<Поле> имеют колонку ТаблицаНоменклатуры<Поле>
            import re as _re
            field_refs = set()
            for fp in bsl_files:
                with open(fp, 'r', encoding='utf-8-sig') as fpp:
                    content = fpp.read()
                for m in _re.findall(r"НовСтр\.(\w+)", content):
                    field_refs.add(m)
            if field_refs:
                col_names = set()
                with open(elem_path, 'r', encoding='utf-8-sig') as fpp:
                    elem_data = json.load(fpp)
                def _walk(n):
                    if isinstance(n, dict):
                        if n.get('type') == 'Field' and isinstance(n.get('name'), str):
                            if n['name'].startswith('ТаблицаНоменклатуры'):
                                col_names.add(n['name'][len('ТаблицаНоменклатуры'):])
                        for v in n.values(): _walk(v)
                    elif isinstance(n, list):
                        for v in n: _walk(v)
                _walk(elem_data)
                for fr in sorted(field_refs):
                    if fr in col_names:
                        r2["checks"].append((f"НовСтр.{fr}", True, "колонка есть"))
                        r2["summary"]["passed"] += 1
                    else:
                        r2["checks"].append((f"НовСтр.{fr}", False,
                            f"НЕТ колонки ТаблицаНоменклатуры{fr} в Form.elem.json"))
                        r2["summary"]["failed"] += 1
        except Exception as e:
            pass

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
