#!/usr/bin/env python3
import json, os, uuid, copy

BUILD = os.path.join(os.path.dirname(__file__), "build")
FORM = os.path.join(BUILD, "Form", "Форма")
TEMPLATE = os.path.join(os.path.dirname(__file__), "..", "epf4_контрагенты", "build")

OLD_PROC = "3e90bfa8-006d-4d66-b526-c076cb77901f"
OLD_FORM = "f4088d88-e4ce-4d0f-838a-d21f5149c847"
OLD_FILE = "2dc6ef1e-d677-4a5c-aa58-75d5475fd95e"
NEW_PROC = str(uuid.uuid4())
NEW_FORM = str(uuid.uuid4())
NEW_FILE = str(uuid.uuid4())


def replace_uuids(obj, mapping):
    if isinstance(obj, str):
        return mapping.get(obj, obj)
    if isinstance(obj, list):
        return [replace_uuids(v, mapping) for v in obj]
    if isinstance(obj, dict):
        return {k: replace_uuids(v, mapping) for k, v in obj.items()}
    return obj


def write_external():
    with open(os.path.join(TEMPLATE, "ExternalDataProcessor.json")) as f:
        d = json.load(f)
    d = replace_uuids(d, {OLD_PROC: NEW_PROC, OLD_FORM: NEW_FORM, OLD_FILE: NEW_FILE})
    d["name"] = "ЗагрузкаКонтрагентовИзXML_v2"
    d["name2"]["ru"] = "Загрузка контрагентов из XML v2.0"
    try:
        h = d["header"]
        h[0][3][1][1][3][1][2] = '"ЗагрузкаКонтрагентовИзXML_v2"'
        h[0][3][1][1][3][1][3][2] = '"Загрузка контрагентов из XML v2.0"'
    except Exception:
        pass
    with open(os.path.join(BUILD, "ExternalDataProcessor.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print("ExternalDataProcessor.json OK")


def write_form_json():
    with open(os.path.join(TEMPLATE, "Form", "Форма", "Form.json")) as f:
        d = json.load(f)
    d = replace_uuids(d, {OLD_PROC: NEW_PROC, OLD_FORM: NEW_FORM, OLD_FILE: NEW_FILE})
    with open(os.path.join(FORM, "Form.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print("Form/Форма/Form.json OK")


def write_form_id():
    with open(os.path.join(FORM, "Form.id.json"), "w", encoding="utf-8") as f:
        json.dump({"uuid": NEW_FORM}, f, indent=2, ensure_ascii=False)
    print("Form/Форма/Form.id.json OK")


def write_elem():
    with open(os.path.join(TEMPLATE, "Form", "Форма", "Form.elem.json")) as f:
        d = json.load(f)
    d = replace_uuids(d, {OLD_PROC: NEW_PROC, OLD_FORM: NEW_FORM, OLD_FILE: NEW_FILE})
    with open(os.path.join(FORM, "Form.elem.json"), "w", encoding="utf-8") as f:
        json.dump(d, f, indent=2, ensure_ascii=False)
    print("Form.elem.json OK (template, no modifications)")


if __name__ == "__main__":
    os.makedirs(FORM, exist_ok=True)
    write_external()
    write_form_json()
    write_form_id()
    write_elem()
    print("Done")
