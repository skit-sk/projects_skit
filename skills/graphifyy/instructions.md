# graphifyy - Installation & Usage Guide

## Installation

### Prerequisites
- Python 3.10+
- uv tool (recommended) or pipx

### Install via uv
```bash
uv tool install graphifyy
```

### Platform-Specific Setup

**For OpenCode:**
```bash
graphify opencode install
```

**For Claude Code (Linux/Mac):**
```bash
graphify install
```

**For Claude Code (Windows):**
```bash
graphify install --platform windows
```

**For Cursor:**
```bash
graphify cursor install
```

**For other platforms:**
```bash
graphify install --platform <name>
# Options: codex, copilot, aider, claw, droid, trae, gemini, hermes, kiro, pi, antigravity
```

## Basic Usage

### Build a Graph

```bash
# Current directory
/graphify .

# Specific path
/graphify ./src

# Update only changed files (fast)
/graphify ./src --update
```

### Query the Graph

```bash
# Ask questions about your code
graphify query "how is authentication implemented?"

# Find path between components
graphify path "UserService" "DatabasePool"

# Explain a concept
graphify explain "RateLimiter"
```

### Graph Output

After running `/graphify .`, you'll get:

| File | Purpose |
|------|---------|
| `graphify-out/graph.html` | Interactive visualization - open in browser |
| `graphify-out/GRAPH_REPORT.md` | Summary with key concepts and connections |
| `graphify-out/graph.json` | Full graph data for programmatic access |

## Workflow: Update + Rename Communities

```bash
# Option 1: Manual workflow
cd /workspace
graphify update /workspace
python3 graphify-out/rename_communities.py

# Option 2: Use the workflow script
./graphify-out/graphify-workflow.sh /workspace
```

The `rename_communities.py` script renames communities from "Community N" to project names based on the dominant source file location.

## Team Workflow

1. One person runs `/graphify .` and commits `graphify-out/`
2. Team members pull and AI reads the graph
3. Use `graphify hook install` for auto-rebuild on git commit

```bash
# Install git hook for auto-rebuild
graphify hook install

# Uninstall hook
graphify hook uninstall
```

## Advanced Options

| Flag | Description |
|------|-------------|
| `--mode deep` | More aggressive relationship extraction |
| `--update` | Re-extract only changed files |
| `--cluster-only` | Rerun clustering without re-extracting |
| `--no-viz` | Skip HTML visualization |
| `--wiki` | Build markdown wiki from graph |
| `--watch` | Auto-sync as files change |

## Ignoring Files

Create `.graphifyignore` in project root (same syntax as .gitignore):

```
node_modules/
dist/
*.generated.py
```

## Privacy

- **Code files**: Processed locally via tree-sitter
- **Video/audio**: Transcribed locally with faster-whisper
- **Docs/PDFs**: Sent to your AI assistant's model API

No telemetry or analytics.

## Using MCP Server

```bash
# Start MCP server for repeated tool-call access
python -m graphify.serve graphify-out/graph.json
```

This exposes: `query_graph`, `get_node`, `get_neighbors`, `shortest_path`