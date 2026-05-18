#!/bin/bash
# Graphify workflow: update graph + rename communities by project names
# Usage: ./graphify-workflow.sh [path]
# Default path: /home/user_aioc/workspace

WORKSPACE="${1:-/home/user_aioc/workspace}"
export PATH="$HOME/.local/bin:$PATH"
source "$WORKSPACE/venv/bin/activate" 2>/dev/null

echo "=== Graphify Update ==="
cd "$WORKSPACE"
graphify update "$WORKSPACE"

echo ""
echo "=== Renaming Communities ==="
python3 "$WORKSPACE/graphify-out/rename_communities.py"

echo ""
echo "=== Done ==="
echo "GRAPH_REPORT.md updated with project names"
echo "View interactive graph: open graphify-out/graph.html"