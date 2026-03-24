import importlib.resources
import json
import sqlite3

from agent_shims.model import Model


def _db_path() -> str:
    return str(importlib.resources.files(__package__).joinpath("parameters.db"))


def get_model(model_id: str) -> Model | None:
    with sqlite3.connect(_db_path()) as conn:
        row = conn.execute(
            "SELECT \"Model Name\", context_length, max_completion_tokens, parameters"
            " FROM model_info WHERE \"Model Name\" = ?",
            (model_id,),
        ).fetchone()

    if row is None:
        return None
    return Model(
        id=row[0],
        context_length=row[1],
        max_completion_tokens=row[2],
        sampling_parameters=json.loads(row[3]),
    )


def list_models() -> list[Model]:
    with sqlite3.connect(_db_path()) as conn:
        rows = conn.execute(
            "SELECT \"Model Name\", context_length, max_completion_tokens, parameters"
            " FROM model_info"
        ).fetchall()
    return [
        Model(
            id=row[0],
            context_length=row[1],
            max_completion_tokens=row[2],
            sampling_parameters=json.loads(row[3]) if row[3] else {},
        )
        for row in rows
    ]


def reset_db() -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute("DELETE FROM model_info")


def insert_model(model: Model) -> None:
    with sqlite3.connect(_db_path()) as conn:
        conn.execute(
            "INSERT OR REPLACE INTO model_info (\"Model Name\", context_length, max_completion_tokens, parameters)"
            " VALUES (?, ?, ?, ?)",
            (
                model.id,
                model.context_length,
                model.max_completion_tokens,
                json.dumps(model.sampling_parameters if model.sampling_parameters is not None else {}),
            ),
        )
