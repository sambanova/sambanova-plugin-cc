"""Offline tests for the model_info skill's fetch+format logic. Mocks only the
HTTP call so the parsing/formatting is exercised with no network or secret."""

import json

import pytest

import server  # made importable by conftest (mcp_server/ on sys.path)


class _FakeResp:
    def __init__(self, payload):
        self._bytes = json.dumps(payload).encode()

    def read(self):
        return self._bytes

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False


def _patch_urlopen(monkeypatch, payload, captured):
    def fake_urlopen(req, *args, **kwargs):
        captured["url"] = req.full_url
        captured["auth"] = req.get_header("Authorization")
        return _FakeResp(payload)

    monkeypatch.setattr(server.urllib.request, "urlopen", fake_urlopen)


def test_formats_models_and_filters_unknown_fields(monkeypatch):
    monkeypatch.delenv("SAMBANOVA_API_OVERRIDE", raising=False)
    monkeypatch.setenv("SAMBA_CLAUDE_API_KEY", "k")
    payload = {
        "data": [
            {"id": "m1", "context_length": 100, "max_completion_tokens": 50, "owned_by": "acme"},
            {"id": "m2", "context_length": 200, "max_completion_tokens": 60},
        ]
    }
    cap = {}
    _patch_urlopen(monkeypatch, payload, cap)

    out = server._model_info_impl()

    lines = out.splitlines()
    assert len(lines) == 2
    assert "m1" in out and "m2" in out
    assert "owned_by" not in out and "acme" not in out  # non-Model field filtered out
    assert cap["url"].endswith("/models")
    assert cap["auth"] == "Bearer k"


def test_no_models_message(monkeypatch):
    monkeypatch.setenv("SAMBA_CLAUDE_API_KEY", "k")
    _patch_urlopen(monkeypatch, {"data": []}, {})
    assert server._model_info_impl() == "No models returned by the platform."


def test_honors_base_url_override(monkeypatch):
    monkeypatch.setenv("SAMBA_CLAUDE_API_KEY", "k")
    monkeypatch.setenv("SAMBANOVA_API_OVERRIDE", "https://endpoint.test/v1")
    cap = {}
    _patch_urlopen(monkeypatch, {"data": []}, cap)
    server._model_info_impl()
    assert cap["url"] == "https://endpoint.test/v1/models"


def test_missing_key_raises(monkeypatch):
    monkeypatch.delenv("SAMBA_CLAUDE_API_KEY", raising=False)
    monkeypatch.delenv("SAMBANOVA_API_KEY", raising=False)
    with pytest.raises(EnvironmentError):
        server._model_info_impl()
