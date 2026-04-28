CLAUDE_PLUGIN_DIR=$1
if [[ -z "$CLAUDE_PLUGIN_DIR" ]]; then
    echo "CLAUDE_PLUGIN_DIR -- exiting"
    exit 1
fi

if [ ! -d "${CLAUDE_PLUGIN_DIR}/.env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "${CLAUDE_PLUGIN_DIR}/.env"
fi

source "${CLAUDE_PLUGIN_DIR}/.env/bin/activate"
pip install -e "${CLAUDE_PLUGIN_DIR}/agent_shims"

echo "Creating /tmp/samba-claude directories..."
mkdir -p /tmp/samba-claude/prompts
mkdir -p /tmp/samba-claude/progress
