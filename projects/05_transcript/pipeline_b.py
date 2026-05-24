import subprocess, json, os, time
from audio import download_audio, extract_topic, get_duration, video_id_from_url, get_title
from log_utils import log_start, log_step, log_end


def _call_asr(audio_path: str, model: str, language: str) -> tuple[str, float, int]:
    if model.startswith("openrouter/") or model.startswith("opencode/"):
        prompt = f"Transcribe this audio file verbatim in {language}. Return only the transcript text, no commentary."
        try:
            proc = subprocess.run(
                ["opencode", "run", "--model", model, "--format", "json",
                 "--dir", os.path.dirname(audio_path), prompt],
                capture_output=True, text=True, timeout=600
            )
            if proc.returncode != 0:
                return proc.stderr[:200], 0, 0
            j = json.loads(proc.stdout)
            text = j.get("data", {}).get("output", proc.stdout)
            usage = j.get("usage", j.get("data", {}).get("usage", {}))
            tok = usage.get("total_tokens", usage.get("output_tokens", 0))
            cost = usage.get("cost", usage.get("total_cost", 0.0))
            return text, tok, cost
        except Exception as e:
            return str(e), 0, 0
    return "unknown ASR model", 0, 0


def _call_summarize(text: str, model: str, language: str) -> tuple[str, float, int]:
    prompt = (
        f"Summarize the following transcript in {language} language.\n\n"
        f"Format:\n## Summary\n- key point 1\n- key point 2\n..."
        f"\n## Key Ideas\n- Bullet list of the most important concepts\n\n"
        f"Transcript:\n{text}"
    )
    try:
        proc = subprocess.run(
            ["opencode", "run", "--model", model, "--format", "json", prompt],
            capture_output=True, text=True, timeout=300
        )
        if proc.returncode != 0:
            return proc.stderr[:200], 0, 0
        j = json.loads(proc.stdout)
        summary = j.get("data", {}).get("output", proc.stdout)
        usage = j.get("usage", j.get("data", {}).get("usage", {}))
        tok_in = usage.get("input_tokens", usage.get("total_tokens", 0))
        tok_out = usage.get("output_tokens", 0)
        cost = usage.get("cost", usage.get("total_cost", 0.0))
        return summary, tok_out, cost
    except Exception as e:
        return str(e), 0, 0


def run(url: str, models: dict, uid: str = "", chain: str = "",
        language: str = "ru", out_path: str = "") -> dict:
    t0 = time.time()
    audio_path = download_audio(url)
    if not audio_path:
        return {"error": "audio download failed", "output": None}

    audio_dur = get_duration(audio_path)
    topic = extract_topic(get_title(url))
    asr_model = models.get("asr", "")
    summ_model = models.get("summarizer", "")

    log_start(cmd=f"pipeline_b {url}", chain=chain, model=f"{asr_model}+{summ_model}",
              uid=uid, url=url, audio_duration_sec=audio_dur)

    total_tokens_in = 0
    total_tokens_out = 0
    total_cost = 0.0
    steps = []

    t_asr = time.time()
    transcript, asr_tok, asr_cost = _call_asr(audio_path, asr_model, language)
    dur_asr = time.time() - t_asr
    total_tokens_out += asr_tok
    total_cost += asr_cost
    log_step("asr", model=asr_model, tokens_out=asr_tok,
             cost=asr_cost, duration_sec=dur_asr, chain=chain, uid=uid)
    steps.append(f"asr({dur_asr:.1f}s)")

    if not transcript or transcript.startswith("error"):
        return {"error": f"ASR failed: {transcript}", "output": None,
                "tokens": total_tokens_out, "cost": total_cost}

    t_summ = time.time()
    summary, summ_tok, summ_cost = _call_summarize(transcript, summ_model, language)
    dur_summ = time.time() - t_summ
    total_tokens_in += len(transcript)
    total_tokens_out += summ_tok
    total_cost += summ_cost
    log_step("summarize", model=summ_model, tokens_in=len(transcript),
             tokens_out=summ_tok, cost=summ_cost, duration_sec=dur_summ,
             chain=chain, uid=uid)
    steps.append(f"summarize({dur_summ:.1f}s)")

    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(
                f"---\nchain: {chain}\nasr_model: {asr_model}\n"
                f"summarizer_model: {summ_model}\nuid: {uid}\nurl: {url}\n"
                f"language: {language}\nduration_sec: {audio_dur:.0f}\n"
                f"total_cost_usd: {total_cost:.4f}\n"
                f"total_tokens_in: {total_tokens_in}\n"
                f"total_tokens_out: {total_tokens_out}\n---\n\n"
                f"## Transcript\n\n{transcript}\n\n{summary}\n"
            )

    total_sec = time.time() - t0
    dowload_dur = t_asr - t0
    steps.insert(0, f"download({dowload_dur:.1f}s)")

    log_end(total_sec=total_sec, total_cost=total_cost,
            total_tokens_in=total_tokens_in, total_tokens_out=total_tokens_out,
            output_file=out_path, steps=steps, chain=chain, uid=uid)

    return {"output": out_path, "tokens": total_tokens_out, "cost": total_cost,
            "duration": total_sec, "error": None}
