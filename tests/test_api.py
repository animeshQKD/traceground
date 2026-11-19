import json

import pytest

from traceground import Finding, Result, check_answer, normalize_sources


def test_source_shapes():
    assert normalize_sources(None) == []
    assert normalize_sources("a") == [("S1", "a")]
    assert normalize_sources(["a", "b"]) == [("S1", "a"), ("S2", "b")]
    assert normalize_sources({"doc1": "a"}) == [("doc1", "a")]
    assert normalize_sources([("x", "a"), {"id": "y", "text": "b"}, {"text": "c"}]) == [("x", "a"), ("y", "b"), ("S3", "c")]


def test_bad_sources_are_refused():
    with pytest.raises(TypeError):
        normalize_sources([42])
    with pytest.raises(ValueError):
        normalize_sources([("x", "a"), ("x", "b")])
    with pytest.raises(TypeError):
        check_answer(None, ["a"])


def test_verdicts():
    assert check_answer("It is 42.5.", ["It is 42.5."]).verdict == "ok"
    assert check_answer("It is 42.6.", ["It is 42.5."]).verdict == "problems"
    assert check_answer("It is 42.6.").verdict == "unsure"
    assert check_answer("No numbers.").verdict == "ok"
    assert check_answer("It is 1.97.", ["1.9799"]).verdict == "ok"          # a minor finding only


def test_summaries():
    assert check_answer("It is 42.5 and 43.5.", ["42.5"], "Is it 43.5?").summary == (
        "2 numbers checked against 1 source and the question: all supported.")
    assert check_answer("It is 42.5 and 44.5.", [], "Is it 42.5?").summary == (
        "2 numbers checked against the question: 1 number not supported.")
    assert check_answer("It is 42.6.").summary == "1 number in the answer, but no sources or question to check against."
    assert check_answer('It is 1.97, "small but robust" and "large and fragile" [S1].', ["1.9799, small but robust"]).summary == (
        "1 number and 2 quotes checked against 1 source: 1 number cut short; 1 quote not found.")
    assert check_answer("No numbers.", ["x"]).summary == "No numbers or quotes to check."


def test_result_to_json_round_trip():
    r = check_answer("Revenue was $42.1 million.", {"report": "Revenue was $41.2 million."})
    d = json.loads(r.to_json())
    assert d["verdict"] == "problems" and d["corrected_answer"] is None
    (f,) = d["findings"]
    assert set(f) == {"check", "severity", "start", "end", "text", "sentence", "message", "evidence", "suggestion"}
    assert f["evidence"][0]["source"] == "report"
    assert d["stats"] == {"numbers_checked": 1, "numbers_not_checked": 0, "numbers_derived": 0, "numbers_unsupported": 1,
                          "numbers_cut_short": 0, "numbers_computed_in_answer": 0, "quotes_checked": 0, "quotes_not_found": 0,
                          "quotes_wrong_source": 0, "quotes_changed_slightly": 0, "bindings_checked": 0, "bindings_wrong": 0,
                          "question_values": 0, "arguments_wrong": 0, "tool_calls_failed_unreported": 0,
                          "tool_claims_unbacked": 0, "self_talk": 0, "self_contradictions": 0, "sources": 1,
                          "tool_calls": 0, "tool_calls_failed": 0}
    assert isinstance(r, Result) and isinstance(r.findings[0], Finding)


def test_the_answer_is_never_changed():
    answer = "It is 1.97 and 42.6."
    r = check_answer(answer, ["1.9799"])
    assert r.corrected_answer is None and answer == "It is 1.97 and 42.6."


def test_text_report():
    text = check_answer("It is 1.97 and 42.6.", ["1.9799"]).to_text()
    assert text.splitlines()[0] == ("PROBLEMS: 2 numbers checked against 1 source: "
                                    "1 number not supported; 1 number cut short.")
    assert '[number (minor)] "1.97"' in text and '[number] "42.6"' in text


def test_the_id_question_is_reserved():
    with pytest.raises(ValueError):
        normalize_sources({"question": "x"})


def test_findings_are_in_answer_order_and_quotes_can_be_turned_off():
    answer = 'It says "fast and very cheap" and costs 42.6 [S1].'
    r = check_answer(answer, ["It is fast and cheap, at 42.5."])
    assert [f.check for f in r.findings] == ["quote", "number"]
    assert [f.check for f in check_answer(answer, ["It is fast and cheap, at 42.5."], check_quotes=False).findings] == ["number"]
