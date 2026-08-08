#!/usr/bin/env python3
"""
Строгая верификация Form.elem.json перед сборкой релиза.
Проверяет целостность структуры 1С-формы, выявляет причины «Ошибка формата потока».

Использование:
  python3 verify_elem_strict.py <Form.elem.json>
  python3 verify_elem_strict.py --build-dir <dir>    # проверяет весь build-каталог
"""
import json
import sys
import os
from collections import Counter


def check(fp):
    errors = []
    warnings = []

    try:
        with open(fp, 'r', encoding='utf-8-sig') as f:
            data = json.load(f)
    except Exception as e:
        return [f"FATAL: не удалось прочитать JSON: {e}"], []

    props = data.get('props', [])
    tree = data.get('tree', [])
    data_entries = data.get('data', {})
    commands = data.get('commands', [])

    # ===== 1. Уникальность name в props (только верхний уровень) =====
    prop_names = [p['name'] for p in props]
    counts = Counter(prop_names)
    for name, cnt in counts.items():
        if cnt > 1:
            errors.append(f"Дубликат name='{name}' в props ({cnt} раз)")

    # ===== 2. Уникальность id в props (только верхний уровень) =====
    prop_ids = [p['id'] for p in props]
    id_counts = Counter(prop_ids)
    for id_, cnt in id_counts.items():
        if cnt > 1:
            errors.append(f"Дубликат id='{id_}' в props ({cnt} раз)")

    # ===== 2b. Уникальность name/id ВНУТРИ каждой таблицы =====
    for p in props:
        children = p.get('child', [])
        if not children:
            continue
        child_names = [c['name'] for c in children]
        child_ncounts = Counter(child_names)
        for name, cnt in child_ncounts.items():
            if cnt > 1:
                errors.append(
                    f"Дубликат name='{name}' в child таблицы '{p['name']}' ({cnt} раз) — ЭТО ВЫЗЫВАЕТ ОШИБКУ ФОРМАТА ПОТОКА"
                )

        child_ids = [c['id'] for c in children]
        child_icounts = Counter(child_ids)
        for id_, cnt in child_icounts.items():
            if cnt > 1:
                errors.append(f"Дубликат id='{id_}' в child таблицы '{p['name']}' ({cnt} раз)")

    # ===== 3. data-ключи ссылаются на существующие tree-элементы =====
    tree_names = set()

    def walk_tree(elem, path=''):
        name = elem.get('name', '')
        full = path + '/' + name if path else name
        tree_names.add(full)
        for c in elem.get('child', []):
            walk_tree(c, full)

    for t in tree:
        walk_tree(t)

    for key in data_entries:
        if key not in tree_names and '/' in key:
            parent_part = '/'.join(key.split('/')[:-1])
            if parent_part in tree_names:
                errors.append(
                    f"data['{key}'] — элемент не найден в tree (родитель '{parent_part}' существует) "
                    f"— битая ссылка, возможна ОШИБКА ФОРМАТА ПОТОКА"
                )

    # ===== 4. Для каждого Field в tree (не Button, не Group без data) — есть data-запись =====
    # Собираем все leaf Field-элементы из tree (не Table, не Group, не Button)
    fields_in_tree = set()

    def walk_tree_fields(elem, path=''):
        name = elem.get('name', '')
        typ = elem.get('type', '')
        full = path + '/' + name if path else name
        # Пропускаем Group, Table (у них свои правила)
        if typ == 'Field':
            fields_in_tree.add(full)
        for c in elem.get('child', []):
            walk_tree_fields(c, full)

    for t in tree:
        walk_tree_fields(t)

    for field_path in sorted(fields_in_tree):
        if field_path not in data_entries:
            warnings.append(
                f"Field '{field_path}' есть в tree, но нет data['{field_path}'] "
                f"— может работать с настройками по умолчанию, но риск ОШИБКИ ФОРМАТА ПОТОКА"
            )

    # ===== 5. raw[12] (data source binding) ссылается на существующий prop ID =====
    for key, entry in data_entries.items():
        if not isinstance(entry, dict):
            continue
        raw = entry.get('raw', [])
        if len(raw) > 12 and isinstance(raw[12], list) and len(raw[12]) >= 2:
            ref_type = raw[12][0]
            ref_ids = raw[12][1] if isinstance(raw[12][1], list) else [raw[12][1]]
            if ref_type == "1":
                for rid in ref_ids:
                    try:
                        rid_int = int(rid)
                        found = any(int(p['id']) == rid_int for p in props)
                        if not found and rid_int >= 100 and rid_int < 1000:
                            errors.append(
                                f"data['{key}'] raw[12] ссылается на prop id={rid_int}, "
                                f"но такого prop нет — Field не привязан к данным, "
                                f"возможна ОШИБКА ФОРМАТА ПОТОКА"
                            )
                    except (ValueError, TypeError):
                        pass

    # ===== 6. Уникальность command id/name =====
    cmd_ids = [c.get('id', '?') for c in commands]
    cmd_counts = Counter(cmd_ids)
    for cid, cnt in cmd_counts.items():
        if cnt > 1:
            errors.append(f"Дубликат command id='{cid}' ({cnt} раз)")

    cmd_names = [c.get('name', '?') for c in commands]
    cmd_name_counts = Counter(cmd_names)
    for cn, cnt in cmd_name_counts.items():
        if cnt > 1:
            errors.append(f"Дубликат command name='{cn}' ({cnt} раз)")

    # ===== 7. raw массивы не содержат None =====
    def check_raw(obj, path=''):
        if isinstance(obj, list):
            for i, item in enumerate(obj):
                check_raw(item, f"{path}[{i}]")
        elif obj is None:
            errors.append(f"None в raw по пути {path} — ОШИБКА ФОРМАТА ПОТОКА")

    for p in props:
        check_raw(p.get('raw', []), f"props['{p['name']}'].raw")
        for c in p.get('child', []):
            check_raw(c.get('raw', []), f"props['{p['name']}'].child['{c['name']}'].raw")
    for key, entry in data_entries.items():
        if not isinstance(entry, dict):
            continue
        check_raw(entry.get('raw', []), f"data['{key}'].raw")

    # ===== 8. ПРОВЕРКА: raw[8] содержит ожидаемый тип поля для number =====
    # Для числовых полей raw[8] должен быть "1" (а не что-то другое)
    for key, entry in data_entries.items():
        if not isinstance(entry, dict):
            continue
        raw = entry.get('raw', [])
        if len(raw) > 12 and isinstance(raw[12], list) and len(raw[12]) >= 2:
            if raw[12][0] == "1":
                ref_prop_id = raw[12][1][0] if isinstance(raw[12][1], list) else raw[12][1]
                try:
                    pid = int(ref_prop_id)
                    for p in props:
                        if int(p['id']) == pid:
                            pattern = p.get('raw', [])[5] if len(p.get('raw', [])) > 5 else None
                            if pattern and 'N' in str(pattern) and len(raw) > 8:
                                if raw[8] not in ("1", 1):
                                    warnings.append(
                                        f"data['{key}']: prop id={pid} число, но raw[8]={raw[8]} "
                                        f"(ожидается 1 для поля ввода)"
                                    )
                            break
                except (ValueError, TypeError, IndexError):
                    pass

    return errors, warnings


def check_build_dir(build_dir):
    """Проверить весь build-каталог: Form.elem.json + Form.obj.bsl + ExternalDataProcessor.json."""
    errors = []
    warnings = []
    form_elem = os.path.join(build_dir, 'Form', 'Форма', 'Form.elem.json')
    form_bsl = os.path.join(build_dir, 'Form', 'Форма', 'Form.obj.bsl')
    edp_json = os.path.join(build_dir, 'ExternalDataProcessor.json')

    for fp in [form_elem, form_bsl, edp_json]:
        if not os.path.isfile(fp):
            errors.append(f"Файл не найден: {fp}")

    # Проверка Form.elem.json
    if os.path.isfile(form_elem):
        e, w = check(form_elem)
        errors.extend(e)
        warnings.extend(w)

    # Проверка, что ExternalDataProcessor.json ссылается на правильную форму
    if os.path.isfile(edp_json):
        try:
            with open(edp_json, 'r', encoding='utf-8-sig') as f:
                edp = json.load(f)
            form_ref = edp.get('form1')
            if form_ref is None:
                warnings.append("ExternalDataProcessor.json: form1=null — форма может не открыться")
        except Exception as e:
            errors.append(f"Ошибка чтения ExternalDataProcessor.json: {e}")

    return errors, warnings


def main():
    if len(sys.argv) < 2:
        print("Использование:")
        print("  python3 verify_elem_strict.py <Form.elem.json>")
        print("  python3 verify_elem_strict.py --build-dir <build_dir>")
        sys.exit(1)

    fp = sys.argv[1]

    if fp == '--build-dir' and len(sys.argv) > 2:
        build_dir = sys.argv[2]
        errors, warnings = check_build_dir(build_dir)
        print("=" * 60)
        print(f"  Build-dir верификация: {build_dir}")
        print("=" * 60)
    else:
        errors, warnings = check(fp)
        print("=" * 60)
        print(f"  Верификация: {fp}")
        print("=" * 60)

    if errors:
        print(f"\n  ❌ ОШИБКИ ({len(errors)}):")
        for e in errors:
            print(f"    ✗ {e}")
        print(f"\n  ИТОГО: {len(errors)} ошибок, {len(warnings)} предупреждений")
        sys.exit(2)
    else:
        if warnings:
            print(f"\n  ⚠️  ПРЕДУПРЕЖДЕНИЯ ({len(warnings)}):")
            for w in warnings:
                print(f"    △ {w}")
        print(f"\n  ✅ Все проверки пройдены (предупреждений: {len(warnings)})")
        sys.exit(0 if not warnings else 3)


if __name__ == '__main__':
    main()
