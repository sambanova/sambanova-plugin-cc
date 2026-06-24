"""End-to-end, secret-gated tests for the two skills that need real
infrastructure. Run only with `-m live`. They self-skip when the API key (and,
for `code`, the opencode CLI) is absent, so fork PRs stay green.
"""

import json
import os
import shutil
import urllib.request

import pytest

pytestmark = pytest.mark.live

_HAS_KEY = bool(os.environ.get("SAMBA_CLAUDE_API_KEY") or os.environ.get("SAMBANOVA_API_KEY"))
requires_key = pytest.mark.skipif(not _HAS_KEY, reason="no SambaNova API key in environment")


def _platform_models():
    from agent_shims.environment import get_sambanova_base_url, get_sambanova_key

    req = urllib.request.Request(
        f"{get_sambanova_base_url()}/models",
        headers={"Authorization": f"Bearer {get_sambanova_key()}"},
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read()).get("data", [])


@requires_key
def test_model_info_live():
    import server

    out = server._model_info_impl()
    assert out and out != "No models returned by the platform."
    assert "Model(" in out  # each line is a Model repr


@requires_key
@pytest.mark.skipif(shutil.which("opencode") is None, reason="opencode CLI not installed")
def test_code_live(tmp_path):
    import server
    from agent_shims.model import Model

    models = _platform_models()
    if not models:
        pytest.skip("platform returned no models")

    entry = models[0]
    model = Model(
        id=entry["id"],
        context_length=int(entry.get("context_length", 8192)),
        max_completion_tokens=int(entry.get("max_completion_tokens", 1024)),
    )

    out = server._run_and_format(
        model, "Reply with exactly: OK", str(tmp_path),
        ["--format", "json", "--thinking"], None,
    )
    assert "sessionID:" in out
    assert out.strip()
