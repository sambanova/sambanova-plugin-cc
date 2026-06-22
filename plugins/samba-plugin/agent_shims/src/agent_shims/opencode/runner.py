import contextlib
import importlib.resources
import logging
import os
import pathlib
import subprocess
import tempfile

import jinja2

from agent_shims.environment import get_sambanova_base_url, get_sambanova_key
from agent_shims.model import Model

logger = logging.getLogger(__name__)


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


def get_rule_files() -> list[str]:
    """Absolute paths of the top-level ``rules/*.md`` files.

    These are injected directly into every agent's ``instructions`` (always
    loaded). opencode resolves relative ``instructions`` paths against the
    project root (``--dir``), not our package, so we hand it absolute paths.
    """
    rules_dir = get_rules_dir()
    if rules_dir is None:
        return []
    return sorted(str(p) for p in rules_dir.glob("*.md") if _is_rule_file(p))


def get_nested_rule_files() -> list[str]:
    """Absolute paths of ``rules/<subdir>/**/*.md`` — rules in subdirectories.

    These are NOT injected into context. They are surfaced via the manifest
    (see ``build_rule_manifest``) for progressive disclosure: the agent reads a
    nested file on demand when its topic is relevant, keeping the base prompt
    small.
    """
    rules_dir = get_rules_dir()
    if rules_dir is None:
        return []
    return sorted(str(p) for p in rules_dir.rglob("*.md")
                  if p.parent != rules_dir and _is_rule_file(p))


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


def build_rule_manifest(nested_files: list[str]) -> str:
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
        rule_files=get_rule_files() + list(extra_instruction_files or []),
        # opencode's file tools auto-reject paths outside the project root
        # (--dir) unless the dir is granted here; each entry becomes an
        # `external_directory: allow` glob. NOTE: opencode (through 1.17.9)
        # treats this grant as read+write -- the documented per-tool read-only
        # override (edit/write deny) is silently ignored for external dirs
        # (verified) -- so granting a dir also gives the sub-agent write access.
        external_dirs=list(external_dirs or []),
    )


def run(model: Model, prompt: str, cwd: str, extra_args: list[str] | None = None,
        capture_output: bool = False,
        external_dirs: list[str] | None = None) -> subprocess.CompletedProcess:
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
        # stdin when no positional message is given. subprocess writes `input`
        # then closes the pipe, so opencode still gets the immediate EOF it needs
        # to exit its event loop (the reason we previously used DEVNULL).
        cmd = ["opencode", "run", "--dir", cwd] + (extra_args or [])
        return subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            env={**os.environ, "OPENCODE_CONFIG": f.name, "SAMBANOVA_API_KEY": get_sambanova_key()},
            input=prompt,
            capture_output=capture_output,
        )


def export_session(session_id: str, cwd: str) -> str:
    """Export a finished session's full transcript as JSON via `opencode export`.

    Used to recover the assistant's answer when `opencode run --format json`
    drops the final `text` part: its event loop breaks on `session.status=idle`
    and only emits `text`/`reasoning` parts that already carry `time.end`, so on
    fast endpoints the finalized answer loses the race and never reaches stdout.
    The part is still persisted, and `export` reads it straight from storage.

    Sessions live in opencode's global storage keyed by ID, so this needs
    neither OPENCODE_CONFIG nor a matching --dir. Progress ("Exporting
    session: ...") goes to stderr; stdout is clean JSON.
    """
    return subprocess.run(
        ["opencode", "export", session_id],
        cwd=cwd,
        text=True,
        stdin=subprocess.DEVNULL,
        capture_output=True,
    ).stdout or ""
