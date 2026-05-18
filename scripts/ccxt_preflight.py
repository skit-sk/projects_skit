#!/usr/bin/env python3
"""
Preflight check for all public ccxt methods on a given exchange.
Usage: python3 scripts/ccxt_preflight.py [exchange=bitget] [base_url=http://localhost:5000]
"""

import sys
import json
import time
import urllib.request
import urllib.error
from urllib.parse import quote
import requests

EXCHANGE = sys.argv[1] if len(sys.argv) > 1 else 'bitget'
BASE_URL = sys.argv[2] if len(sys.argv) > 2 else 'http://localhost:5000'


def api_get(path):
    url = f'{BASE_URL}{path}'
    try:
        with urllib.request.urlopen(url, timeout=15) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        return {'error': f'HTTP {e.code}: {e.read().decode()[:200]}'}
    except Exception as e:
        return {'error': str(e)}


def api_execute(method, params):
    url = f'{BASE_URL}/ccxt-api/api/execute'
    data = json.dumps({
        'exchange': EXCHANGE,
        'method': method,
        'params': params,
    }).encode()
    req = urllib.request.Request(url, data=data,
        headers={'Content-Type': 'application/json'})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.loads(r.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:500]
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {'error': f'HTTP {e.code}: {body}'}
    except Exception as e:
        return {'error': str(e)}


def build_default_params(sig):
    """Build default params from method signature metadata."""
    params = {}
    for p in sig:
        name = p['name']
        default = p.get('default')
        annotation = p.get('annotation', '')

        if name == 'params':
            continue
        if name == 'symbols':
            params[name] = ['BTC/USDT']
        elif name == 'symbol':
            params[name] = 'BTC/USDT'
        elif name == 'timeframe':
            params[name] = '1d'
        elif name == 'limit':
            params[name] = 1
        elif name == 'since':
            continue
        elif name == 'codes':
            continue
        elif default is not None:
            # Use default if it's not None
            if default != 'None' and str(default) != '':
                pass  # skip, let ccxt use default
        # else: skip unknown optional params
    return params


def retry_with_fixes(method, sig, error_msg, timing):
    """Try alternative parameters on failure."""
    fixes = []

    symbol_found = any(p['name'] == 'symbol' for p in sig)
    if symbol_found and 'BTC/USDT' in error_msg:
        fixes.append({'symbol': 'ETH/USDT'})

    if symbol_found and ('not found' in error_msg.lower() or 'invalid' in error_msg.lower()):
        for alt in ['ETH/USDT', 'BTC/USDT', 'BTC/USDT:USDT', 'BTCUSDT']:
            if alt not in str(fixes):
                fixes.append({'symbol': alt})
                break

    if 'timeframe' in error_msg.lower():
        fixes.append({'timeframe': '1h'})
        fixes.append({'timeframe': '1m'})

    if 'limit' in error_msg.lower():
        fixes.append({'limit': 5})

    # Try fixes
    for fix in fixes:
        test_params = build_default_params(sig)
        test_params.update(fix)
        result = api_execute(method, test_params)
        if 'response' in result and 'error' not in result:
            timing = result.get('timing', {})
            return result, f'✅ fixed with {fix}'
        else:
            err = result.get('error', 'unknown')
            if 'symbol' in str(fix).lower() and ('not found' in err.lower() or 'invalid' in err.lower()):
                continue
            if 'timeframe' in str(fix) and 'timeframe' in err.lower():
                continue

    return None, None


def main():
    print(f'\n{"=" * 90}')
    print(f'  PREFLIGHT CHECK: {EXCHANGE} @ {BASE_URL}')
    print(f'  Started: {time.strftime("%Y-%m-%d %H:%M:%S")}')
    print(f'{"=" * 90}\n')

    methods_data = api_get(f'/ccxt-api/api/methods/{EXCHANGE}')
    if 'error' in methods_data:
        print(f'  ❌ Failed to load methods: {methods_data["error"]}')
        sys.exit(1)

    categories = methods_data.get('categories', {})
    signatures = methods_data.get('signatures', {})

    all_public = []
    for cat_name, methods in categories.items():
        for m in methods:
            if not m['auth_required']:
                all_public.append((cat_name, m['name']))

    unique_methods = list(dict.fromkeys(all_public))

    if not unique_methods:
        print('  No public methods found.')
        sys.exit(0)

    print(f'  Found {len(unique_methods)} public methods to test\n')

    # Header
    print(f'  {"№":>3} {"Method":<32} {"Status":<8} {"Gen(ms)":<8} {"RTT(ms)":<8} {"Note"}')
    print(f'  {"─"*3} {"─"*32} {"─"*8} {"─"*8} {"─"*8} {"─"*40}')

    results = []
    for idx, (cat, method) in enumerate(unique_methods, 1):
        sig = signatures.get(method, [])
        params = build_default_params(sig)

        t0 = time.perf_counter()
        result = api_execute(method, params)
        elapsed = (time.perf_counter() - t0) * 1000

        if 'response' in result and 'error' not in result:
            timing = result.get('timing', {})
            gen = timing.get('gen_ms', '?')
            rtt = timing.get('rtt_ms', '?')
            resp = result['response']
            resp_type = type(resp).__name__
            resp_len = len(resp) if isinstance(resp, (list, dict)) else '-'
            note = f'{resp_type}({resp_len})'
            status = '✅'
            results.append((status, method, gen, rtt, note))
            print(f'  {idx:>3} {method:<32} {status:<8} {str(gen):<8} {str(rtt):<8} {note}')
        else:
            error = result.get('error', 'unknown error')

            # Check if it's a WS method — test via SSE stream
            if method.endswith('_ws'):
                ws_params = build_default_params(sig)
                ws_url = f'{BASE_URL}/ccxt-api/api/ws-stream?method={method}&params={quote(json.dumps(ws_params))}'
                try:
                    ws_resp = requests.get(ws_url, stream=True, timeout=15)
                    got_connected = False
                    got_message = False
                    for line in ws_resp.iter_lines(decode_unicode=True):
                        if line and line.startswith('data: '):
                            payload = json.loads(line[6:])
                            if payload.get('type') == 'connected':
                                got_connected = True
                            if payload.get('type') == 'message':
                                got_message = True
                        if got_connected and got_message:
                            break
                    ws_resp.close()
                    if got_connected and got_message:
                        status = '✅'
                        results.append((status, method, '-', '-', 'WS stream SSE'))
                        print(f'  {idx:>3} {method:<32} {status:<8} {"-":<8} {"-":<8} WS stream SSE')
                        continue
                except Exception as e:
                    error = str(e)[:80]

            # Try REST fixes
            timing = result.get('timing', {})
            gen = timing.get('gen_ms', '?')
            rtt = timing.get('rtt_ms', '?')

            fix_result, fix_note = retry_with_fixes(method, sig, error, timing)
            if fix_result:
                gen = fix_result.get('timing', {}).get('gen_ms', '?')
                rtt = fix_result.get('timing', {}).get('rtt_ms', '?')
                status = '⚠️'
                results.append((status, method, gen, rtt, fix_note))
                print(f'  {idx:>3} {method:<32} {status:<8} {str(gen):<8} {str(rtt):<8} {fix_note}')
            else:
                # Categorize error
                error_lower = error.lower()
                if 'ws' in method or 'websocket' in error_lower:
                    note = 'WS endpoint (REST unsupported)'
                elif 'rate' in error_lower and 'limit' in error_lower:
                    note = 'Rate limited'
                elif 'not found' in error_lower or 'invalid symbol' in error_lower:
                    note = f'Bad params: {error[:60]}'
                else:
                    note = error[:80]
                status = '❌'
                results.append((status, method, '-', '-', note))
                print(f'  {idx:>3} {method:<32} {status:<8} {"-":<8} {"-":<8} {note}')

    # Summary
    passed = sum(1 for r in results if r[0] == '✅')
    warned = sum(1 for r in results if r[0] == '⚠️')
    failed = sum(1 for r in results if r[0] == '❌')
    total = len(results)

    print(f'  {"─"*3} {"─"*32} {"─"*8} {"─"*8} {"─"*8} {"─"*40}')
    print(f'\n  Results: ✅ {passed} working, ⚠️ {warned} partial, ❌ {failed} failed — {total} total\n')

    if failed > 0:
        print('  Failed methods detail:')
        print(f'  {"─"*80}')
        for r in results:
            if r[0] == '❌':
                print(f'    ❌ {r[1]:<32} → {r[4]}')
        print()

    # Save report
    report = {
        'exchange': EXCHANGE,
        'timestamp': time.strftime('%Y-%m-%d %H:%M:%S'),
        'total': total,
        'passed': passed,
        'warned': warned,
        'failed': failed,
        'results': [
            {'method': r[1], 'status': r[0], 'gen_ms': r[2], 'rtt_ms': r[3], 'note': r[4]}
            for r in results
        ],
    }
    return report


if __name__ == '__main__':
    report = main()
    report_path = f'/home/user_aioc/workspace/share/docs/01_fundament_rf/ccxt_preflight_report.json'
    import os
    os.makedirs(os.path.dirname(report_path), exist_ok=True)
    with open(report_path, 'w') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    print(f'\n  Report saved: {report_path}\n')
