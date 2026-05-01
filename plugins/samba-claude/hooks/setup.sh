CLAUDE_PLUGIN_DIR=$1
if [[ -z "$CLAUDE_PLUGIN_DIR" ]]; then
    echo "CLAUDE_PLUGIN_DIR not set -- exiting"
    exit 1
fi

if [ ! -d "${CLAUDE_PLUGIN_DIR}/.env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${CLAUDE_PLUGIN_DIR}/.env"
fi

SENTINEL="${CLAUDE_PLUGIN_DIR}/.env/.installed_version"
CURRENT_VERSION=$(python3 -c "import json; print(json.load(open('${CLAUDE_PLUGIN_DIR}/.claude-plugin/plugin.json'))['version'])" 2>/dev/null)

if [ ! -f "$SENTINEL" ] || [ "$(cat "$SENTINEL")" != "$CURRENT_VERSION" ]; then
    "${CLAUDE_PLUGIN_DIR}/.env/bin/pip" install -e "${CLAUDE_PLUGIN_DIR}/agent_shims"
    echo "$CURRENT_VERSION" > "$SENTINEL"
fi

mkdir -p /tmp/samba-claude/prompts /tmp/samba-claude/progress

echo "export SAMBA_CLAUDE_PYTHON=\"${CLAUDE_PLUGIN_DIR}/.env/bin/python3\"" >> "$CLAUDE_ENV_FILE"

