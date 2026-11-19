"""check_messages reads OpenAI, Anthropic and LangChain chats the same way."""
import json

import pytest

from traceground import check_messages

QUESTION = "How many yen is 250 euros?"
ARGS = {"amount": 25, "from_currency": "EUR", "to_currency": "JPY"}     # 25: the call is wrong
RESULT = {"converted_amount": 4098.36}
ANSWER = "250 euros is about 4,098.36 yen."
WANT = ["The question asks for 250, but convert_currency was called with amount=25."]

OPENAI = [{"role": "user", "content": QUESTION},
          {"role": "assistant", "content": None, "tool_calls": [{"id": "c1", "type": "function", "function": {
              "name": "convert_currency", "arguments": json.dumps(ARGS)}}]},
          {"role": "tool", "tool_call_id": "c1", "content": json.dumps(RESULT)},
          {"role": "assistant", "content": ANSWER}]

ANTHROPIC = [{"role": "user", "content": QUESTION},
             {"role": "assistant", "content": [{"type": "text", "text": "Let me convert that."},
                                               {"type": "tool_use", "id": "toolu_1", "name": "convert_currency",
                                                "input": ARGS}]},
             {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "toolu_1",
                                           "content": [{"type": "text", "text": json.dumps(RESULT)}]}]},
             {"role": "assistant", "content": [{"type": "text", "text": ANSWER}]}]

# what langchain_core.messages.messages_to_dict gives (fields trimmed)
LANGCHAIN_DICTS = [
    {"type": "human", "data": {"content": QUESTION, "type": "human"}},
    {"type": "ai", "data": {"content": "", "type": "ai", "tool_calls": [
        {"name": "convert_currency", "args": ARGS, "id": "call_1", "type": "tool_call"}]}},
    {"type": "tool", "data": {"content": json.dumps(RESULT), "type": "tool", "tool_call_id": "call_1",
                              "status": "success"}},
    {"type": "ai", "data": {"content": ANSWER, "type": "ai", "tool_calls": []}}]


class _Msg:                     # stands in for LangChain message objects: .type, .content, ...
    def __init__(self, **kw):
        self.__dict__.update(kw)


LANGCHAIN_OBJECTS = [_Msg(type="human", content=QUESTION),
                     _Msg(type="ai", content="", tool_calls=[{"name": "convert_currency", "args": ARGS, "id": "c"}]),
                     _Msg(type="tool", content=json.dumps(RESULT), tool_call_id="c", status="success"),
                     _Msg(type="ai", content=ANSWER, tool_calls=[])]


@pytest.mark.parametrize("chat", [OPENAI, ANTHROPIC, LANGCHAIN_DICTS, LANGCHAIN_OBJECTS],
                         ids=["openai", "anthropic", "langchain dicts", "langchain objects"])
def test_same_report_in_every_format(chat):
    r = check_messages(chat)
    assert [f.message for f in r.findings] == WANT
    assert r.stats["tool_calls"] == 1


def test_anthropic_tool_results_do_not_start_a_new_question():
    from traceground.traces import load_trace
    question, calls, answer = load_trace(ANTHROPIC)
    assert (question, answer, calls[0].result) == (QUESTION, ANSWER, RESULT)


def test_failed_calls_in_each_format():
    args = dict(ARGS, amount=250)
    anth = [ANTHROPIC[0], {"role": "assistant", "content": [{"type": "tool_use", "id": "t", "name": "convert_currency",
                                                             "input": args}]},
            {"role": "user", "content": [{"type": "tool_result", "tool_use_id": "t", "content": "service unavailable",
                                          "is_error": True}]},
            {"role": "assistant", "content": [{"type": "text", "text": "250 euros is about 40,983 yen."}]}]
    lc = [_Msg(type="human", content=QUESTION),
          _Msg(type="ai", content="", tool_calls=[{"name": "convert_currency", "args": args, "id": "c"}]),
          _Msg(type="tool", content="service unavailable", tool_call_id="c", status="error"),
          _Msg(type="ai", content="250 euros is about 40,983 yen.", tool_calls=[])]
    for chat in (anth, lc):
        assert "failed-call" in [f.check for f in check_messages(chat).findings]


def test_not_a_chat():
    with pytest.raises(TypeError):
        check_messages([_Msg(type="banana", content="x")])


def test_real_langchain_objects():
    m = pytest.importorskip("langchain_core.messages")
    chat = [m.HumanMessage(QUESTION),
            m.AIMessage("", tool_calls=[{"name": "convert_currency", "args": ARGS, "id": "call_1"}]),
            m.ToolMessage(json.dumps(RESULT), tool_call_id="call_1"), m.AIMessage(ANSWER)]
    assert [f.message for f in check_messages(chat).findings] == WANT
    assert [f.message for f in check_messages(m.messages_to_dict(chat)).findings] == WANT
