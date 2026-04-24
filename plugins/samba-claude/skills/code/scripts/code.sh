SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/../../../.env/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment. Please run the setup skill first."
    exit 1
fi

# Log invocation for debugging
LOG_DIR="/tmp/samba-claude/logs"
mkdir -p "$LOG_DIR"
LOG_FILE="$LOG_DIR/code_$(date +%Y%m%d_%H%M%S)_$$.log"

echo "[$(date)] Starting: python3 $SCRIPT_DIR/code.py $@" >> "$LOG_FILE"
python3 $SCRIPT_DIR/code.py "$@" 2>&1 | tee -a "$LOG_FILE"
EXIT_CODE=${PIPESTATUS[0]}
echo "[$(date)] Finished with exit code $EXIT_CODE" >> "$LOG_FILE"
exit $EXIT_CODE
