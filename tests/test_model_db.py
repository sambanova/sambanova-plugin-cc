"""Offline unit tests for the model-parameters DB layer that backs the
list-models / update-model / reset-model-db skills. Runs against a temp DB."""

from agent_shims.model import Model
from agent_shims.model_parameters import get_model, insert_model, list_models, reset_db


def test_list_empty(temp_db):
    assert list_models() == []


def test_get_missing_returns_none(temp_db):
    assert get_model("nope") is None


def test_insert_and_get_round_trip(temp_db):
    m = Model(
        id="test-model",
        context_length=4096,
        max_completion_tokens=2048,
        sampling_parameters={"temperature": 0.7, "top_p": 0.9},
    )
    insert_model(m)

    got = get_model("test-model")
    assert got == m
    assert got.sampling_parameters == {"temperature": 0.7, "top_p": 0.9}


def test_list_returns_all(temp_db):
    insert_model(Model(id="a", context_length=10, max_completion_tokens=5))
    insert_model(Model(id="b", context_length=20, max_completion_tokens=6))
    ids = {m.id for m in list_models()}
    assert ids == {"a", "b"}


def test_insert_is_upsert(temp_db):
    insert_model(Model(id="dup", context_length=10, max_completion_tokens=5))
    insert_model(Model(id="dup", context_length=99, max_completion_tokens=7,
                       sampling_parameters={"temperature": 1.0}))
    models = list_models()
    assert len(models) == 1
    assert models[0].context_length == 99
    assert models[0].max_completion_tokens == 7
    assert models[0].sampling_parameters == {"temperature": 1.0}


def test_reset_clears_all(temp_db):
    insert_model(Model(id="a", context_length=10, max_completion_tokens=5))
    assert list_models()
    reset_db()
    assert list_models() == []
