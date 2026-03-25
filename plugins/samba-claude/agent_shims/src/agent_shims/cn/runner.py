import importlib.resources
import os
import pathlib
import subprocess
import tempfile

import jinja2

from agent_shims.model import Model


def get_config_template() -> str:
    ref = importlib.resources.files(__package__).joinpath("config.yaml.jinja")
    return ref.read_text(encoding="utf-8")


def run(model: Model, prompt: str, cwd: str, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    config = render_config(model, model.sampling_parameters or None)
    with tempfile.TemporaryDirectory(prefix="cn-home-") as tmp_home:
        pathlib.Path(tmp_home, ".continue").mkdir()
        config_path = pathlib.Path(tmp_home, "config.yaml")
        config_path.write_text(config)
        cmd = ["cn", "--config", str(config_path), "-p", prompt, "--silent", "--auto"] + (extra_args or [])
        env = {**os.environ, "HOME": tmp_home}
        return subprocess.run(
            cmd,
            cwd=cwd,
            capture_output=True,
            text=True,
            env=env,
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
