import argparse
import pathlib
import sys

from agent_shims.cn import runner as cn
from agent_shims.model_parameters import get_model


def main():
    parser = argparse.ArgumentParser(description="Run a coding tool as a sub-agent.")
    parser.add_argument("tool", choices=["continue"], help="Coding tool to use")
    parser.add_argument("model", help="Model name (must exist in the parameters database)")
    parser.add_argument("prompt", help="Prompt to send to the tool")
    parser.add_argument("cwd", help="Working directory for the tool")
    parser.add_argument("files", nargs="*", help="Optional list of files to grant access to")
    args = parser.parse_args()

    model = get_model(args.model)
    if model is None:
        print(f"Error: model '{args.model}' not found in database.", file=sys.stderr)
        sys.exit(1)

    if args.tool == "continue":
        result = cn.run(model, args.prompt, args.cwd)
        if result.stdout:
            print(result.stdout, end="")
        if result.returncode != 0:
            print(result.stderr, end="", file=sys.stderr)
            sys.exit(result.returncode)


if __name__ == "__main__":
    main()
