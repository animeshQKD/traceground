"""The 20 survey cases, given to traceground as the survey gives them (sources as passages, trace
cases as traces; citation markers taken out, or kept). Every error must be flagged for its own
reason, and no correct answer may get any finding. The one exception is q2 with its citation marker
taken out: the quote is then in a source, and only the marker made it wrong."""
import sys
from pathlib import Path

import pytest

from traceground import check_answer

SURVEY = Path(__file__).resolve().parents[1] / "survey"
if not (SURVEY / "run_survey.py").exists():
    pytest.skip("the survey folder is not here (e.g. in the source distribution)", allow_module_level=True)
sys.path.insert(0, str(SURVEY))
import run_survey as rs  # noqa: E402

CASES = rs.load_cases()


def _check(case, markers="strip"):
    answer = rs.answer_for_tools(case["answer"], markers)
    if case["kind"] == "trace":
        return check_answer(answer, None, case["question"], trace=case["trace"])
    passages = rs.render_passages(case)
    return check_answer(answer, [p for p in passages if p[0] != "Q"], case["question"])


def test_flags_exactly_these_cases():
    errors = [c["id"] for c in CASES if c["expect"] == "flag"]
    assert [c["id"] for c in CASES if _check(c, "keep").verdict == "problems"] == errors
    assert [c["id"] for c in CASES if _check(c).verdict == "problems"] == [e for e in errors if e != "q2"]


def test_each_error_for_its_own_reason():
    by_id = {c["id"]: c for c in CASES}
    expected = {"n1": "number", "v1": "value-to-field", "v2": "value-to-field", "v3": "value-to-field",
                "a1": "argument", "a2": "argument", "a3": "argument", "f1": "failed-call", "t1": "tool-not-called",
                "q1": "quote", "q2": "quote", "s1": "self-talk", "c1": "self-contradiction"}
    for cid, check in expected.items():
        assert check in {f.check for f in _check(by_id[cid], "keep").findings}, cid


@pytest.mark.parametrize("markers", ["strip", "keep"])
@pytest.mark.parametrize("case", [c for c in CASES if c["expect"] == "pass"], ids=lambda c: c["id"])
def test_no_finding_at_all_on_correct_answers(case, markers):
    assert _check(case, markers).findings == []


def test_the_reasons_point_at_the_wrong_numbers():
    by_id = {c["id"]: c for c in CASES}
    (f,) = _check(by_id["n1"]).findings
    assert f.text == "42.1 million" and "41.2 million (S1)" in f.message
    fs = _check(by_id["f1"]).findings
    assert [f.check for f in fs] == ["failed-call", "number"]
    assert fs[1].text == "70%" and "they give no value close to it" in fs[1].message
    assert [f.check for f in _check(by_id["v1"]).findings] == ["value-to-field"]
    assert [f.text for f in _check(by_id["v2"]).findings] == ["7 rebounds", "11 assists"]
    assert [f.text for f in _check(by_id["v3"]).findings] == ["4% chance of rain"]
    assert [f.check for c in ("a1", "a2", "a3") for f in _check(by_id[c]).findings] == ["argument"] * 3
    (f,) = _check(by_id["q1"]).findings
    assert f.check == "quote" and "does not guarantee that the reconstructed matrix is positive" in f.message
    (f,) = _check(by_id["q2"], "keep").findings
    assert f.message.startswith("The quote is not in S1, which this sentence cites. It is in S2")
