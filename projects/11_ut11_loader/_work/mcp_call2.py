import json
import urllib.request

SID = "2bc92110add6"
code = r'''
import json

# Шаг 3: TRACE — ищем, как УТ 11.5 правильно заполняет СтавкуНДС номенклатуры.
# 1) Ищем модуль УчетНДСРФВызовСервера
# 2) Ищем функции, связанные со ставками НДС
# 3) Проверяем CatalogRef.СтавкиНДС — что за справочник
results = {}

# 1) УчетНДСРФВызовСервера
try:
    nm = find_module('УчетНДСРФВызовСервера')
    if nm:
        # Возьмём только .bsl
        bsl_items = [x for x in nm if x.get('path', '').endswith('Module.bsl') and 'CommonModules' in x.get('path', '')]
        results['УчетНДСРФВызовСервера'] = bsl_items[:3]
        if bsl_items:
            # Извлекаем экспорты и процедуры из первого модуля
            path = bsl_items[0]['path']
            results['exports'] = find_exports(path)
            results['procedures'] = extract_procedures(path)
except Exception as e:
    results['УчетНДСРФВызовСервера'] = {'error': str(e)}

# 2) Справочник СтавкиНДС — структура
try:
    results['СтавкиНДС'] = parse_object_xml('Catalogs/СтавкиНДС')
except Exception as e:
    results['СтавкиНДС'] = {'error': str(e)}

# 3) Общий модуль РаботаСНоменклатурой (часто содержит хелперы)
try:
    nm2 = find_module('РаботаСНоменклатурой')
    if nm2:
        bsl2 = [x for x in nm2 if x.get('path', '').endswith('Module.bsl') and 'CommonModules' in x.get('path', '')]
        results['РаботаСНоменклатурой_CommonModule'] = bsl2[:2]
        if bsl2:
            results['РаботаСНоменклатурой_exports'] = find_exports(bsl2[0]['path'])
except Exception as e:
    results['РаботаСНоменклатурой_CommonModule'] = {'error': str(e)}

# 4) Документ ВводОстатков
try:
    results['ВводОстатков'] = parse_object_xml('Documents/ВводОстатков')
except Exception as e:
    results['ВводОстатков'] = {'error': str(e)}

print(json.dumps(results, ensure_ascii=False, indent=2))
'''

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "rlm_execute", "arguments": {"session_id": SID, "code": code}}
}

req = urllib.request.Request(
    "http://127.0.0.1:9000/mcp",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"},
    method="POST"
)

with urllib.request.urlopen(req, timeout=120) as resp:
    body = resp.read().decode("utf-8")

for line in body.splitlines():
    if line.startswith("data: "):
        data = json.loads(line[6:])
        out = data.get("result", {}).get("content", [{}])[0].get("text", "")
        try:
            parsed = json.loads(out)
            print(json.dumps(parsed, ensure_ascii=False, indent=2)[:12000])
        except Exception:
            print(out[:12000])
        break
