SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
${SAMBA_CLAUDE_PYTHON} $SCRIPT_DIR/list_models.py
