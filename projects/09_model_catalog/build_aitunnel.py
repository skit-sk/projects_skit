#!/usr/bin/env python3
"""Update aitunnel.json with full 152 model list from aitunnel.ru/models"""
import json, re, sys
from pathlib import Path

OUT = Path(__file__).resolve().parent / "ai_providers" / "aitunnel.json"

text = """Qwen3.7 Max 480 1440 1000000
Grok Build 0.1 192 384 256000
Gemini 3.5 Flash 288 1728 1048576
Gemini 3.1 Flash Lite 48 288 1048576
Grok 4.3 240 480 1000000
Qwen3.5 Plus 2026-04-20 76.8 460.8 1000000
Qwen3.6 Flash 48 288 1000000
Qwen3.6 35b A3b 30.95 185.34 262144
Qwen3.6 Max Preview 249.6 1497.6 262144
Qwen3.6 27b 37.44 299.52 262144
GPT 5.5 Pro 576 34560 1050000
GPT 5.5 96 5760 1050000
DeepSeek V4 Pro 83.52 167.04 1048576
DeepSeek V4 Flash 19.2 38.4 1048576
Kimi K2.6 182.4 768 262144
Claude Opus 4.7 960 4800 1000000
GLM 5.1 268.8 844.8 202752
Gemma 4 26b A4b It 24.96 76.8 262144
Gemma 4 31b It 26.88 76.8 262144
GLM 5v Turbo 230.4 768 202752
Grok 4.20 Multi Agent 384 1152 2000000
Grok 4.20 384 1152 2000000
MiniMax M2.7 57.6 230.4 204800
GPT 5.4 Nano 3.84 240 400000
GPT 5.4 Mini 14.4 864 400000
Mistral Small 2603 28.8 115.2 262144
GLM 5 Turbo 184.32 614.4 202752
Qwen3.5 9b 19.2 28.8 262144
GPT 5.4 Pro 576 34560 1050000
GPT 5.4 48 2880 1050000
GPT 5.3 Chat 33.6 2688 128000
Gemini 3.1 Flash Lite Preview 48 288 1048576
Qwen3.5 35b A3b 48 384 262144
Qwen3.5 27b 57.6 460.8 262144
Qwen3.5 122b A10b 76.8 614.4 262144
Qwen3.5 Flash 02 23 19.2 76.8 1000000
Gemini 3.1 Pro Preview Customtools 38.4 2304 1048576
GPT 5.3 Codex 33.6 2688 400000
Gemini 3.1 Pro Preview 38.4 2304 1048576
Claude Sonnet 4.6 57.6 2880 1000000
Qwen3.5 Plus 02 15 76.8 460.8 1000000
Qwen3.5 397b A17b 115.2 691.2 256000
MiniMax M2.5 52.03 230.4 196608
GLM 5 57.6 489.6 204800
Qwen3 Max Thinking 230.4 1152 262144
Claude Opus 4.6 960 4800 1000000
Qwen3 Coder Next 38.4 288 262144
Kimi K2.5 96 537.6 262144
MiniMax M2 Her 51.84 230.4 65536
GPT Audio 480 1920 128000
GPT Audio Mini 115.2 460.8 128000
GLM 4.7 Flash 9.61 76.8 202752
GPT 5.2 Codex 33.6 2688 400000
MiniMax M2.1 46.09 182.4 196608
GLM 4.7 38.4 288 202752
Gemini 3 Flash Preview 96 576 1048576
GPT 5.2 Chat 33.6 2688 128000
GPT 5.2 Pro 403.2 32256 400000
GPT 5.2 33.6 2688 400000
GLM 4.6v 57.6 172.8 131072
GPT 5.1 Codex Max 24 1920 400000
Mistral Large 2512 96 288 262144
DeepSeek V3.2 Speciale 53.76 80.64 131072
DeepSeek V3.2 53.76 80.64 131072
Claude Opus 4.5 960 4800 200000
GPT 5.1 24 1920 400000
GPT 5.1 Chat 24 1920 128000
GPT 5.1 Codex 24 1920 400000
GPT 5.1 Codex Mini 28.8 1152 400000
Kimi K2 Thinking 86.4 451.2 262144
Sonar Pro Search 576 2880 200000
GPT OSS Safeguard 20b 14.4 57.6 131072
MiniMax M2 43.18 192 196608
Claude Haiku 4.5 192 960 200000
GPT 5 Pro 288 23040 400000
GLM 4.6 33.6 288 202752
Claude Sonnet 4.5 576 2880 1000000
DeepSeek V3.2 Exp 51.84 78.72 163840
Gemini 2.5 Flash Lite Preview 09 2025 19.2 76.8 1048576
Qwen3 Max 230.4 1152 256000
GPT 5 Codex 24 1920 400000
DeepSeek V3.1 Terminus 51.84 192 131072
Kimi K2 0905 74.88 364.8 262144
DeepSeek Chat V3.1 51.84 211.2 131072
Mistral Medium 3.1 76.8 384 131072
GLM 4.5v 94.12 345.6 65536
GPT 5 Chat 24 1920 400000
GPT 5 24 1920 400000
GPT 5 Mini 4.8 384 400000
GPT 5 Nano 0.96 76.8 400000
GPT OSS 120b 28.8 115.2 131072
GPT OSS 20b 9.6 38.4 131072
Claude Opus 4.1 2880 14400 200000
Codestral 2508 57.6 172.8 256000
Qwen3 Coder 30b A3b Instruct 11.52 48 262144
GLM 4.5 33.6 297.6 131072
GLM 4.5 Air 20.17 163.2 131072
GLM 4 32b 19.2 19.2 128000
Qwen3 Coder 57.6 230.4 262144
Gemini 2.5 Flash Lite 19.2 76.8 1048576
Qwen3 235b A22b 2507 14.98 59.9 262144
Devstral Small 13.44 53.76 128000
Mistral Small 3.2 24b Instruct 11.52 34.56 131072
MiniMax M1 76.8 422.4 1000000
Gemini 2.5 Flash 57.6 480 1048576
Gemini 2.5 Pro 240 1920 1048576
O3 Pro 1000 8500 200000
Gemini 2.5 Pro Preview 240 1920 1048576
DeepSeek R1 0528 96 418.56 163840
Claude Opus 4 2880 14400 200000
Claude Sonnet 4 576 2880 200000
Qwen3 30b A3b 3.84 15.36 40960
O3 192 1536 200000
O4 Mini 105.6 844.8 200000
GPT 4.1 192 1536 1047576
GPT 4.1 Mini 38.4 307.2 1047576
GPT 4.1 Nano 9.6 76.8 1047576
Llama 4 Maverick 38.4 115.2 1048576
Llama 4 Scout 15.36 86.4 328000
DeepSeek Chat V3 0324 51.84 211.2 640000
O1 Pro 7500 70000 200000
GPT 4o Mini Search Preview 14.4 115.2 128000
GPT 4o Search Preview 240 1920 128000
Sonar Reasoning Pro 384 1536 128000
Sonar Pro 576 2880 200000
Sonar Deep Research 384 1536 128000
Gemini 2.0 Flash Lite 001 14.4 57.6 1048576
Gemini 2.0 Flash 001 19.2 76.8 1000000
O3 Mini 105.6 844.8 128000
Sonar 192 192 127072
DeepSeek R1 105.6 420.48 640000
MiniMax 01 38.4 211.2 1000192
DeepSeek Chat 26.88 53.76 640000
O1 1150 7200 200000
Llama 3.3 70b Instruct 23.04 57.6 131072
GPT-4o 2024-11-20 240 1920 128000
Claude 3.5 Haiku 192 960 200000
Llama 3.2 1b Instruct 1.92 1.92 131072
Llama 3.2 3b Instruct 2.88 4.8 131072
Llama 3.2 11b Vision Instruct 10.56 10.56 131072
GPT-4o 2024-08-06 240 1920 128000
Mistral Nemo 3.84 7.68 131072
GPT 4o Mini 14.4 115.2 128000
GPT-4o-Mini 2024-07-18 14.4 115.2 128000
GPT 4o 240 1920 128000
GPT 4 Turbo 1920 5760 128000
GPT 4 5760 11520 8191
GPT 3.5 Turbo 96 288 16385
GPT-5-Mini 2025-08-07 4.8 384 400000
GigaChat 2 111 111 128000
GigaChat 2 Pro 850 850 128000
GigaChat 2 Max 1105 1105 128000"""

models = []
for line in text.strip().split('\n'):
    parts = line.rsplit(' ', 3)
    if len(parts) < 4:
        continue
    name = parts[0].strip()
    inp = float(parts[1])
    out = float(parts[2])
    ctx = int(parts[3])
    
    mid = name.lower()
    # Skip known non-text models
    has_audio = 'audio' in mid
    has_vision = any(k in mid for k in ['vision', 'vl', 'gemini', 'claude-opus', 'claude-sonnet', 'gpt-4o', 'gpt-5', 'grok', 'lyria'])
    has_image = any(k in mid for k in ['gpt-image', 'dall-e', 'flux', 'seedream'])
    
    caps = {'text': True}
    if has_audio:
        caps['audio'] = True
    if has_vision or has_image:
        caps['image'] = True
    
    mtype = 'llm'
    if has_audio:
        mtype = 'asr+summarize'
    
    audio_flag = True if has_audio else False
    
    models.append({
        'id': name,
        'name': name,
        'pricing': {'input_rub': inp, 'output_rub': out},
        'context': ctx,
        'capabilities': caps,
        'type': mtype,
        'in_opencode': name in ['claude-sonnet-4-20250514', 'mistral-nemo']
    })

output = {
    'provider': 'aitunnel',
    'label': 'AITunnel',
    'homepage': 'https://aitunnel.ru',
    'balance': 'prepaid',
    'updated': '2026-05-23',
    'opencode_prefix': 'aitunnel/',
    'models_count': len(models),
    'pricing_unit': 'RUB per 1M tokens',
    'models': models
}

OUT.parent.mkdir(parents=True, exist_ok=True)
with open(OUT, 'w', encoding='utf-8') as f:
    json.dump(output, f, ensure_ascii=False, indent=1)

print(f"✅ {OUT.name}: {len(models)} models (was 2)")
audio_count = sum(1 for m in models if m['capabilities'].get('audio'))
print(f"   Audio-capable: {audio_count}")
print(f"   Price range: {min(m['pricing']['input_rub'] for m in models)}-{max(m['pricing']['input_rub'] for m in models)} RUB input")
