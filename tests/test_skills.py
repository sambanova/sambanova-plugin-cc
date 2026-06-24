"""Every skill is well-formed and its MCP tool references actually exist.

This is the core "are the skills still wired up?" gate. It discovers skills and
tools dynamically, so it adapts to additions and only fails when wiring breaks.
"""

import pytest

from conftest import (
    allowed_tools_list,
    discover_server_tool_names,
    iter_skill_dirs,
    read_frontmatter,
    tool_ref_prefix,
)

SKILL_DIRS = iter_skill_dirs()
SERVER_TOOLS = discover_server_tool_names()
PREFIX = tool_ref_prefix()


def test_at_least_one_skill():
    assert SKILL_DIRS, "no skills found under plugins/samba-plugin/skills"


def test_server_exposes_tools():
    assert SERVER_TOOLS, "no @mcp.tool() functions found in server.py"


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_has_valid_frontmatter(skill_dir):
    skill_md = skill_dir / "SKILL.md"
    assert skill_md.is_file(), f"{skill_dir.name}/SKILL.md missing"

    fm = read_frontmatter(skill_md)
    assert isinstance(fm, dict), f"{skill_dir.name}: SKILL.md has no YAML frontmatter"

    for key in ("name", "description", "allowed-tools"):
        assert fm.get(key), f"{skill_dir.name}: frontmatter missing '{key}'"

    assert fm["name"] == skill_dir.name, (
        f"frontmatter name '{fm['name']}' != directory '{skill_dir.name}'"
    )


@pytest.mark.parametrize("skill_dir", SKILL_DIRS, ids=lambda p: p.name)
def test_skill_mcp_tool_refs_resolve(skill_dir):
    fm = read_frontmatter(skill_dir / "SKILL.md")
    for entry in allowed_tools_list(fm["allowed-tools"]):
        if not entry.startswith("mcp__"):
            continue  # built-in tool (Read, Write, WebFetch(*), ...) — not our concern
        assert entry.startswith(PREFIX), (
            f"{skill_dir.name}: MCP tool ref '{entry}' does not match this "
            f"plugin's prefix '{PREFIX}'"
        )
        tool = entry[len(PREFIX):]
        assert tool in SERVER_TOOLS, (
            f"{skill_dir.name}: references MCP tool '{tool}' with no matching "
            f"@mcp.tool() in server.py (have: {sorted(SERVER_TOOLS)})"
        )
