#!/usr/bin/env python3
"""
Обрезает Остатки.xml с сохранением оригинального форматирования (1С-совместимый XML).
- Все справочники (Склады, ТипыЦен, ЕдиницыИзмерения) — без изменений
- Номенклатура: все группы, элементы — не более N на единицу измерения
"""
import sys, os, re

MAX_PER_UNIT = 2

def trim_xml(src_path, dst_path):
    counts = {}
    stats = {'total': 0, 'kept': 0, 'skipped': 0}
    in_nomenclature = False
    in_element = False
    element_lines = []

    with open(src_path, 'r', encoding='utf-8-sig') as f_src, \
         open(dst_path, 'w', encoding='utf-8') as f_dst:

        for line in f_src:

            if '<Справочник_Номенклатура>' in line:
                in_nomenclature = True
                f_dst.write(line)
                continue
            if '</Справочник_Номенклатура>' in line:
                in_nomenclature = False
                f_dst.write(line)
                continue
            if not in_nomenclature:
                f_dst.write(line)
                continue

            # Inside Номенклатура
            if '<Элемент ' in line:
                in_element = True
                element_lines = [line]
                if '/>' in line:
                    keep = _should_keep(element_lines[0], counts, stats)
                    if keep:
                        f_dst.writelines(element_lines)
                    in_element = False
            elif in_element:
                element_lines.append(line)
                if '</Элемент>' in line:
                    keep = _should_keep(element_lines[0], counts, stats)
                    if keep:
                        f_dst.writelines(element_lines)
                    in_element = False
            else:
                f_dst.write(line)

    print(f"Original: {stats['total']} elements")
    print(f"Kept:     {stats['kept']}")
    print(f"Skipped:  {stats['skipped']}")
    print(f"Units:    {len(counts)}")
    for unit, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        if cnt > 0:
            print(f"  {unit or '(none)'}: {cnt}")
    print(f"File:     {dst_path}")
    print(f"Size:     {os.path.getsize(dst_path) / 1024:.1f} KB")


def _should_keep(first_line, counts, stats):
    if 'ЭтоГруппа="true"' in first_line:
        stats['kept'] += 1
        return True
    stats['total'] += 1
    m = re.search(r'ЕдиницаИзмерения="([^"]*)"', first_line)
    unit = m.group(1).strip() if m else ''
    key = unit or '__none__'
    counts.setdefault(key, 0)
    if counts[key] < MAX_PER_UNIT:
        counts[key] += 1
        stats['kept'] += 1
        return True
    stats['skipped'] += 1
    return False


if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 trim_xml_v2.py <source.xml> <dest.xml> [max_per_unit]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    if len(sys.argv) > 3:
        MAX_PER_UNIT = int(sys.argv[3])
    trim_xml(src, dst)
