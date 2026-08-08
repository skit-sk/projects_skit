import json
import urllib.request

SID = "601f6dc5f0ca"
code = r'''
import json
results = {}

# 1. Каталог ВидыНоменклатуры — какие реквизиты обязательны
try:
    info = parse_object_xml('Catalogs/ВидыНоменклатуры')
    results['ВидыНоменклатуры'] = {
        'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in info.get('attributes', [])],
        'tabular_sections': [
            {'name': t.get('name'),
             'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in t.get('attributes', [])]}
            for t in info.get('tabular_sections', [])
        ]
    }
except Exception as e:
    results['ВидыНоменклатуры_err'] = str(e)

# 2. Каталог УпаковкиЕдиницыИзмерения
try:
    info = parse_object_xml('Catalogs/УпаковкиЕдиницыИзмерения')
    results['УпаковкиЕдиницыИзмерения'] = {
        'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in info.get('attributes', [])],
        'tabular_sections': [
            {'name': t.get('name'),
             'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in t.get('attributes', [])]}
            for t in info.get('tabular_sections', [])
        ]
    }
except Exception as e:
    results['УпаковкиЕдиницыИзмерения_err'] = str(e)

# 3. Документ УстановкаЦенНоменклатуры — структура шапки
try:
    info = parse_object_xml('Documents/УстановкаЦенНоменклатуры')
    results['УстановкаЦен.Шапка'] = [{'name': a.get('name'), 'type': a.get('type')} for a in info.get('attributes', [])]
    results['УстановкаЦен.ТабличныеЧасти'] = [
        {'name': t.get('name'),
         'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in t.get('attributes', [])]}
        for t in info.get('tabular_sections', [])
    ]
except Exception as e:
    results['УстановкаЦен_err'] = str(e)

# 4. Проверим, есть ли в Справочнике.Номенклатура поле для Упаковки (отдельная табличная часть)
try:
    info = parse_object_xml('Catalogs/Номенклатура')
    ts = info.get('tabular_sections', [])
    results['Номенклатура.ТабличныеЧасти'] = [
        {'name': t.get('name'),
         'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in t.get('attributes', [])][:15]}
        for t in ts
    ]
except Exception as e:
    results['Номенклатура_err'] = str(e)

# 5. Найдём предопределённые элементы справочника СтавкиНДС
try:
    pd = find_predefined(object_name='СтавкиНДС')
    results['СтавкиНДС_предопределённые'] = pd
except Exception as e:
    results['СтавкиНДС_предопределённые_err'] = str(e)

print(json.dumps(results, ensure_ascii=False, indent=2)[:25000])
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

with urllib.request.urlopen(req, timeout=180) as resp:
    body = resp.read().decode("utf-8")

for line in body.splitlines():
    if line.startswith("data: "):
        data = json.loads(line[6:])
        out = data.get("result", {}).get("content", [{}])[0].get("text", "")
        print(out[:30000])
        break
