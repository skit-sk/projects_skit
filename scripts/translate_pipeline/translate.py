#!/usr/bin/env python3
import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from openai import OpenAI


def load_providers(config_path: str) -> dict:
    with open(config_path, "r", encoding="utf-8") as f:
        config = json.load(f)

    env_vars = {
        "AITUNEL_API_KEY": os.environ.get("AITUNEL_API_KEY", ""),
        "ROUTERAI_API_KEY": os.environ.get("ROUTERAI_API_KEY", ""),
        "APIYI_API_KEY": os.environ.get("APIYI_API_KEY", ""),
        "OPENROUTER_API_KEY": os.environ.get("OPENROUTER_API_KEY", ""),
        "OPENCODE_API_KEY": os.environ.get("OPENCODE_API_KEY", ""),
    }

    for provider_name, provider_config in config.items():
        env_key = provider_config.get("api_key", "").strip()
        if env_key.startswith("${") and env_key.endswith("}"):
            env_name = env_key[2:-1]
            config[provider_name]["api_key"] = env_vars.get(env_name, "")

    return config


def build_client(provider: str, config: dict):
    cfg = config.get(provider)
    if not cfg:
        raise ValueError(f"Unknown provider: {provider}")

    api_key = cfg.get("api_key")
    if not api_key:
        raise ValueError(f"No API key for provider: {provider}")

    base_url = cfg.get("base_url", "")

    if provider == "opencode":
        base_url = "https://opencode.ai/v1"

    client = OpenAI(api_key=api_key, base_url=base_url)
    return client, cfg


def translate_text(client, model: str, text: str) -> str:
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "user",
                "content": f"Translate the following English transcript to Russian. Preserve the formatting with timestamps as they are. Output ONLY the translated text, nothing else.\n\n{text}"
            }
        ],
        max_tokens=8192,
        temperature=0.3
    )
    return response.choices[0].message.content


def extract_video_id(url: str) -> str:
    m = re.search(r"v=([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    m = re.search(r"youtu\.be/([A-Za-z0-9_-]{11})", url)
    if m:
        return m.group(1)
    return None


def main():
    parser = argparse.ArgumentParser(description="Translate EN transcript to RU and style as study guide")
    parser.add_argument("en_path", help="Path to .en.md file")
    parser.add_argument("--provider", "-p", default="openrouter", help="AI provider (default: openrouter)")
    parser.add_argument("--model", "-m", help="Model (default: provider default)")
    parser.add_argument("--config", "-c", default=None, help="providers.json path")

    args = parser.parse_args()

    if args.config:
        config_path = args.config
    else:
        script_dir = Path(__file__).parent.resolve()
        config_path = script_dir / "providers.json"

    config = load_providers(str(config_path))

    client, provider_config = build_client(args.provider, config)

    model = args.model
    if not model:
        models = provider_config.get("models", [])
        model = models[0] if models else "gpt-4o-mini"

    with open(args.en_path, "r", encoding="utf-8") as f:
        en_text = f.read()

    ru_text = translate_text(client, model, en_text)

    en_path = Path(args.en_path)
    ru_path = en_path.parent / f"{en_path.stem}.ru.md"

    url = None
    for line in en_text.splitlines():
        if line.startswith("url:"):
            url = line.split(":", 1)[1].strip().strip('"')
            break

    video_id = extract_video_id(url) if url else en_path.stem.replace(".en", "")

    date_str = datetime.now().strftime("%Y-%m-%d")

    lines = [
        "---",
        f"video_id: {video_id}",
        f"title: {en_path.stem.replace('.en', '')}",
        f"url: {url or 'unknown'}",
        f"date: {date_str}",
        f"language: ru",
        f"format: transcript-timestamps",
        f"provider: {args.provider}",
        f"model: {model}",
        "---\n",
        "# Transcript (RU)\n",
        ru_text
    ]

    ru_md = "\n".join(lines)

    with open(ru_path, "w", encoding="utf-8") as f:
        f.write(ru_md)

    print(f"RU transcript: {ru_path}")


if __name__ == "__main__":
    main()