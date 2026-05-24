"""Сборщик JSON-файлов провайдеров в ai_providers/"""
import json, os, sys

OUT_DIR = os.path.join(os.path.dirname(__file__), "ai_providers")
os.makedirs(OUT_DIR, exist_ok=True)


def save(name, data):
    path = os.path.join(OUT_DIR, name)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print(f"✅ {name}: {data.get('models_count', len(data.get('models', [])))} models")


# ─── 1. openrouter.json (358 models, pricing) ──────────────────────────────
def build_openrouter():
    from pathlib import Path
    p = Path.home() / ".local/share/opencode/tool-output/tool_e55bf92cc001AO6tlI0h16ct1R"
    if not p.exists():
        print("⚠️ openrouter source not found")
        return
    data = json.loads(p.read_text())
    models = data["data"]
    out = {
        "provider": "openrouter", "label": "OpenRouter",
        "homepage": "https://openrouter.ai",
        "balance": "prepaid", "updated": "2026-05-23",
        "opencode_prefix": "openrouter/",
        "models_count": len(models),
        "pricing_unit": "USD per token",
        "models": []
    }
    for m in models:
        p = m.get("pricing", {})
        inp = float(p.get("prompt", 0) or 0)
        out_cost = float(p.get("completion", 0) or 0)
        mid = m["id"].lower()
        caps = {"text": True}
        if any(k in mid for k in ["gemini","lyria","gpt-audio","gpt-4o-audio","omni"]):
            caps["audio"] = True
        if "vl-" in mid or "vision" in mid or "image" in mid:
            caps["image"] = True
        mtype = "llm"
        if caps.get("audio"): mtype = "asr+summarize"
        if "ocr" in mid: mtype = "ocr"
        if "mt-" in mid or "translate" in mid: mtype = "translation"
        if "embed" in mid: mtype = "embedding"
        out["models"].append({
            "id": m["id"], "name": m.get("name", ""),
            "pricing": {"input": inp, "output": out_cost},
            "context": m.get("context_length"),
            "capabilities": caps, "type": mtype
        })
    save("openrouter.json", out)


# ─── 2. novita-ai.json (104 models, pricing) ─────────────────────────────
def build_novita():
    from pathlib import Path
    p = Path.home() / ".local/share/opencode/tool-output/tool_e55c06a58001MXE1HQbPRHIjl8"
    if not p.exists():
        print("⚠️ novita source not found")
        return
    data = json.loads(p.read_text())
    models = data["data"]
    out = {
        "provider": "novita-ai", "label": "Novita AI",
        "homepage": "https://novita.ai",
        "balance": "prepaid", "updated": "2026-05-23",
        "opencode_prefix": "novita-ai/",
        "models_count": len(models),
        "pricing_unit": "units (divide raw/1e7 for USD per 1M tok)",
        "models": []
    }
    for m in models:
        inp = m.get("input_token_price_per_m", 0) or 0
        out_raw = m.get("output_token_price_per_m", 0) or 0
        mid = m["id"].lower()
        caps = {"text": True}
        if any(k in mid for k in ["omni","glm-asr","whisper","speech","tts"]):
            caps["audio"] = True
        if any(k in mid for k in ["ocr","vl-"]):
            caps["image"] = True
        mtype = "llm"
        if caps.get("audio"): mtype = "asr"
        if "ocr" in mid: mtype = "ocr"
        if "mt-" in mid or "translate" in mid: mtype = "translation"
        if "embed" in mid: mtype = "embedding"
        out["models"].append({
            "id": m["id"], "name": m.get("title", ""),
            "pricing": {"input": inp, "output": out_raw},
            "context": None, "capabilities": caps, "type": mtype
        })
    save("novita-ai.json", out)


# ─── 3. apiyi.json (362 models, no pricing) ──────────────────────────────
def build_apiyi():
    models_raw = ""
    models_raw += "bge-m3,bge-reranker-v2-m3,chat-latest,chatgpt-4o-latest,chatgpt-image-latest,"
    models_raw += "claude-haiku-4-5-20251001,claude-haiku-4-5-20251001-thinking,"
    models_raw += "claude-opus-4-1-20250805,claude-opus-4-1-20250805-thinking,"
    models_raw += "claude-opus-4-5-20251101,claude-opus-4-5-20251101-thinking,"
    models_raw += "claude-opus-4-6,claude-opus-4-6-thinking,claude-opus-4-7,claude-opus-4-7-thinking,"
    models_raw += "claude-sonnet-4-20250514,claude-sonnet-4-20250514-thinking,"
    models_raw += "claude-sonnet-4-5-20250929,claude-sonnet-4-5-20250929-thinking,"
    models_raw += "claude-sonnet-4-6,claude-sonnet-4-6-thinking,dall-e-3,"
    models_raw += "deepseek-chat,deepseek-ocr,deepseek-r1,deepseek-r1-0528,deepseek-r1-250528,"
    models_raw += "deepseek-r1-distill-qwen-32b,deepseek-reasoner,"
    models_raw += "deepseek-v3,deepseek-v3-0324,deepseek-v3-1-250821,deepseek-v3-20250324,deepseek-v3-250324,"
    models_raw += "deepseek-v3.1,deepseek-v3.1-fast,deepseek-v3.1-terminus,"
    models_raw += "deepseek-v3.2,deepseek-v3.2-exp,deepseek-v3.2-fast,"
    models_raw += "deepseek-v4-flash,deepseek-v4-pro,"
    models_raw += "doubao-seed-1-6-250615,doubao-seed-1-6-251015,doubao-seed-1-8-251228,"
    models_raw += "flux-2-flex,flux-2-klein-4b,flux-2-klein-9b,flux-2-max,flux-2-pro,"
    models_raw += "flux-dev,flux-kontext-max,flux-kontext-pro,flux-pro,flux-pro-1.1,flux-pro-1.1-ultra,"
    models_raw += "gemini-2.5-computer-use-preview-10-2025,"
    models_raw += "gemini-2.5-flash,gemini-2.5-flash-image,gemini-2.5-flash-image-preview,"
    models_raw += "gemini-2.5-flash-lite,gemini-2.5-flash-lite-preview-06-17,gemini-2.5-flash-lite-preview-09-2025,"
    models_raw += "gemini-2.5-flash-nothinking,gemini-2.5-flash-preview,gemini-2.5-flash-preview-04-17,"
    models_raw += "gemini-2.5-flash-preview-05-20,gemini-2.5-flash-preview-09-2025,"
    models_raw += "gemini-2.5-flash-preview-09-2025-nothinking,gemini-2.5-flash-preview-09-2025-thinking,"
    models_raw += "gemini-2.5-flash-thinking,gemini-2.5-flash-tts,"
    models_raw += "gemini-2.5-pro,gemini-2.5-pro-exp,gemini-2.5-pro-exp-03-25,"
    models_raw += "gemini-2.5-pro-nothinking,gemini-2.5-pro-preview-03-25,gemini-2.5-pro-preview-05-06,"
    models_raw += "gemini-2.5-pro-preview-06-05,gemini-2.5-pro-preview-tts,"
    models_raw += "gemini-2.5-pro-thinking,gemini-2.5-pro-tts,"
    models_raw += "gemini-3-flash-preview,gemini-3-flash-preview-nothinking,gemini-3-flash-preview-thinking,"
    models_raw += "gemini-3-pro-image-preview,gemini-3-pro-image-preview-1k,"
    models_raw += "gemini-3-pro-image-preview-2k,gemini-3-pro-image-preview-4k,"
    models_raw += "gemini-3-pro-preview,gemini-3-pro-preview-thinking,"
    models_raw += "gemini-3.1-flash-image-preview,gemini-3.1-flash-image-preview-4k,"
    models_raw += "gemini-3.1-flash-lite,gemini-3.1-flash-lite-preview,"
    models_raw += "gemini-3.1-pro-preview,gemini-3.1-pro-preview-customtools,gemini-3.1-pro-preview-thinking,"
    models_raw += "gemini-3.5-flash,gemini-embedding-001,gemini-embedding-2-preview,"
    models_raw += "glm-4.5,glm-4.5-air,glm-4.5v,glm-4.6,glm-4.7,glm-5,glm-5.1,"
    models_raw += "gpt-3.5-turbo,gpt-3.5-turbo-0125,gpt-3.5-turbo-0613,gpt-3.5-turbo-1106,"
    models_raw += "gpt-3.5-turbo-16k,gpt-3.5-turbo-16k-0613,gpt-4-32k,gpt-4-turbo,"
    models_raw += "gpt-4.1,gpt-4.1-2025-04-14,gpt-4.1-mini,gpt-4.1-mini-2025-04-14,"
    models_raw += "gpt-4.1-nano,gpt-4.1-nano-2025-04-14,"
    models_raw += "gpt-4o,gpt-4o-2024-05-13,gpt-4o-2024-08-06,gpt-4o-2024-11-20,"
    models_raw += "gpt-4o-mini,gpt-4o-mini-2024-07-18,gpt-4o-mini-audio-preview,"
    models_raw += "gpt-4o-mini-transcribe,gpt-4o-transcribe,"
    models_raw += "gpt-5,gpt-5-2025-08-07,gpt-5-chat-latest,gpt-5-codex,"
    models_raw += "gpt-5-codex-high,gpt-5-codex-medium,gpt-5-high,gpt-5-medium,"
    models_raw += "gpt-5-mini,gpt-5-mini-2025-08-07,gpt-5-minimal,"
    models_raw += "gpt-5-nano,gpt-5-nano-2025-08-07,"
    models_raw += "gpt-5-pro,gpt-5-pro-2025-10-06,"
    models_raw += "gpt-5.1,gpt-5.1-2025-11-13,gpt-5.1-all,gpt-5.1-chat-latest,"
    models_raw += "gpt-5.1-codex,gpt-5.1-codex-high,gpt-5.1-codex-max,gpt-5.1-codex-medium,gpt-5.1-codex-mini,"
    models_raw += "gpt-5.1-thinking-all,"
    models_raw += "gpt-5.2,gpt-5.2-2025-12-11,gpt-5.2-chat-latest,gpt-5.2-codex,"
    models_raw += "gpt-5.2-high,gpt-5.2-pro,gpt-5.2-pro-2025-12-11,"
    models_raw += "gpt-5.3-all,gpt-5.3-chat,gpt-5.3-chat-latest,gpt-5.3-codex,"
    models_raw += "gpt-5.3-instant-all,gpt-5.3-thinking-all,"
    models_raw += "gpt-5.4,gpt-5.4-mini,gpt-5.4-nano,gpt-5.4-nano-2026-03-17,"
    models_raw += "gpt-5.4-pro,gpt-5.4-pro-2026-03-05,gpt-5.4-thinking-all,"
    models_raw += "gpt-5.5,gpt-5.5-pro,"
    models_raw += "gpt-image-1,gpt-image-1-mini,gpt-image-1.5,gpt-image-1.5-2025-12-16,"
    models_raw += "gpt-image-2,gpt-image-2-all,gpt-image-2-vip,"
    models_raw += "gpt-oss-120b,gpt-oss-120b-1,gpt-oss-20b,"
    models_raw += "grok-2-image,grok-2-image-1212,grok-2-image-latest,"
    models_raw += "grok-4,grok-4-0709,grok-4-1-fast,grok-4-1-fast-non-reasoning,"
    models_raw += "grok-4-1-fast-non-reasoning-latest,grok-4-1-fast-reasoning,grok-4-1-fast-reasoning-latest,"
    models_raw += "grok-4-fast,grok-4-fast-non-reasoning,grok-4-fast-non-reasoning-latest,"
    models_raw += "grok-4-fast-reasoning,grok-4-fast-reasoning-latest,grok-4-latest,"
    models_raw += "grok-4.20-beta,grok-4.20-beta-0309-non-reasoning,grok-4.20-beta-0309-reasoning,"
    models_raw += "grok-4.20-multi-agent-beta-0309,grok-4.3,"
    models_raw += "grok-code-fast,grok-code-fast-1,grok-code-fast-1-0825,"
    models_raw += "kimi-k2-0711-preview,kimi-k2-0905,kimi-k2-128k,kimi-k2-250711,"
    models_raw += "kimi-k2-instruct,kimi-k2-thinking,kimi-k2.5,kimi-k2.6,"
    models_raw += "longcat-flash-chat,longcat-flash-thinking,"
    models_raw += "mimo-v2-omni,mimo-v2-pro,"
    models_raw += "MiniMax-M2.1,MiniMax-M2.5,MiniMax-M2.5-lightning,MiniMax-M2.7,MiniMax-M2.7-highspeed,"
    models_raw += "multimodal-embedding-v1,"
    models_raw += "nano-banana,nano-banana-2,nano-banana-pro,"
    models_raw += "o1,o1-2024-12-17,o1-mini,o1-mini-2024-09-12,o1-preview,o1-preview-2024-09-12,"
    models_raw += "o1-pro,o1-pro-2025-03-19,"
    models_raw += "o3,o3-2025-04-16,o3-deep-research-2025-06-26,"
    models_raw += "o3-mini,o3-mini-2025-01-31,o3-mini-2025-01-31-high,"
    models_raw += "o3-mini-2025-01-31-low,o3-mini-2025-01-31-medium,"
    models_raw += "o3-mini-low,o3-mini-medium,"
    models_raw += "o3-pro,o3-pro-2025-06-10,o4-mini,o4-mini-2025-04-16,"
    models_raw += "omni-moderation-2024-09-26,omni-moderation-latest,"
    models_raw += "qvq-max,qvq-max-2025-05-15,qvq-max-latest,qvq-plus,qvq-plus-2025-05-15,"
    models_raw += "qwen-long,qwen-max,qwen-max-latest,qwen-max-longcontext,"
    models_raw += "qwen-mt-plus,qwen-mt-turbo,"
    models_raw += "qwen-plus,qwen-plus-2025-07-14,qwen-plus-2025-09-11,qwen-plus-latest,"
    models_raw += "qwen-turbo,qwen-turbo-2025-07-15,qwen-turbo-latest,"
    models_raw += "qwen-vl-max,qwen-vl-max-latest,qwen-vl-ocr,qwen-vl-ocr-2025-11-20,"
    models_raw += "qwen-vl-ocr-latest,qwen-vl-plus,qwen-vl-plus-latest,"
    models_raw += "qwen2-72b-instruct,qwen2-vl-72b-instruct,qwen2-vl-7b-instruct,"
    models_raw += "qwen2.5-32b-instruct,qwen2.5-72b-instruct,qwen2.5-7b-instruct,"
    models_raw += "qwen2.5-vl-32b-instruct,qwen2.5-vl-72b-instruct,qwen2.5-vl-7b-instruct,"
    models_raw += "qwen3-14b,qwen3-235b-a22b,qwen3-235b-a22b-instruct-2507,qwen3-235b-a22b-thinking-2507,"
    models_raw += "qwen3-30b-a3b,qwen3-30b-a3b-instruct-2507,qwen3-30b-a3b-thinking-2507,"
    models_raw += "qwen3-32b,"
    models_raw += "qwen3-coder,qwen3-coder-480b-a35b-instruct,qwen3-coder-flash,"
    models_raw += "qwen3-coder-plus,qwen3-coder-plus-2025-07-22,qwen3-coder-plus-2025-09-23,"
    models_raw += "qwen3-max,qwen3-max-2025-09-23,qwen3-max-preview,"
    models_raw += "qwen3-next-80b-a3b-instruct,qwen3-next-80b-a3b-thinking,"
    models_raw += "qwen3-omni-flash,qwen3-omni-flash-2025-09-15,"
    models_raw += "qwen3-vl-235b-a22b-instruct,qwen3-vl-235b-a22b-thinking,"
    models_raw += "qwen3-vl-30b-a3b-thinking,qwen3-vl-32b-thinking,"
    models_raw += "qwen3-vl-embedding,qwen3-vl-flash,qwen3-vl-flash-2025-10-15,"
    models_raw += "qwen3-vl-plus,qwen3-vl-plus-2025-09-23,"
    models_raw += "qwen3.5-122b-a10b,qwen3.5-27b,qwen3.5-35b-a3b,qwen3.5-397b-a17b,"
    models_raw += "qwen3.5-flash,qwen3.5-flash-2026-02-23,qwen3.5-plus,qwen3.5-plus-2026-02-15,"
    models_raw += "qwen3.6-27b,qwen3.6-35b-a3b,qwen3.6-flash,qwen3.6-max-preview,qwen3.6-plus,"
    models_raw += "qwen3.7-max,"
    models_raw += "qwq-32b,qwq-plus,qwq-plus-2025-03-05,qwq-plus-latest,"
    models_raw += "seed-1-6-250615,seed-1-6-flash-250615,seed-1-6-flash-250715,seed-1-8-251228,"
    models_raw += "seed-2-0-code-preview-260328,seed-2-0-lite-260228,seed-2-0-lite-260428,"
    models_raw += "seed-2-0-mini-260215,seed-2-0-mini-260428,seed-2-0-pro-260328,"
    models_raw += "seedream-4-0-250828,seedream-4-5-251128,seedream-5-0-260128,"
    models_raw += "step-3.5-flash,"
    models_raw += "text-embedding-3-large,text-embedding-3-small,text-embedding-ada-002,"
    models_raw += "text-embedding-v4,text-moderation-stable,"
    models_raw += "tongyi-embedding-vision-flash,tongyi-embedding-vision-plus,"
    models_raw += "veo-3.1-fast-generate-preview,veo-3.1-generate-preview"

    model_list = [m.strip() for m in models_raw.split(",") if m.strip()]
    out = {
        "provider": "apiyi", "label": "APIyi",
        "homepage": "https://api.apiyi.com",
        "api_endpoint": "https://api.apiyi.com/v1/models",
        "balance": "unknown",
        "updated": "2026-05-23",
        "opencode_prefix": "apiyi/",
        "models_count": len(model_list),
        "pricing_available": False,
        "models": []
    }
    for mid in model_list:
        ml = mid.lower()
        caps = {"text": True}
        if any(k in ml for k in ["gemini","gpt-4o-audio","gpt-4o-mini-audio","gpt-audio","gpt-4o-mini-transcribe","gpt-4o-transcribe","omni","flash-tts","pro-tts","voice"]):
            caps["audio"] = True
        if any(k in ml for k in ["flux","dall-e","gpt-image","seedream","image"]):
            caps["image"] = True
        if any(k in ml for k in ["vl-","ocr","vl/"]):
            caps["image"] = True
        mtype = "llm"
        if caps.get("audio"): mtype = "asr+summarize"
        if "ocr" in ml: mtype = "ocr"
        if "mt-" in ml or "translate" in ml or "mt/" in ml: mtype = "translation"
        if "embed" in ml or "bge-" in ml: mtype = "embedding"
        if "flux" in ml or "dall-e" in ml or "seedream" in ml: mtype = "image_gen"
        if "veo" in ml: mtype = "video_gen"
        out["models"].append({
            "id": mid, "name": mid,
            "pricing": None,
            "context": None,
            "capabilities": caps,
            "type": mtype,
            "notes": "pricing unavailable without API key"
        })
    save("apiyi.json", out)


# ─── 4. deepseek.json (4 models) ───────────────────────────────────────
def build_deepseek():
    models = [
        {"id": "deepseek-v4-flash", "name": "DeepSeek V4 Flash", "type": "llm"},
        {"id": "deepseek-v4-pro", "name": "DeepSeek V4 Pro", "type": "llm"},
        {"id": "deepseek-chat", "name": "DeepSeek Chat (deprecated)", "type": "llm"},
        {"id": "deepseek-reasoner", "name": "DeepSeek Reasoner (deprecated)", "type": "llm"},
    ]
    out = {
        "provider": "deepseek", "label": "DeepSeek",
        "homepage": "https://platform.deepseek.com",
        "api_endpoint": "https://api.deepseek.com/chat/completions",
        "balance": "needs-key", "updated": "2026-05-23",
        "opencode_prefix": "deepseek/",
        "models_count": len(models),
        "pricing_available": False,
        "models": [{"id": m["id"], "name": m["name"], "type": m["type"],
                     "pricing": None, "context": None,
                     "capabilities": {"text": True}} for m in models]
    }
    save("deepseek.json", out)


# ─── 5. deepgram.json (3 models) ──────────────────────────────────────
def build_deepgram():
    models = [
        {"id": "nova-3-monolingual", "name": "Deepgram Nova-3 Monolingual",
         "pricing": {"per_min": 0.0048}, "quality": 9, "languages": ["en","ru","de","fr","es","pt","it"]},
        {"id": "nova-3-multilingual", "name": "Deepgram Nova-3 Multilingual",
         "pricing": {"per_min": 0.0058}, "quality": 9, "languages": "45+"},
        {"id": "flux-multilingual", "name": "Deepgram Flux Multilingual",
         "pricing": {"per_min": 0.0078}, "quality": 8, "languages": "10"},
    ]
    out = {
        "provider": "deepgram", "label": "Deepgram",
        "homepage": "https://deepgram.com",
        "api_endpoint": "https://api.deepgram.com/v1/listen",
        "balance": "no_key", "free_tier": "$200 credit",
        "key_var": "DEEPGRAM_API_KEY",
        "updated": "2026-05-23",
        "models_count": len(models),
        "pricing_unit": "USD per minute",
        "models": models
    }
    save("deepgram.json", out)


# ─── 6. assemblyai.json (3 models) ────────────────────────────────────
def build_assemblyai():
    models = [
        {"id": "universal-2", "name": "AssemblyAI Universal-2",
         "pricing": {"per_hour": 0.15}, "quality": 8, "languages": "99+",
         "description": "12.5M hours training data, 99 languages"},
        {"id": "universal-3-pro", "name": "AssemblyAI Universal-3 Pro",
         "pricing": {"per_hour": 0.21}, "quality": 9, "languages": "6 (en,es,de,fr,it,pt)",
         "description": "Most accurate, multilingual"},
    ]
    out = {
        "provider": "assemblyai", "label": "AssemblyAI",
        "homepage": "https://www.assemblyai.com",
        "api_endpoint": "https://api.assemblyai.com/v2/transcript",
        "balance": "no_key", "free_tier": "185h pre-recorded + 333h streaming",
        "key_var": "ASSEMBLYAI_API_KEY",
        "updated": "2026-05-23",
        "models_count": len(models),
        "pricing_unit": "USD per hour",
        "models": models
    }
    save("assemblyai.json", out)


# ─── 7-8. opencode.json + opencode-go.json (from CLI) ──────────────────
def build_opencode():
    out = {
        "provider": "opencode", "label": "OpenCode",
        "homepage": "https://opencode.ai",
        "balance": "prepaid", "updated": "2026-05-23",
        "opencode_prefix": "opencode/",
        "models_count": None,
        "pricing_available": False,
        "models": []
    }
    # key models from opencode list
    key_models = [
        "gemini-3.5-flash", "deepseek-v4-flash-free", "gpt-5.4-nano",
        "gpt-5.4", "gpt-5.5", "gpt-5.5-pro",
        "claude-sonnet-4-6", "claude-haiku-4-5", "claude-opus-4-7",
        "kimi-k2.5", "kimi-k2.6",
        "minimax-m2.5", "minimax-m2.7",
        "qwen3.5-plus", "qwen3.6-plus",
        "glm-5", "glm-5.1",
        "grok-build-0.1",
        "nemotron-3-super-free"
    ]
    out["models"] = [{"id": m, "name": m, "type": "llm", "pricing": None,
                       "context": None, "capabilities": {"text": True}} for m in key_models]
    out["models_count"] = len(key_models)
    save("opencode.json", out)

    out2 = {
        "provider": "opencode-go", "label": "OpenCode Go",
        "homepage": "https://opencode.ai",
        "balance": "prepaid", "updated": "2026-05-23",
        "opencode_prefix": "opencode-go/",
        "models_count": None,
        "pricing_available": False,
        "models": []
    }
    key_go = [
        "deepseek-v4-flash", "deepseek-v4-pro",
        "qwen3.5-plus", "qwen3.6-plus",
        "kimi-k2.5", "kimi-k2.6",
        "minimax-m2.5", "minimax-m2.7",
        "glm-5", "glm-5.1",
        "mimo-v2.5", "mimo-v2.5-pro"
    ]
    out2["models"] = [{"id": m, "name": m, "type": "llm", "pricing": None,
                        "context": None, "capabilities": {"text": True}} for m in key_go]
    out2["models_count"] = len(key_go)
    save("opencode-go.json", out2)


# ─── 9-10. aitunnel.json + minimax-cn.json ────────────────────────────
def build_small_providers():
    aitunnel = {
        "provider": "aitunnel", "label": "AI Tunnel",
        "homepage": None, "balance": "unknown",
        "updated": "2026-05-23",
        "opencode_prefix": "aitunnel/",
        "models_count": 2,
        "pricing_available": False,
        "models": [
            {"id": "claude-sonnet-4-20250514", "name": "Claude Sonnet 4", "type": "llm",
             "pricing": None, "capabilities": {"text": True}},
            {"id": "mistral-nemo", "name": "Mistral Nemo", "type": "llm",
             "pricing": None, "capabilities": {"text": True}},
        ]
    }
    save("aitunnel.json", aitunnel)

    minimax = {
        "provider": "minimax-cn", "label": "MiniMax China",
        "homepage": None, "balance": "unknown",
        "updated": "2026-05-23",
        "opencode_prefix": "minimax-cn/",
        "models_count": 6,
        "pricing_available": False,
        "models": [
            {"id": m, "name": m, "type": "llm", "pricing": None, "capabilities": {"text": True}}
            for m in ["MiniMax-M2", "MiniMax-M2.1", "MiniMax-M2.5", "MiniMax-M2.5-highspeed",
                       "MiniMax-M2.7", "MiniMax-M2.7-highspeed"]
        ]
    }
    save("minimax-cn.json", minimax)


# ─── 11. routerai.json (361 models from API) ─────────────────────────
def build_routerai():
    from pathlib import Path
    p = Path.home() / ".local/share/opencode/tool-output/tool_e55b5b099001IdWL5yD5Iqm3l1"
    if not p.exists():
        print("⚠️ routerai source not found")
        return
    api_data = json.loads(p.read_text())
    models = api_data.get("data", [])
    out = {
        "provider": "routerai", "label": "RouterAI Gateway",
        "homepage": "https://routerai.ru",
        "api_endpoint": "https://routerai.ru/api/v1/models",
        "balance": "prepaid", "updated": "2026-05-23",
        "opencode_prefix": "routerai/",
        "models_count": len(models),
        "pricing_available": False,
        "models": []
    }
    for m in models:
        mid = m.get("id", "")
        ml = mid.lower()
        caps = {"text": True}
        if any(k in ml for k in ["gemini","lyria","gpt-audio","gpt-4o-audio","omni","flash-tts","pro-tts"]):
            caps["audio"] = True
        if any(k in ml for k in ["flux","dall-e","gpt-image","seedream","image"]):
            caps["image"] = True
        if any(k in ml for k in ["vl-","ocr"]):
            caps["image"] = True
        mtype = "llm"
        if caps.get("audio"): mtype = "asr+summarize"
        if "ocr" in ml: mtype = "ocr"
        if "mt-" in ml or "translate" in ml: mtype = "translation"
        if "embed" in ml: mtype = "embedding"
        out["models"].append({
            "id": mid, "name": m.get("name", mid),
            "pricing": None, "context": None,
            "capabilities": caps, "type": mtype,
            "notes": "pricing not available via API"
        })
    save("routerai.json", out)


# ─── RUN ────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    build_openrouter()
    build_novita()
    build_apiyi()
    build_routerai()
    build_deepseek()
    build_deepgram()
    build_assemblyai()
    build_opencode()
    build_small_providers()
    print("\n✅ All provider files created in", OUT_DIR)
