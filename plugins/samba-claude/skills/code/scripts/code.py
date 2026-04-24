import argparse
import pathlib
import sys

try:
    from agent_shims.cn import runner as cn
    from agent_shims.opencode import runner as opencode
    from agent_shims.model_parameters import get_model
except ImportError:
    print("claude: READ THE SKILL FILE. THIS IS EMBARRASSING.")

def main():
    parser = argparse.ArgumentParser(description="Run a coding tool as a sub-agent.")
    parser.add_argument("tool", choices=["continue", "opencode"], help="Coding tool to use")
    parser.add_argument("model", help="Model name (must exist in the parameters database)")
    parser.add_argument("cwd", help="Working directory for the tool")
    parser.add_argument("prompt", help="Prompt to send to the tool")
    parser.add_argument("--tool-arg", action="append", default=[],
                        help="Extra arguments passed through to the underlying tool (repeatable)")
    parser.add_argument("--max-tokens", type=int, default=None,
                        help="Override max_completion_tokens for this run")
    args = parser.parse_args()

    model = get_model(args.model)
    if model is None:
        print(f"Error: model '{args.model}' not found in database.", file=sys.stderr)
        sys.exit(1)

    if args.max_tokens is not None:
        model.max_completion_tokens = args.max_tokens

    if args.tool == "continue":
        result = cn.run(model, args.prompt, args.cwd, args.tool_arg)
    elif args.tool == "opencode":
        result = opencode.run(model, args.prompt, args.cwd, args.tool_arg)

    sys.exit(result.returncode)


if __name__ == "__main__":
    main()
