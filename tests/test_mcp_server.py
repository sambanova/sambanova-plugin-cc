"""Boot the real MCP server over stdio and confirm it exposes exactly the tools
the skills reference. This is the strongest "the plugin is wired up" check.

Read-only: CI installs agent_shims editable, so the packaged parameters.db IS
the repo file and a subprocess can't be monkeypatched. We only list tools and
call the read-only list_models — never the mutating tools.
"""

import asyncio
import os
import sys

from conftest import PLUGIN_ROOT, SERVER_PY, discover_server_tool_names


async def _boot_and_query():
    from mcp import ClientSession, StdioServerParameters
    from mcp.client.stdio import stdio_client

    env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN_ROOT)}
    params = StdioServerParameters(command=sys.executable, args=[str(SERVER_PY)], env=env)
    async with stdio_client(params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {t.name for t in tools.tools}
            result = await session.call_tool("list_models", {})
            return names, result


def test_server_boots_and_tools_match_source():
    names, result = asyncio.run(asyncio.wait_for(_boot_and_query(), timeout=90))
    assert names == discover_server_tool_names(), (
        f"live tool set {sorted(names)} != source @mcp.tool() set "
        f"{sorted(discover_server_tool_names())}"
    )
    # list_models is read-only and must succeed (empty DB is fine).
    assert result.isError is False
