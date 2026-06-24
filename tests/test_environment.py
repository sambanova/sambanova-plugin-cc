"""Offline unit tests for API-key / base-URL env handling."""

import pytest

from agent_shims.environment import (
    DEFAULT_SAMBANOVA_BASE_URL,
    get_sambanova_base_url,
    get_sambanova_key,
)

KEY_VARS = ("SAMBA_CLAUDE_API_KEY", "SAMBANOVA_API_KEY")


def _clear_keys(monkeypatch):
    for var in KEY_VARS + ("SAMBANOVA_API_OVERRIDE",):
        monkeypatch.delenv(var, raising=False)


def test_key_missing_raises(monkeypatch):
    _clear_keys(monkeypatch)
    with pytest.raises(EnvironmentError):
        get_sambanova_key()


def test_samba_claude_key_takes_precedence(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("SAMBA_CLAUDE_API_KEY", "preferred")
    monkeypatch.setenv("SAMBANOVA_API_KEY", "fallback")
    assert get_sambanova_key() == "preferred"


def test_sambanova_key_used_as_fallback(monkeypatch):
    _clear_keys(monkeypatch)
    monkeypatch.setenv("SAMBANOVA_API_KEY", "fallback")
    assert get_sambanova_key() == "fallback"


def test_base_url_default(monkeypatch):
    _clear_keys(monkeypatch)
    assert get_sambanova_base_url() == DEFAULT_SAMBANOVA_BASE_URL


def test_base_url_override_strips_trailing_slash(monkeypatch):
    monkeypatch.setenv("SAMBANOVA_API_OVERRIDE", "https://example.test/v1/")
    assert get_sambanova_base_url() == "https://example.test/v1"
