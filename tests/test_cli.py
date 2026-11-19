import json
import subprocess
import sys

import pytest

from traceground.cli import main


@pytest.fixture
def files(tmp_path):
    def make(name, text, bom=False):
        p = tmp_path / name
        p.write_bytes((b"\xef\xbb\xbf" if bom else b"") + text.encode("utf-8"))
        return str(p)
    return make


def test_exit_code_0_when_supported(files, capsys):
    a = files("answer.txt", "The high is about 24 °C.")
    s = files("forecast.txt", "High 23.7 °C.")
    assert main(["--answer", a, "--sources", s]) == 0
    assert capsys.readouterr().out.startswith("OK: 1 number checked against 1 source: all supported.")


def test_exit_code_1_with_the_source_file_name_as_id(files, capsys):
    a = files("answer.txt", "Revenue was $42.1 million.")
    s = files("report.txt", "Revenue was $41.2 million.", bom=True)       # Notepad's BOM is read correctly
    assert main(["--answer", a, "--sources", s]) == 1
    out = capsys.readouterr().out
    assert out.startswith("PROBLEMS:") and "41.2 million (report.txt)" in out


def test_exit_code_3_without_evidence(files, capsys):
    assert main(["--answer", files("answer.txt", "It is 42.6.")]) == 3
    assert capsys.readouterr().out.startswith("UNSURE:")


def test_question_file_and_json(files, capsys):
    a = files("answer.txt", "Over 36 months you pay 340.29.")
    s = files("quote.txt", "monthly 340.29")
    q = files("question.txt", "What is the 36-month cost?")
    assert main(["--answer", a, "--sources", s, "--question", q, "--json"]) == 0
    assert json.loads(capsys.readouterr().out)["verdict"] == "ok"


def test_options(files, capsys):
    a = files("answer.txt", "There are 3 options at 7%.")
    s = files("s.txt", "options: a, b; rate 0.07")
    assert main(["--answer", a, "--sources", s]) == 0
    assert main(["--answer", a, "--sources", s, "--check-small-integers"]) == 1
    assert main(["--answer", a, "--sources", s, "--no-percent-as-fraction"]) == 1


def test_missing_file_is_exit_code_2(files, capsys):
    assert main(["--answer", "no_such_file.txt", "--sources", files("s.txt", "x")]) == 2
    assert "cannot read no_such_file.txt" in capsys.readouterr().err


def test_same_source_name_twice_is_refused(tmp_path):
    (tmp_path / "x").mkdir()
    for p in (tmp_path / "a.txt", tmp_path / "x" / "a.txt"):
        p.write_text("1.5", encoding="utf-8")
    ans = tmp_path / "ans.txt"
    ans.write_text("1.5", encoding="utf-8")
    with pytest.raises(SystemExit) as e:
        main(["--answer", str(ans), "--sources", str(tmp_path / "a.txt"), str(tmp_path / "x" / "a.txt")])
    assert e.value.code == 2


def test_standard_input():
    out = subprocess.run([sys.executable, "-m", "traceground", "--answer", "-", "--json"],
                         input="It is 42.6.", capture_output=True, text=True, encoding="utf-8")
    assert out.returncode == 3 and json.loads(out.stdout)["verdict"] == "unsure"


def test_quotes_and_no_quotes(files, capsys):
    a = files("answer.txt", 'The manual says "updates are installed every week" [manual.txt].')
    s = files("manual.txt", "Updates are installed automatically every night.")
    assert main(["--answer", a, "--sources", s]) == 1
    assert "The closest wording, in manual.txt" in capsys.readouterr().out
    assert main(["--answer", a, "--sources", s, "--no-quotes"]) == 0


def test_trace_of_chat_messages(files, capsys):
    msgs = [{"role": "user", "content": "What is the 5-year cost at 7% interest?"},
            {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
                "name": "loan_cost", "arguments": json.dumps({"rate": 0.07, "years": 3})}}]},
            {"role": "tool", "tool_call_id": "c1", "content": json.dumps({"total": 12250.43, "monthly": 340.29})},
            {"role": "assistant", "content": "Over 5 years at 7% you pay 12,250 in total, 340.29 a month."}]
    t = files("chat.json", json.dumps(msgs))
    assert main(["--trace", t]) == 1
    out = capsys.readouterr().out
    assert "The question asks for 5-year, but loan_cost was called with years=3." in out


def test_trace_of_calls_with_answer_and_question_files(files, capsys):
    t = files("calls.json", json.dumps([{"name": "get_forecast", "args": {"city": "Oslo"},
                                         "result": {"high_c": 9, "rain_chance_pct": 70}}]))
    a = files("answer.txt", "A high of 9 °C and a 70% chance of rain.")
    assert main(["--trace", t, "--answer", a]) == 0
    assert capsys.readouterr().out.startswith("OK: 1 number and 2 value-to-field bindings checked against 1 tool call")


def test_trace_errors_are_usage_errors(files, capsys):
    assert main(["--trace", files("bad.json", "{not json")]) == 2
    assert "is not valid JSON" in capsys.readouterr().err
    assert main(["--trace", files("calls.json", '[{"name": "f", "args": {}, "result": 1}]')]) == 2
    assert "no answer to check" in capsys.readouterr().err


def test_no_wording(files, capsys):
    a = files("answer.txt", "Wait, let me check: the total is 42.5.")
    s = files("s.txt", "total 42.5")
    assert main(["--answer", a, "--sources", s]) == 1
    assert main(["--answer", a, "--sources", s, "--no-wording"]) == 0
