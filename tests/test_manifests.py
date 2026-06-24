"""Static validation: every config/manifest in the plugin parses, and the
plugin/server names line up so MCP tool references are derivable."""

import json

import jinja2
import pytest

try:
    import tomllib  # py3.11+
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None

from conftest import MCP_JSON, PLUGIN_JSON, PLUGIN_ROOT, mcp_server_name, plugin_name


def _json_files():
    return sorted(p for p in PLUGIN_ROOT.rglob("*.json") if ".env" not in p.parts)


@pytest.mark.parametrize("path", _json_files(), ids=lambda p: str(p.name))
def test_json_parses(path):
    json.loads(path.read_text(encoding="utf-8"))


def test_pyproject_parses():
    pyproject = PLUGIN_ROOT / "agent_shims" / "pyproject.toml"
    assert pyproject.is_file()
    if tomllib is None:
        pytest.skip("tomllib unavailable")
    data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
    assert data["project"]["name"]


def test_jinja_templates_compile():
    env = jinja2.Environment()
    templates = list(PLUGIN_ROOT.rglob("*.jinja"))
    assert templates, "expected at least one .jinja template"
    for tpl in templates:
        env.parse(tpl.read_text(encoding="utf-8"))  # raises on syntax error


def test_plugin_metadata_present():
    meta = json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))
    for key in ("name", "version", "description"):
        assert meta.get(key), f"plugin.json missing {key}"


def test_plugin_name_matches_mcp_server_key():
    # Tool references (mcp__plugin_{plugin}_{server}__tool) depend on these
    # matching; the convention in this plugin is they are identical.
    assert plugin_name() == mcp_server_name()


def test_hooks_session_start_defined():
    hooks = json.loads((PLUGIN_ROOT / "hooks" / "hooks.json").read_text(encoding="utf-8"))
    session_start = hooks.get("hooks", {}).get("SessionStart")
    assert session_start, "hooks.json must define a SessionStart hook"


def test_mcp_server_command_present():
    servers = json.loads(MCP_JSON.read_text(encoding="utf-8"))["mcpServers"]
    cfg = next(iter(servers.values()))
    assert cfg.get("command"), "MCP server entry must define a command"
