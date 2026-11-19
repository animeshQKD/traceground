"""Tests for the demo's logic (no Gradio needed) and, when Gradio is installed, for the app's two checks."""
import json

import pytest

import demo_logic as D


def test_parse_sources():
    assert D.parse_sources("") == {}
    assert D.parse_sources("one text") == {"S1": "one text"}
    assert D.parse_sources("[S1] a\n[doc 2] b\nmore b") == {"S1": "a", "doc 2": "b\nmore b"}
    assert D.parse_sources("a\n---\nb") == {"S1": "a", "S2": "b"}
    with pytest.raises(ValueError):
        D.parse_sources("[S1] a\n[S1] b")


def test_parse_trace():
    assert D.parse_trace("") == ("calls", [])
    assert D.parse_trace('[{"name": "f", "args": {}, "result": 1}]')[0] == "calls"
    assert D.parse_trace('[{"role": "user", "content": "hi"}]')[0] == "chat"
    assert D.parse_trace('{"messages": [{"role": "user", "content": "hi"}]}')[0] == "chat"
    with pytest.raises(ValueError):
        D.parse_trace("[not json")
    with pytest.raises(ValueError):
        D.parse_trace('"a string"')


def test_highlight_covers_the_whole_answer():
    r = D.run(D.SOURCE_EXAMPLES[0]["answer"], "", D.SOURCE_EXAMPLES[0]["sources"], "")
    assert "".join(t for t, _l in r["highlight"]) == D.SOURCE_EXAMPLES[0]["answer"]
    assert [l for _t, l in r["highlight"] if l] == ["number not supported", "quote not found"]
    assert all(l in D.COLORS for _t, l in r["highlight"] if l)


@pytest.mark.parametrize("ex, labels", [
    (D.SOURCE_EXAMPLES[0], ["number not supported", "quote not found"]),
    (D.SOURCE_EXAMPLES[1], []),
    (D.SOURCE_EXAMPLES[2], ["self-contradiction"]),
], ids=["wrong number and quote", "correct", "self-contradiction"])
def test_source_examples(ex, labels):
    r = D.run(ex["answer"], ex["question"], ex["sources"], "")
    assert [row[1] for row in r["rows"]] == labels
    assert ("tg-ok" if not labels else "tg-problems") in r["banner"]


@pytest.mark.parametrize("i, labels, words", [
    (0, ["value attached to the wrong field"] * 2, "7 is the assists"),
    (1, ["tool argument different from the question"], "called with years=3"),
    (2, ["failed call reported as if it had worked", "number not supported"], "timed out"),
    (3, ["claim about a tool that was not called"], "web search"),
])
def test_trace_examples(i, labels, words):
    ex = D.TRACE_EXAMPLES[i]
    r = D.run(ex["answer"], ex["question"], "", ex["trace"])
    assert [row[1] for row in r["rows"]] == labels
    assert words in json.dumps(r["json"])


@pytest.mark.parametrize("i, labels, marked", [
    (0, [], []),
    (1, ["number not supported"], ["16:00"]),        # the finding is on "16"; the whole time is marked
    (2, ["value attached to the wrong field"] * 2, ["€1.84\u202fbillion in revenue", "€221.4\u202fmillion in net income"]),
    (3, ["number not supported"], ["14.4\u202f%"]),
    (4, ["number not supported"] * 2, ["400", "600"]),
], ids=["correct", "departure time", "currency", "growth rate", "own knowledge"])
def test_real_examples(i, labels, marked):
    ex = D.REAL_EXAMPLES[i]
    r = D.run(ex["answer"], ex["question"], ex["sources"], ex["trace"])
    assert [row[1] for row in r["rows"]] == labels
    assert [t for t, l in r["highlight"] if l] == marked
    assert ex["title"].startswith("Real: ") and ex["model"].startswith("openai/gpt-oss-")


def test_real_correct_example_shows_what_is_not_checked():
    ex = D.REAL_EXAMPLES[0]
    r = D.run(ex["answer"], ex["question"], ex["sources"], ex["trace"])
    assert "tg-ok" in r["banner"] and [ok for _a, _b, ok in r["coverage"]] == [True, False]
    assert "The other one, in grey, has nothing traceground checks" in r["answer_html"]


def test_real_examples_are_the_recorded_chats():
    """The chats in real_examples.json are the eval runs' chats, unchanged, and hold no key or path."""
    import pathlib
    text = (pathlib.Path(D.__file__).parent / "real_examples.json").read_text(encoding="utf-8")
    for bad in ("api_key", "gsk_", "sk-", "hf_", "Bearer", "C:\\", "/home/", "/Users/"):
        assert bad not in text
    data = json.loads(text)
    for e in data["examples"]:
        assert e["messages"][0]["role"] == "system" and e["messages"][-1]["role"] == "assistant"


def test_chat_with_a_typed_answer_checks_the_typed_answer():
    chat = D.TRACE_EXAMPLES[1]["trace"]
    r = D.run("Over 3 years at 7% you pay 13,338.72 in total.", "", "", chat)
    assert "13,338.72" in "".join(t for t, _l in r["highlight"])


def test_input_errors_are_shown_not_raised():
    for r in (D.run("", "", "", ""), D.run("x", "", "", "[oops"), D.run("x", "", "[S1] a\n[S1] b", "")):
        assert not r["ok"] and "tg-error" in r["banner"] and r["findings_html"] == ""
    assert "not valid JSON" in D.run("x", "", "", "[oops")["banner"]


def test_documents_and_tools_together():
    ex = D.BOTH_EXAMPLES[0]
    r = D.run(ex["answer"], ex["question"], ex["sources"], ex["trace"])
    assert [row[1] for row in r["rows"]] == ["value attached to the wrong field"]   # 4.8 million; the quote is right
    assert r["json"]["stats"]["quotes_checked"] == 1 and r["json"]["stats"]["tool_calls"] == 1


def test_highlight_takes_in_currency_signs_and_quote_marks():
    ex = D.REAL_EXAMPLES[2]                                                   # "€1.84 billion in revenue"
    marked = [t for t, l in D.run(ex["answer"], ex["question"], "", ex["trace"])["highlight"] if l]
    assert marked[0].startswith("€1.84\u202fbillion")             # the model's own narrow no-break space
    ex = D.SOURCE_EXAMPLES[0]
    marked = [t for t, l in D.run(ex["answer"], ex["question"], ex["sources"], "")["highlight"] if l]
    assert marked[1] == '"will be open every day of the week"'


def test_summary_counts_each_problem_once():
    ex = D.BOTH_EXAMPLES[0]
    r = D.run(ex["answer"], ex["question"], ex["sources"], ex["trace"])
    assert "1 value attached to the wrong field." in r["banner"] and "number not supported" not in r["banner"]


def test_labels_use_the_words_of_the_summary():
    ex = D.SOURCE_EXAMPLES[0]
    r = D.run(ex["answer"], ex["question"], ex["sources"], "")
    for label in ("number not supported", "quote not found"):
        assert label in r["banner"] and label in r["answer_html"] and label in r["findings_html"]


def test_quote_in_another_source_has_its_own_label():
    r = D.run('Rao said it "will be open seven days a week" [S1].', "", D.SOURCE_EXAMPLES[0]["sources"], "")
    assert [row[1] for row in r["rows"]] == [D.WRONG_SOURCE]


def test_marked_answer_numbers_the_findings_and_shows_only_kinds_present():
    ex = D.SOURCE_EXAMPLES[0]
    h = D.run(ex["answer"], ex["question"], ex["sources"], "")["answer_html"]
    assert '<sup class="tg-num">1</sup>' in h and '<sup class="tg-num">2</sup>' in h
    assert "self-contradiction" not in h and "thinking aloud" not in h      # the legend has only these two


def test_sentences_with_nothing_to_check_are_grey():
    src = "[S1] The library opens in March 2027."
    r = D.run("The library opens in March 2027. It will be a lovely place for families.", "", src, "")
    assert [ok for _a, _b, ok in r["coverage"]] == [True, False]
    assert '<span class="tg-unchecked">It will be a lovely place for families.</span>' in r["answer_html"]
    assert "1 of 2 sentences has numbers" in r["answer_html"] and "The other one, in grey, has nothing" in r["answer_html"]
    r = D.run("The library opens in March 2027.", "", src, "")
    assert "tg-unchecked" not in r["answer_html"] and "Every sentence (1)" in r["answer_html"]


def test_evidence_shows_the_closest_value_in_its_source():
    ex = D.SOURCE_EXAMPLES[0]
    f = D.run(ex["answer"], ex["question"], ex["sources"], "")["findings_html"]
    assert "<mark>4.2 million</mark>" in f and "<mark>will be open seven days a week</mark>" in f
    ex = D.TRACE_EXAMPLES[0]
    f = D.run(ex["answer"], ex["question"], "", ex["trace"])["findings_html"]
    assert "<mark>&quot;rebounds&quot;: 11</mark>" in f
    ex = D.TRACE_EXAMPLES[1]
    assert "<mark>years=3</mark>" in D.run(ex["answer"], ex["question"], "", ex["trace"])["findings_html"]


def test_markdown_bold_marks_are_not_shown():
    ex = D.REAL_EXAMPLES[0]                              # the model wrote **€7.30**
    h = D.run(ex["answer"], ex["question"], ex["sources"], ex["trace"])["answer_html"]
    assert "€7.30" in h and "**" not in h


def test_the_page_escapes_what_was_typed():
    r = D.run("<b>Revenue</b> was 5 million.", "", "[S1] <script>x</script> Revenue was 4 million.", "")
    assert "<b>Revenue" not in r["answer_html"] and "&lt;b&gt;" in r["answer_html"]
    assert "<script>" not in r["findings_html"]


@pytest.mark.parametrize("ex", D.REAL_EXAMPLES + D.SOURCE_EXAMPLES + D.TRACE_EXAMPLES + D.BOTH_EXAMPLES,
                         ids=lambda e: e["title"])
def test_the_code_shown_gives_the_same_report(ex, capsys):
    r = D.run(ex["answer"], ex["question"], ex.get("sources", ""), ex.get("trace", ""))
    exec(compile(r["code"], "<shown code>", "exec"), {})
    printed = capsys.readouterr().out
    assert printed.startswith(r["json"]["verdict"].upper() + ": " + r["json"]["summary"])


def test_options_appear_in_the_code():
    ex = D.SOURCE_EXAMPLES[0]
    code = D.run(ex["answer"], "", ex["sources"], "", check_small_integers=True, check_quotes=False)["code"]
    assert "check_small_integers=True" in code and "check_quotes=False" in code


def test_report_files(tmp_path):
    ex = D.SOURCE_EXAMPLES[0]
    r = D.run(ex["answer"], ex["question"], ex["sources"], "", files=True)
    js, md = r["files"]
    data = json.load(open(js, encoding="utf-8"))
    assert data["verdict"] == "problems" and len(data["findings"]) == 2 and data["version"]
    text = open(md, encoding="utf-8").read()
    assert "**PROBLEMS**" in text and "1. **number not supported** (high)" in text


def test_app_functions():
    gr = pytest.importorskip("gradio")
    import app
    assert isinstance(app.build(), gr.Blocks)
    assert len(app.EXAMPLES) == (len(D.REAL_EXAMPLES) + len(D.SOURCE_EXAMPLES) + len(D.TRACE_EXAMPLES)
                                 + len(D.BOTH_EXAMPLES))
    out = app.check(D.TRACE_EXAMPLES[0]["answer"], "", "", D.TRACE_EXAMPLES[0]["trace"], False, True)
    banner, marked, cards, code, get_json, get_md, raw = out[:7]
    assert "tg-problems" in banner and cards.count('class="tg-card"') == 2 and raw["value"]["verdict"] == "problems"
    assert "check_answer" in code["value"]
    assert get_json["value"].endswith(".json") and get_md["value"].endswith(".md")
    banner, *_ = app.check(D.SOURCE_EXAMPLES[1]["answer"], "", D.SOURCE_EXAMPLES[1]["sources"], "", False, True)
    assert "tg-ok" in banner
    out = app.check("", "", "", "", False, True)
    assert "tg-error" in out[0] and all(box["visible"] is False for box in out[7:])


# ------------------------------------------------------------------ the API and MCP tool
def test_tool_returns_the_report_as_json():
    out = json.loads(D.traceground_check("Revenue was 5 million.", "[S1] Revenue was 4 million."))
    assert out["verdict"] == "problems" and out["findings"][0]["text"] == "5 million"
    assert out["report"].startswith("PROBLEMS: ") and out["version"]
    out = json.loads(D.traceground_check("Revenue was 4 million.", '{"S1": "Revenue was 4 million."}'))
    assert out["verdict"] == "ok"


def test_tool_checks_a_whole_chat():
    out = json.loads(D.traceground_check(tool_calls=D.REAL_EXAMPLES[3]["trace"]))
    assert out["verdict"] == "problems" and [f["text"] for f in out["findings"]] == ["14.4 %"]


def test_tool_reports_input_it_cannot_read():
    assert "not valid JSON" in json.loads(D.traceground_check("x", tool_calls="[oops"))["error"]
    assert "not valid JSON" in json.loads(D.traceground_check("x", sources="{oops"))["error"]
    assert json.loads(D.traceground_check())["error"] == "type or paste the answer to check"


def test_tool_docstring_gives_each_argument_on_one_line():
    """Gradio reads one line per argument for the MCP tool's description; a wrapped line would be cut."""
    import inspect
    doc = inspect.getdoc(D.traceground_check)
    args = doc.split("Args:\n", 1)[1].split("\n\nReturns:", 1)[0].splitlines()
    names = list(inspect.signature(D.traceground_check).parameters)
    assert [line.split(":", 1)[0].strip() for line in args] == names


def test_app_exposes_one_api_endpoint():
    pytest.importorskip("gradio")
    import app
    names = [fn.api_name for fn in app.build().fns.values()]
    assert "traceground_check" in names and "check_page" in names
