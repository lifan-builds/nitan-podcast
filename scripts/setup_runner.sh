#!/usr/bin/env bash
# One-time setup helper for the self-hosted GitHub Actions runner.
# Run this BEFORE installing the runner to verify prerequisites.
set -euo pipefail

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

ok()   { echo -e "${GREEN}✓${NC} $1"; }
warn() { echo -e "${YELLOW}!${NC} $1"; }
fail() { echo -e "${RED}✗${NC} $1"; ERRORS=$((ERRORS + 1)); }

ERRORS=0
ROOT="$(cd "$(dirname "$0")/.." && pwd)"

echo "=== Nitan Podcast: Self-Hosted Runner Prerequisites ==="
echo ""

# Python
if command -v python3 &>/dev/null; then
  PY_VER=$(python3 --version 2>&1)
  ok "Python: $PY_VER"
else
  fail "Python 3.10+ not found"
fi

# venv
if [ -x "$ROOT/.venv/bin/python" ]; then
  ok "venv: $ROOT/.venv/bin/python"
else
  fail "venv not found at $ROOT/.venv — run: python3 -m venv .venv && .venv/bin/pip install -r requirements.txt"
fi

# Node
if command -v node &>/dev/null; then
  ok "Node: $(node --version)"
else
  fail "Node.js not found — needed for npx / nitan-mcp"
fi

# gh CLI
if command -v gh &>/dev/null; then
  if gh auth status &>/dev/null; then
    ok "gh CLI: authenticated"
  else
    fail "gh CLI installed but not authenticated — run: gh auth login"
  fi
else
  fail "gh CLI not found — install: brew install gh"
fi

# .env
if [ -f "$ROOT/.env" ]; then
  ok ".env file exists"
  # Check key vars
  for var in MCP_SERVER_COMMAND MCP_EXTRACT_TOOL NOTEBOOKLM_NOTEBOOK_ID; do
    if grep -q "^${var}=.\+" "$ROOT/.env" 2>/dev/null; then
      ok ".env: $var is set"
    else
      warn ".env: $var is not set (may be needed)"
    fi
  done
else
  fail ".env not found — copy .env.example to .env and configure"
fi

# NotebookLM session
STORAGE="$HOME/.notebooklm/storage_state.json"
if [ -f "$STORAGE" ]; then
  ok "NotebookLM session: $STORAGE"
else
  fail "NotebookLM session not found — run: notebooklm login"
fi

# notebooklm-py
if "$ROOT/.venv/bin/python" -c "import notebooklm" 2>/dev/null; then
  ok "notebooklm-py installed"
else
  warn "notebooklm-py not installed — run: .venv/bin/pip install -r requirements-integrations.txt && playwright install chromium"
fi

echo ""
if [ $ERRORS -gt 0 ]; then
  echo -e "${RED}$ERRORS issue(s) found. Fix them before installing the runner.${NC}"
  echo ""
fi

echo "=== Next Steps ==="
echo ""
echo "1. Fix any issues above"
echo "2. Go to: https://github.com/lifan-builds/nitan-podcast/settings/actions/runners/new"
echo "3. Select macOS, follow the download + configure instructions"
echo "4. Add label 'macos' when prompted (or after via Settings > Runners)"
echo "5. Install as a service:  cd actions-runner && ./svc.sh install && ./svc.sh start"
echo "6. Verify: gh api repos/lifan-builds/nitan-podcast/actions/runners --jq '.runners[].name'"
echo ""
echo "The workflow triggers 3x on Monday (6 AM / 12 PM / 6 PM PST)."
echo "First successful run publishes the episode; rest are skipped."
