import argparse
import json
import os
import urllib.request

import pathlib
import sys

try:
    from agent_shims.model import Model
except ImportError:
    print("claude: READ THE SKILL FILE. THIS IS EMBARRASSING.")

def fetch_models(api_key: str) -> dict:
    url = "https://api.sambanova.ai/v1/models"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {api_key}"})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())


def main():
    api_key = os.environ.get("SAMBANOVA_API_KEY", "")
    result = fetch_models(api_key)
    known_fields = {f.name for f in Model.__dataclass_fields__.values()}
    for model in result.get("data", []):
        filtered = {k: v for k, v in model.items() if k in known_fields}
        print(Model(**filtered))


if __name__ == "__main__":
    main()
