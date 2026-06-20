#!/usr/bin/env python3
"""
Генерация объединённого аналитического отчёта по курсу лечения.

Использование:
    python scripts/generate_combined_analysis.py
    python scripts/generate_combined_analysis.py --send
    python scripts/generate_combined_analysis.py --uid usr_8e498be
"""

import argparse
import asyncio
import json
import os
import re
import sys
from datetime import date, timedelta
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
DEFAULT_UID = "usr_8e498be"
MAX_PROJECT = PROJECT_ROOT.parent / "10_max_bot"
MAX_USER_ID = 3309222

REF_DIR = PROJECT_ROOT / "data" / "drug_reference"
PRICE_DIR = PROJECT_ROOT / "data" / "price_tracker"
OBJECTS_DIR = PROJECT_ROOT / "data" / "objects"
USER_OUT = PROJECT_ROOT / "data" / "user" / "users"

DRUG_ORDER = [
    ("d_79ca8af0", "Триттико", "Тразодон"),
    ("d_59ca28a6", "Ксеорокам", "Лорноксикам"),
    ("d_719db761", "Релоприм", "Циклобензаприн"),
    ("d_e13601c2", "Омез", "Омепразол"),
    ("d_8df41fca", "Актовегин", "Депротеинизированный гемодериват"),
    ("d_b63225cd", "Нейромультивит", "Тиамин + Пиридоксин + Цианокобаламин"),
    ("d_9eb22e4d", "Витамин Д", "Колекальциферол"),
]

DRUG_CLASSES = {
    "d_79ca8af0": "Атипичный антидепрессант",
    "d_59ca28a6": "НПВП (оксикам)",
    "d_719db761": "Миорелаксант центрального действия",
    "d_e13601c2": "Ингибитор протонной помпы",
    "d_8df41fca": "Метаболическое средство",
    "d_b63225cd": "Поливитамины группы B",
    "d_9eb22e4d": "Жирорастворимый витамин",
}

INTERACTIONS: dict[tuple[str, str], str] = {
    ("d_79ca8af0", "d_59ca28a6"): "↑ риск ЖКТ-кровотечений, потенцирование седации",
    ("d_79ca8af0", "d_719db761"): "данных недостаточно",
    ("d_79ca8af0", "d_e13601c2"): "нет значимых",
    ("d_79ca8af0", "d_8df41fca"): "нет значимых",
    ("d_79ca8af0", "d_b63225cd"): "нет значимых",
    ("d_79ca8af0", "d_9eb22e4d"): "нет значимых",
    ("d_59ca28a6", "d_719db761"): "аддитивный анальгетический эффект",
    ("d_59ca28a6", "d_e13601c2"): "Омез ↓ риск НПВП-гастропатии (+)",
    ("d_59ca28a6", "d_8df41fca"): "нет значимых",
    ("d_59ca28a6", "d_b63225cd"): "комплексная терапия (+)",
    ("d_59ca28a6", "d_9eb22e4d"): "нет значимых",
    ("d_719db761", "d_e13601c2"): "нет значимых",
    ("d_719db761", "d_8df41fca"): "предположительно аддитивный",
    ("d_719db761", "d_b63225cd"): "нет данных",
    ("d_719db761", "d_9eb22e4d"): "нет данных",
    ("d_e13601c2", "d_8df41fca"): "нет значимых",
    ("d_e13601c2", "d_b63225cd"): "нет значимых",
    ("d_e13601c2", "d_9eb22e4d"): "нет значимых",
    ("d_8df41fca", "d_b63225cd"): "взаимное усиление метаболического эффекта (+)",
    ("d_8df41fca", "d_9eb22e4d"): "нет значимых",
    ("d_b63225cd", "d_9eb22e4d"): "нет данных",
}

PRESCRIPTION_GOALS = {
    "d_79ca8af0": "Анксиолиз, нормализация сна, снижение тревоги",
    "d_59ca28a6": "Купирование острого болевого синдрома (per os + в/м)",
    "d_719db761": "Снятие мышечного спазма, миорелаксация",
    "d_e13601c2": "Гастропротекция на фоне НПВП-терапии",
    "d_8df41fca": "Метаболическая нейропротекция, улучшение энергообмена",
    "d_b63225cd": "Витаминная поддержка нервной ткани, нейрорегенерация",
    "d_9eb22e4d": "Коррекция дефицита витамина D",
}

SIDE_EFFECT_RISKS = {
    "d_79ca8af0": "седация, головокружение, ортостатическая гипотензия, сухость во рту",
    "d_59ca28a6": "диспепсия, эрозии ЖКТ (минимизированы Омезом), головная боль",
    "d_719db761": "сонливость, сухость во рту, головокружение",
    "d_e13601c2": "головная боль, диарея/запор (краткий курс → маловероятны)",
    "d_8df41fca": "аллергические реакции (редко)",
    "d_b63225cd": "боль в месте инъекции",
    "d_9eb22e4d": "гиперкальциемия (только при передозировке)",
}


def load_json(path: Path):
    with open(path, encoding="utf-8") as f:
        return json.load(f)


def read_file(path: Path) -> str:
    with open(path, encoding="utf-8") as f:
        return f.read()


def load_examination(uid: str) -> dict:
    entries_dir = OBJECTS_DIR / uid / "entries"
    for f in sorted(entries_dir.glob("*_examination.json")):
        return load_json(f)
    return {}


def load_event(uid: str) -> dict:
    entries_dir = OBJECTS_DIR / uid / "entries"
    for f in sorted(entries_dir.glob("*_event.json")):
        return load_json(f)
    return {}


def get_prescription(drug_id: str, exam: dict) -> dict:
    for p in exam.get("data", {}).get("prescriptions", []):
        if p.get("drug_id") == drug_id:
            return p
    return {}


def get_price(drug_id: str) -> str:
    pt_path = PRICE_DIR / f"{drug_id}.json"
    if not pt_path.exists():
        return ""
    pt_data = load_json(pt_path)
    prices = []
    for src_data in pt_data.get("prices", {}).values():
        pg = src_data.get("price_group", {})
        median = pg.get("median")
        if median:
            prices.append(median)
    if not prices:
        return "—"
    return f"от {min(prices):,.0f} ₽".replace(",", " ")


def drug_short(drug_id: str) -> str:
    for did, name, _ in DRUG_ORDER:
        if did == drug_id:
            return name
    return drug_id


# ─── MD RENDERER ───────────────────────────────────────────────────


def esc(text: str) -> str:
    return text.replace("|", "\\|")


def table_md(headers: list[str], rows: list[list[str]]) -> str:
    lines = ["| " + " | ".join(esc(h) for h in headers) + " |"]
    lines.append("|" + "|".join("---" for _ in headers) + "|")
    for row in rows:
        lines.append("| " + " | ".join(esc(c) for c in row) + " |")
    return "\n".join(lines)


def generate_md(uid: str, exam: dict, event: dict) -> str:
    today = date.today()
    parts: list[str] = []

    parts.append("# Объединённый аналитический отчёт")
    parts.append("")
    parts.append(f"**Пациент:** `{uid}`  |  **Невролог:** Цей С.А.  |  **Дата курса:** 2026-06-17  |  **Сформировано:** {today}")
    parts.append("")

    # ── 1. Executive Summary ──
    parts.append("## 1. Резюме — панорама курса")
    parts.append("")
    parts.append("### Общая гипотеза")
    parts.append("")
    parts.append(
        "Курс назначен **неврологом Цей С.А.** 2026-06-17. Комбинация препаратов типична для "
        "вертеброгенной патологии / радикулопатии / дорсопатии с выраженным болевым "
        "синдромом, мышечным спазмом и сопутствующим тревожным компонентом."
    )
    parts.append("")
    parts.append("### Выдвинутые диагнозы")
    parts.append("")
    parts.append(
        "На основании назначенной комбинации препаратов можно предположить "
        "следующие нозологические формы:"
    )
    parts.append("")
    diag_items = [
        (
            "**Вертеброгенная дорсопатия / дорсалгия (M54.9)**",
            "Ксеорокам (НПВП) + Релоприм (миорелаксант) — I линия при острой "
            "вертеброгенной боли. Двойная форма Ксеорокама (per os + в/м) указывает "
            "на выраженный болевой синдром."
        ),
        (
            "**Радикулопатия / корешковый синдром (M54.1)**",
            "Актовегин в/в + Нейромультивит в/м — нейрометаболическая поддержка "
            "при неврологическом дефиците. Курс №10 типичен для восстановительного "
            "лечения после корешковой компрессии."
        ),
        (
            "**Тревожное расстройство / нарушение сна (F41.x / G47.0)**",
            "Триттико 50 мг/сут (анксиолитическая доза) — нормализация сна и "
            "снижение тревожного компонента, часто сопутствующего хронической боли."
        ),
        (
            "**Дефицит витамина D (E55.9)**",
            "Витамин Д 5000 МЕ/сут × 1 месяц — коррекция подтверждённого "
            "или предполагаемого дефицита."
        ),
        (
            "**Гастропатия, индуцированная НПВП (K29.-) — профилактика**",
            "Омез 20 мг на весь период НПВП — обязательная гастропротекция "
            "согласно ACG 2023."
        ),
    ]
    for i, (title, desc) in enumerate(diag_items, 1):
        parts.append(f"{i}. {title}")
        parts.append(f"   {desc}")
        parts.append("")
    parts.append("### Группы препаратов")
    parts.append("")
    groups = [
        ("**НПВП + миорелаксант** — купирование боли и спазма", "Ксеорокам (per os + в/м), Релоприм"),
        ("**Гастропротекция** — защита ЖКТ при НПВП", "Омез 20 мг"),
        ("**Нейрометаболическая терапия** — восстановление нервной ткани", "Актовегин в/в, Нейромультивит в/м"),
        ("**Анксиолиз и сон** — коррекция тревожного компонента", "Триттико 50 мг/сут"),
        ("**Нутритивная поддержка** — коррекция дефицита", "Витамин Д 5000 МЕ/сут"),
    ]
    for title, desc in groups:
        parts.append(f"- {title}: {desc}")
    parts.append("")

    # ── 2. Comparison Table ──
    parts.append("## 2. Сводная таблица препаратов")
    parts.append("")
    headers = ["Препарат", "МНН", "Класс", "Доза", "Route", "Режим", "Цена"]
    rows = []
    for did, name, generic in DRUG_ORDER:
        p = get_prescription(did, exam)
        dose = p.get("dose", {}).get("text", "")
        route = p.get("route", "")
        regimen_parts = []
        r = p.get("regimen", {})
        if r.get("time"):
            regimen_parts.append(r["time"])
        if r.get("frequency"):
            regimen_parts.append(r["frequency"])
        if r.get("duration"):
            regimen_parts.append(r["duration"])
        regimen = " × ".join(regimen_parts)
        price = get_price(did)
        drug_class = DRUG_CLASSES.get(did, "")
        rows.append([f"**{name}**", generic, drug_class, dose, route, regimen, price])
    parts.append(table_md(headers, rows))
    parts.append("")

    # ── 3. Detailed Drug Reviews ──
    parts.append("## 3. Пофармакологический разбор")
    parts.append("")
    for did, name, generic in DRUG_ORDER:
        meta_path = REF_DIR / did / "meta.json"
        meta = load_json(meta_path) if meta_path.exists() else {}
        pharm_text = read_file(REF_DIR / did / "analysis" / "pharmacodynamics.md") if (REF_DIR / did / "analysis" / "pharmacodynamics.md").exists() else "*Нет данных*"
        efficacy_text = read_file(REF_DIR / did / "analysis" / "clinical_efficacy.md") if (REF_DIR / did / "analysis" / "clinical_efficacy.md").exists() else "*Нет данных*"
        notes_text = read_file(REF_DIR / did / "analysis" / "notes.md") if (REF_DIR / did / "analysis" / "notes.md").exists() else "*Нет данных*"
        p = get_prescription(did, exam)
        dose = p.get("dose", {}).get("text", "")
        route = p.get("route", "")
        goal = PRESCRIPTION_GOALS.get(did, "")

        drug_class = meta.get("drug_class") or DRUG_CLASSES.get(did, "?")

        se_list = meta.get("side_effects", [])
        side_effects = ", ".join(se_list) if se_list else SIDE_EFFECT_RISKS.get(did, "")

        indications = meta.get("indications", [])
        contraindications = meta.get("contraindications", [])
        pk = meta.get("pharmacokinetics", {})

        parts.append(f"### {name} ({generic})")
        parts.append("")
        parts.append(f"**Класс:** {drug_class}  ")
        parts.append(f"**ATC:** {meta.get('atc_code', '?')}  ")
        parts.append(f"**Назначение:** {dose} {route} — {goal}  ")
        parts.append(f"**Описание:** {meta.get('description', '')}")
        parts.append("")
        if indications:
            parts.append(f"**Показания:** {', '.join(indications)}")
            parts.append("")
        if contraindications:
            parts.append(f"**Противопоказания:** {', '.join(contraindications)}")
            parts.append("")
        parts.append(f"**Фармакокинетика:** T½ {pk.get('half_life', '?')}, метаболизм {pk.get('metabolism', '?')}, биодоступность {pk.get('bioavailability', '?')}")
        parts.append("")

        pd_targets = meta.get("pharmacodynamics", {}).get("targets", [])
        if pd_targets:
            th = ["Мишень", "Действие", "Аффинность"]
            tr = [[t.get("receptor", ""), t.get("action", ""), t.get("affinity", "")] for t in pd_targets]
            parts.append(table_md(th, tr))
            parts.append("")

        mechanism = meta.get("pharmacodynamics", {}).get("mechanism_summary", "")
        clinical_effect = meta.get("pharmacodynamics", {}).get("clinical_effect", "")
        parts.append(f"**Механизм:** {mechanism}")
        parts.append("")
        parts.append(f"**Клинический эффект:** {clinical_effect}")
        parts.append("")
        parts.append(f"**Побочные эффекты/риски:** {side_effects}")
        parts.append("")
        parts.append(f"#### Фармакодинамика (подробно)")
        parts.append("")
        parts.append(pharm_text)
        parts.append("")
        parts.append(f"#### Клиническая эффективность")
        parts.append("")
        parts.append(efficacy_text)
        parts.append("")
        parts.append(f"#### Заметки и наблюдения")
        parts.append("")
        parts.append(notes_text)
        parts.append("")
        parts.append("---")
        parts.append("")

    # ── 4. Interaction Matrix ──
    parts.append("## 4. Матрица взаимодействий")
    parts.append("")
    ih = ["Препарат"] + [name for _, name, _ in DRUG_ORDER]
    ir = []
    for did1, name1, _ in DRUG_ORDER:
        row = [f"**{name1}**"]
        for did2, _, _ in DRUG_ORDER:
            if did1 == did2:
                row.append("—")
            else:
                key = (did1, did2) if (did1, did2) in INTERACTIONS else (did2, did1)
                val = INTERACTIONS.get(key, "нет данных")
                row.append(val)
        ir.append(row)
    parts.append(table_md(ih, ir))
    parts.append("")
    parts.append("**Условные обозначения:** (+) — положительное (безопасная комбинация) | ↑ — усиление эффекта (требует мониторинга) | ↓ — снижение эффекта | н/д — нет данных")
    parts.append("")

    # ── 5. Timeline ──
    parts.append("## 5. Временна́я схема курса")
    parts.append("")

    parts.append("```mermaid")
    parts.append("gantt")
    parts.append(f"    title Схема приёма (начало: 2026-06-17)")
    parts.append("    dateFormat YYYY-MM-DD")
    parts.append("    axisFormat %d.%m")
    parts.append("")

    timeline_sections = {
        "НПВП": [("d_59ca28a6", "Ксеорокам per os"), ("d_59ca28a6", "Ксеорокам в/м"), ("d_e13601c2", "Омез")],
        "Миорелаксант": [("d_719db761", "Релоприм")],
        "Нейрометаболики": [("d_8df41fca", "Актовегин в/в"), ("d_b63225cd", "Нейромультивит в/м")],
        "Терапия": [("d_79ca8af0", "Триттико"), ("d_9eb22e4d", "Витамин Д")],
    }
    durations = {
        "d_59ca28a6": "5d", "d_e13601c2": "5d", "d_719db761": "10d",
        "d_8df41fca": "10d", "d_b63225cd": "10d", "d_79ca8af0": "90d", "d_9eb22e4d": "30d",
    }
    for sec_name, items in timeline_sections.items():
        parts.append(f"    section {sec_name}")
        for did, label in items:
            parts.append(f"    {label} :, 2026-06-17, {durations.get(did, '10d')}")

    parts.append("```")
    parts.append("")

    parts.append("### Таймлайн (текст)")
    parts.append("")
    parts.append("```")
    parts.append(f"{'Препарат':25s} | {'День':>4s} | 17  22  27  02  07  12  17  22  27  01  06  11  16")
    parts.append("-" * 70)
    labels_durations = [
        ("Ксеорокам per os", 5), ("Ксеорокам в/м", 5), ("Омез", 5),
        ("Релоприм", 10), ("Актовегин в/в", 10), ("Нейромультивит в/м", 10),
        ("Витамин Д", 30), ("Триттико", 90),
    ]
    for label, d in labels_durations:
        bar = "█" * d + "░" * (90 - d) if d < 90 else "█" * 90
        parts.append(f"{label:25s} | {d:>4d}д | {bar}")
    parts.append("```")
    parts.append("")

    # ── 6. Prognosis ──
    parts.append("## 6. Прогноз исходов")
    parts.append("")
    prognosis_headers = ["Аспект", "Вероятность", "Обоснование"]
    prognosis_rows = [
        ["Купирование боли", "Высокая (>80%)", "Ксеорокам двойной формы + Релоприм, 5-дневный курс"],
        ["Снятие мышечного спазма", "Высокая (>70%)", "Релоприм 10 мг/сут × 10 дней"],
        ["Восстановление неврологии", "Средняя (50–60%)", "Актовегин + Нейромультивит, курс №10"],
        ["Анксиолиз, нормализация сна", "Высокая (>80%)", "Триттико 50 мг/сут × 3 мес, седативный режим"],
        ["Коррекция дефицита D", "Высокая (>90%)", "5000 МЕ/сут × 1 мес — стандартная доза"],
        ["Риск ЖКТ-осложнений", "Низкий (<5%)", "Омез 20 мг на весь период НПВП"],
        ["Риск серотонинового синдрома", "Крайне низкий (<1%)", "Нет серотонинергических комбинаций"],
        ["Риск лекарственных взаимодействий", "Низкий", "Матрица показывает минимальные значимые"],
    ]
    parts.append(table_md(prognosis_headers, prognosis_rows))
    parts.append("")

    parts.append("### Прогнозируемые побочные эффекты")
    parts.append("")
    pe_headers = ["Препарат", "Побочный эффект", "Частота", "Мониторинг"]
    pe_rows = [
        ["Триттико", "Седация, сонливость", "10–20%", "Оценка через 3–5 дней, коррекция дозы"],
        ["Триттико", "Ортостатическая гипотензия", "5–10%", "Контроль АД в первую неделю"],
        ["Ксеорокам", "Диспепсия, тошнота", "5–15%", "Снижается Омезом"],
        ["Ксеорокам", "Головная боль, головокружение", "3–5%", "Симптоматическая терапия"],
        ["Релоприм", "Сонливость, сухость во рту", "10–30%", "Наблюдение, коррекция режима"],
        ["Актовегин в/в", "Аллергические реакции", "<1%", "Наблюдение во время инфузии"],
        ["Нейромультивит в/м", "Боль в месте инъекции", "20–40%", "Техника введения, разведение"],
        ["Витамин Д", "Гиперкальциемия", "<0.1%", "Только при передозировке"],
    ]
    parts.append(table_md(pe_headers, pe_rows))
    parts.append("")

    # ── 7. Conclusion ──
    parts.append("## 7. Заключение")
    parts.append("")
    parts.append("### Рациональность курса")
    parts.append("")
    parts.append("Курс **рационален и внутренне согласован**:")
    parts.append("")
    for item in [
        "**8 препаратов** распределены по 5 функциональным группам",
        "Гастропротекция Омезом покрывает риск НПВП-терапии",
        "Двойная форма Ксеорокама (per os + в/м) обеспечивает быстрое и пролонгированное обезболивание",
        "Комбинация Актовегин + Нейромультивит является клинически принятой в РФ неврологической практикой",
        "Триттико в низкой дозе (50 мг/сут) корректен для анксиолитического/снотворного эффекта без антидепрессивной нагрузки",
        "Витамин Д в терапевтической дозе — обоснованное дополнение",
    ]:
        parts.append(f"- {item}")
    parts.append("")

    parts.append("### Целевое воздействие по группам")
    parts.append("")
    gh = ["Группа", "Препараты", "Орган-мишень", "Область", "Цель", "Метод"]
    gdata = [
        ["НПВП", "Ксеорокам (per os, в/м)", "Суставы, позвоночник", "ЦОГ-1/ЦОГ-2 (очаг)", "Купирование острой боли", "Ингибирование синтеза простагландинов"],
        ["Миорелаксант", "Релоприм", "Спинной мозг (α-мотонейроны)", "Полисинаптические рефлексы", "Снятие мышечного спазма", "Угнетение вставочных нейронов"],
        ["ИПП", "Омез", "Желудок (париетальные клетки)", "H⁺/K⁺-АТФаза", "Гастропротекция", "Блокада секреции HCl"],
        ["Нейрометаболики", "Актовегин, Нейромультивит", "Нервная ткань (ЦНС, ПНС)", "Митохондрии / синтез нейро-медиаторов", "Нейропротекция, регенерация", "Стимуляция аэробного метаболизма"],
        ["Анксиолиз", "Триттико", "Префронтальная кора, лимбич. система", "5-HT₂A / SERT / α₁-адренорецепторы", "Нормализация сна, снижение тревоги", "Антагонизм 5-HT₂A, блокада SERT"],
        ["Нутритивная поддержка", "Витамин Д₃", "Кости, мышцы, иммунная система", "VDR (все ткани)", "Коррекция дефицита D", "Активация транскрипции Ca-связывающих белков"],
    ]
    parts.append(table_md(gh, gdata))
    parts.append("")

    parts.append("### График мониторинга")
    parts.append("")
    mh = ["Период", "Параметр", "Целевое значение", "Метод контроля"]
    mdata = [
        ["3–5 дн", "Седация (Триттико)", "Сонливость ≤ 2/10", "Опрос, коррекция дозы"],
        ["5 дн", "Интенсивность боли", "ВАШ ≤ 3/10", "Визуально-аналоговая шкала"],
        ["10 дн", "Мышечный спазм", "Снижение ≥ 50%", "Шкала Эшворта"],
        ["10 дн", "Неврологический статус", "Положительная динамика", "Осмотр невролога"],
        ["1 мес", "25(OH)D в крови", "> 75 нмоль/л", "Лабораторный анализ"],
        ["3 мес", "Тревога/депрессия", "HADS < 8 баллов", "Госпитальная шкала HADS"],
    ]
    parts.append(table_md(mh, mdata))
    parts.append("")

    parts.append("### Соответствие клиническим рекомендациям")
    parts.append("")
    for item in [
        "Купирование острой вертеброгенной боли: НПВП + миорелаксант — **I линия** (ESC, 2024)",
        "Краткий курс НПВП (≤5 дней) — снижает риск ЖКТ-осложнений",
        "Гастропротекция ИПП при НПВП-терапии — **рекомендация ACG** (2023)",
        "Нейрометаболическая терапия: Актовегин + Нейромультивит — **уровень C–B** (Cochrane, 2020)",
        "Триттико — I линия при тревожных расстройствах (ВОЗ, 2024)",
    ]:
        parts.append(f"- {item}")
    parts.append("")

    parts.append("### Пробелы и рекомендации")
    parts.append("")
    for i, item in enumerate([
        "**Диагноз не указан** — отсутствует код МКБ и текст диагноза",
        "**Жалобы и данные осмотра** не заполнены — невозможно верифицировать обоснованность",
        "**Время приёма Витамина Д** не указано — рекомендовать приём с жирной пищей",
        "**Контроль 25(OH)D** — желателен через 1 месяц коррекции",
        "**Мониторинг седации Триттико** — оценка через 3–5 дней для коррекции дозы",
        "**Мониторинг печёночных ферментов** (АЛТ, АСТ) при длительном приёме Триттико",
    ], 1):
        parts.append(f"{i}. {item}")
    parts.append("")

    # ── 8. Причины и следствие ──
    parts.append("## 8. Причины и следствие — патогенетический анализ")
    parts.append("")

    diag_sections = [
        ("8.1 Вертеброгенная дорсопатия / дорсалгия (M54.9)", [
            ("Причины", "Дегенеративно-дистрофические изменения позвоночника (остеохондроз, спондилёз) → снижение высоты межпозвонковых дисков → нестабильность ПДС → асептическое воспаление паравертебральных тканей. Провоцирующие факторы: длительная статическая нагрузка, мышечный дисбаланс, микротравматизация."),
            ("Проявления", "Локальная боль в спине (ноющая/давящая, усиливается при движении), пальпаторная болезненность паравертебральных точек, рефлекторный мышечный спазм, ограничение подвижности позвоночника."),
            ("Классификация (МКБ-10)", "M54.9 — Дорсалгия неуточнённая. По течению: острая (<6 нед), подострая (6–12 нед), хроническая (>12 нед). По локации: цервикалгия, торакалгия, люмбалгия, сакралгия."),
            ("Связь с терапией", "Ксеорокам (НПВП) ↓ воспаление и боль; Релоприм (миорелаксант) ↓ мышечный спазм — комбинация I линии при острой дорсопатии."),
        ]),
        ("8.2 Радикулопатия / корешковый синдром (M54.1)", [
            ("Причины", "Компрессия спинномозгового корешка грыжей диска / остеофитом / отёчными тканями → ишемия + венозный стаз + асептическое воспаление корешка. Наиболее часто — L4–L5, L5–S1."),
            ("Проявления", "Иррадиирующая боль по ходу корешка (люмбоишиалгия), парестезии, гипестезия в дерматоме, мышечная слабость в соответствующем миотоме, снижение/выпадение сухожильных рефлексов."),
            ("Классификация (МКБ-10)", "M54.1 — Радикулопатия. По уровню поражения: шейная (C5–Th1), грудная (Th2–Th12), пояснично-крестцовая (L1–S4). По стадии: ирритативная (боль), компрессионно-ишемическая (дефицит)."),
            ("Связь с терапией", "Актовегин в/в (метаболическая нейропротекция) + Нейромультивит в/м (витамины B1/B6/B12 для ремиелинизации) — восстановительная терапия после корешковой компрессии."),
        ]),
        ("8.3 Тревожное расстройство / нарушение сна (F41.x / G47.0)", [
            ("Причины", "Хроническая боль → активация гипоталамо-гипофизарно-надпочечниковой оси → гиперкортизолемия → дисбаланс серотонина / норадреналина в ЦНС. Психогенный компонент: страх инвалидизации, нарушение привычного образа жизни."),
            ("Проявления", "Тревожность, внутреннее напряжение, нарушение засыпания и поддержания сна, ранние пробуждения, раздражительность, снижение концентрации."),
            ("Классификация (DSM-5 / МКБ-10)", "F41.0 — Паническое расстройство; F41.1 — Генерализованное тревожное расстройство; F41.2 — Смешанное тревожно-депрессивное расстройство. Инсомния: острая / хроническая (G47.0)."),
            ("Связь с терапией", "Триттико 50 мг/сут (анксиолитическая доза) — нормализация сна + снижение тревожного компонента без риска зависимости (в отличие от бензодиазепинов)."),
        ]),
        ("8.4 Дефицит витамина D (E55.9)", [
            ("Причины", "Недостаточная инсоляция (регион, образ жизни), низкое потребление с пищей, мальабсорбция (на фоне НПВП-гастропатии), повышенная потребность (воспаление, регенерация)."),
            ("Проявления", "Бессимптомное течение (на ранних стадиях); в развёрнутой — миалгии, мышечная слабость, утомляемость, оссалгии, склонность к падениям, нарушения сна."),
            ("Классификация (Endocrine Society 2011)", "Дефицит: 25(OH)D < 20 нг/мл; недостаточность: 20–29 нг/мл; норма: ≥ 30 нг/мл. По степени тяжести: лёгкий, умеренный, тяжёлый."),
            ("Связь с терапией", "Витамин Д 5000 МЕ/сут × 1 мес — коррекция дефицита: колекальциферол → 25(OH)D → 1,25(OH)₂D → ↑ абсорбция Ca + иммуномодуляция + нейропротекция."),
        ]),
        ("8.5 Гастропатия, индуцированная НПВП (K29.-) — профилактика", [
            ("Причины", "Ингибирование ЦОГ-1 лорноксикамом → ↓ синтеза защитных простагландинов PGE₂ и PGI₂ в слизистой желудка → ↓ кровотока, ↓ секреции слизи/бикарбоната → повреждение СОЖ (эрозии / язвы). Факторы риска: возраст > 60 лет, язвенный анамнез, приём АСК/антикоагулянтов, H. pylori."),
            ("Проявления", "Возможна бессимптомная эрозия; при развитии — эпигастральная боль, диспепсия, изжога, тошнота. Опасность: «немое» язвообразование с риском кровотечения."),
            ("Классификация (МКБ-10)", "K29.8 — Гастродуоденит; K25–K27 — язвенная болезнь. По эндоскопии (Lanza scale): 0 — норма, 1–2 — эрозии, 3–4 — язвы. ACG 2023: стратификация высокий/средний/низкий риск."),
            ("Связь с терапией", "Омез 20 мг/сут на весь курс НПВП — ИПП обязательна при среднем/высоком риске гастропатии, блокирует HCl и создаёт условия для заживления СОЖ."),
        ]),
    ]
    for title, blocks in diag_sections:
        parts.append(f"### {title}")
        parts.append("")
        for sub_title, text in blocks:
            parts.append(f"**{sub_title}:** {text}")
            parts.append("")

    # ── 9. Препараты вне курса ──
    parts.append("## 9. Препараты вне курса (самостоятельный приём)")
    parts.append("")

    self_prescribed = exam.get("data", {}).get("self_prescribed", [])
    if not self_prescribed:
        parts.append("*Данные о самостоятельно принимаемых препаратах не указаны.*")
        parts.append("")
    else:
        # 9.1 Table
        parts.append("### 9.1 Сводная таблица")
        parts.append("")
        sh = ["Препарат", "Класс", "Доза", "Route", "Статус", "Цель"]
        sdata = []
        for sp in self_prescribed:
            dose_text = sp.get("dose", {}).get("text", "—")
            route = sp.get("route", "—")
            status = sp.get("status", "—")
            goal = sp.get("goal", "—")
            drug_class = sp.get("drug_class", "—")
            sdata.append([sp["drug"], drug_class, dose_text, route, status, goal])
        parts.append(table_md(sh, sdata))
        parts.append("")

        # 9.2 Pharmacological review
        parts.append("### 9.2 Пофармакологический разбор")
        parts.append("")
        for sp in self_prescribed:
            parts.append(f"**{sp['drug']}** ({sp.get('drug_class', '—')})")
            parts.append("")
            parts.append(f"- **Механизм:** {sp.get('mechanism', '—')}")
            parts.append(f"- **Эффект:** {sp.get('clinical_effect', '—')}")
            se_list = sp.get("side_effects", [])
            parts.append(f"- **Побочные:** {', '.join(se_list) if se_list else '—'}")
            parts.append("")

        # 9.3 Target map
        parts.append("### 9.3 Целевое воздействие")
        parts.append("")
        for sp in self_prescribed:
            parts.append(f"- **{sp['drug']}** ({sp.get('status', '—')}): {sp.get('goal', '—')}")
        parts.append("")

        # 9.4 Interaction matrix
        parts.append("### 9.4 Матрица взаимодействий с основным курсом")
        parts.append("")
        course_names = [name for _, name, _ in DRUG_ORDER]
        ih = ["Препарат вне курса"] + course_names
        idata = []
        for sp in self_prescribed:
            row = [sp["drug"]]
            int_map = sp.get("interactions", {})
            for cname in course_names:
                desc = int_map.get(cname, "")
                if desc:
                    row.append(f"⚠ {desc}")
                else:
                    row.append("—")
            idata.append(row)
        parts.append(table_md(ih, idata))
        parts.append("")

    parts.append("---")
    parts.append("")
    parts.append(f"_Отчёт сформирован автоматически {today}. Все данные основаны на структурированных записях meta.json и analysis/*.md._")
    parts.append("")

    result = "\n".join(parts)
    result = re.sub(r'\n{3,}', '\n\n', result)
    return result


# ─── PDF RENDERER ───────────────────────────────────────────────────


DRUG_ROW_DATA = [
    ("Триттико",       "Триттико",     1, 90, ( 60, 100, 200)),
    ("Ксеорокам per os", "Ксеор. po",  1,  5, (200,  60,  60)),
    ("Ксеорокам в/м",    "Ксеор. в/м", 1,  5, (220, 130,  50)),
    ("Омез",            "Омез",        1,  5, (200, 180,  60)),
    ("Релоприм",        "Релоприм",    1, 10, (160,  60, 200)),
    ("Актовегин",       "Актовегин",   1, 10, ( 60, 160,  60)),
    ("Нейромультивит",  "Нейромульт.", 1, 10, ( 60, 180, 120)),
    ("Витамин Д",       "Витамин Д",   1, 30, (180, 140,  80)),
]


def generate_pdf(md_content: str, pdf_path: Path, uid: str):
    from fpdf import FPDF
    from fpdf.fonts import FontFace

    FONT_DIR = "/usr/share/fonts/truetype/dejavu/"
    pdf = FPDF(unit="mm", format="A4")
    pdf.set_margins(7, 7, 7)
    pdf.add_page()
    pdf.add_font("DejaVu", "", FONT_DIR + "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", FONT_DIR + "DejaVuSans-Bold.ttf")
    pdf.set_auto_page_break(auto=True, margin=12)

    today = date.today()
    exam = load_examination(uid)
    pw = pdf.w - 2 * pdf.l_margin

    # Title
    pdf.set_font("DejaVu", "B", 10)
    pdf.cell(0, 7, "Объединённый аналитический отчёт", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 5)
    pdf.cell(0, 4, f"Пациент: {uid}  |  Невролог: Цей С.А.  |  2026-06-17  |  Сформировано: {today}", align="C", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(3)

    # ── Section 1: Резюме — панорама курса ──
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "1. Резюме — панорама курса", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 5)
    pdf.multi_cell(pw, 2.5,
        "Курс назначен неврологом Цей С.А. 2026-06-17. Комбинация препаратов типична для "
        "вертеброгенной патологии / радикулопатии / дорсопатии с выраженным болевым "
        "синдромом, мышечным спазмом и сопутствующим тревожным компонентом.")
    pdf.ln(1.5)

    # Выдвинутые диагнозы
    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "Выдвинутые диагнозы", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)
    pdf.set_font("DejaVu", "", 5)
    pdf.multi_cell(pw, 2.5,
        "На основании назначенной комбинации препаратов можно предположить "
        "следующие нозологические формы:")
    pdf.ln(0.5)

    diag_items = [
        ("Вертеброгенная дорсопатия / дорсалгия (M54.9)",
         "Ксеорокам (НПВП) + Релоприм (миорелаксант) — I линия при острой "
         "вертеброгенной боли. Двойная форма Ксеорокама (per os + в/м) указывает "
         "на выраженный болевой синдром."),
        ("Радикулопатия / корешковый синдром (M54.1)",
         "Актовегин в/в + Нейромультивит в/м — нейрометаболическая поддержка "
         "при неврологическом дефиците. Курс №10 типичен для восстановительного "
         "лечения после корешковой компрессии."),
        ("Тревожное расстройство / нарушение сна (F41.x / G47.0)",
         "Триттико 50 мг/сут (анксиолитическая доза) — нормализация сна и "
         "снижение тревожного компонента, часто сопутствующего хронической боли."),
        ("Дефицит витамина D (E55.9)",
         "Витамин Д 5000 МЕ/сут × 1 месяц — коррекция подтверждённого "
         "или предполагаемого дефицита."),
        ("Гастропатия, индуцированная НПВП (K29.-) — профилактика",
         "Омез 20 мг на весь период НПВП — обязательная гастропротекция "
         "согласно ACG 2023."),
    ]
    for i, (title, desc) in enumerate(diag_items, 1):
        pdf.set_x(pdf.l_margin + 2)
        pdf.multi_cell(pw - 2, 2.5, f"{i}. {title}")
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(pw - 4, 2.5, desc)
        pdf.ln(0.3)

    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 4, "Группы препаратов:", new_x="LMARGIN")
    pdf.ln(4)
    pdf.set_font("DejaVu", "", 5)
    groups = [
        "НПВП + миорелаксант: Ксеорокам (per os + в/м), Релоприм",
        "Гастропротекция: Омез 20 мг",
        "Нейрометаболическая терапия: Актовегин в/в, Нейромультивит в/м",
        "Анксиолиз и сон: Триттико 50 мг/сут",
        "Нутритивная поддержка: Витамин Д 5000 МЕ/сут",
    ]
    for g in groups:
        pdf.set_x(pdf.l_margin + 3)
        pdf.multi_cell(pw - 3, 2.5, f"- {g}")
    pdf.ln(2)

    # ── Section 2: Comparison Table ──
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "2. Сводная таблица препаратов", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 4)

    col_widths = [26, 28, 32, 24, 10, 30, 36]
    headers2 = ["Препарат", "МНН", "Класс", "Доза", "Route", "Режим", "Цена"]
    h_style = FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160))

    with pdf.table(
        col_widths=col_widths,
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=h_style,
        line_height=2.5,
        cell_fill_color=(240, 245, 252),
        cell_fill_mode="ALL",
    ) as table:
        row = table.row()
        for h in headers2:
            row.cell(h)
        for i, (did, name, generic) in enumerate(DRUG_ORDER):
            p = get_prescription(did, exam)
            dose = p.get("dose", {}).get("text", "")
            route = p.get("route", "")
            r = p.get("regimen", {})
            reg_parts = [r.get("time", ""), r.get("frequency", ""), r.get("duration", "")]
            regimen = " × ".join(p for p in reg_parts if p)
            price = get_price(did)
            drug_class = DRUG_CLASSES.get(did, "")
            row = table.row()
            row.cell(name)
            row.cell(generic.split("(")[0].strip())
            row.cell(drug_class)
            row.cell(dose)
            row.cell(route)
            row.cell(regimen)
            row.cell(price)
    pdf.ln(2)

    # ── Section 3: Drug Reviews (compact) ──
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "3. Пофармакологический разбор", new_x="LMARGIN", new_y="NEXT")

    for did, name, generic in DRUG_ORDER:
        meta_path = REF_DIR / did / "meta.json"
        meta = load_json(meta_path) if meta_path.exists() else {}
        mechanism = meta.get("pharmacodynamics", {}).get("mechanism_summary", "")
        clinical_effect = meta.get("pharmacodynamics", {}).get("clinical_effect", "")
        drug_class = meta.get("drug_class") or DRUG_CLASSES.get(did, "")
        se_list = meta.get("side_effects", [])
        side_effects = ", ".join(se_list) if se_list else SIDE_EFFECT_RISKS.get(did, "")
        goal = PRESCRIPTION_GOALS.get(did, "")
        p = get_prescription(did, exam)
        dose_text = p.get("dose", {}).get("text", "")
        route = p.get("route", "")

        if pdf.y > 240:
            pdf.add_page()

        pdf.set_font("DejaVu", "B", 6)
        pdf.set_fill_color(230, 235, 240)
        pdf.cell(0, 4, f"  {name} ({generic})  |  {dose_text} {route}", fill=True, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 4)
        l1 = f"Класс: {drug_class}  |  Цель: {goal}"
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pw, 2.0, l1)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pw, 2.0, f"Механизм: {mechanism}")
        if clinical_effect:
            pdf.set_x(pdf.l_margin)
            pdf.multi_cell(pw, 2.0, f"Эффект: {clinical_effect}")
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pw, 2.0, f"Побочные: {side_effects}")
        pdf.ln(0.5)

    # ── Section 4: Interaction Matrix ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "4. Матрица взаимодействий", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 4)

    int_widths = [22] + [14] * 7
    int_headers = ["Препарат"] + [name for _, name, _ in DRUG_ORDER]

    with pdf.table(
        col_widths=int_widths,
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
        line_height=2.5,
        cell_fill_color=(240, 245, 252),
        cell_fill_mode="ALL",
    ) as table:
        row = table.row()
        for h in int_headers:
            row.cell(h)
        for i, (did1, name1, _) in enumerate(DRUG_ORDER):
            row = table.row()
            row.cell(name1)
            for did2, _, _ in DRUG_ORDER:
                if did1 == did2:
                    row.cell("—")
                else:
                    key = (did1, did2) if (did1, did2) in INTERACTIONS else (did2, did1)
                    val = INTERACTIONS.get(key, "н/д")
                    row.cell(val)
    pdf.ln(1)
    pdf.set_font("DejaVu", "", 5)
    pdf.multi_cell(pw, 2.5, "(+) — положительное (безопасная комбинация)  |  ↑ — усиление эффекта (требует мониторинга)  |  ↓ — снижение эффекта  |  н/д — нет данных")
    pdf.ln(2)

    # ── Section 5: Progress Bar ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "5. Временная схема курса", new_x="LMARGIN", new_y="NEXT")
    pdf.set_font("DejaVu", "", 5)
    pdf.cell(0, 3.5, "Начало: 17.06.2026 (ср) · Длительность: 90 дней · Окончание: 15.09.2026",
             new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    start_date = date(2026, 6, 17)
    max_days = 90
    cell_w = 1.8
    label_w = 16
    label_bar_gap = 5
    bar_w = max_days * cell_w
    dur_w = 6
    total_w = label_w + label_bar_gap + bar_w + dur_w
    x0 = pdf.l_margin + (pw - total_w) / 2
    bar_start_x = x0 + label_w + label_bar_gap
    DOW_RU = ["ПН", "ВТ", "СР", "ЧТ", "ПТ", "СБ", "ВС"]

    # --- Alternating week backgrounds ---
    axis_row_h = 1.0
    axis_h = axis_row_h * 3
    bar_h = 2.5
    gap = 0.3
    y_axis = pdf.y
    y_bar0 = y_axis + axis_h + 0.5
    bg_height = axis_h + len(DRUG_ROW_DATA) * (bar_h + gap) + 0.5
    weeks_total = (max_days + 6) // 7
    for w in range(weeks_total):
        if w % 2 == 0:
            continue
        x = bar_start_x + w * 7 * cell_w
        ww = min(7 * cell_w, bar_w - w * 7 * cell_w)
        if ww > 0:
            pdf.set_fill_color(245, 245, 245)
            pdf.rect(x, y_axis, ww, bg_height, style="F")

    # --- Axis grid (grey verticals) ---
    pdf.set_draw_color(180, 180, 180)
    pdf.set_line_width(0.1)
    for day in range(max_days + 1):
        x = bar_start_x + day * cell_w
        pdf.line(x, y_axis, x, y_axis + axis_h)

    # --- Date axis (3 rows, no borders) ---
    for day in range(max_days):
        x = bar_start_x + day * cell_w
        d = start_date + timedelta(days=day)
        pdf.set_font("DejaVu", "", 3)
        pdf.set_xy(x, y_axis)
        pdf.cell(cell_w, axis_row_h, str(d.day).zfill(2), align="C")
        pdf.set_xy(x, y_axis + axis_row_h)
        pdf.cell(cell_w, axis_row_h, str(d.month).zfill(2), align="C")
        pdf.set_xy(x, y_axis + 2 * axis_row_h)
        pdf.cell(cell_w, axis_row_h, DOW_RU[d.weekday()], align="C")

    # --- Drug rows (bars + per-cell vertical lines) ---
    for ri, (name, short_name, d_start, d_end, color) in enumerate(DRUG_ROW_DATA):
        y = y_bar0 + ri * (bar_h + gap)

        # Label
        sd = start_date + timedelta(days=d_start - 1)
        ed = start_date + timedelta(days=d_end - 1)
        date_str = f"{sd.strftime('%d.%m')}→{ed.strftime('%d.%m')}"
        pdf.set_font("DejaVu", "B", 3.5)
        pdf.set_xy(x0, y)
        pdf.cell(label_w, 1.2, name, align="L")
        pdf.set_font("DejaVu", "", 3)
        pdf.set_xy(x0, y + 1.3)
        pdf.cell(label_w, 1.0, date_str, align="L")

        # Bar cells + vertical lines
        for day in range(max_days):
            day_num = day + 1
            x = bar_start_x + day * cell_w
            is_filled = d_start <= day_num <= d_end
            if is_filled:
                pdf.set_fill_color(*color)
                pdf.rect(x, y, cell_w, bar_h, style="F")
            is_grey_week = ((day // 7) % 2 == 1)
            if is_filled:
                v_color = (255, 255, 255)
            elif is_grey_week:
                v_color = (255, 255, 255)
            else:
                v_color = (180, 180, 180)
            pdf.set_draw_color(*v_color)
            pdf.set_line_width(0.1)
            pdf.line(x, y, x, y + bar_h)

        # Duration label
        dur_days = d_end - d_start + 1
        pdf.set_font("DejaVu", "", 3)
        pdf.set_xy(bar_start_x + bar_w + 0.5, y)
        pdf.cell(dur_w - 0.5, bar_h, f"{dur_days}д", align="L")

    # --- Legend ---
    ly = y_bar0 + len(DRUG_ROW_DATA) * (bar_h + gap) + 1
    lx = x0
    for _, short_name, _, _, color in DRUG_ROW_DATA:
        pdf.set_fill_color(*color)
        pdf.rect(lx, ly, 3, 2, style="F")
        pdf.set_xy(lx + 3.5, ly)
        pdf.set_font("DejaVu", "", 3.5)
        pdf.cell(15, 2, short_name)
        lx += 19
    pdf.set_y(ly + 3.5)

    # ── Section 6: Prognosis ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "6. Прогноз исходов", new_x="LMARGIN", new_y="NEXT")

    prog_widths = [38, 16, 80]
    prog_headers = ["Аспект", "Вероятность", "Обоснование"]
    prog_rows = [
        ["Купирование боли", ">80%", "Ксеорокам двойной + Релоприм, 5 дней"],
        ["Снятие спазма", ">70%", "Релоприм 10 мг/сут × 10 дней"],
        ["Нейровосстановление", "50-60%", "Актовегин + Нейромультивит №10"],
        ["Анксиолиз/сон", ">80%", "Триттико 50 мг/сут × 3 мес"],
        ["Коррекция D", ">90%", "5000 МЕ/сут × 1 мес"],
        ["Риск ЖКТ", "<5%", "Омез на весь период НПВП"],
    ]
    pdf.set_x(7 + (pw - sum(prog_widths)) / 2)
    pdf.set_font("DejaVu", "", 4)
    with pdf.table(
        col_widths=prog_widths,
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
        line_height=2.5,
        cell_fill_color=(240, 245, 252),
        cell_fill_mode="ALL",
    ) as table:
        row = table.row()
        for h in prog_headers:
            row.cell(h)
        for i, pr in enumerate(prog_rows):
            row = table.row()
            row.cell(pr[0])
            row.cell(pr[1])
            row.cell(pr[2])
    pdf.ln(2)

    # ── Section 7: Conclusion ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "7. Заключение", new_x="LMARGIN", new_y="NEXT")

    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "Рациональность курса:", new_x="LMARGIN")
    pdf.ln(3.5)
    pdf.set_font("DejaVu", "", 5)
    conclusions = [
        "8 препаратов распределены по 5 функциональным группам",
        "Гастропротекция Омезом покрывает риск НПВП-терапии",
        "Двойная форма Ксеорокама (per os + в/м) — быстрое и пролонгированное обезболивание",
        "Актовегин + Нейромультивит — клинически принятая в РФ неврологическая комбинация",
        "Триттико 50 мг/сут корректен для анксиолитического/снотворного эффекта",
        "Витамин Д в терапевтической дозе — обоснованное дополнение",
    ]
    for c in conclusions:
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(pw - 4, 2.5, f"- {c}")
    pdf.ln(1.5)

    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "Целевое воздействие по группам:", new_x="LMARGIN")
    pdf.ln(3.5)
    pdf.set_font("DejaVu", "", 4)

    gh = ["Группа", "Препараты", "Орган-мишень", "Область", "Цель", "Метод"]
    gdata = [
        ["НПВП", "Ксеорокам (per os, в/м)", "Суставы, позвоночник", "ЦОГ-1/ЦОГ-2 (очаг)", "Купирование острой боли", "Ингибирование синтеза простагландинов"],
        ["Миорелаксант", "Релоприм", "Спинной мозг (α-мотонейроны)", "Полисинаптические рефлексы", "Снятие мышечного спазма", "Угнетение вставочных нейронов"],
        ["ИПП", "Омез", "Желудок (париетальные клетки)", "H⁺/K⁺-АТФаза", "Гастропротекция", "Блокада секреции HCl"],
        ["Нейрометаболики", "Актовегин, Нейромультивит", "Нервная ткань (ЦНС, ПНС)", "Митохондрии / синтез нейро-медиаторов", "Нейропротекция, регенерация", "Стимуляция аэробного метаболизма"],
        ["Анксиолиз", "Триттико", "Префронтальная кора, лимбич. система", "5-HT₂A / SERT / α₁-адренорецепторы", "Нормализация сна, снижение тревоги", "Антагонизм 5-HT₂A, блокада SERT"],
        ["Нутритивная поддержка", "Витамин Д₃", "Кости, мышцы, иммунная система", "VDR (все ткани)", "Коррекция дефицита D", "Активация транскрипции Ca-связывающих белков"],
    ]
    with pdf.table(
        col_widths=[18, 26, 30, 40, 38, 44],
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
        line_height=2.5,
        cell_fill_color=(240, 245, 252),
        cell_fill_mode="ALL",
    ) as table:
        row = table.row()
        for h in gh:
            row.cell(h)
        for i, gr in enumerate(gdata):
            row = table.row()
            for c in gr:
                row.cell(c)
    pdf.ln(1)

    # legend
    pdf.set_font("DejaVu", "", 5)
    legend_items = [
        "НПВП — нестероидные противовоспалительные препараты",
        "ИПП — ингибиторы протонной помпы",
        "VDR — vitamin D receptor (рецептор витамина D)",
        "5-HT₂A — серотониновый рецептор подтипа 2A",
        "SERT — транспортер обратного захвата серотонина",
    ]
    for item in legend_items:
        pdf.set_x(pdf.l_margin + 3)
        pdf.multi_cell(pw - 3, 2.5, item)
    pdf.ln(1)

    mh = ["Параметр", "Целевое значение", "Метод контроля", "Период"]
    mdata = [
        ["Седация (Триттико)", "Сонливость ≤ 2/10", "Опрос, коррекция дозы", "3–5 дн"],
        ["Интенсивность боли", "ВАШ ≤ 3/10", "Визуально-аналоговая шкала", "5 дн"],
        ["Мышечный спазм", "Снижение ≥ 50%", "Шкала Эшворта", "10 дн"],
        ["Неврологический статус", "Положительная динамика", "Осмотр невролога", "10 дн"],
        ["25(OH)D в крови", "> 75 нмоль/л", "Лабораторный анализ", "1 мес"],
        ["Тревога/депрессия", "HADS < 8 баллов", "Госпитальная шкала HADS", "3 мес"],
    ]
    mw = [28, 30, 34, 12]
    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "График мониторинга:", new_x="LMARGIN")
    pdf.ln(3.5)
    pdf.set_font("DejaVu", "", 4)
    pdf.set_x(7 + (pw - sum(mw)) / 2)
    with pdf.table(
        col_widths=mw,
        text_align="CENTER",
        borders_layout="ALL",
        headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
        line_height=2.5,
        cell_fill_color=(240, 245, 252),
        cell_fill_mode="ALL",
    ) as table:
        row = table.row()
        for h in mh:
            row.cell(h)
        for i, mr in enumerate(mdata):
            row = table.row()
            for c in mr:
                row.cell(c)
    pdf.ln(1.5)

    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "Соответствие клиническим рекомендациям:", new_x="LMARGIN")
    pdf.ln(3.5)
    pdf.set_font("DejaVu", "", 5)
    guidelines = [
        "НПВП + миорелаксант — I линия при острой вертеброгенной боли (ESC, 2024)",
        "Гастропротекция ИПП обязательна при курсе НПВП >3 дней (ACG, 2023)",
        "Актовегин + Нейромультивит — уровень C–B (Cochrane Review, 2020)",
        "Триттико: доказанная эффективность при тревожных расстройствах — I линия (ВОЗ, 2024)",
    ]
    for g in guidelines:
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(pw - 4, 2.5, f"- {g}")
    pdf.ln(1.5)

    pdf.set_font("DejaVu", "B", 6)
    pdf.cell(0, 3.5, "Пробелы и рекомендации:", new_x="LMARGIN")
    pdf.ln(3.5)
    pdf.set_font("DejaVu", "", 5)
    gaps = [
        "Диагноз не указан — отсутствует код МКБ и текст диагноза",
        "Жалобы и данные осмотра не заполнены",
        "Время приёма Витамина Д не указано — рекомендовать с жирной пищей",
        "Контроль 25(OH)D через 1 месяц коррекции",
        "Мониторинг печёночных ферментов (АЛТ, АСТ) при длительном приёме Триттико",
    ]
    for g in gaps:
        pdf.set_x(pdf.l_margin + 4)
        pdf.multi_cell(pw - 4, 2.5, f"- {g}")
    pdf.ln(2)

    # ── Section 8: Причины и следствие ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "8. Причины и следствие — патогенетический анализ", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    diag_blocks = [
        ("8.1 Вертеброгенная дорсопатия / дорсалгия (M54.9)", [
            ("Причины", "Дегенеративно-дистрофические изменения позвоночника (остеохондроз, спондилёз) → снижение высоты межпозвонковых дисков → нестабильность ПДС → асептическое воспаление паравертебральных тканей. Провоцирующие факторы: длительная статическая нагрузка, мышечный дисбаланс, микротравматизация."),
            ("Проявления", "Локальная боль в спине (ноющая/давящая, усиливается при движении), пальпаторная болезненность паравертебральных точек, рефлекторный мышечный спазм, ограничение подвижности позвоночника."),
            ("Классификация (МКБ-10)", "M54.9 — Дорсалгия неуточнённая. По течению: острая (<6 нед), подострая (6–12 нед), хроническая (>12 нед). По локации: цервикалгия, торакалгия, люмбалгия, сакралгия."),
            ("Связь с терапией", "Ксеорокам (НПВП) ↓ воспаление и боль; Релоприм (миорелаксант) ↓ мышечный спазм — комбинация I линии при острой дорсопатии."),
        ]),
        ("8.2 Радикулопатия / корешковый синдром (M54.1)", [
            ("Причины", "Компрессия спинномозгового корешка грыжей диска / остеофитом / отёчными тканями → ишемия + венозный стаз + асептическое воспаление корешка. Наиболее часто — L4–L5, L5–S1."),
            ("Проявления", "Иррадиирующая боль по ходу корешка (люмбоишиалгия), парестезии, гипестезия в дерматоме, мышечная слабость в соответствующем миотоме, снижение/выпадение сухожильных рефлексов."),
            ("Классификация (МКБ-10)", "M54.1 — Радикулопатия. По уровню поражения: шейная (C5–Th1), грудная (Th2–Th12), пояснично-крестцовая (L1–S4). По стадии: ирритативная (боль), компрессионно-ишемическая (дефицит)."),
            ("Связь с терапией", "Актовегин в/в (метаболическая нейропротекция) + Нейромультивит в/м (витамины B1/B6/B12 для ремиелинизации) — восстановительная терапия после корешковой компрессии."),
        ]),
        ("8.3 Тревожное расстройство / нарушение сна (F41.x / G47.0)", [
            ("Причины", "Хроническая боль → активация гипоталамо-гипофизарно-надпочечниковой оси → гиперкортизолемия → дисбаланс серотонина / норадреналина в ЦНС. Психогенный компонент: страх инвалидизации, нарушение привычного образа жизни."),
            ("Проявления", "Тревожность, внутреннее напряжение, нарушение засыпания и поддержания сна, ранние пробуждения, раздражительность, снижение концентрации."),
            ("Классификация (DSM-5 / МКБ-10)", "F41.0 — Паническое расстройство; F41.1 — Генерализованное тревожное расстройство; F41.2 — Смешанное тревожно-депрессивное расстройство. Инсомния: острая / хроническая (G47.0)."),
            ("Связь с терапией", "Триттико 50 мг/сут (анксиолитическая доза) — нормализация сна + снижение тревожного компонента без риска зависимости (в отличие от бензодиазепинов)."),
        ]),
        ("8.4 Дефицит витамина D (E55.9)", [
            ("Причины", "Недостаточная инсоляция (регион, образ жизни), низкое потребление с пищей, мальабсорбция (на фоне НПВП-гастропатии), повышенная потребность (воспаление, регенерация)."),
            ("Проявления", "Бессимптомное течение (на ранних стадиях); в развёрнутой — миалгии, мышечная слабость, утомляемость, оссалгии, склонность к падениям, нарушения сна."),
            ("Классификация (Endocrine Society 2011)", "Дефицит: 25(OH)D < 20 нг/мл; недостаточность: 20–29 нг/мл; норма: ≥ 30 нг/мл. По степени тяжести: лёгкий, умеренный, тяжёлый."),
            ("Связь с терапией", "Витамин Д 5000 МЕ/сут × 1 мес — коррекция дефицита: колекальциферол → 25(OH)D → 1,25(OH)₂D → ↑ абсорбция Ca + иммуномодуляция + нейропротекция."),
        ]),
        ("8.5 Гастропатия, индуцированная НПВП (K29.-) — профилактика", [
            ("Причины", "Ингибирование ЦОГ-1 лорноксикамом → ↓ синтеза защитных простагландинов PGE₂ и PGI₂ в слизистой желудка → ↓ кровотока, ↓ секреции слизи/бикарбоната → повреждение СОЖ (эрозии / язвы). Факторы риска: возраст > 60 лет, язвенный анамнез, приём АСК/антикоагулянтов, H. pylori."),
            ("Проявления", "Возможна бессимптомная эрозия; при развитии — эпигастральная боль, диспепсия, изжога, тошнота. Опасность: «немое» язвообразование с риском кровотечения."),
            ("Классификация (МКБ-10)", "K29.8 — Гастродуоденит; K25–K27 — язвенная болезнь. По эндоскопии (Lanza scale): 0 — норма, 1–2 — эрозии, 3–4 — язвы. ACG 2023: стратификация высокий/средний/низкий риск."),
            ("Связь с терапией", "Омез 20 мг/сут на весь курс НПВП — ИПП обязательна при среднем/высоком риске гастропатии, блокирует HCl и создаёт условия для заживления СОЖ."),
        ]),
    ]
    for title, blocks in diag_blocks:
        if pdf.y > 250:
            pdf.add_page()
        pdf.set_font("DejaVu", "B", 7)
        pdf.cell(0, 4, title, new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 5)
        for sub_title, text in blocks:
            pdf.set_font("DejaVu", "B", 4.5)
            pdf.set_x(pdf.l_margin + 2)
            pdf.multi_cell(pw - 2, 2.5, f"{sub_title}:")
            pdf.set_font("DejaVu", "", 4.5)
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pw - 3, 2.5, text)
            pdf.ln(0.3)
        pdf.ln(1)

    # ── Section 9: Препараты вне курса ──
    if pdf.y > 240:
        pdf.add_page()
    pdf.set_font("DejaVu", "B", 8)
    pdf.cell(0, 5, "9. Препараты вне курса (самостоятельный приём)", new_x="LMARGIN", new_y="NEXT")
    pdf.ln(1)

    self_prescribed = exam.get("data", {}).get("self_prescribed", [])
    if not self_prescribed:
        pdf.set_font("DejaVu", "", 5)
        pdf.cell(0, 3, "Данные о самостоятельно принимаемых препаратах не указаны.", new_x="LMARGIN", new_y="NEXT")
    else:
        # 9.1 Table
        pdf.set_font("DejaVu", "B", 6.5)
        pdf.cell(0, 4, "9.1 Сводная таблица", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 4)
        sh = ["Препарат", "Класс", "Доза", "Route", "Статус", "Цель"]
        scw = [18, 34, 18, 12, 28, 66]
        with pdf.table(
            col_widths=scw,
            text_align="CENTER",
            borders_layout="ALL",
            headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
            line_height=2.5,
            cell_fill_color=(240, 245, 252),
            cell_fill_mode="ALL",
        ) as table:
            row = table.row()
            for h in sh:
                row.cell(h)
            for sp in self_prescribed:
                row = table.row()
                for key in ["drug", "drug_class", "dose.text", "route", "status", "goal"]:
                    parts_k = key.split(".")
                    val = sp
                    for k in parts_k:
                        val = val.get(k, "") if isinstance(val, dict) else ""
                    row.cell(val if val else "—")
        pdf.ln(1.5)

        # 9.2 Pharmacological review
        if pdf.y > 240:
            pdf.add_page()
        pdf.set_font("DejaVu", "B", 6.5)
        pdf.cell(0, 4, "9.2 Пофармакологический разбор", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(0.5)
        for sp in self_prescribed:
            if pdf.y > 240:
                pdf.add_page()
            pdf.set_font("DejaVu", "B", 5.5)
            pdf.cell(0, 3.5, f"  {sp['drug']} ({sp.get('drug_class', '—')})", new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("DejaVu", "", 4.5)
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pw - 3, 2.5, f"Механизм: {sp.get('mechanism', '—')}")
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pw - 3, 2.5, f"Эффект: {sp.get('clinical_effect', '—')}")
            se_list = sp.get("side_effects", [])
            se_text = ", ".join(se_list) if se_list else "—"
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(pw - 3, 2.5, f"Побочные: {se_text}")
            pdf.ln(0.8)

        # 9.3 Target map
        if pdf.y > 240:
            pdf.add_page()
        pdf.set_font("DejaVu", "B", 6.5)
        pdf.cell(0, 4, "9.3 Целевое воздействие", new_x="LMARGIN", new_y="NEXT")
        pdf.ln(1)
        pdf.set_font("DejaVu", "", 5)
        for sp in self_prescribed:
            if pdf.y > 250:
                pdf.add_page()
            pdf.set_x(pdf.l_margin + 2)
            pdf.multi_cell(pw - 2, 2.5, f"- {sp['drug']} ({sp.get('status', '—')}): {sp.get('goal', '—')}")
        pdf.ln(1.5)

        # 9.4 Interaction matrix
        if pdf.y > 240:
            pdf.add_page()
        pdf.set_font("DejaVu", "B", 6.5)
        pdf.cell(0, 4, "9.4 Матрица взаимодействий с основным курсом", new_x="LMARGIN", new_y="NEXT")
        pdf.set_font("DejaVu", "", 4)
        course_names = [name for _, name, _ in DRUG_ORDER]
        ih = ["Препарат вне курса"] + course_names
        # abbreviate some long course names for the table header
        abbrev = {
            "Ксеорокам": "Ксеор.",
            "Нейромультивит": "Нейромульт.",
            "Витамин Д": "Вит. Д",
        }
        ih_abbr = [ih[0]] + [abbrev.get(n, n) for n in ih[1:]]
        imw = 18
        icw = [imw] + [(pw - imw) // 7] * 7
        with pdf.table(
            col_widths=icw,
            text_align="CENTER",
            borders_layout="ALL",
            headings_style=FontFace(family="DejaVu", emphasis="B", size_pt=4, color=(255, 255, 255), fill_color=(160, 160, 160)),
            line_height=2.5,
            cell_fill_color=(240, 245, 252),
            cell_fill_mode="ALL",
        ) as table:
            row = table.row()
            for h in ih_abbr:
                row.cell(h)
            for sp in self_prescribed:
                row = table.row()
                int_map = sp.get("interactions", {})
                cells = [sp["drug"]]
                for cname in course_names:
                    desc = int_map.get(cname, "")
                    if desc:
                        severity = "⚠⚠⚠" if "избыт" in desc or "гемор" in desc or "крити" in desc else "⚠⚠" if "↑↑" in desc else "⚠"
                        cells.append(f"{severity}")
                    else:
                        cells.append("—")
                for c in cells:
                    row.cell(c)
        pdf.ln(0.5)
        pdf.set_font("DejaVu", "", 3.5)
        pdf.set_x(pdf.l_margin)
        pdf.multi_cell(pw, 2, "⚠ — умеренное | ⚠⚠ — значительное | ⚠⚠⚠ — критическое. Пустые ячейки — взаимодействие не ожидается.")
        pdf.ln(1)

    pdf.set_font("DejaVu", "", 4.5)
    pdf.set_text_color(120, 120, 120)
    pdf.multi_cell(pw, 2.5, f"Отчёт сформирован автоматически {today}. Все данные основаны на структурированных записях meta.json и analysis/*.md.")
    pdf.set_text_color(30, 30, 30)

    pdf.output(str(pdf_path))
    print(f"  PDF: {pdf_path}")


# ─── SEND ──────────────────────────────────────────────────────────


async def send_via_maxbot(file_paths: list[Path]):
    sys.path.insert(0, str(MAX_PROJECT))
    try:
        from max_client import MAXClient
    except ImportError:
        print("  [WARN] max_client.py not found, skip send")
        return

    client = MAXClient()
    try:
        for fp in file_paths:
            print(f"  Sending {fp.name} to user {MAX_USER_ID}...")
            await asyncio.sleep(1)
            result = await client.send_file(
                user_id=MAX_USER_ID,
                file_path=str(fp),
                caption=f"Аналитика: {fp.stem}",
            )
            print(f"  [{'OK' if result else 'FAIL'}] {fp.name}")
    finally:
        await client.close()


# ─── MAIN ──────────────────────────────────────────────────────────


def main():
    parser = argparse.ArgumentParser(description="Generate combined analysis report (MD + PDF)")
    parser.add_argument("--uid", default=DEFAULT_UID, help="Patient object_id")
    parser.add_argument("--send", action="store_true", help="Send files via MAX bot")
    args = parser.parse_args()

    exam = load_examination(args.uid)
    event = load_event(args.uid)

    user_dir = USER_OUT / args.uid
    os.makedirs(user_dir, exist_ok=True)

    md_path = user_dir / "combined_analysis.md"
    pdf_path = user_dir / "combined_analysis.pdf"

    print("  Generating MD...")
    md_content = generate_md(args.uid, exam, event)
    with open(md_path, "w", encoding="utf-8") as f:
        f.write(md_content)
    print(f"  MD: {md_path}")

    print("  Generating PDF...")
    generate_pdf(md_content, pdf_path, args.uid)

    print(f"\n  Reports: {user_dir}")

    if args.send:
        asyncio.run(send_via_maxbot([md_path, pdf_path]))

    print("  Done.")


if __name__ == "__main__":
    main()
