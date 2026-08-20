#!/usr/bin/env python3
"""sambanova-plugin-cc MCP server.

Exposes the plugin's skills (code, list-models, model-info, reset-model-db,
update-model) as MCP tools backed by the same `agent_shims` library.
"""

import json
import os
import sys
import tempfile
import urllib.request
from collections import deque

import anyio.to_thread

try:
    from mcp.server.fastmcp import FastMCP
except ImportError:
    print('Missing dependencies. Run: pip install "mcp[cli]"', file=sys.stderr)
    sys.exit(1)

try:
    from agent_shims.environment import get_sambanova_base_url, get_sambanova_key
    from agent_shims.opencode import runner as opencode
    from agent_shims.model import Model
    from agent_shims.model_parameters import (
        get_model,
        insert_model,
        list_models as _list_models,
        reset_db,
    )
except ImportError:
    print(
        "agent_shims not importable. Install with: "
        "pip install -e <plugin>/agent_shims",
        file=sys.stderr,
    )
    sys.exit(1)

mcp = FastMCP("sambanova-plugin-cc")


@mcp.tool()
async def code(
    model: str,
    prompt: str,
    cwd: str | None = None,
    session_id: str | None = None,
    max_tokens: int | None = None,
    progress_token: str | None = None,
    tool_args: list[str] | None = None,
    external_dirs: list[str] | None = None,
) -> str:
    """Powerful coding tool as sub-agent, given model + prompt. Use when: run task
    (e.g. build-and-test), code review + edit, need second opinion, or read +
    summarize file.

    Pass the prompt verbatim — do not pre-resolve references to git/grep/etc.
    Runs opencode in `--format json --thinking` mode and returns the session ID
    and the model's text output.

    Args:
        model: Bare model ID from the parameters DB, not
            provider-prefixed. Use list_models to see options.
        prompt: Prompt to send.
        cwd: Working directory for the tool. Defaults to $CLAUDE_PROJECT_DIR when
            omitted; an absolute path is recommended. Must be an existing dir.
        session_id: Optional session ID (from a prior code() call) to continue
            that session, preserving the train of thought. NOTE: opencode keys
            sessions by project root, so a resume must use the SAME `cwd` as the
            original call -- resuming with a different (or defaulted) cwd
            silently finds no session and starts fresh.
        max_tokens: Override the model's max_completion_tokens for this run.
        tool_args: Extra args passed verbatim to opencode (after the prompt).
        external_dirs: Absolute paths of directories OUTSIDE cwd to grant the
            sub-agent access to. opencode sandboxes the sub-agent to cwd and
            auto-rejects file access elsewhere; list a dir here to allow it.
            Granted as read+write -- opencode has no working read-only external
            grant (the documented edit/write deny is ignored through 1.17.9).
            For read-only context from a single external file, prefer attaching
            it via tool_args ["-f", "/abs/path"], which loads it into the
            message without granting filesystem access.
        progress_token: If set, stream this call's opencode output live to
            {tempdir}/sambanova_code_logs/<progress_token>/progress.log
            (flushed per line) so it can be polled via get_progress() while the
            call runs. The log is EPHEMERAL -- its directory is removed when the
            call finishes, so poll it only during the run; the full output
            returns via this call's result regardless. Default None = no log
            file (unchanged behavior).
    """
    m = get_model(model)
    if m is None:
        raise ValueError(f"model '{model}' not found in database")
    if max_tokens is not None:
        m.max_completion_tokens = max_tokens

    cwd = cwd or os.environ.get("CLAUDE_PROJECT_DIR")
    if not cwd:
        raise ValueError(
            "cwd not given and CLAUDE_PROJECT_DIR is not set; pass an absolute cwd"
        )
    cwd = os.path.abspath(cwd)
    if not os.path.isdir(cwd):
        raise ValueError(f"cwd is not an existing directory: {cwd}")

    norm_external = None
    if external_dirs:
        norm_external = []
        for d in external_dirs:
            ad = os.path.abspath(d)
            if not os.path.isdir(ad):
                raise ValueError(
                    f"external_dirs entry is not an existing directory: {d}"
                )
            norm_external.append(ad)

    args = ["--format", "json", "--thinking"]
    if session_id:
        args += ["--session", session_id]
    args += (tool_args or [])
    # opencode.run drives the subprocess with asyncio, so awaiting it here lets
    # independent `code` calls run concurrently on the server's event loop
    # without tying up a worker thread each (the turn blocks for
    # seconds-to-minutes). The sqlite/HTTP tools below still offload to threads
    # because they have no async equivalent.
    return await _run_and_format(m, prompt, cwd, args, norm_external, progress_token)


@mcp.tool()
def get_progress(token: str, tail_lines: int = 200) -> str:
    """Return the tail of a `code` call's live progress log.

    Pass the same `progress_token` you gave `code(...)`. Use it to watch a
    long or backgrounded call's progress, or to detect a stall. Returns a
    "(no log ...)" notice if the token's log file does not exist yet.
    """
    path = os.path.join(tempfile.gettempdir(), "sambanova_code_logs",
                        os.path.basename(token), "progress.log")
    if not os.path.exists(path):
        return f"(no log for token '{token}' at {path})"
    with open(path, "r", errors="replace") as f:
        lines = deque(f, maxlen=tail_lines)
    return "".join(lines)


async def _run_and_format(m: Model, prompt: str, cwd: str, args: list[str],
                          external_dirs: list[str] | None,
                          progress_token: str | None = None) -> str:
    """Run opencode and format its output."""
    result = await opencode.run(m, prompt, cwd, args,
                                external_dirs=external_dirs,
                                log_name=(progress_token if progress_token else None))
    if result.returncode != 0:
        # opencode exits non-zero on a hard failure (auth, model-not-found, bad
        # endpoint) with the real cause on stderr and empty stdout. Without this
        # check that error is silently swallowed and surfaces as the bland
        # "[no text or reasoning output]", making an endpoint/model mismatch look
        # like a mysterious quick death.
        err = result.stderr.strip() or "(no stderr)"
        raise RuntimeError(
            f"opencode exited {result.returncode} "
            f"(baseURL={get_sambanova_base_url()}, model={m.id})\n{err}\n"
            "If this is a model-not-found / auth error, the model may not be "
            "served on this endpoint — set SAMBANOVA_API_OVERRIDE to the "
            "endpoint that serves it."
        )
    text = _format_opencode_run(result.stdout)
    return text


def _parse_stream(stdout: str) -> tuple[str, str, str]:
    """Pull (session_id, text, reasoning) from opencode's `--format json`
    newline-delimited event stream.

    The stream is the complete, authoritative record of the turn on opencode
    >= v1.17.0 (see runner.require_opencode_version): text/reasoning parts are
    concatenated across every step of the run."""
    session_id = ""
    text: list[str] = []
    reasoning: list[str] = []
    for line in stdout.splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            ev = json.loads(line)
        except json.JSONDecodeError:
            continue
        session_id = session_id or ev.get("sessionID", "")
        part = ev.get("part", {})
        t = ev.get("type")
        if t == "text":
            text.append(part.get("text", ""))
        elif t == "reasoning":
            reasoning.append(part.get("text", ""))
    return session_id, "".join(text).strip(), "".join(reasoning).strip()


def _format_opencode_run(stdout: str) -> str:
    """Extract the session ID and output from opencode's `--format json`
    newline-delimited event stream.

    The stream is the source of truth. (opencode < v1.17.0 could exit `run`
    before draining the final events and drop a fast turn's answer; runner
    enforces >= v1.17.0 so that can't happen here -- see
    runner.require_opencode_version.) If there is no text we surface the
    reasoning trace, flagged so the caller knows it is the trace and not a
    final answer.
    """
    session_id, text, reasoning = _parse_stream(stdout)

    claude_session_id = os.environ.get("CLAUDE_CODE_SESSION_ID", "")
    header = f"sessionID: {session_id}\nCLAUDE_SESSION_ID: {claude_session_id}\n\n"

    if text:
        return header + text
    if reasoning:
        return (
            header
            + "[no text output; returning the model's reasoning trace instead]\n\n"
            + reasoning
        )
    return header + "[no text or reasoning output]"


@mcp.tool()
async def list_models() -> str:
    """List all model in param database + their param. Use when user say
    "list models", "show models in the database", or "what models are stored".
    """
    # Called inline: a query against the packaged ~12KB sqlite db is sub-ms, so
    # the event-loop block is invisible and a thread hop would cost more than
    # the work. (Same reason `code` reads get_model inline.) Only genuinely
    # slow I/O -- the opencode subprocess, the platform HTTP call -- goes async.
    models = _list_models()
    if not models:
        return "No models in database."
    return "\n".join(str(m) for m in models)


@mcp.tool()
async def model_info() -> str:
    """Show all model on SambaNova platform + context length + max completion
    token. Use when user ask "what models are available", "show platform models",
    or need look up model param before add to database. Requires
    SAMBA_CLAUDE_API_KEY or SAMBANOVA_API_KEY in the environment.
    """
    # The HTTP round-trip to the platform is genuinely blocking (seconds), so
    # offload it to a worker thread to keep the event loop free -- unlike the
    # local sqlite tools, which run inline.
    return await anyio.to_thread.run_sync(_model_info_impl)


def _model_info_impl() -> str:
    """Fetch + format the platform model list. Blocking; runs in a worker thread."""
    api_key = get_sambanova_key()

    req = urllib.request.Request(
        f"{get_sambanova_base_url()}/models",
        headers={"Authorization": f"Bearer {api_key}"},
    )
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())

    known_fields = set(Model.__dataclass_fields__)
    lines = []
    for model in result.get("data", []):
        filtered = {k: v for k, v in model.items() if k in known_fields}
        lines.append(str(Model(**filtered)))
    return "\n".join(lines) if lines else "No models returned by the platform."


@mcp.tool()
async def update_model(
    name: str,
    context_length: int,
    max_completion_tokens: int,
    sampling_parameters: dict | None = None,
) -> str:
    """Insert or update model in param database. Use when user say "update model",
    "add model", or "insert model" with model detail.

    Args:
        name: Model name/ID.
        context_length: Context length.
        max_completion_tokens: Max completion tokens.
        sampling_parameters: Optional sampling parameters (e.g. temperature).
    """
    model = Model(
        id=name,
        context_length=context_length,
        max_completion_tokens=max_completion_tokens,
        sampling_parameters=sampling_parameters or {},
    )
    insert_model(model)  # inline: local sqlite write, sub-ms (see list_models)
    return f"Model '{model.id}' inserted/updated successfully."


@mcp.tool()
async def reset_model_db() -> str:
    """Reset model param database, clear all entry. Use when user say
    "reset the database", "clear the model database", or "wipe model parameters".
    """
    reset_db()  # inline: local sqlite write, sub-ms (see list_models)
    return "Database reset successfully."


if __name__ == "__main__":
    mcp.run()
