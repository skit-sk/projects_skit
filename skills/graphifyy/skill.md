# graphifyy Skill for AI Agent

## Description

**graphifyy** builds a queryable knowledge graph from your codebase. It maps code, docs, PDFs, images, and videos into an interactive graph you can query instead of grepping through files.

## Installation

```bash
# Installed via uv tool
uv tool install graphifyy

# For OpenCode integration
graphify opencode install
```

## Commands

| Command | Description |
|---------|-------------|
| `/graphify .` | Build graph for current directory |
| `/graphify ./path --update` | Re-extract only changed files |
| `/graphify . --cluster-only` | Rerun clustering without re-extracting |
| `/graphify query "question"` | Query the graph |
| `/graphify path "NodeA" "NodeB"` | Find path between nodes |
| `/graphify explain "Concept"` | Explain a concept |

## Output Files

```
graphify-out/
├── graph.html       # Interactive visualization (open in browser)
├── GRAPH_REPORT.md  # Summary: key concepts, connections, questions
└── graph.json       # Full graph for queries
```

## AI Workflow

```
1. /graphify .                    # Build the graph
2. /graphify query "how is auth implemented?"
3. /graphify path "UserService" "Database"
```

## Supported Files

| Type | Extensions |
|------|------------|
| Code | .py .js .ts .jsx .tsx .go .rs .java .c .cpp .rb .cs .kt .php .swift .sql |
| Docs | .md .html .txt .rst .yaml .yml |
| Office | .docx .xlsx |
| Media | .png .jpg .pdf .mp4 .mp3 |

## Notes

- Code is processed locally via tree-sitter (no API calls)
- Docs/PDFs/images sent to AI model API
- `--update` flag re-extracts only changed files (fast)
- `graphify opencode install` enables automatic GRAPH_REPORT.md loading

## Troubleshooting

```bash
# Reinstall for OpenCode
graphify opencode install

# Check help
graphify --help
```