"""Offline tests for the `code` skill's orchestration: the opencode command the
runner builds, and the guard paths in the `code` MCP tool. subprocess is mocked
so no opencode binary or network is needed."""

import asyncio
import types

import pytest

import server
from agent_shims.model import Model
from agent_shims.opencode import runner


def _model():
    return Model(id="m", context_length=10, max_completion_tokens=5)


def test_runner_builds_opencode_command(monkeypatch, tmp_path):
    captured = {}

    def fake_run(cmd, **kwargs):
        captured["cmd"] = cmd
        captured.update(kwargs)
        return types.SimpleNamespace(returncode=0, stdout="", stderr="")

    monkeypatch.setattr(runner.subprocess, "run", fake_run)
    monkeypatch.setattr(runner, "get_sambanova_key", lambda: "secret-key")

    runner.run(_model(), "PROMPT-TEXT", str(tmp_path),
               extra_args=["--format", "json"], capture_output=True)

    assert captured["cmd"][:4] == ["opencode", "run", "--dir", str(tmp_path)]
    assert "--format" in captured["cmd"] and "json" in captured["cmd"]
    assert captured["input"] == "PROMPT-TEXT"          # prompt goes on stdin
    assert captured["cwd"] == str(tmp_path)
    assert captured["capture_output"] is True
    env = captured["env"]
    assert env["SAMBANOVA_API_KEY"] == "secret-key"
    assert "OPENCODE_CONFIG" in env                     # rendered config path


def test_run_and_format_raises_on_nonzero_exit(monkeypatch, tmp_path):
    monkeypatch.setattr(server.opencode, "run",
                        lambda *a, **k: types.SimpleNamespace(
                            returncode=1, stdout="", stderr="boom: auth failed"))
    with pytest.raises(RuntimeError, match="opencode exited 1"):
        server._run_and_format(_model(), "p", str(tmp_path), ["--format", "json"], None)


def test_code_rejects_unknown_model(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "get_model", lambda name: None)
    with pytest.raises(ValueError, match="not found"):
        asyncio.run(server.code(model="ghost", prompt="p", cwd=str(tmp_path)))


def test_code_requires_cwd(monkeypatch):
    monkeypatch.setattr(server, "get_model", lambda name: _model())
    monkeypatch.delenv("CLAUDE_PROJECT_DIR", raising=False)
    with pytest.raises(ValueError, match="cwd"):
        asyncio.run(server.code(model="m", prompt="p"))


def test_code_rejects_nonexistent_cwd(monkeypatch, tmp_path):
    monkeypatch.setattr(server, "get_model", lambda name: _model())
    missing = str(tmp_path / "does-not-exist")
    with pytest.raises(ValueError, match="existing directory"):
        asyncio.run(server.code(model="m", prompt="p", cwd=missing))
