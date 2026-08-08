#!/usr/bin/env python3
"""
Обрезает Остатки.xml до минимального тестового набора:
  - Все справочники (Склады, ТипыЦен, ЕдиницыИзмерения) — полностью
  - Номенклатура: все группы, элементы — не более 5 на единицу измерения
"""
import sys
import os
from xml.parsers import expat

MAX_PER_UNIT = 5

def trim_xml(src_path, dst_path):
    counts = {}
    out_lines = []
    current_section = None
    in_nomenclature = False
    current_unit = None
    elem_count_for_unit = 0
    skipped = 0
    total_groups = 0
    total_elems = 0

    def start_element(name, attrs):
        nonlocal current_section, in_nomenclature, current_unit, elem_count_for_unit, skipped, total_groups, total_elems

        tag = '<' + name
        for k, v in attrs.items():
            tag += f' {k}="{v}"'
        tag += '>'

        if name == 'Справочник_Склады':
            current_section = 'Склады'
            out_lines.append(tag)
        elif name == 'Справочник_ТипыЦен':
            current_section = 'ТипыЦен'
            out_lines.append(tag)
        elif name == 'Справочник_ЕдиницыИзмерения':
            current_section = 'ЕдиницыИзмерения'
            out_lines.append(tag)
        elif name == 'Справочник_Номенклатура':
            current_section = 'Номенклатура'
            in_nomenclature = True
            out_lines.append(tag)
        elif name == 'Справочник_Контрагенты':
            current_section = 'Контрагенты'
            out_lines.append(tag)
        elif name == 'Элемент':
            if current_section == 'Номенклатура':
                is_group = attrs.get('ЭтоГруппа', '').lower() in ('true', '1', 'истина', 'да')
                unit = attrs.get('ЕдиницаИзмерения', '').strip()
                if is_group:
                    total_groups += 1
                    out_lines.append(tag)
                else:
                    total_elems += 1
                    key = unit or '__none__'
                    counts.setdefault(key, 0)
                    if counts[key] < MAX_PER_UNIT:
                        counts[key] += 1
                        out_lines.append(tag)
                    else:
                        skipped += 1
            else:
                out_lines.append(tag)
        else:
            out_lines.append(tag)

    def end_element(name):
        tag = f'</{name}>'
        out_lines.append(tag)

    def char_data(data):
        if data.strip():
            out_lines.append(data)

    parser = expat.ParserCreate()
    parser.StartElementHandler = start_element
    parser.EndElementHandler = end_element
    parser.CharacterDataHandler = char_data

    with open(src_path, 'rb') as f:
        parser.ParseFile(f)

    result = '\n'.join(out_lines)

    with open(dst_path, 'w', encoding='utf-8') as f:
        f.write(result)

    print(f"Original: {total_groups} groups, {total_elems} elements")
    print(f"Trimmed:  {sum(counts.values())} elements ({skipped} skipped)")
    print(f"Units:    {len(counts)} unique")
    for unit, cnt in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {unit or '(none)'}: {cnt}")
    print(f"Saved to: {dst_path}")
    print(f"Size:     {os.path.getsize(dst_path) / 1024:.1f} KB")

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print("Usage: python3 trim_xml.py <source.xml> <dest.xml> [max_per_unit]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2]
    if len(sys.argv) > 3:
        MAX_PER_UNIT = int(sys.argv[3])
    trim_xml(src, dst)
