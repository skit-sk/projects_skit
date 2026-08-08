# 🧪 Visualization Lab — Integrated Plan

## Pipeline: data → transcription → content generation → next step

### Output types
📄 Doc · 🖼 Image · 🎬 Video · 🔊 Audio · 📊 Pres · 🎙 Transcription

### Key feature
Result of transcription → input for next generation step (chainable pipeline)

### File structure per session
```
data/viz_sessions/{id}/
├── history/                    # flat list of all files ever
│   ├── step_001_data.csv
│   ├── step_002_transcript.md
│   ├── step_003_report.md
│   └── step_004_chart.png
├── input/                      # symlinks/copies of selected sources
├── results/                    # latest output
└── session.json
```

### Model Catalog — separate section `/viz-models/`
- Table of all models (350+ from `opencode models`)
- Categorized by type: chat, vision, audio, TTS, screenshot, tool
- Provider management: view, test, custom add
- Refresh via `opencode models` → parse → enrich → cache
- Links to provider config files and URLs

### Voice models
- TTS: gemini-2.5-flash-tts (apiyi), gemini-2.5-pro-tts (apiyi)
- STT/audio: gpt-4o-audio-preview (routerai), gpt-audio-mini (routerai), GPT Audio (aitunnel)
- Integration via opencode CLI (same as other providers)

### Transcription integration
- New module: `viz_lab/services/transcriber.py` wrapping `05_transcript/pipeline_a.py`
- Two pipelines: one-pass (ASR+summarize) / split (ASR → summarize)
- Result goes to `input/` for subsequent generation steps
- Output types `[🎙 Transcription]` + `[📄 Doc]` = transcribe → summarize → generate doc

### UI changes
- Output type toggle buttons next to model selector
- Source file checkboxes in left panel tree
- Model cards with [✕] remove and [⚙] settings
- "+ Add Model" panel with provider tree → model select
- Model settings: provider, model_id, output_types, preferred_for

### Future
- Orchestration engine (DAG pipeline)
- Progress bars for multi-step generation
- Async SSE streaming for real-time updates
