#!/usr/bin/env bash
# MCP server launcher (the .mcp.json `command`).
#
# Runs when Claude Code spawns the server -- i.e. after the plugin has loaded --
# so venv creation never races the SessionStart hook. ensure_venv.sh is
# flock-guarded and shared with that hook, so the two are mutually exclusive.
set -euo pipefail

PLUGIN_DIR="${CLAUDE_PLUGIN_ROOT:?CLAUDE_PLUGIN_ROOT not set}"

# Guarantee the venv before handing off. All build output goes to stderr; only
# the server may speak on stdout (the MCP protocol channel).
"${PLUGIN_DIR}/hooks/ensure_venv.sh" "$PLUGIN_DIR"

exec "${PLUGIN_DIR}/.env/bin/python3" "${PLUGIN_DIR}/mcp_server/server.py" "$@"
