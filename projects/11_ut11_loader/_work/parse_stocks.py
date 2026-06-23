#!/usr/bin/env python3
"""
Парсер XML выгрузки остатков из УТ 10.3.

Использование:
    python3 parse_stocks.py <путь_к_xml> [путь_к_отчёту.md]

Выводит статистику в stdout (или в .md файл если указан).
"""
import sys
import time
import collections
import xml.sax


class FullCounter(xml.sax.ContentHandler):
    def __init__(self):
        self.in_section = None
        self.in_item = False
        self.cur_attrs = {}
        self.cur_inner_name = None
        self.cur_inner_text = ""
        self.sklad = []
        self.prices = []
        self.units = []
        self.contractors = []
        self.nomen_groups = 0
        self.nomen_items = 0
        self.nomen_with_qty = 0
        self.nomen_zero_qty = 0
        self.nomen_neg_qty = 0
        self.qty_sum = 0.0
        self.nomen_with_barcode = 0
        self.nomen_with_multi_barcode = 0
        self.price_tag_count = collections.Counter()
        self.price_total_value = collections.Counter()
        self.cost_total_value = 0.0
        self.cost_n_with_qty = 0
        self.cur_prices = {}
        self.cur_cost = 0.0
        self.vat_rates = collections.Counter()
        self.unit_names = collections.Counter()
        self.top_qty = []
        self.group_names = set()

    def startElement(self, name, attrs):
        if name in (
            "Справочник_Склады", "Справочник_ТипыЦен", "Справочник_ЕдиницыИзмерения",
            "Справочник_Номенклатура", "Справочник_Контрагенты"
        ):
            self.in_section = name
        elif name == "Элемент":
            self.in_item = True
            self.cur_attrs = dict(attrs)
            self.cur_inner_name = None
            self.cur_inner_text = ""
            self.cur_prices = {}
            self.cur_cost = 0.0
        elif self.in_item and self.in_section == "Справочник_Номенклатура":
            self.cur_inner_name = name
            self.cur_inner_text = ""

    def characters(self, content):
        if self.in_item and self.cur_inner_name:
            self.cur_inner_text += content

    def endElement(self, name):
        if name == "Элемент":
            if self.in_section == "Справочник_Склады":
                self.sklad.append(self.cur_attrs.get("Наименование", ""))
            elif self.in_section == "Справочник_ТипыЦен":
                self.prices.append((
                    self.cur_attrs.get("ИмяЭлемента", ""),
                    self.cur_attrs.get("Наименование", ""),
                    self.cur_attrs.get("Код", "")
                ))
            elif self.in_section == "Справочник_ЕдиницыИзмерения":
                self.units.append((
                    self.cur_attrs.get("Код", ""),
                    self.cur_attrs.get("Наименование", "")
                ))
            elif self.in_section == "Справочник_Контрагенты":
                self.contractors.append(self.cur_attrs)
            elif self.in_section == "Справочник_Номенклатура":
                is_grp = self.cur_attrs.get("ЭтоГруппа", "false").lower() in ("true", "1", "да")
                if is_grp:
                    self.nomen_groups += 1
                    self.group_names.add(self.cur_attrs.get("Наименование", "").strip())
                else:
                    self.nomen_items += 1
                    self.unit_names[self.cur_attrs.get("ЕдиницаИзмерения", "")] += 1
                    self.vat_rates[self.cur_attrs.get("СтавкаНДС", "")] += 1
                    try:
                        q = float(self.cur_attrs.get("Количество", "0").replace(",", "."))
                    except Exception:
                        q = 0
                    if q > 0:
                        self.nomen_with_qty += 1
                        self.qty_sum += q
                        self.top_qty.append((
                            q,
                            self.cur_attrs.get("Наименование", "").strip()[:80]
                        ))
                        if self.cur_cost > 0:
                            self.cost_total_value += self.cur_cost * q
                            self.cost_n_with_qty += 1
                        for tag, val in self.cur_prices.items():
                            if val > 0:
                                self.price_total_value[tag] += val * q
                    elif q < 0:
                        self.nomen_neg_qty += 1
                    else:
                        self.nomen_zero_qty += 1
                    bc = self.cur_attrs.get("ШтрихКод", "").strip()
                    if bc:
                        self.nomen_with_barcode += 1
                        if "," in bc:
                            self.nomen_with_multi_barcode += 1
                    for tag, val in self.cur_prices.items():
                        if val > 0:
                            self.price_tag_count[tag] += 1
            self.in_item = False
            self.cur_attrs = {}
            self.cur_inner_name = None
        elif name in (
            "Справочник_Склады", "Справочник_ТипыЦен", "Справочник_ЕдиницыИзмерения",
            "Справочник_Номенклатура", "Справочник_Контрагенты"
        ):
            self.in_section = None
        elif self.in_item and self.cur_inner_name == name:
            try:
                v = float(self.cur_inner_text.strip().replace(",", "."))
            except Exception:
                v = 0
            if name == "Себестоимость":
                self.cur_cost = v
            elif name.startswith("Цена_"):
                self.cur_prices[name] = v
            self.cur_inner_name = None
            self.cur_inner_text = ""


def parse(path):
    t0 = time.time()
    h = FullCounter()
    xml.sax.parse(path, h)
    dt = time.time() - t0
    h.top_qty.sort(reverse=True)
    return h, dt


def report(h, dt, path):
    out = []
    out.append(f"# Статистика: {path}")
    out.append("")
    out.append(f"Время парсинга: {dt:.2f} сек")
    out.append("")
    out.append("## Склады")
    for s in h.sklad:
        out.append(f"- {s}")
    out.append("")
    out.append(f"## Типы цен ({len(h.prices)})")
    for u, n, c in h.prices:
        out.append(f"- `{u}` — {n!r} (код: `{c!r}`)")
    out.append("")
    out.append(f"## Единиц измерения: {len(h.units)}")
    out.append("")
    out.append(f"## Контрагентов: {len(h.contractors)}")
    out.append("")
    out.append("## Номенклатура")
    out.append(f"- Групп: {h.nomen_groups}")
    out.append(f"- Элементов: {h.nomen_items}")
    out.append(f"  - с qty>0: {h.nomen_with_qty} (∑={h.qty_sum:,.2f})")
    out.append(f"  - с qty=0: {h.nomen_zero_qty}")
    out.append(f"  - с qty<0: {h.nomen_neg_qty}")
    out.append(f"- Штрих-кодов: {h.nomen_with_barcode} (в т.ч. несколько: {h.nomen_with_multi_barcode})")
    out.append("")
    out.append("## Цены (тег: записей с ценой>0 / сумма стоимости по типу цены)")
    code2name = {c: n for u, n, c in h.prices}
    for tag, cnt in sorted(h.price_tag_count.items(), key=lambda x: -x[1]):
        code = tag.replace("Цена_", "")
        name = code2name.get(code, "?")
        out.append(f"- `{tag}` ({name}) — записей: {cnt}, сумма: {h.price_total_value[tag]:,.2f} ₽")
    out.append("")
    out.append("## Себестоимость")
    out.append(f"- С qty>0 и cost>0: {h.cost_n_with_qty} элементов")
    out.append(f"- Сумма (cost × qty): {h.cost_total_value:,.2f} ₽")
    out.append("")
    out.append("## Ставки НДС")
    for k, v in h.vat_rates.most_common():
        out.append(f"- `{k!r}`: {v}")
    out.append("")
    out.append("## Единицы измерения (топ-10)")
    for k, v in h.unit_names.most_common(10):
        out.append(f"- `{k!r}`: {v}")
    out.append("")
    out.append("## Топ-10 по количеству")
    for q, n in h.top_qty[:10]:
        out.append(f"- {q:,.2f}  {n}")
    out.append("")
    return "\n".join(out)


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 parse_stocks.py <файл.xml> [файл_отчёта.md]")
        sys.exit(1)
    src = sys.argv[1]
    dst = sys.argv[2] if len(sys.argv) > 2 else None
    h, dt = parse(src)
    if dst:
        with open(dst, "w", encoding="utf-8") as f:
            f.write(report(h, dt, src))
        print(f"Отчёт записан в {dst}")
    else:
        print(report(h, dt, src))


if __name__ == "__main__":
    main()
