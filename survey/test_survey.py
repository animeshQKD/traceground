"""Offline tests of the survey: the cases are well-formed and their numbers consistent, and the
harness works with no tool installed and with a fake tool. No network, no models.

    python -m pytest test_survey.py -q
"""
import json
import math

import pytest

import run_survey as rs

CASES = rs.load_cases()
BY_ID = {c["id"]: c for c in CASES}


def test_twenty_cases_thirteen_errors_seven_correct():
    assert len(CASES) == 20
    assert len(BY_ID) == 20                                   # ids unique
    assert sum(c["expect"] == "flag" for c in CASES) == 13
    assert sum(c["expect"] == "pass" for c in CASES) == 7


@pytest.mark.parametrize("case", CASES, ids=[c["id"] for c in CASES])
def test_case_shape(case):
    for key in ("id", "kind", "error_type", "domain", "origin", "expect", "why", "question", "answer"):
        assert isinstance(case[key], str) and case[key].strip(), key
    assert case["kind"] in ("sources", "trace")
    assert case["expect"] in ("flag", "pass")
    if case["kind"] == "sources":
        assert case["sources"] and all(s["id"] and s["text"] for s in case["sources"])
    else:
        assert case["trace"] and all(set(t) == {"name", "args", "result"} for t in case["trace"])
    if case["expect"] == "flag":
        assert case["flag_span"] in case["answer"]           # the span a checker should point at exists
    else:
        assert "flag_span" not in case


def _werner_concurrence(w):
    return max(0.0, (3 * w - 1) / 2)


def _werner_purity(w):
    return (1 + 3 * w * w) / 4


def test_physics_results_are_consistent():
    """Every concurrence and purity in the traces is that of the Werner weight the noise call gave:
    global depolarizing p -> weight 1 - p; local depolarizing p on both photons -> (1 - p)^2."""
    for case in CASES:
        if case["kind"] != "trace" or case["domain"] != "physics":
            continue
        weights = {}
        for call in case["trace"]:
            a, r = call["args"], call["result"]
            if call["name"] == "apply_global_noise":
                assert math.isclose(r["werner_weight"], 1 - a["param"], abs_tol=1e-12), case["id"]
                weights[r["state"]] = r["werner_weight"]
            elif call["name"] == "apply_local_noise":
                assert a["qubits"] == "both"
                assert math.isclose(r["werner_weight"], (1 - a["param"]) ** 2, abs_tol=1e-12), case["id"]
                weights[r["state"]] = r["werner_weight"]
            elif call["name"] == "compute_measures":
                w = weights[a["state"]]
                assert math.isclose(r["concurrence"], _werner_concurrence(w), abs_tol=1e-9), case["id"]
                assert math.isclose(r["purity"], _werner_purity(w), abs_tol=1e-9), case["id"]
                if "negativity" in r:
                    assert math.isclose(r["negativity"], max(0.0, (3 * w - 1) / 4), abs_tol=1e-9), case["id"]


def test_loan_numbers_are_consistent():
    """340.29 a month for 36 months at 7% is a principal of 11020.78 and 12250.43 in total."""
    r, n, principal = 0.07 / 12, 36, 11020.78
    monthly = principal * r / (1 - (1 + r) ** -n)
    assert round(monthly, 2) == 340.29
    assert round(monthly * n, 2) == 12250.43
    for case in CASES:
        for call in case.get("trace", []):
            if call["name"] == "loan_cost":
                assert call["result"] == {"total": 12250.43, "monthly": 340.29}


def test_currency_numbers_are_consistent():
    for call in BY_ID["a3"]["trace"]:
        a, res = call["args"], call["result"]
        assert math.isclose(a["amount"] * res["rate"], res["amount_eur"], abs_tol=1e-9)


def test_trace_passages_one_per_call_and_question_last():
    p = rs.render_passages(BY_ID["a2"])
    assert p[0] == ("T1", 'Tool call 1: loan_cost(rate=0.07, years=3)\nResult: {"total": 12250.43, "monthly": 340.29}')
    assert p[-1] == ("Q", "User question: What is the 5-year cost at 7% interest?")
    failed = rs.render_passages(BY_ID["f1"])
    assert failed[0][1].endswith("Result: Error: upstream service timed out")


def test_source_passages_keep_their_ids():
    assert [pid for pid, _t in rs.render_passages(BY_ID["q2"])] == ["S1", "S2", "Q"]


def test_citation_markers_are_taken_out_unless_kept():
    a = BY_ID["n1"]["answer"]
    assert rs.answer_for_tools(a) == "Acme's Q3 revenue was $42.1 million, up 8% from Q2."
    assert rs.answer_for_tools(a, "keep") == a
    assert rs.answer_for_tools('x "y" [S1, S2] z') == 'x "y" z'


def test_tool_not_installed_is_reported_not_crashed(monkeypatch):
    monkeypatch.setattr(rs.Adapter, "version", lambda self: "")
    run = rs.run_tool(rs.GroundLens(), CASES)
    assert run["setup_error"].startswith("not installed") and run["results"] == []


class FakeFlagsNumbers(rs.Adapter):
    """Flags an answer when it has a digit that no passage has: a crude number check."""
    name = "groundlens"                      # reuses a known name so version() can be patched

    def check(self, case, passages):
        import re
        hay = " ".join(t for _p, t in passages)
        bad = [n for n in re.findall(r"\d+(?:\.\d+)?", case["answer"].replace(",", "")) if n not in hay]
        return ("flag", f"not in passages: {bad}") if bad else ("pass", "")


def test_harness_with_a_fake_tool(monkeypatch, tmp_path):
    monkeypatch.setattr(rs.Adapter, "version", lambda self: "0.0-fake")
    run = rs.run_tool(FakeFlagsNumbers(), CASES)
    assert len(run["results"]) == 20 and run["results"][0]["warmup"]
    s = rs.summarize(run, CASES)
    # worked out by hand: n1 '42.1' (a real catch); a3 '73.60' and f1 '9' (the passages have '73.6'
    # and no forecast); n2 '24' (23.7 rounded: a false alarm). Every other number is in a passage or
    # the question, which is why a plain number check misses v1-v3, a1, a2, t1, s1 and c1.
    flagged = sorted(r["id"] for r in run["results"] if r["verdict"] == "flag")
    assert flagged == ["a3", "f1", "n1", "n2"]
    assert s["flagged_errors"] == 3 and s["false_alarms"] == 1 and s["crashes"] == 0
    md = rs.markdown({"date": "2026-11-17T12:00:00", "python": "3.11", "platform": "test",
                      "cases_version": "x", "runs": [dict(run, summary=s)]}, CASES)
    assert "| groundlens | 0.0-fake | 3 of 13 | 1 of 7 | 0 |" in md
    assert md.count("| Right reason? |") == 20


def test_main_writes_both_files(monkeypatch, tmp_path):
    monkeypatch.setattr(rs.Adapter, "version", lambda self: "")
    assert rs.main(["--tools", "groundlens,halluguard", "--out", str(tmp_path)]) == 0
    files = sorted(f.suffix for f in tmp_path.iterdir())
    assert files == [".json", ".md"]
    report = json.loads(next(tmp_path.glob("*.json")).read_text(encoding="utf-8"))
    assert [r["tool"] for r in report["runs"]] == ["groundlens", "halluguard"]


def test_unknown_tool_is_refused():
    with pytest.raises(SystemExit):
        rs.main(["--tools", "nosuchtool"])


def test_a_second_run_never_overwrites_the_first(monkeypatch, tmp_path):
    monkeypatch.setattr(rs.Adapter, "version", lambda self: "")
    for _ in range(2):
        assert rs.main(["--tools", "groundlens", "--out", str(tmp_path)]) == 0
    names = sorted(f.name for f in tmp_path.iterdir())
    day = names[0][len("survey_"):len("survey_") + 10]
    assert names == [f"survey_{day}_groundlens.json", f"survey_{day}_groundlens.md",
                     f"survey_{day}_groundlens_2.json", f"survey_{day}_groundlens_2.md"]
