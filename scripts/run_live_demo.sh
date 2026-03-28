#!/usr/bin/env bash
# Live demo: Nitan MCP (npx) → weekly top topics → demo/output/DEMO_notebooklm_weekly.md
# → optional NotebookLM upload + Audio Overview MP3 under releases/ (requires .env + notebooklm login).
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"
PY="$ROOT/.venv/bin/python"
if [[ ! -x "$PY" ]]; then
  echo "Create venv first: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt" >&2
  exit 1
fi
export MCP_SERVER_COMMAND=npx
export MCP_SERVER_ARGS="[\"-y\",\"@nitansde/mcp@latest\",\"--python_path\",\"$PY\"]"
export MCP_EXTRACT_TOOL=discourse_list_top_topics
export MCP_EXTRACT_TOOL_ARGUMENTS='{"period":"weekly","limit":5}'
exec "$PY" run_pipeline.py --skip-briefing \
  --export-dir "$ROOT/demo/output" \
  --output-filename DEMO_notebooklm_weekly.md \
  --publish-notebooklm \
  --log-level INFO
