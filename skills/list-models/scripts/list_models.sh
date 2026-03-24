SCRIPT_DIR=$( cd -- "$( dirname -- "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )
source $SCRIPT_DIR/../../../.env/bin/activate

if [ $? -ne 0 ]; then
    echo "Failed to activate virtual environment. Please run the setup skill first."
    exit 1
fi

python3 $SCRIPT_DIR/list_models.py
