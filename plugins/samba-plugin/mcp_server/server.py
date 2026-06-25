#!/usr/bin/env python3
"""sambanova-plugin-cc MCP server.

Exposes the plugin's skills (code, list-models, model-info, reset-model-db,
update-model) as MCP tools backed by the same `agent_shims` library.
"""

import json
import os
import sys
import urllib.request

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
    # The opencode subprocess (and the export call inside _run_and_format) block
    # for seconds-to-minutes. FastMCP runs sync tools directly on its event loop,
    # so doing this inline would serialize every concurrent MCP call. Offload to
    # a worker thread (subprocess.run releases the GIL while waiting) so
    # independent `code` calls actually run in parallel.
    return await anyio.to_thread.run_sync(
        _run_and_format, m, prompt, cwd, args, norm_external
    )


def _run_and_format(m: Model, prompt: str, cwd: str, args: list[str],
                    external_dirs: list[str] | None) -> str:
    """Run opencode and format its output. Blocking; runs in a worker thread."""
    result = opencode.run(m, prompt, cwd, args, capture_output=True,
                          external_dirs=external_dirs)
    if result.returncode != 0:
        # opencode exits non-zero on a hard failure (auth, model-not-found, bad
        # endpoint) with the real cause on stderr and empty stdout. Without this
        # check that error is silently swallowed and surfaces as the bland
        # "[no text or reasoning output]", making an endpoint/model mismatch look
        # like a mysterious quick death. (A *dropped answer* is different: there
        # opencode exits 0 — that path stays in _format_opencode_run.)
        err = (result.stderr or "").strip() or "(no stderr)"
        raise RuntimeError(
            f"opencode exited {result.returncode} "
            f"(baseURL={get_sambanova_base_url()}, model={m.id})\n{err}\n"
            "If this is a model-not-found / auth error, the model may not be "
            "served on this endpoint — set SAMBANOVA_BASE_URL to the "
            "endpoint that serves it."
        )
    return _format_opencode_run(result.stdout or "", cwd)


def _parse_stream(stdout: str) -> tuple[str, str, str, list[str]]:
    """Pull (session_id, text, reasoning, message_ids) from opencode's
    `--format json` newline-delimited event stream.

    message_ids is every assistant message this run touched, in first-seen order.
    `step_start` carries the messageID and prints even in the worst case (when no
    text/reasoning ever flush), so it reliably scopes the run for export
    recovery."""
    session_id = ""
    text: list[str] = []
    reasoning: list[str] = []
    message_ids: list[str] = []
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
        mid = part.get("messageID", "")
        if mid and mid not in message_ids:
            message_ids.append(mid)
        t = ev.get("type")
        if t == "text":
            text.append(part.get("text", ""))
        elif t == "reasoning":
            reasoning.append(part.get("text", ""))
    return session_id, "".join(text).strip(), "".join(reasoning).strip(), message_ids


def _parse_export(export_json: str, message_ids: list[str]) -> tuple[str, str]:
    """Pull (text, reasoning) from the `opencode export` transcript, scoped to
    this run's assistant messages.

    A single run can span several assistant messages (text → tool → text → ...),
    so we concatenate every text part across them — matching the stream's
    all-text semantics, not just the final message. Filtering by message_ids also
    excludes earlier turns when resuming a session. Falls back to the last
    assistant message if the stream gave us no ids to filter on."""
    try:
        data = json.loads(export_json)
    except json.JSONDecodeError:
        return "", ""
    assistant = [m for m in data.get("messages", []) if m.get("info", {}).get("role") == "assistant"]
    wanted = message_ids and [m for m in assistant if m.get("info", {}).get("id") in message_ids]
    msgs = wanted or (assistant[-1:] if assistant else [])
    parts = [p for m in msgs for p in m.get("parts", [])]
    text = [p.get("text", "") for p in parts if p.get("type") == "text"]
    reasoning = [p.get("text", "") for p in parts if p.get("type") == "reasoning"]
    return "".join(text).strip(), "".join(reasoning).strip()


def _format_opencode_run(stdout: str, cwd: str) -> str:
    """Extract the session ID and output from opencode's `--format json`
    newline-delimited event stream.

    opencode's run loop breaks on `session.status=idle` and only emits
    `text`/`reasoning` parts that already carry `time.end`; on fast endpoints
    parts that finalize as the session goes idle lose that race and never hit
    stdout. The catch: a *non-final* text part can finalize early (when its step
    ends) and print, while the final answer finalizes at idle and is dropped --
    so the stream can hold *partial* text, not just all-or-nothing. We therefore
    can't trust a non-empty stream body to be complete.

    A printed part was finalized, hence persisted, so `opencode export` is a
    strict superset of the stream. Whenever we have a session we treat export as
    the source of truth and fall back to the streamed parts only if export is
    unavailable. On these fast endpoints the stream is usually empty anyway, so
    this rarely costs an export call we weren't already making. If neither yields
    text we surface the reasoning trace, flagged so the caller knows it is the
    trace and not a final answer.
    """
    session_id, stream_text, stream_reasoning, message_ids = _parse_stream(stdout)

    ex_text = ex_reasoning = ""
    if session_id:
        try:
            ex_text, ex_reasoning = _parse_export(
                opencode.export_session(session_id, cwd), message_ids
            )
        except Exception:
            ex_text = ex_reasoning = ""

    text = ex_text or stream_text
    reasoning = ex_reasoning or stream_reasoning

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
    # Offload the sqlite read to a worker thread so it never blocks the server
    # event loop (and concurrent calls). Same rationale as `code`.
    models = await anyio.to_thread.run_sync(_list_models)
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
    # The HTTP round-trip to the platform is blocking; offload it.
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
    await anyio.to_thread.run_sync(insert_model, model)
    return f"Model '{model.id}' inserted/updated successfully."


@mcp.tool()
async def reset_model_db() -> str:
    """Reset model param database, clear all entry. Use when user say
    "reset the database", "clear the model database", or "wipe model parameters".
    """
    await anyio.to_thread.run_sync(reset_db)
    return "Database reset successfully."


if __name__ == "__main__":
    mcp.run()
