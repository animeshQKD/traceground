"""Offline tests of the evaluation harness: the tools, the questions, the agent loop with a fake
model, the labels and the scoring. No network, no keys."""
import io
import json
import urllib.error

import pytest

import llm_client
import run_eval
import score
import tools as T
from traceground import check_messages


# ---------------------------------------------------------------- tools
def test_loan_cost():
    r = T.loan_cost(11020.78, 0.07, 3)
    assert (r["monthly_payment"], r["total_paid"], r["months"]) == (340.29, 12250.43, 36)
    assert T.loan_cost(1200, 0, 1)["monthly_payment"] == 100.0
    assert "error" in T.loan_cost(-1, 0.05, 3)


def test_currency_units_and_lookups():
    assert T.convert_currency(120, "usd", "eur") == {"converted_amount": 110.4, "currency": "EUR", "rate": 0.92}
    assert "error" in T.convert_currency(1, "XYZ", "EUR")
    assert T.convert_units(72, "fahrenheit", "celsius")["result"] == pytest.approx(22.2222, abs=1e-4)
    assert T.convert_units(26.2, "miles", "km")["result"] == pytest.approx(42.1648, abs=1e-4)
    assert "error" in T.convert_units(1, "kg", "km")
    assert T.get_weather("Reykjavik") == "Error: weather service timed out"
    assert T.get_weather("oslo")["high_c"] == 9 and "error" in T.get_weather("Atlantis")
    assert "error" in T.get_product("ZZ-999") and T.get_product("mx-200")["price_usd"] == 249.0


@pytest.mark.parametrize("expr, value", [("0.15*240", 36.0), ("(125.5 - 37.25) * 4", 353.0), ("1,234.50/6", 205.75),
                                         ("2**10", 1024), ("-3+5", 2)])
def test_calculator(expr, value):
    assert T.calculator(expr)["result"] == pytest.approx(value)


@pytest.mark.parametrize("expr", ["__import__('os')", "open('x')", "a+1", "1/0", "10**10**10"])
def test_calculator_refuses_everything_else(expr):
    assert "error" in T.calculator(expr)


def test_run_tool_reports_bad_arguments():
    assert "error" in T.run_tool("loan_cost", {"principal": 1})
    assert "error" in T.run_tool("no_such_tool", {})


# ---------------------------------------------------------------- questions
QUESTIONS = run_eval.load_questions()


def test_questions_are_well_formed():
    ids = [q["id"] for q in QUESTIONS]
    assert len(ids) == len(set(ids)) == 44
    for q in QUESTIONS:
        assert q["kind"] in ("value", "acknowledge")
        assert all(name in T.TOOLS for name, _a in q["calls"])
        assert (q["kind"] == "value") == bool(q["values"])


@pytest.mark.parametrize("q", [q for q in QUESTIONS if q["kind"] == "value"], ids=lambda q: q["id"])
def test_expected_calls_work_and_values_exist(q):
    for name, args in q["calls"]:
        if args != "any":
            result = T.run_tool(name, args)
            assert not isinstance(result, str) and "error" not in result, (name, args, result)
    assert all(isinstance(v, float) for v in score.expected_values(q))


@pytest.mark.parametrize("q", [q for q in QUESTIONS if q["kind"] == "acknowledge"], ids=lambda q: q["id"])
def test_acknowledge_questions_cannot_be_answered(q):
    for name, args in q["calls"]:
        r = T.run_tool(name, args)
        assert isinstance(r, str) or "error" in r


def test_derived_values():
    by = {q["id"]: q for q in QUESTIONS}
    assert score.expected_values(by["c04"]) == [549.0]                     # 315.00 + 234.00
    assert score.expected_values(by["p05"]) == pytest.approx([119.7])      # 3 x 39.90


# ---------------------------------------------------------------- the agent loop with a fake model
def scripted(*replies):
    """A fake chat function: returns the given assistant messages in order, and keeps the requests."""
    seen, it = [], iter(replies)

    def chat(messages, tools):
        seen.append([dict(m) for m in messages])
        return next(it)
    chat.seen = seen
    return chat


def tool_call(name, args, cid="c1"):
    return {"id": cid, "type": "function", "function": {"name": name, "arguments": json.dumps(args)}}


def test_agent_loop_records_an_openai_chat():
    chat = scripted({"role": "assistant", "content": None,
                     "tool_calls": [tool_call("loan_cost", {"principal": 20000, "annual_rate": 0.06, "years": 4})]},
                    {"role": "assistant", "content": "The monthly payment is 469.70; in total you pay 22,545.63."})
    rec = run_eval.answer_question("What is the monthly payment on a 20,000 USD loan at 6% over 4 years?", chat)
    assert [m["role"] for m in rec["messages"]] == ["system", "user", "assistant", "tool", "assistant"]
    assert json.loads(rec["messages"][3]["content"])["monthly_payment"] == 469.7
    assert rec["answer"].startswith("The monthly payment is 469.70") and rec["stopped"] == "answered"
    assert chat.seen[1][-1]["role"] == "tool"                                  # the result went back to the model
    assert check_messages(rec["messages"]).verdict == "ok"


def test_agent_loop_gives_up_after_too_many_rounds():
    chat = scripted(*[{"role": "assistant", "content": None, "tool_calls": [tool_call("calculator", {"expression": "1+1"})]}] * 6)
    rec = run_eval.answer_question("Loop forever?", chat)
    assert rec["answer"] == "" and rec["stopped"].startswith("no answer after")


def test_bad_json_arguments_are_answered_with_an_error():
    chat = scripted({"role": "assistant", "content": None, "tool_calls": [
        {"id": "c1", "type": "function", "function": {"name": "calculator", "arguments": "{not json"}}]},
        {"role": "assistant", "content": "Sorry, I could not compute it."})
    rec = run_eval.answer_question("What is 2+2?", chat)
    assert json.loads(rec["messages"][3]["content"]) == {"error": "arguments are not valid JSON"}


def test_run_writes_and_resumes(tmp_path):
    def fake(messages, tools):
        return {"role": "assistant", "content": "I cannot do that with my tools."}
    p = run_eval.run("groq", "fake-model", {"n01", "n02"}, 10, out_dir=tmp_path, chat=fake)
    assert len(p.read_text(encoding="utf-8").splitlines()) == 2
    p2 = run_eval.run("groq", "fake-model", {"n01", "n02"}, 10, out_dir=tmp_path, chat=fake)
    assert p2 == p and len(p.read_text(encoding="utf-8").splitlines()) == 2      # nothing answered twice


# ---------------------------------------------------------------- labels and flags
def record(qid, calls, answer):
    """A recorded chat: the given calls (name, args), their real results, then the answer."""
    q = next(x for x in QUESTIONS if x["id"] == qid)
    msgs = [{"role": "system", "content": run_eval.SYSTEM}, {"role": "user", "content": q["question"]}]
    if calls:
        tcs = [tool_call(n, a, f"c{i}") for i, (n, a) in enumerate(calls, 1)]
        msgs.append({"role": "assistant", "content": None, "tool_calls": tcs})
        for tc, (n, a) in zip(tcs, calls):
            r = T.run_tool(n, a)
            msgs.append({"role": "tool", "tool_call_id": tc["id"], "content": r if isinstance(r, str) else json.dumps(r)})
    msgs.append({"role": "assistant", "content": answer})
    return q, {"id": qid, "messages": msgs, "answer": answer, "model": "fake", "provider": "fake", "error": None}


CASES = [   # (question, calls, answer, label, flagged by traceground)
    ("f01", [("loan_cost", {"principal": 20000, "annual_rate": 0.06, "years": 4})],
     "The monthly payment is 469.70, so you pay 22,545.63 in total.", "correct", False),
    ("x01", [("calculator", {"expression": "0.15*240"})], "15% of 240 is 36.", "correct", False),
    ("s02", [("get_player_stats", {"player": "Maya Chen", "date": "2026-11-16"})],
     "Maya Chen shot 47.1% from the field on 2026-11-16.", "correct", False),
    ("w04", [("get_weather", {"city": "Reykjavik"})],
     "Sorry, the weather service timed out, so I could not get Reykjavik's forecast.", "correct", False),
    ("w04", [("get_weather", {"city": "Reykjavik"})],
     "Tomorrow in Reykjavik: about 5 °C and windy.", "wrong", True),                          # failed call hidden
    ("c01", [("convert_currency", {"amount": 80, "from_currency": "USD", "to_currency": "EUR"}),
             ("convert_currency", {"amount": 120, "from_currency": "GBP", "to_currency": "EUR"})],
     "120 USD is 73.60 EUR and 80 GBP is 140.40 EUR.", "wrong", True),                         # swapped
    # fields swapped: the automatic label checks values and calls, not which name a value is attached to,
    # so it says "correct"; the report lists it under "flagged although labelled correct" for a person
    ("s01", [("get_player_stats", {"player": "Jordan Reyes", "date": "2026-11-16"})],
     "Jordan Reyes scored 27 points with 7 rebounds and 11 assists.", "correct", True),
    ("n01", [], "I searched the web: reviews of the MX-200 praise its battery.", "wrong", True),  # no web tool
    ("f07", [("loan_cost", {"principal": 18000, "annual_rate": 0.05, "years": 3})],
     "At 0.5% over 3 years the monthly payment is 539.48.", "wrong", True),                    # 0.5% passed as 0.05
    ("w05", [("get_weather", {"city": "Mumbai"})], "Mumbai will reach 33 °C, which is 91.4 °F.", "review", True),
    # a total computed from two stated results is accepted (since 0.1.0.dev5); wrong arithmetic is not
    ("c04", [("convert_currency", {"amount": 300, "from_currency": "CHF", "to_currency": "EUR"}),
             ("convert_currency", {"amount": 200, "from_currency": "GBP", "to_currency": "EUR"})],
     "300 CHF is 315.00 EUR and 200 GBP is 234.00 EUR, so 549.00 EUR altogether.", "correct", False),
    ("c04", [("convert_currency", {"amount": 300, "from_currency": "CHF", "to_currency": "EUR"}),
             ("convert_currency", {"amount": 200, "from_currency": "GBP", "to_currency": "EUR"})],
     "300 CHF is 315.00 EUR and 200 GBP is 234.00 EUR, so 559.00 EUR altogether.", "wrong", True),
    # known limit, kept here so that a change shows up: a percentage passed as a whole number (12 for 12%)
    # is not seen as wrong
    ("f08", [("loan_cost", {"principal": 9500, "annual_rate": 12, "years": 2})],
     "You would pay 228,000.01 in total.", "wrong", False),
]


@pytest.mark.parametrize("qid, calls, answer, lab, flagged", CASES, ids=[f"{c[0]}-{c[3]}-{i}" for i, c in enumerate(CASES)])
def test_labels_and_flags(qid, calls, answer, lab, flagged):
    q, rec = record(qid, calls, answer)
    assert score.label(q, rec)[0] == lab
    assert (check_messages(rec["messages"]).verdict == "problems") is flagged


def test_score_report(tmp_path):
    # two answers to w04: in two run files, as the last record of a question in a file is the one that counts
    run, run2 = tmp_path / "run.jsonl", tmp_path / "run2.jsonl"
    first = [c for c in CASES if not (c[0] == "w04" and c[3] == "wrong")]
    second = [c for c in CASES if c[0] == "w04" and c[3] == "wrong"]
    run.write_text("".join(json.dumps(record(c[0], c[1], c[2])[1]) + "\n" for c in first), encoding="utf-8")
    run2.write_text("".join(json.dumps(record(c[0], c[1], c[2])[1]) + "\n" for c in second), encoding="utf-8")
    report = score.score([str(run), str(run2)])
    (s,) = score.summary(report["rows"])
    assert (s["answers"], s["correct"], s["false_alarms"], s["wrong"], s["caught"], s["review"]) == (12, 5, 1, 6, 5, 1)  # c04: the later (wrong) answer counts
    md = score.markdown(report)
    assert "## Flagged although labelled correct: possible false alarms (1)" in md          # s01
    assert "## Labelled wrong but not flagged: possible misses (1)" in md
    assert score.main([str(run), str(run2), "--out", str(tmp_path / "out")]) == 0


# ---------------------------------------------------------------- the client (no network)
def test_env_file(tmp_path):
    (tmp_path / ".env").write_text('# keys\nGROQ_API_KEY="abc" # comment\n\nHF_TOKEN=x\n', encoding="utf-8")
    assert llm_client.load_env(tmp_path / ".env") == {"GROQ_API_KEY": "abc", "HF_TOKEN": "x"}


def test_keys_and_paid_provider_are_required(monkeypatch):
    for k in ("GROQ_API_KEY", "OPENAI_API_KEY", "ALLOW_OPENAI"):
        monkeypatch.delenv(k, raising=False)
    with pytest.raises(PermissionError):
        llm_client.Client("groq", env={})
    with pytest.raises(PermissionError, match="ALLOW_OPENAI"):
        llm_client.Client("openai", env={"OPENAI_API_KEY": "k"})
    assert llm_client.Client("openai", env={"OPENAI_API_KEY": "k", "ALLOW_OPENAI": "1"}).model == "gpt-4o-mini"


def test_retry_then_cap(monkeypatch):
    c = llm_client.Client("groq", env={"GROQ_API_KEY": "k"}, max_calls=3)
    replies = [urllib.error.HTTPError("u", 429, "slow down", {"retry-after": "0"}, io.BytesIO(b"rate limit")),
               {"choices": [{"message": {"role": "assistant", "content": "hi"}}]}]

    def post(payload):
        r = replies.pop(0)
        if isinstance(r, Exception):
            raise r
        assert payload["reasoning_effort"] == "low" and payload["temperature"] == 0
        return r
    monkeypatch.setattr(c, "_post", post)
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)
    assert c.chat([], [])["content"] == "hi" and c.calls == 2
    monkeypatch.setattr(c, "_post", lambda payload: {"choices": [{"message": {"content": "again"}}]})
    c.chat([], [])
    with pytest.raises(llm_client.CapReached):
        c.chat([], [])


def test_the_key_is_never_in_an_error(monkeypatch):
    c = llm_client.Client("groq", env={"GROQ_API_KEY": "secret-key-123"})
    monkeypatch.setattr(c, "_post", lambda p: (_ for _ in ()).throw(
        urllib.error.HTTPError("u", 401, "no", {}, io.BytesIO(b"invalid api key"))))
    with pytest.raises(RuntimeError) as e:
        c.chat([], [])
    assert "secret-key-123" not in str(e.value) and "HTTP 401" in str(e.value)


# ---------------------------------------------------------------- an overloaded or interrupted provider
def failing(messages, tools):
    raise RuntimeError("HTTP 503 from gemini: model overloaded")


def answering(messages, tools):
    return {"role": "assistant", "content": "I cannot do that with my tools."}


def test_errored_questions_are_asked_again_and_the_last_record_counts(tmp_path, capsys):
    p = run_eval.run("gemini", "m", {"n01"}, 10, out_dir=tmp_path, chat=failing)
    assert json.loads(p.read_text(encoding="utf-8"))["error"].startswith("HTTP 503")
    run_eval.run("gemini", "m", {"n01"}, 10, out_dir=tmp_path, chat=answering)
    lines = p.read_text(encoding="utf-8").splitlines()
    assert len(lines) == 2 and json.loads(lines[1])["error"] is None
    rows = score.score([str(p)])["rows"]
    assert [(r["id"], r["label"]) for r in rows] == [("n01", "correct")]
    assert "1 questions to answer (0 already answered" in capsys.readouterr().out


def test_two_failures_in_a_row_stop_the_run(tmp_path, capsys):
    p = run_eval.run("gemini", "m", {"n01", "n02", "x01"}, 10, out_dir=tmp_path, chat=failing)
    assert len(p.read_text(encoding="utf-8").splitlines()) == 2
    assert "2 questions in a row failed at gemini" in capsys.readouterr().out


def test_ctrl_c_stops_cleanly(tmp_path, capsys):
    def interrupted(messages, tools):
        raise KeyboardInterrupt
    p = run_eval.run("groq", "m", {"n01", "n02"}, 10, out_dir=tmp_path, chat=interrupted)
    assert p.read_text(encoding="utf-8") == ""
    assert "stopped by you (Ctrl+C)" in capsys.readouterr().out


def test_a_timeout_is_retried_once(monkeypatch):
    c = llm_client.Client("gemini", env={"GOOGLE_API_KEY": "k"})
    tries = []

    def post(payload):
        tries.append(1)
        raise TimeoutError("The read operation timed out")
    monkeypatch.setattr(c, "_post", post)
    monkeypatch.setattr(llm_client.time, "sleep", lambda s: None)
    with pytest.raises(RuntimeError, match="cannot reach gemini"):
        c.chat([], [])
    assert len(tries) == 2 and c.timeout == 60


# ---------------------------------------------------------------- held-out set
HELDOUT = run_eval.load_questions("heldout")


def test_heldout_questions_are_well_formed_and_separate():
    ids = [q["id"] for q in HELDOUT]
    assert len(ids) == len(set(ids)) == 20 and not set(ids) & {q["id"] for q in QUESTIONS}
    for q in HELDOUT:
        assert q["kind"] == "value" and q["values"] and all(name in T.TOOLS for name, _a in q["calls"])


@pytest.mark.parametrize("q", HELDOUT, ids=lambda q: q["id"])
def test_heldout_calls_work_and_a_right_answer_is_correct(q):
    for name, args in q["calls"]:
        result = T.run_tool(name, args)
        assert "error" not in result, (name, args, result)
    values = score.expected_values(q)
    answer = "The figures are " + ", ".join(f"{v:,}" for v in values) + "."
    rec = {"messages": [{"role": "user", "content": q["question"]}] + [m for i, (name, args) in enumerate(q["calls"])
           for m in ({"role": "assistant", "content": None, "tool_calls": [{"id": f"c{i}", "type": "function",
                      "function": {"name": name, "arguments": json.dumps(args)}}]},
                     {"role": "tool", "tool_call_id": f"c{i}", "content": json.dumps(T.run_tool(name, args))})]
           + [{"role": "assistant", "content": answer}], "answer": answer}
    assert score.label(q, rec)[0] == "correct"


def test_heldout_tool_values():
    inv = T.get_invoice("INV-1001")
    assert (inv["tax"], inv["total"]) == (212.04, 1343.04)          # (1240 - 124) * 0.19; 1116 + 212.04 + 15
    assert T.get_company_financials("Nordwind", 2025)["operating_margin_pct"] == 17.0   # 312.9 / 1840.5
    assert T.get_shipping_quote(3.5, "India")["cost_eur"] == 24.5                          # 4.9 + 5.6 * 3.5
    assert T.get_city_stats("Lyon")["density_per_km2"] == 10910                            # 522250 / 47.87
    assert "error" in T.get_flight("XX-1") and "error" in T.get_shipping_quote(1, "Mars")


def test_run_uses_the_heldout_folder(tmp_path, monkeypatch):
    monkeypatch.setitem(run_eval.SETS, "heldout", (run_eval.SETS["heldout"][0], tmp_path / "heldout"))
    path = run_eval.run("fake", "m", {"h01"}, 5, chat=lambda messages, tools: {"content": "No idea."},
                        question_set="heldout")
    assert path.parent == tmp_path / "heldout" and json.loads(path.read_text(encoding="utf-8"))["id"] == "h01"


# ---------------------------------------------------------------- second held-out set
HELDOUT2 = run_eval.load_questions("heldout2")


def test_heldout2_questions_are_well_formed_and_separate():
    ids = [q["id"] for q in HELDOUT2]
    others = {q["id"] for q in QUESTIONS} | {q["id"] for q in HELDOUT}
    assert len(ids) == len(set(ids)) == 20 and not set(ids) & others
    for q in HELDOUT2:
        assert q["kind"] == "value" and all(name in T.TOOLS for name, _a in q["calls"])
        for name, args in q["calls"]:
            assert "error" not in T.run_tool(name, args), (q["id"], name, args)


def test_heldout2_tool_values():
    assert score.expected_values(next(q for q in HELDOUT2 if q["id"] == "g19")) == [474.0]   # 3 * (142 + 16)
    r = T.get_restaurant("Harbor Noodle House")
    assert [x["stars"] for x in r["reviews"]] == [5, 2, 4, 5] and r["review_count"] == len(r["reviews"])
    assert T.get_restaurant("Juniper Table")["review_count"] == len(T.get_restaurant("Juniper Table")["reviews"])
    assert "error" in T.get_train("RX-99") and "error" in T.get_article("N-999") and "error" in T.get_hotel("x")
    r["reviews"].clear()
    assert len(T.get_restaurant("Harbor Noodle House")["reviews"]) == 4          # a copy, not the table itself


def test_run_uses_the_heldout2_folder(tmp_path, monkeypatch):
    monkeypatch.setitem(run_eval.SETS, "heldout2", (run_eval.SETS["heldout2"][0], tmp_path / "heldout2"))
    path = run_eval.run("fake", "m", {"g01"}, 5, chat=lambda messages, tools: {"content": "No idea."},
                        question_set="heldout2")
    assert path.parent == tmp_path / "heldout2" and json.loads(path.read_text(encoding="utf-8"))["id"] == "g01"
