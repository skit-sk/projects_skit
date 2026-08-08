import json
import urllib.request

SID = "601f6dc5f0ca"
code = r'''
import json
results = {}

# 1. Значения ключевых перечислений
for ename in ['ТипыНоменклатуры', 'СтавкиНДС', 'ХозяйственныеОперации', 'ВариантыИспользованияХарактеристикНоменклатуры', 'ТипыНалогообложенияНДС', 'ГрадацииКачества']:
    try:
        v = find_enum_values(ename)
        results[f'enum.{ename}'] = v
    except Exception as e:
        results[f'enum.{ename}'] = {'error': str(e)}

# 2. Структура документов ВводОстатков и УстановкаЦенНоменклатуры
for path in ['Documents/ВводОстатков', 'Documents/УстановкаЦенНоменклатуры']:
    try:
        info = parse_object_xml(path)
        # Сокращаем: только имена и типы реквизитов + табл. части
        results[f'obj.{path}'] = {
            'name': info.get('name'),
            'synonym': info.get('synonym'),
            'attributes': [{'name': a.get('name'), 'type': a.get('type')} for a in info.get('attributes', [])],
            'tabular_sections': [
                {
                    'name': t.get('name'),
                    'attributes': [{'name': c.get('name'), 'type': c.get('type')} for c in t.get('attributes', [])]
                }
                for t in info.get('tabular_sections', [])
            ]
        }
    except Exception as e:
        results[f'obj.{path}'] = {'error': str(e)}

print(json.dumps(results, ensure_ascii=False, indent=2)[:20000])
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
        print(out[:25000])
        break
