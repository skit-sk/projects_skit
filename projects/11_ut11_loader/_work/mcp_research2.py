import json
import urllib.request

SID = "601f6dc5f0ca"
code = r'''
import json
results = {}

# 1. Найдём все Enums/СтавкиНДС (их может быть несколько)
enum_files = glob_files('Enums/СтавкиНДС*')
results['enum_files'] = enum_files

# 2. Прочитаем Enum.СтавкиНДС (основной) — через parse_object_xml
#    Обычно он на category 'Enums' / Enums/СтавкиНДС.xml
try:
    results['Enums/СтавкиНДС'] = find_enum_values('СтавкиНДС')
except Exception as e:
    results['Enums/СтавкиНДС_err'] = str(e)

# 3. Табличные части Documents/ВводОстатков (полные)
try:
    info = parse_object_xml('Documents/ВводОстатков')
    ts = info.get('tabular_sections', [])
    results['ВводОстатков.ТабличныеЧасти'] = []
    for t in ts:
        results['ВводОстатков.ТабличныеЧасти'].append({
            'name': t.get('name'),
            'synonym': t.get('synonym'),
            'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in t.get('attributes', [])]
        })
    results['ВводОстатков.АтрибутыШапки'] = [
        {'name': a.get('name'), 'type': a.get('type')}
        for a in info.get('attributes', [])
    ]
except Exception as e:
    results['ВводОстатков_err'] = str(e)

# 4. Документ УстановкаЦенНоменклатуры
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

# 5. Каталог ВидыНоменклатуры — структура
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

# 6. Каталог УпаковкиЕдиницыИзмерения
try:
    info = parse_object_xml('Catalogs/УпаковкиЕдиницыИзмерения')
    results['УпаковкиЕдиницыИзмерения'] = {
        'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in info.get('attributes', [])]
    }
except Exception as e:
    results['УпаковкиЕдиницыИзмерения_err'] = str(e)

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
