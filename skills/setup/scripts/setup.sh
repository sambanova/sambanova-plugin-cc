SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
SKILLS_DIR="$SCRIPT_DIR/../../.."

if [ ! -d "$SKILLS_DIR/.env" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$SKILLS_DIR/.env"
fi

source "$SKILLS_DIR/.env/bin/activate"
pip install -e "$SKILLS_DIR/agent_shims"
