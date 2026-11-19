"""Tool-call traces: read them, and turn them into evidence.

Accepted shapes (load_trace):
  * a list of calls: [{"name": ..., "args": {...}, "result": ...}, ...]; "arguments", "input" or
    "parameters" for args, "output", "content" or "observation" for result, and an optional
    "error": true are also read;
  * OpenAI-style chat messages: user, assistant (with "tool_calls"), tool (with "tool_call_id") and
    the final assistant answer; the older "function_call" / role "function" form too;
  * a dict with "messages", "calls" or "trace" holding either of the above.

A call failed when it says so ("error": true), when its result is a dict with a non-empty "error" or a
"status" of error/failed, or when its result text starts with Error, Exception, Traceback or Failed.
"""
import json
import re
from dataclasses import dataclass, field
from typing import Any

_ERROR_TEXT = re.compile(r"^\s*(?:error|exception|traceback|failed|failure)\b", re.I)
_ARG_KEYS = ("args", "arguments", "input", "parameters", "params")
_RESULT_KEYS = ("result", "output", "content", "observation", "response", "return")


@dataclass
class ToolCall:
    name: str
    args: dict = field(default_factory=dict)
    result: Any = None
    error: bool = False
    id: str = ""                 # how reports name it: the tool name, or "name (call 2)" when it repeats
    call_id: str = ""            # the id the trace gave it, if any

    def render(self) -> str:
        """One line of text: the call and what it returned (used as evidence for numbers and quotes)."""
        args = ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in self.args.items())
        res = self.result if isinstance(self.result, str) else json.dumps(self.result, ensure_ascii=False)
        return f"{self.name}({args}) {'failed: ' if self.error else 'returned '}{res}"


def _parse(value):
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (ValueError, TypeError):
            return value
    return value


def _text(content) -> str:
    if content is None:
        return ""
    if isinstance(content, str):
        return content
    if isinstance(content, list):                     # [{"type": "text", "text": ...}, ...]
        return "".join(p.get("text", "") if isinstance(p, dict) else str(p) for p in content)
    return str(content)


def is_error(result, explicit=None) -> bool:
    if explicit is not None:
        return bool(explicit)
    if isinstance(result, dict):
        if result.get("error") or result.get("errors"):
            return True
        return str(result.get("status", "")).lower() in ("error", "failed", "failure")
    return isinstance(result, str) and bool(_ERROR_TEXT.match(result))


def calls_from_list(items) -> list:
    calls = []
    for i, it in enumerate(items, 1):
        if not isinstance(it, dict):
            raise TypeError(f"trace item {i}: expected a dict, got {type(it).__name__}")
        name = it.get("name") or it.get("tool") or it.get("tool_name")
        if not name:
            raise ValueError(f"trace item {i} has no tool name")
        args = next((it[k] for k in _ARG_KEYS if k in it), {})
        args = _parse(args)
        if not isinstance(args, dict):
            args = {"input": args}
        result = _parse(next((it[k] for k in _RESULT_KEYS if k in it), None))
        explicit = it.get("error", it.get("is_error"))
        if isinstance(explicit, str):              # "error": "timed out" is a failure with a message
            result, explicit = (result if result is not None else explicit), True
        calls.append(ToolCall(name=str(name), args=args, result=result, error=is_error(result, explicit),
                              call_id=str(it.get("id", ""))))
    return calls


_LC_ROLES = {"human": "user", "ai": "assistant", "tool": "tool", "system": "system", "function": "function",
             "user": "user", "assistant": "assistant"}


def _lc_message(m) -> dict:
    """A LangChain message (an object with .type, or its dict from messages_to_dict) as an OpenAI-style dict."""
    if isinstance(m, dict):
        data = m.get("data") if isinstance(m.get("data"), dict) else m
        get = data.get
        kind = m.get("type") or get("type")
    else:
        def get(key, default=None):
            return getattr(m, key, default)
        kind = get("type")
    role = _LC_ROLES.get(str(kind))
    if role is None:
        raise TypeError(f"not a chat message: {type(m).__name__}")
    out = {"role": role, "content": get("content")}
    if role == "assistant":
        out["tool_calls"] = [{"id": str(tc.get("id") or ""), "type": "function",
                              "function": {"name": tc.get("name", ""), "arguments": tc.get("args", {})}}
                             for tc in (get("tool_calls") or [])]
    if role == "tool":
        out["tool_call_id"] = str(get("tool_call_id") or "")
        out["name"] = get("name")
        if get("status") == "error":
            out["is_error"] = True
    return out


def _anthropic_messages(m: dict) -> list:
    """An Anthropic Messages API message (content as blocks) as OpenAI-style dicts: tool_use blocks become
    tool calls, tool_result blocks become tool messages, text blocks stay text."""
    blocks = m.get("content")
    if not isinstance(blocks, list):
        return [m]
    texts = [b.get("text", "") for b in blocks if isinstance(b, dict) and b.get("type") == "text"]
    if m.get("role") == "assistant":
        uses = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_use"]
        return [{"role": "assistant", "content": "".join(texts),
                 "tool_calls": [{"id": str(b.get("id", "")), "type": "function",
                                 "function": {"name": b.get("name", ""), "arguments": b.get("input", {})}}
                                for b in uses]}]
    results = [b for b in blocks if isinstance(b, dict) and b.get("type") == "tool_result"]
    out = [{"role": "tool", "tool_call_id": str(b.get("tool_use_id", "")), "content": b.get("content"),
            **({"is_error": True} if b.get("is_error") else {})} for b in results]
    if texts or not results:
        out.append({"role": m.get("role"), "content": "".join(texts)})
    return out


def normalize_messages(messages) -> list:
    """OpenAI-style dicts from OpenAI, Anthropic (content blocks with tool_use and tool_result) or
    LangChain messages (objects, or dicts from messages_to_dict)."""
    out = []
    for m in messages:
        if isinstance(m, dict) and "role" in m:
            content = m.get("content")
            if isinstance(content, list) and any(isinstance(b, dict) and b.get("type") in ("tool_use", "tool_result")
                                                 for b in content):
                out += _anthropic_messages(m)
            else:
                out.append(m)
        else:
            out.append(_lc_message(m))
    return out


def is_chat(obj) -> bool:
    """True for a list of chat messages in any accepted format."""
    if not isinstance(obj, (list, tuple)) or not obj:
        return False
    first = obj[0]
    if isinstance(first, dict):
        return "role" in first or (str(first.get("type")) in _LC_ROLES and ("data" in first or "content" in first))
    return str(getattr(first, "type", "")) in _LC_ROLES and hasattr(first, "content")


def from_messages(messages) -> tuple:
    """(question, calls, answer) from chat messages (OpenAI, Anthropic or LangChain format). The question is
    the last user message before the final answer; the answer is the last assistant message that calls no
    tool."""
    calls, by_id, question, answer = [], {}, "", ""
    for m in normalize_messages(messages):
        if not isinstance(m, dict):
            raise TypeError(f"expected messages as dicts, got {type(m).__name__}")
        role = m.get("role")
        if role == "user":
            question, answer = _text(m.get("content")), ""
        elif role == "assistant":
            tcs = m.get("tool_calls") or []
            if m.get("function_call"):
                tcs = tcs + [{"id": "", "function": m["function_call"]}]
            for tc in tcs:
                fn = tc.get("function", tc)
                args = _parse(fn.get("arguments", {}))
                call = ToolCall(name=str(fn.get("name", "")), args=args if isinstance(args, dict) else {"input": args},
                                call_id=str(tc.get("id", "")))
                calls.append(call)
                if call.call_id:
                    by_id[call.call_id] = call
            if not tcs and _text(m.get("content")).strip():
                answer = _text(m.get("content"))
        elif role in ("tool", "function"):
            call = by_id.get(str(m.get("tool_call_id", "")))
            if call is None:                          # no id: the latest call of that name still waiting
                call = next((c for c in reversed(calls) if c.result is None
                             and (not m.get("name") or c.name == m.get("name"))), None)
            if call is not None:
                call.result = _parse(_text(m.get("content")))
                call.error = is_error(call.result, m.get("is_error"))
    return question, calls, answer


def load_trace(obj) -> tuple:
    """(question, calls, answer) from any accepted shape; question and answer are "" for a list of calls."""
    if isinstance(obj, dict):
        for key in ("messages", "calls", "trace"):
            if key in obj:
                q, calls, a = load_trace(obj[key])
                return obj.get("question", q) or q, calls, obj.get("answer", a) or a
        raise ValueError('a trace dict needs "messages", "calls" or "trace"')
    if not isinstance(obj, (list, tuple)):
        raise TypeError(f"a trace is a list or a dict, got {type(obj).__name__}")
    if is_chat(obj):
        return from_messages(obj)
    return "", calls_from_list(obj), ""


def name_calls(calls: list) -> list:
    """Give each call its report id: the tool name, or "name (call k)" when the name repeats."""
    count = {}
    for c in calls:
        count[c.name] = count.get(c.name, 0) + 1
    seen = {}
    for c in calls:
        seen[c.name] = seen.get(c.name, 0) + 1
        c.id = c.name if count[c.name] == 1 else f"{c.name} (call {seen[c.name]})"
    return calls


def numeric_fields(obj, path: str = "") -> list:
    """[(path, key, value)] of every number in a JSON value; numeric strings ("12.5") count."""
    out = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            out += numeric_fields(v, f"{path}.{k}" if path else str(k)) if isinstance(v, (dict, list)) else \
                _leaf(f"{path}.{k}" if path else str(k), str(k), v)
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            if isinstance(v, (dict, list)):
                out += numeric_fields(v, f"{path}[{i}]")
    return out


def _leaf(path, key, v) -> list:
    if isinstance(v, bool) or v is None:
        return []
    if isinstance(v, (int, float)):
        return [(path, key, float(v))]
    if isinstance(v, str) and re.fullmatch(r"\s*-?\d+(?:\.\d+)?\s*", v):
        return [(path, key, float(v))]
    return []
