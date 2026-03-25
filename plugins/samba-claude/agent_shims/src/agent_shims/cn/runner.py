import importlib.resources
import subprocess
import tempfile

import jinja2

from agent_shims.model import Model


def get_config_template() -> str:
    ref = importlib.resources.files(__package__).joinpath("config.yaml.jinja")
    return ref.read_text(encoding="utf-8")


def run(model: Model, prompt: str, cwd: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    config = render_config(model, model.sampling_parameters or None)
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml") as f:
        f.write(config)
        f.flush()
        config_path = f.name
        cmd = ["cn", "--config", config_path, "-p", prompt, "--silent", "--auto"] + (extra_args or [])
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
        )


def render_config(model: Model, sampling_parameters: dict | None = None) -> str:
    template = jinja2.Environment().from_string(get_config_template())
    return template.render(
        model={
            "name": model.id,
            "maxTokens": model.max_completion_tokens,
            "contextLength": model.context_length,
        },
        sampling_parameters=sampling_parameters or {},
    )
