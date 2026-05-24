import subprocess, json, os, time, tempfile
from pathlib import Path
from audio import download_audio, extract_topic, get_duration, get_title
from log_utils import log_start, log_step, log_end


def run(url: str, model: str, uid: str = "", chain: str = "",
        language: str = "ru", out_path: str = "") -> dict:
    t0 = time.time()
    audio_path = download_audio(url)
    if not audio_path:
        return {"error": "audio download failed", "output": None}

    audio_dur = get_duration(audio_path)
    topic = extract_topic(get_title(url))

    log_start(
        cmd=f"pipeline_a {url}",
        chain=chain, model=model, uid=uid, url=url,
        audio_duration_sec=audio_dur
    )

    prompt = (
        f"Transcribe the following audio file into text in {language} language."
        f" Then provide a concise summary with key points.\n"
        f"Format: ## Transcript\\n\\n[full transcript]\\n\\n## Summary\\n\\n[bullet points]"
    )

    t_asr = time.time()
    try:
        proc = subprocess.run(
            ["opencode", "run",
             "--model", model,
             "--format", "json",
             "--dir", os.path.dirname(audio_path),
             prompt],
            capture_output=True, text=True, timeout=600
        )
        dur = time.time() - t_asr
        if proc.returncode != 0:
            return {"error": f"opencode failed: {proc.stderr[:200]}", "output": None}

        output_raw = proc.stdout.strip()
        result = json.loads(output_raw)
        transcript = result.get("data", {}).get("output", result.get("output", output_raw))
    except subprocess.TimeoutExpired:
        return {"error": "opencode timeout (600s)", "output": None}
    except json.JSONDecodeError:
        transcript = proc.stdout.strip()
    except Exception as e:
        return {"error": str(e), "output": None}

    total_tokens = 0
    cost = 0.0
    try:
        j = json.loads(proc.stdout)
        usage = j.get("usage", j.get("data", {}).get("usage", {}))
        total_tokens = usage.get("total_tokens", usage.get("output_tokens", 0))
        cost = usage.get("cost", usage.get("total_cost", 0.0))
    except Exception:
        pass

    log_step("asr+summarize", model=model, tokens_out=total_tokens,
             cost=cost, duration_sec=dur, chain=chain, uid=uid)

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(
                f"---\nchain: {chain}\nmodel: {model}\nuid: {uid}\n"
                f"url: {url}\nlanguage: {language}\n"
                f"duration_sec: {audio_dur:.0f}\ntotal_cost_usd: {cost:.4f}\n"
                f"total_tokens: {total_tokens}\n---\n\n{transcript}\n"
            )

    total_sec = time.time() - t0
    steps = [f"download({t_asr - t0:.1f}s)", f"asr+summarize({dur:.1f}s)"]
    log_end(total_sec=total_sec, total_cost=cost,
            total_tokens_in=0, total_tokens_out=total_tokens,
            output_file=out_path, steps=steps, chain=chain, uid=uid)

    return {"output": out_path, "tokens": total_tokens, "cost": cost,
            "duration": total_sec, "error": None}


def get_title(url: str) -> str:
    import subprocess
    try:
        res = subprocess.run(["yt-dlp", "--get-title", url],
                             capture_output=True, text=True, timeout=30)
        return res.stdout.strip() or "video"
    except Exception:
        return "video"
