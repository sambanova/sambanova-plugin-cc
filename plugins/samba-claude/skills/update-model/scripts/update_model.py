import argparse
import json

from agent_shims.model import Model
from agent_shims.model_parameters import insert_model


def main():
    parser = argparse.ArgumentParser(description="Insert or update a model in the database.")
    parser.add_argument("name", help="Model name/ID")
    parser.add_argument("context_length", type=int, help="Context length")
    parser.add_argument("max_completion_tokens", type=int, help="Max completion tokens")
    parser.add_argument("sampling_parameters", nargs="?", default=None,
                        help="Sampling parameters as a JSON string")
    args = parser.parse_args()

    sampling_parameters = json.loads(args.sampling_parameters) if args.sampling_parameters else {}

    model = Model(
        id=args.name,
        context_length=args.context_length,
        max_completion_tokens=args.max_completion_tokens,
        sampling_parameters=sampling_parameters,
    )
    insert_model(model)
    print(f"Model '{model.id}' inserted/updated successfully.")


if __name__ == "__main__":
    main()
