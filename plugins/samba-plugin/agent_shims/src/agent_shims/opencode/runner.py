import asyncio
import contextlib
import importlib.resources
import logging
import os
import pathlib
import re
import shutil
import subprocess
import tempfile
from collections.abc import Iterable

import jinja2

from agent_shims.environment import get_sambanova_base_url, get_sambanova_key
from agent_shims.model import Model

logger = logging.getLogger(__name__)

# `opencode run --format json` dropped a fast turn's final text before v1.17.0:
# its event loop was fire-and-forget, so the process exited before draining the
# final events. Fixed upstream in commit 0a7cb20e66 ("await run event loop",
# #31389), first released in v1.17.0 -- bisected and confirmed (v1.16.2 BAD,
# v1.17.0 GOOD). We parse that stream as the source of truth, so we require the
# fixed binary rather than silently returning truncated answers.
MIN_OPENCODE_VERSION = (1, 17, 0)


async def _opencode_version() -> tuple[int, int, int] | None:
    """(major, minor, patch) of the ``opencode`` on PATH.

    Returns None when opencode is present but reports an unparseable version
    (a ``local``/dev build) -- callers let those through. Raises RuntimeError
    when the binary is missing or ``--version`` cannot be run at all, so callers
    fail with a clear message instead of the raw ``FileNotFoundError`` that
    ``run()`` would otherwise throw mid-invocation."""
    try:
        proc = await asyncio.create_subprocess_exec(
            "opencode", "--version",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.DEVNULL,
        )
    except FileNotFoundError:
        raise RuntimeError(
            "opencode not found on PATH. The `code` tool shells out to it -- "
            "install opencode (https://opencode.ai) and make sure `opencode` "
            "is runnable."
        ) from None
    except OSError as e:
        raise RuntimeError(f"could not run `opencode --version`: {e}") from e
    try:
        stdout_b, _ = await asyncio.wait_for(proc.communicate(), timeout=10)
    except asyncio.TimeoutError as e:
        proc.kill()
        await proc.wait()
        raise RuntimeError(
            "could not run `opencode --version`: timed out after 10s"
        ) from e
    out = stdout_b.decode(errors="replace").strip()
    m = re.search(r"(\d+)\.(\d+)\.(\d+)", out)
    return (int(m[1]), int(m[2]), int(m[3])) if m else None


# `require_opencode_version` caches its success so the probe runs once per
# process (the binary does not change mid-run). An async function can't use
# `functools.cache` -- that would cache the coroutine, which can only be
# awaited once. Instead we guard a module-level flag with a lock: concurrent
# first-callers serialize so only one probe fires, and a raised error leaves
# the flag unset so a later call re-probes after the user fixes the binary
# (same "errors are not cached" semantics as the old `functools.cache`).
_version_lock = asyncio.Lock()
_version_checked = False


async def require_opencode_version() -> None:
    """Fail fast if opencode is missing or predates the dropped-output fix.

    A missing/unrunnable binary raises via ``_opencode_version``; a dev build
    (unparseable version) is allowed through -- we can't compare it and it is
    assumed current."""
    global _version_checked
    if _version_checked:
        return
    async with _version_lock:
        if _version_checked:
            return
        v = await _opencode_version()
        if v is not None and v < MIN_OPENCODE_VERSION:
            got = ".".join(map(str, v))
            need = ".".join(map(str, MIN_OPENCODE_VERSION))
            raise RuntimeError(
                f"opencode {got} is too old: `opencode run --format json` drops "
                f"a fast turn's final answer before v{need}. Upgrade opencode "
                f"(e.g. `opencode upgrade`) and retry."
            )
        _version_checked = True


def get_config_template() -> str:
    ref = importlib.resources.files(__package__).joinpath("opencode.json.jinja")
    return ref.read_text(encoding="utf-8")


def get_rules_dir() -> pathlib.Path | None:
    """Filesystem path of the packaged ``rules/`` directory, or None.

    Source installs expose package data as real filesystem paths; a zip install
    would not, so callers must tolerate None rather than assume a path exists.
    """
    ref = importlib.resources.files(__package__).joinpath("rules")
    path = pathlib.Path(str(ref))
    return path if path.is_dir() else None


def _is_rule_file(path: pathlib.Path) -> bool:
    """A ``.md`` rule file, excluding ``.original.md`` compression backups.

    ``/caveman:compress`` writes a ``<name>.original.md`` backup next to the
    file it compresses; without this filter that backup would be injected
    alongside the compressed rule, duplicating the content.
    """
    return path.name.endswith(".md") and not path.name.endswith(".original.md")


def get_rule_files() -> tuple[str, ...]:
    """Absolute paths of the top-level ``rules/*.md`` files.

    These are injected directly into every agent's ``instructions`` (always
    loaded). opencode resolves relative ``instructions`` paths against the
    project root (``--dir``), not our package, so we hand it absolute paths.
    Sorted so the ``NN-`` filename prefixes (00-, 01-, ...) drive a stable
    injection order; ``glob`` alone yields arbitrary filesystem order.
    """
    rules_dir = get_rules_dir()
    if rules_dir is None:
        return ()
    return tuple(sorted(str(p) for p in rules_dir.glob("*.md")
                        if _is_rule_file(p)))


def get_nested_rule_files() -> tuple[str, ...]:
    """Absolute paths of ``rules/<subdir>/**/*.md`` — rules in subdirectories.

    These are NOT injected into context. They are surfaced via the manifest
    (see ``build_rule_manifest``) for progressive disclosure: the agent reads a
    nested file on demand when its topic is relevant, keeping the base prompt
    small. Sorted for a stable, reproducible manifest.
    """
    rules_dir = get_rules_dir()
    if rules_dir is None:
        return ()
    return tuple(sorted(str(p) for p in rules_dir.rglob("*.md")
                        if p.parent != rules_dir and _is_rule_file(p)))


def _rule_description(path: pathlib.Path) -> str:
    """The rule's frontmatter ``description`` — the manifest's routing hint.

    Every rule file is authored with a leading ``---`` frontmatter block
    carrying a flat ``description: ...`` line (not full YAML, so no dependency
    needed), so this is the trigger the agent routes on.
    """
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError:
        return ""
    if not lines or lines[0].strip() != "---":
        return ""
    for line in lines[1:]:
        if line.strip() == "---":
            break
        key, sep, value = line.partition(":")
        if sep and key.strip() == "description":
            return value.strip()
    return ""


def build_rule_manifest(nested_files: Iterable[str]) -> str:
    """Render a markdown index of on-demand (nested) rule files.

    Each entry is the file's absolute path plus a one-line summary so the agent
    can decide whether to read it. Injected as an instruction file itself.
    """
    lines = [
        "# On-demand rules",
        "",
        "The rule files below are NOT loaded into context. When a task touches "
        "one of these topics, read the file at its absolute path before "
        "proceeding:",
        "",
    ]
    for p in nested_files:
        description = _rule_description(pathlib.Path(p))
        if not description:
            # No parseable description means the agent has nothing to route on,
            # so the entry would be useless. Exclude it, but warn — a missing
            # description is an authoring bug, not something to hide silently.
            logger.warning("Rule excluded from manifest (no frontmatter "
                           "description): %s", p)
            continue
        lines.append(f"- `{p}` — {description}")
    return "\n".join(lines) + "\n"


def render_config(model: Model, sampling_parameters: dict | None = None,
                  extra_instruction_files: list[str] | None = None,
                  external_dirs: list[str] | None = None) -> str:
    template = jinja2.Environment().from_string(get_config_template())
    return template.render(
        model=model,
        sampling_parameters=sampling_parameters or model.sampling_parameters,
        base_url=get_sambanova_base_url(),
        rule_files=[*get_rule_files(), *(extra_instruction_files or [])],
        # opencode's file tools auto-reject paths outside the project root
        # (--dir) unless the dir is granted here; each entry becomes an
        # `external_directory: allow` glob. NOTE: opencode (through 1.17.9)
        # treats this grant as read+write -- the documented per-tool read-only
        # override (edit/write deny) is silently ignored for external dirs
        # (verified) -- so granting a dir also gives the sub-agent write access.
        external_dirs=external_dirs or [],
    )


async def run(model: Model, prompt: str, cwd: str,
              extra_args: list[str] | None = None,
              external_dirs: list[str] | None = None,
              log_name: str | None = None
              ) -> subprocess.CompletedProcess:
    await require_opencode_version()
    with contextlib.ExitStack() as stack:
        # Nested rules are advertised through a manifest file that is itself an
        # instruction. Both temp files must outlive the subprocess, so they
        # share this ExitStack rather than nested `with` blocks.
        extra_instructions = []
        # Caller-granted external dirs, plus -- when nested rules exist -- the
        # packaged rules dir so the agent can open the on-demand rules the
        # manifest points at. All are granted as external_directory globs.
        granted_dirs = list(external_dirs or [])
        nested = get_nested_rule_files()
        if nested:
            manifest = stack.enter_context(
                tempfile.NamedTemporaryFile(mode="w", suffix=".md"))
            manifest.write(build_rule_manifest(nested))
            manifest.flush()
            extra_instructions.append(manifest.name)
            rules_dir = get_rules_dir()
            if rules_dir is not None:
                granted_dirs.append(str(rules_dir))

        config = render_config(model, extra_instruction_files=extra_instructions,
                               external_dirs=granted_dirs)
        f = stack.enter_context(tempfile.NamedTemporaryFile(mode="w", suffix=".json"))
        f.write(config)
        f.flush()
        # opencode determines its project root from --dir, not the process cwd,
        # so pass cwd explicitly or it writes files to the wrong directory.
        # Pass the prompt on stdin, NOT as an argv element. A long/structured
        # prompt (the skill explicitly encourages writing these) can exceed the
        # OS per-argument limit (MAX_ARG_STRLEN, ~128KB on Linux) and fail to
        # exec with OSError "Argument list too long" before opencode even starts
        # -- a fast, endpoint-independent death. opencode reads the message from
        # stdin when no positional message is given. communicate() writes the
        # input then closes the pipe, so opencode still gets the immediate EOF
        # it needs to exit its event loop (the reason we previously used DEVNULL).
        cmd = ["opencode", "run", "--dir", cwd] + (extra_args or [])
        env = {**os.environ, "OPENCODE_CONFIG": f.name,
               "SAMBANOVA_API_KEY": get_sambanova_key()}
        # Async subprocess: the opencode turn blocks for seconds-to-minutes, so
        # awaiting it (rather than blocking a worker thread with subprocess.run)
        # lets concurrent `code` calls run on the one event loop. stdout/stderr
        # are streamed line-by-line to a per-invocation log file (flushed per
        # line) so an external watcher can poll progress / detect a stall, while
        # still being accumulated for the returned CompletedProcess. Draining
        # concurrently with the stdin write avoids a pipe-full deadlock.
        pipe = asyncio.subprocess.PIPE
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            cwd=cwd,
            env=env,
            stdin=pipe,
            stdout=pipe,
            stderr=pipe,
        )

        # Optional live-progress log: written ONLY when the caller names it
        # (log_name), so default behavior is unchanged -- no file is created.
        # The name is caller-supplied so the caller knows the path up front and
        # can poll it while this call runs. Output is accumulated for the return
        # regardless. Draining concurrently with the stdin write avoids a
        # pipe-full deadlock.
        log_path = None
        logf = None
        run_dir = None
        if log_name:
            log_base = os.path.join(tempfile.gettempdir(), "sambanova_code_logs")
            # Per-run dir keyed by the caller's token so get_progress() can
            # locate the log by token alone, and so the whole run's logs can be
            # removed wholesale below. The log is EPHEMERAL: it exists only
            # while this call runs (for live polling) and is deleted when the
            # call finishes -- the full output still returns via the result --
            # so logs never accumulate in the temp dir.
            run_dir = os.path.join(log_base, os.path.basename(log_name))
            os.makedirs(run_dir, exist_ok=True)
            log_path = os.path.join(run_dir, "progress.log")
            logf = open(log_path, "w")

        stdout_chunks: list[bytes] = []
        stderr_chunks: list[bytes] = []

        async def _drain(stream, sink, prefix):
            while True:
                line = await stream.readline()
                if not line:
                    break
                sink.append(line)
                if logf is not None:
                    logf.write(prefix + line.decode(errors="replace"))
                    logf.flush()

        try:
            stdout_task = asyncio.create_task(_drain(proc.stdout, stdout_chunks, ""))
            stderr_task = asyncio.create_task(_drain(proc.stderr, stderr_chunks, "[stderr] "))
            proc.stdin.write(prompt.encode())
            await proc.stdin.drain()
            proc.stdin.close()
            try:
                await proc.stdin.wait_closed()
            except Exception:
                pass
            await asyncio.gather(stdout_task, stderr_task, proc.wait())
        finally:
            if logf is not None:
                logf.close()
            # Auto-clean the ephemeral per-run log dir. ignore_errors so a
            # concurrent reader or an already-gone dir can't break teardown.
            if run_dir is not None:
                shutil.rmtree(run_dir, ignore_errors=True)

        stdout_b = b"".join(stdout_chunks)
        stderr_b = b"".join(stderr_chunks)
    result = subprocess.CompletedProcess(
        args=cmd,
        returncode=proc.returncode,
        stdout=stdout_b.decode(errors="replace"),
        stderr=stderr_b.decode(errors="replace"),
    )
    result.log_path = log_path
    return result
