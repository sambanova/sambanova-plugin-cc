"""Shared fixtures and helpers for the plugin test suite.

These tests live OUTSIDE plugins/samba-plugin/ (Copybara only manages that
subtree), so they survive every sync and run against whatever the sync brings
in. They are written to *discover* skills and MCP tools rather than hardcode
today's set, so a sync that adds a skill/tool passes automatically while a sync
that breaks the wiring fails.
"""

import ast
import json
import sqlite3
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
PLUGIN_ROOT = REPO_ROOT / "plugins" / "samba-plugin"
MCP_SERVER_DIR = PLUGIN_ROOT / "mcp_server"
SERVER_PY = MCP_SERVER_DIR / "server.py"
SKILLS_DIR = PLUGIN_ROOT / "skills"
PLUGIN_JSON = PLUGIN_ROOT / ".claude-plugin" / "plugin.json"
MCP_JSON = PLUGIN_ROOT / ".mcp.json"

# The MCP server is a standalone script, not an installed module. Put its dir on
# sys.path so tests can `import server` to reach its pure helper functions.
if str(MCP_SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_SERVER_DIR))


def plugin_name() -> str:
    return json.loads(PLUGIN_JSON.read_text(encoding="utf-8"))["name"]


def mcp_server_name() -> str:
    servers = json.loads(MCP_JSON.read_text(encoding="utf-8"))["mcpServers"]
    assert len(servers) == 1, f"expected exactly one MCP server, got {list(servers)}"
    return next(iter(servers))


def tool_ref_prefix() -> str:
    """The `allowed-tools` prefix Claude Code uses for this plugin's MCP tools:
    mcp__plugin_{plugin}_{server}__"""
    return f"mcp__plugin_{plugin_name()}_{mcp_server_name()}__"


def discover_server_tool_names() -> set[str]:
    """Names of every @mcp.tool()-decorated function in server.py, via AST so no
    import (and no deps) is needed for the structural tests."""
    tree = ast.parse(SERVER_PY.read_text(encoding="utf-8"))
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for dec in node.decorator_list:
                target = dec.func if isinstance(dec, ast.Call) else dec
                if isinstance(target, ast.Attribute) and target.attr == "tool":
                    names.add(node.name)
    return names


def iter_skill_dirs() -> list[Path]:
    return sorted(p for p in SKILLS_DIR.iterdir() if p.is_dir())


def read_frontmatter(md_path: Path) -> dict | None:
    """Parse the leading `---` YAML frontmatter block of a SKILL.md."""
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    return yaml.safe_load(parts[1])


def allowed_tools_list(value) -> list[str]:
    """`allowed-tools` may be a YAML list or a comma-separated string."""
    items = value if isinstance(value, list) else str(value).split(",")
    return [str(i).strip() for i in items if str(i).strip()]


@pytest.fixture
def temp_db(monkeypatch, tmp_path):
    """A throwaway model-parameters SQLite DB, wired in by monkeypatching
    agent_shims.model_parameters._db_path (it has no env override)."""
    db_path = tmp_path / "parameters.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        'CREATE TABLE model_info ('
        '    "Model Name" TEXT NOT NULL PRIMARY KEY,'
        '    context_length INTEGER NOT NULL,'
        '    max_completion_tokens INTEGER NOT NULL,'
        '    parameters TEXT CHECK(json_valid(parameters))'
        ')'
    )
    conn.commit()
    conn.close()

    import agent_shims.model_parameters as mp

    monkeypatch.setattr(mp, "_db_path", lambda: str(db_path))
    return db_path
