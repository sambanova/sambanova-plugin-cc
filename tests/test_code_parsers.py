"""Offline tests for the `code` skill's output-recovery logic (the trickiest
part of the plugin): parsing opencode's event stream and export transcript, and
the export-over-stream precedence in _format_opencode_run."""

import json

import server


def _ndjson(events):
    return "\n".join(json.dumps(e) for e in events)


def test_parse_stream_joins_text_and_tracks_ids():
    stdout = "\n".join([
        json.dumps({"type": "step_start", "sessionID": "ses_1", "part": {"messageID": "m1"}}),
        json.dumps({"type": "text", "part": {"messageID": "m1", "text": "Hello "}}),
        "this is not json",  # genuinely malformed line must be skipped
        "",                  # blank line must be skipped
        json.dumps({"type": "text", "part": {"messageID": "m1", "text": "world"}}),
        json.dumps({"type": "reasoning", "part": {"messageID": "m1", "text": "thinking"}}),
    ])
    session_id, text, reasoning, message_ids = server._parse_stream(stdout)
    assert session_id == "ses_1"
    assert text == "Hello world"
    assert reasoning == "thinking"
    assert message_ids == ["m1"]


EXPORT = json.dumps({
    "messages": [
        {"info": {"role": "assistant", "id": "m1"},
         "parts": [{"type": "text", "text": "A1"}, {"type": "reasoning", "text": "R1"}]},
        {"info": {"role": "assistant", "id": "m2"},
         "parts": [{"type": "text", "text": "A2"}]},
        {"info": {"role": "user", "id": "u1"},
         "parts": [{"type": "text", "text": "Q"}]},
    ]
})


def test_parse_export_filters_to_requested_messages():
    text, reasoning = server._parse_export(EXPORT, ["m1"])
    assert text == "A1"
    assert reasoning == "R1"


def test_parse_export_concatenates_multiple_messages():
    text, _ = server._parse_export(EXPORT, ["m1", "m2"])
    assert text == "A1A2"


def test_parse_export_falls_back_to_last_assistant():
    # no ids to filter on -> last assistant message
    assert server._parse_export(EXPORT, [])[0] == "A2"
    # ids that match nothing -> also falls back to last assistant
    assert server._parse_export(EXPORT, ["nope"])[0] == "A2"


def test_parse_export_bad_json_returns_empty():
    assert server._parse_export("{not json", ["m1"]) == ("", "")


def _stream_with(session="ses_1", text=None, reasoning=None):
    events = [{"type": "step_start", "sessionID": session, "part": {"messageID": "m1"}}]
    if text is not None:
        events.append({"type": "text", "part": {"messageID": "m1", "text": text}})
    if reasoning is not None:
        events.append({"type": "reasoning", "part": {"messageID": "m1", "text": reasoning}})
    return _ndjson(events)


def test_format_prefers_export_over_stream(monkeypatch):
    monkeypatch.setattr(server.opencode, "export_session",
                        lambda sid, cwd: json.dumps({"messages": [
                            {"info": {"role": "assistant", "id": "m1"},
                             "parts": [{"type": "text", "text": "EXPORT"}]}]}))
    out = server._format_opencode_run(_stream_with(text="STREAM"), cwd="/tmp")
    assert "sessionID: ses_1" in out
    assert "EXPORT" in out
    assert "STREAM" not in out


def test_format_falls_back_to_stream_when_export_empty(monkeypatch):
    monkeypatch.setattr(server.opencode, "export_session", lambda sid, cwd: "")
    out = server._format_opencode_run(_stream_with(text="STREAM"), cwd="/tmp")
    assert "STREAM" in out


def test_format_reasoning_only(monkeypatch):
    monkeypatch.setattr(server.opencode, "export_session", lambda sid, cwd: "")
    out = server._format_opencode_run(_stream_with(reasoning="WHY"), cwd="/tmp")
    assert "reasoning trace" in out
    assert "WHY" in out


def test_format_empty_output(monkeypatch):
    monkeypatch.setattr(server.opencode, "export_session", lambda sid, cwd: "")
    out = server._format_opencode_run(_stream_with(), cwd="/tmp")
    assert "[no text or reasoning output]" in out
