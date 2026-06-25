#!/usr/bin/env bash
# Idempotent, concurrency-safe builder for the plugin's Python venv.
#
# Safe to call from both the SessionStart hook (warmup) and the MCP bootstrap
# wrapper: a lock serializes the two so they can never clobber each other's
# venv creation / pip install. Whoever gets the lock builds; the other blocks,
# then sees the work is already done and no-ops.
#
# All progress output goes to stderr so this is safe to call from the MCP
# bootstrap wrapper, whose stdout is the MCP protocol channel.
set -euo pipefail

PLUGIN_DIR="${1:-${CLAUDE_PLUGIN_ROOT:-}}"
if [[ -z "$PLUGIN_DIR" ]]; then
    echo "ensure_venv: plugin dir not given (\$1 or CLAUDE_PLUGIN_ROOT)" >&2
    exit 1
fi

VENV="${PLUGIN_DIR}/.env"
PY="${VENV}/bin/python3"
SENTINEL="${VENV}/.installed_version"

# Serialize the two callers. Lock artifacts live OUTSIDE .env so `rm -rf "$VENV"`
# below can't delete them mid-build and break mutual exclusion.
#
# Prefer flock (Linux). macOS has no flock, so fall back to an atomic mkdir
# spinlock: mkdir either creates the dir (we win) or fails because it exists
# (someone else is building, so we wait). A timeout is the safety valve against
# a stale lock left by a killed process -- after it we proceed unlocked rather
# than hang the MCP startup.
if command -v flock >/dev/null 2>&1; then
    exec 9>"${PLUGIN_DIR}/.env.lock"
    flock 9
else
    LOCKDIR="${PLUGIN_DIR}/.env.lock.d"
    tries=0
    until mkdir "$LOCKDIR" 2>/dev/null; do
        tries=$((tries + 1))
        if (( tries > 300 )); then  # ~60s at 0.2s/try
            echo "ensure_venv: lock busy too long; proceeding without it" >&2
            break
        fi
        sleep 0.2
    done
    trap 'rmdir "$LOCKDIR" 2>/dev/null || true' EXIT
fi

VERSION="$(python3 -c "import json; print(json.load(open('${PLUGIN_DIR}/.claude-plugin/plugin.json'))['version'])" 2>/dev/null || true)"

# Rebuild when python3 is missing -- covers both an absent venv and a
# partially-built one (dir exists but no bin/python3).
if [[ ! -x "$PY" ]]; then
    echo "ensure_venv: creating virtual environment..." >&2
    rm -rf "$VENV"
    python3 -m venv "$VENV" >&2
fi

# Install agent_shims only when the recorded version differs. With `set -e`, a
# failed pip exits before the sentinel is written, so the next run retries
# instead of being fooled into thinking the install succeeded.
if [[ ! -f "$SENTINEL" ]] || [[ "$(cat "$SENTINEL")" != "$VERSION" ]]; then
    echo "ensure_venv: installing agent_shims ($VERSION)..." >&2
    "${VENV}/bin/pip" install -e "${PLUGIN_DIR}/agent_shims" >&2
    echo "$VERSION" > "$SENTINEL"
fi
