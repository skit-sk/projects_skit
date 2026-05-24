#!/usr/bin/env python3
"""
Транскрипция видео/аудио через модели opencode.

Использование:
  python3 orchestrator.py <url> [--chain CHAIN] [--model MODEL] [--lang LANG]  [--uid UID]

Примеры:
  python3 orchestrator.py "https://youtu.be/dQw4w9WgXcQ"
  python3 orchestrator.py "url" --chain split-gpt-audio-dsv4
  python3 orchestrator.py "url" --model openrouter/openai/gpt-audio-mini
  python3 orchestrator.py "url" --lang en --chain one-pass-gpt4o-audio
"""
import argparse, json, os, sys
from pathlib import Path

PROJECT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = PROJECT_DIR / "config.yaml"
CATALOG_PATH = PROJECT_DIR / "models_catalog.json"


def load_catalog() -> dict:
    with open(CATALOG_PATH, encoding="utf-8") as f:
        return json.load(f)


def find_chain(catalog: dict, chain_id: str) -> dict | None:
    for c in catalog.get("chains", []):
        if c["id"] == chain_id:
            return c
    return None


def find_model_provider(catalog: dict, model_id: str) -> str | None:
    for prov in catalog.get("providers", []):
        provider_prefix = prov["id"].replace("_", "/") if "/" not in prov["id"] else prov["id"]
        if model_id.startswith(prov["id"]):
            return prov["id"]
        models = prov.get("models", {})
        if isinstance(models, dict):
            for m in models:
                full = f"{prov['id']}/{m}" if not m.startswith(prov['id']) else m
                if full == model_id:
                    return prov["id"]
        elif isinstance(models, list):
            for m in models:
                if m == model_id:
                    return prov["id"]
    return None


def make_output_path(topic: str, uid: str, chain_id: str, model_id: str,
                     is_tg: bool = False, tg_uid: str = "") -> str:
    model_short = model_id.replace("/", "-").split("/")[-1] if "/" in model_id else model_id[:20]
    model_short = model_short.replace(".", "-")[:20]
    fname = f"{topic}_{uid}_{chain_id}_{model_short}.md"

    if is_tg and tg_uid:
        base = os.path.expanduser(
            f"~/workspace/projects/07_tg_bot_aiforguest/TG_ALL/TG_{tg_uid}"
        )
        os.makedirs(base, exist_ok=True)
        return os.path.join(base, fname)

    out_dir = "/tmp/out_transcript"
    os.makedirs(out_dir, exist_ok=True)
    return os.path.join(out_dir, fname)


def main():
    parser = argparse.ArgumentParser(description="Транскрипция видео/аудио")
    parser.add_argument("url", help="YouTube URL или путь к аудиофайлу")
    parser.add_argument("--chain", default=None, help="ID цепочки из каталога")
    parser.add_argument("--model", default=None, help="Модель (переопределяет модель в цепочке)")
    parser.add_argument("--lang", default="ru", help="Язык транскрипции/суммаризации")
    parser.add_argument("--uid", default="anon", help="UID пользователя")
    parser.add_argument("--tg", action="store_true", help="Режим TG бота (файл в папку пользователя)")
    parser.add_argument("--tg-uid", default="", help="TG UID для пути файла")
    args = parser.parse_args()

    catalog = load_catalog()
    defaults = catalog.get("defaults", {})
    chain_id = args.chain or defaults.get("chain", "one-pass-gpt4o-audio")
    language = args.lang or defaults.get("language", "ru")

    if not os.path.exists(args.url) and not args.url.startswith("http"):
        print(f"❌ URL или файл не найден: {args.url}", file=sys.stderr)
        sys.exit(1)

    chain = find_chain(catalog, chain_id)
    if not chain:
        print(f"❌ Цепочка '{chain_id}' не найдена в каталоге", file=sys.stderr)
        print("  Доступные цепочки:", file=sys.stderr)
        for c in catalog.get("chains", []):
            print(f"    {c['id']}: {c['label']}", file=sys.stderr)
        sys.exit(1)

    # Determine model(s)
    model = args.model
    if chain["mode"] == "one-pass":
        models_list = chain.get("models", [])
        selected_model = model or models_list[0] if models_list else None
        if not selected_model:
            print("❌ Нет модели для one-pass цепочки", file=sys.stderr)
            sys.exit(1)
        print(f"🔧 Цепочка: {chain_id} ({chain['label']})")
        print(f"📦 Модель: {selected_model}")
        print(f"🔤 Язык: {language}")

        from audio import get_title, extract_topic
        title = get_title(args.url) if args.url.startswith("http") else os.path.basename(args.url)
        topic = extract_topic(title)
        out_path = make_output_path(topic, args.uid, chain_id, selected_model,
                                    args.tg, args.tg_uid)

        from pipeline_a import run as run_a
        result = run_a(args.url, model=selected_model, uid=args.uid,
                       chain=chain_id, language=language, out_path=out_path)

        if result.get("error"):
            print(f"❌ Ошибка: {result['error']}")
            sys.exit(1)
        print(f"✅ Готово: {result['output']}")
        print(f"⏱ {result.get('duration', 0):.1f}s · 💰 ${result.get('cost', 0):.4f} · "
              f"📊 {result.get('tokens', 0)} токенов")

    elif chain["mode"] == "split":
        models_dict = chain.get("models", {})
        asr_model = model or models_dict.get("asr", "")
        summ_model = models_dict.get("summarizer", "")

        if not asr_model:
            print("❌ Нет ASR модели для split цепочки", file=sys.stderr)
            sys.exit(1)
        print(f"🔧 Цепочка: {chain_id} ({chain['label']})")
        print(f"🎤 ASR: {asr_model}")
        print(f"🧠 Суммаризация: {summ_model}")
        print(f"🔤 Язык: {language}")

        from audio import get_title, extract_topic
        title = get_title(args.url) if args.url.startswith("http") else os.path.basename(args.url)
        topic = extract_topic(title)
        out_path = make_output_path(topic, args.uid, chain_id, asr_model,
                                    args.tg, args.tg_uid)

        from pipeline_b import run as run_b
        result = run_b(args.url, models={"asr": asr_model, "summarizer": summ_model},
                       uid=args.uid, chain=chain_id, language=language, out_path=out_path)

        if result.get("error"):
            print(f"❌ Ошибка: {result['error']}")
            sys.exit(1)
        print(f"✅ Готово: {result['output']}")
        print(f"⏱ {result.get('duration', 0):.1f}s · 💰 ${result.get('cost', 0):.4f} · "
              f"📊 {result.get('tokens', 0)} токенов")

    else:
        print(f"❌ Неизвестный режим цепочки: {chain.get('mode')}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
