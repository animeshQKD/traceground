"""Tests for mutate.py (planted errors). No network."""
import json

import mutate

TRACE_ID = "c1"


def _record(answer, result, model="m", qid="q1", question="How did Jordan Reyes play?"):
    return {"id": qid, "model": model, "provider": "fake", "error": None, "answer": answer, "messages": [
        {"role": "user", "content": question},
        {"role": "assistant", "content": None, "tool_calls": [
            {"id": TRACE_ID, "type": "function", "function": {"name": "get_player_stats", "arguments": "{}"}}]},
        {"role": "tool", "tool_call_id": TRACE_ID, "content": json.dumps(result)},
        {"role": "assistant", "content": answer}]}


RESULT = {"points": 27, "rebounds": 11, "assists": 7, "fg_pct": 0.522}
ANSWER = "He scored 27 points, grabbed 11 rebounds and shot 52.2% from the field."


def test_kinds_and_changed_spans():
    fields = mutate.result_fields(_record(ANSWER, RESULT)["messages"])
    assert ("get_player_stats (c1)", "points", 27.0) in fields
    muts = mutate.mutations(ANSWER, fields)
    kinds = {k for k, *_ in muts}
    assert kinds == {"digits swapped", "last digit off by one", "value of another field", "two values swapped",
                     "fraction as percent"}
    for kind, new, spans, what in muts:
        assert new != ANSWER
        for a, b in spans:
            assert new[a:b] and new[a:b] != ANSWER[a:b] or kind == "two values swapped"
    assert ("digits swapped", "He scored 72 points, grabbed 11 rebounds and shot 52.2% from the field.") in \
        [(k, n) for k, n, *_ in muts]
    assert any(k == "fraction as percent" and "0.522%" in n for k, n, *_ in muts)
    assert any(k == "two values swapped" and "11 points" in n and "27 rebounds" in n for k, n, *_ in muts)


def test_format_like_the_results():
    assert mutate._fmt(22545.63, "469.70") == "22545.63"
    assert mutate._fmt(22545.63, "2,545.63") == "22,545.63"
    assert mutate._fmt(1.05, "315") == "1.05"
    assert mutate._fmt(36.0, "18,139.09") == "36"
    assert mutate._fmt(40983.61, "40 983.61") == "40 983.61"


def test_run_counts_and_skips(tmp_path):
    run = tmp_path / "run.jsonl"
    recs = [_record(ANSWER, RESULT),
            _record("He scored 30 points.", RESULT, qid="q2"),                 # traceground: problems
            _record(ANSWER, RESULT, qid="q3")]                                 # wrong by hand
    run.write_text("".join(json.dumps(r) + "\n" for r in recs), encoding="utf-8")
    report = mutate.run([str(run)], wrong={("m", "q3")})
    assert {(s["id"], s["why"]) for s in report["skipped"]} == {("q2", "traceground says problems"),
                                                                ("q3", "wrong by hand")}
    assert {r["id"] for r in report["rows"]} == {"q1"}
    (total,) = [s for s in mutate.summary(report["rows"]) if s["kind"] == "all"]
    assert total["planted"] == len(report["rows"]) and total["caught"] + total["flagged elsewhere"] + \
        total["missed"] == total["planted"]
    swapped = [r for r in report["rows"] if r["kind"] == "digits swapped" and "72 points" in r["answer"]]
    assert swapped[0]["outcome"] == "caught"
    md = mutate.markdown(report)
    assert "planted errors in 1 real answers" in md and "## Missed" in md


def test_main_writes_files(tmp_path):
    run = tmp_path / "run.jsonl"
    run.write_text(json.dumps(_record(ANSWER, RESULT)) + "\n", encoding="utf-8")
    assert mutate.main([str(run), "--out", str(tmp_path / "out")]) == 0
    assert len(list((tmp_path / "out").glob("mutations_*.md"))) == 1
    assert mutate.main([str(tmp_path / "none*.jsonl"), "--out", str(tmp_path / "out")]) == 2
