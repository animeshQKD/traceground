"""Reading traces: the call list, OpenAI-style messages, failures, ids, numeric fields."""
import json

import pytest

from traceground import check_answer, check_messages
from traceground.traces import ToolCall, from_messages, is_error, load_trace, name_calls, numeric_fields

OPENAI = [
    {"role": "system", "content": "You are a loan assistant."},
    {"role": "user", "content": "What is the 5-year cost at 7% interest?"},
    {"role": "assistant", "content": None, "tool_calls": [
        {"id": "call_1", "type": "function",
         "function": {"name": "loan_cost", "arguments": json.dumps({"rate": 0.07, "years": 3})}}]},
    {"role": "tool", "tool_call_id": "call_1", "content": json.dumps({"total": 12250.43, "monthly": 340.29})},
    {"role": "assistant", "content": "Over 5 years at 7% you pay 12,250 in total, 340.29 a month."},
]


def test_list_of_calls_with_other_key_names():
    _q, calls, _a = load_trace([
        {"name": "a", "args": {"x": 1}, "result": {"y": 2}},
        {"tool": "b", "arguments": '{"x": 3}', "output": '{"y": 4}'},
        {"tool_name": "c", "input": "plain text", "observation": "Error: timed out"},
        {"name": "d", "args": {}, "result": "fine", "error": "rate limited"},
    ])
    assert [(c.name, c.args, c.result, c.error) for c in calls] == [
        ("a", {"x": 1}, {"y": 2}, False), ("b", {"x": 3}, {"y": 4}, False),
        ("c", {"input": "plain text"}, "Error: timed out", True), ("d", {}, "fine", True)]


def test_openai_messages():
    question, calls, answer = from_messages(OPENAI)
    assert question == "What is the 5-year cost at 7% interest?"
    assert answer == "Over 5 years at 7% you pay 12,250 in total, 340.29 a month."
    (c,) = calls
    assert (c.name, c.args, c.result, c.call_id) == ("loan_cost", {"rate": 0.07, "years": 3},
                                                     {"total": 12250.43, "monthly": 340.29}, "call_1")


def test_openai_content_parts_and_old_function_call_form():
    msgs = [{"role": "user", "content": [{"type": "text", "text": "Weather in Oslo?"}]},
            {"role": "assistant", "content": None, "function_call": {"name": "get_forecast", "arguments": '{"city": "Oslo"}'}},
            {"role": "function", "name": "get_forecast", "content": '{"high_c": 9}'},
            {"role": "assistant", "content": [{"type": "text", "text": "A high of 9 °C."}]}]
    question, calls, answer = from_messages(msgs)
    assert question == "Weather in Oslo?" and answer == "A high of 9 °C." and calls[0].result == {"high_c": 9}


def test_wrapped_shapes():
    assert load_trace({"messages": OPENAI})[0] == "What is the 5-year cost at 7% interest?"
    q, calls, a = load_trace({"question": "Q?", "calls": [{"name": "a", "args": {}, "result": 1}], "answer": "A."})
    assert (q, len(calls), a) == ("Q?", 1, "A.")
    with pytest.raises(ValueError):
        load_trace({"steps": []})
    with pytest.raises(TypeError):
        load_trace("not a trace")


@pytest.mark.parametrize("result, failed", [
    ("Error: upstream service timed out", True), ("Traceback (most recent call last): ...", True),
    ({"error": "not found"}, True), ({"status": "failed"}, True), ({"error": None, "value": 3}, False),
    ("The errors are small.", False), ({"status": "ok"}, False), (42, False)])
def test_failures(result, failed):
    assert is_error(result) is failed


def test_ids_name_repeated_calls():
    calls = name_calls([ToolCall("f"), ToolCall("g"), ToolCall("f")])
    assert [c.id for c in calls] == ["f (call 1)", "g", "f (call 2)"]


def test_numeric_fields_flatten_nested_results():
    assert numeric_fields({"a": 1, "b": {"c": 2.5, "d": "3.5", "e": "x", "f": True}, "g": [{"h": 4}, 5]}) == [
        ("a", "a", 1.0), ("b.c", "c", 2.5), ("b.d", "d", 3.5), ("g[0].h", "h", 4.0)]


def test_check_messages_takes_question_and_answer_from_the_chat():
    r = check_messages(OPENAI)
    assert r.verdict == "problems" and [f.check for f in r.findings] == ["argument"]
    assert r.findings[0].message == "The question asks for 5-year, but loan_cost was called with years=3."


def test_tool_results_are_evidence_and_failed_ones_are_not_for_fields():
    trace = [{"name": "get_forecast", "args": {"city": "Oslo"}, "result": {"high_c": 9, "rain_chance_pct": 70}}]
    assert check_answer("A high of 9 °C and a 70% chance of rain.", trace=trace).verdict == "ok"
    r = check_answer("A 75% chance of rain.", trace=trace)
    assert r.findings[0].message.startswith('"75% chance of rain": the tool results give rain_chance_pct = 70')


def test_number_messages_name_the_tool_results():
    (f,) = check_answer("It is 42.6.", trace=[{"name": "t", "args": {}, "result": {"v": 42.5}}]).findings
    assert f.message.startswith('"42.6" is not in the tool results or the question.')


def test_a_source_and_a_call_may_not_share_an_id():
    with pytest.raises(ValueError):
        check_answer("x", {"t": "text"}, trace=[{"name": "t", "args": {}, "result": 1}])
