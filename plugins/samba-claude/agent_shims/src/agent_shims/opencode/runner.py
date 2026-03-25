import importlib.resources
import os
import subprocess
import tempfile

import jinja2

from agent_shims.model import Model


def get_config_template() -> str:
    ref = importlib.resources.files(__package__).joinpath("opencode.json.jinja")
    return ref.read_text(encoding="utf-8")


def render_config(model: Model, sampling_parameters: dict | None = None) -> str:
    template = jinja2.Environment().from_string(get_config_template())
    return template.render(
        model=model,
        sampling_parameters=sampling_parameters or model.sampling_parameters,
    )


def run(model: Model, prompt: str, cwd: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    config = render_config(model)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".json") as f:
        f.write(config)
        f.flush()
        cmd = ["opencode", "run", prompt] + (extra_args or [])
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env={**os.environ, "OPENCODE_CONFIG": f.name},
        )
