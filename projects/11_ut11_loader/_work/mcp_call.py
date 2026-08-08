import json
import urllib.request

SID = "2bc92110add6"
code = r'''
import json
results = {}
for path in ['Catalogs/Номенклатура', 'Catalogs/ВидыНоменклатуры', 'Catalogs/УпаковкиЕдиницыИзмерения']:
    try:
        info = parse_object_xml(path)
        attrs = info.get('attributes', [])
        ts = info.get('tabular_sections', [])
        results[path] = {
            'name': info.get('name'),
            'synonym': info.get('synonym'),
            'attributes_count': len(attrs),
            'attributes': [{'name': a.get('name'), 'type': a.get('type'), 'kind': a.get('kind')} for a in attrs],
            'tabular_sections_count': len(ts),
            'tabular_sections_names': [t.get('name') for t in ts],
        }
    except Exception as e:
        results[path] = {'error': str(e)}
print(json.dumps(results, ensure_ascii=False, indent=2))
'''

payload = {
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {
        "name": "rlm_execute",
        "arguments": {
            "session_id": SID,
            "code": code
        }
    }
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
            print(json.dumps(parsed, ensure_ascii=False, indent=2)[:10000])
        except Exception:
            print(out[:10000])
        break
