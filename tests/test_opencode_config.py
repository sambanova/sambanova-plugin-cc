"""Offline tests for the opencode config rendering and rule-injection helpers
that back the `code` skill. No opencode binary, no network."""

import json
import pathlib

import pytest

from agent_shims.model import Model
from agent_shims.opencode import runner


@pytest.fixture
def model():
    return Model(id="My-Model-v1", context_length=8192, max_completion_tokens=4096)


def test_render_config_is_valid_json(monkeypatch, model):
    monkeypatch.delenv("SAMBANOVA_BASE_URL", raising=False)
    monkeypatch.delenv("SAMBANOVA_API_OVERRIDE", raising=False)
    cfg = json.loads(runner.render_config(model))
    assert cfg["model"] == "sambanova/My-Model-v1"
    opts = cfg["provider"]["sambanova"]["options"]
    assert opts["baseURL"] == "https://api.sambanova.ai/v1"
    limits = cfg["provider"]["sambanova"]["models"]["My-Model-v1"]["limit"]
    assert limits["context"] == 8192
    assert limits["output"] == 4096


def test_render_config_honors_base_url_override(monkeypatch, model):
    monkeypatch.delenv("SAMBANOVA_API_OVERRIDE", raising=False)
    monkeypatch.setenv("SAMBANOVA_BASE_URL", "https://endpoint.test/v1")
    cfg = json.loads(runner.render_config(model))
    assert cfg["provider"]["sambanova"]["options"]["baseURL"] == "https://endpoint.test/v1"


def test_render_config_sets_user_agent_header(monkeypatch, model):
    # The /code path goes through opencode; send an explicit UA so a
    # WAF-gated endpoint doesn't 403 the sub-agent.
    cfg = json.loads(runner.render_config(model))
    opts = cfg["provider"]["sambanova"]["options"]
    assert opts["headers"]["User-Agent"] == "sambanova-plugin-cc"


def test_render_config_with_numeric_sampling_params(model):
    cfg = json.loads(runner.render_config(model, sampling_parameters={"temperature": 0.5}))
    # sampling params are applied to every agent profile
    assert cfg["agent"]["build"]["temperature"] == 0.5


def test_top_level_rule_files_discovered():
    rules = runner.get_rule_files()
    assert rules, "expected packaged top-level rule files"
    assert all(p.endswith(".md") for p in rules)
    assert all(not p.endswith(".original.md") for p in rules)
    # top-level only — no nested task rules here
    assert all(pathlib.Path(p).parent.name == "rules" for p in rules)


def test_nested_rule_files_separate_from_top_level():
    top = set(runner.get_rule_files())
    nested = set(runner.get_nested_rule_files())
    assert nested, "expected packaged nested (on-demand) rule files"
    assert top.isdisjoint(nested)
    assert all(pathlib.Path(p).parent.name != "rules" for p in nested)


def test_is_rule_file_excludes_original_backups(tmp_path):
    assert runner._is_rule_file(tmp_path / "00-x.md")
    assert not runner._is_rule_file(tmp_path / "00-x.original.md")
    assert not runner._is_rule_file(tmp_path / "notes.txt")


def test_rule_description_parses_frontmatter(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("---\ndescription: do the thing\n---\nbody\n", encoding="utf-8")
    assert runner._rule_description(f) == "do the thing"


def test_rule_description_absent_returns_empty(tmp_path):
    f = tmp_path / "r.md"
    f.write_text("no frontmatter here\n", encoding="utf-8")
    assert runner._rule_description(f) == ""


def test_build_rule_manifest_lists_described_files(tmp_path):
    a = tmp_path / "a.md"
    a.write_text("---\ndescription: alpha rule\n---\n", encoding="utf-8")
    b = tmp_path / "b.md"
    b.write_text("no description\n", encoding="utf-8")  # excluded (nothing to route on)
    manifest = runner.build_rule_manifest([str(a), str(b)])
    assert str(a) in manifest and "alpha rule" in manifest
    assert str(b) not in manifest
