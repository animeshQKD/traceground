"""The demo's logic, without Gradio: parse what the person typed, run traceground, and shape the result for
the screen (HTML for the verdict, the marked answer and the findings; Python code; report files). app.py
only lays out the page. Tested by test_demo_logic.py."""
import html
import json
import os
import pprint
import re
import shutil
import tempfile
import time

from traceground import __version__, check_answer, check_messages
from traceground import numbers as _numbers
from traceground import quotes as _quotes
from traceground import textnorm as _textnorm
from traceground import traces as _traces

# finding check -> label; the labels use the words of the report's summary line
LABELS = {
    "number": "number not supported",
    "quote": "quote not found",
    "value-to-field": "value attached to the wrong field",
    "argument": "tool argument different from the question",
    "failed-call": "failed call reported as if it had worked",
    "tool-not-called": "claim about a tool that was not called",
    "self-talk": "model thinking aloud",
    "self-contradiction": "self-contradiction",
}
WRONG_SOURCE = "quote in another source than the one cited"
MINOR = "minor"
COLORS = {label: color for label, color in zip(
    list(LABELS.values()) + [WRONG_SOURCE, MINOR],
    ["#f87171", "#fb923c", "#facc15", "#a78bfa", "#f472b6", "#60a5fa", "#94a3b8", "#2dd4bf", "#fdba74", "#9ca3af"])}


def label_of(f) -> str:
    """The label of a finding, as shown on the page."""
    if f.severity != "high":
        return MINOR
    if f.check == "quote" and "which this sentence cites" in f.message:
        return WRONG_SOURCE
    return LABELS.get(f.check, f.check)


_ID_LINE = re.compile(r"^\s*\[([^\]\n]{1,40})\]\s*", re.M)


def parse_sources(text: str) -> dict:
    """Sources as typed in the box: blocks that start with "[S1]" (any id in brackets), or blocks separated
    by a line "---", or one block. Returns {id: text}."""
    text = (text or "").strip()
    if not text:
        return {}
    marks = list(_ID_LINE.finditer(text))
    if marks and marks[0].start() == 0:
        out = {}
        for m, nxt in zip(marks, marks[1:] + [None]):
            sid = m.group(1).strip()
            if sid in out:
                raise ValueError(f"two sources have the id [{sid}]")
            out[sid] = text[m.end(): nxt.start() if nxt else len(text)].strip()
        return out
    blocks = [b.strip() for b in re.split(r"^\s*---+\s*$", text, flags=re.M) if b.strip()]
    return {f"S{i}": b for i, b in enumerate(blocks, 1)}


def parse_trace(text: str):
    """The trace box: a JSON list of calls ({"name", "args", "result"}) or of chat messages ({"role", ...}).
    Returns ("calls" or "chat", the list)."""
    text = (text or "").strip()
    if not text:
        return "calls", []
    try:
        data = json.loads(text)
    except ValueError as e:
        raise ValueError(f"the trace is not valid JSON: {e}") from None
    if isinstance(data, dict):
        data = data.get("messages") or data.get("calls") or [data]
    if not isinstance(data, list):
        raise ValueError("the trace must be a JSON list of tool calls or of chat messages")
    if data and all(isinstance(m, dict) and "role" in m for m in data):
        return "chat", data
    return "calls", data


_BEFORE = "$€£₹¥\"“‘'"
_AFTER = "\"”’'%"


def marked_spans(answer: str, findings: list) -> list:
    """[(start, end, label, finding number)] of the findings on the answer, in order, without overlaps. A
    currency sign or an opening quote mark just before a finding, and a closing quote mark just after it,
    are marked with it. Where findings overlap, the first (in answer order) wins."""
    spans, last = [], 0
    order = sorted(range(len(findings)), key=lambda i: (findings[i].start, -(findings[i].end - findings[i].start)))
    for i in order:
        f = findings[i]
        a, b = f.start, f.end
        if a < last or b <= a:
            continue
        while a > last and answer[a - 1] in _BEFORE:
            a -= 1
        while b < len(answer) and answer[b] in _AFTER:
            b += 1
        tail = re.match(r":\d\d\b", answer[b:]) if answer[b - 1:b].isdigit() else None
        if tail:                             # "16" of "16:00": mark the whole time, number after it
            b += tail.end()
        spans.append((a, b, label_of(f), i + 1))
        last = b
    return spans


def highlight(answer: str, findings: list) -> list:
    """[(text, label or None)] covering the whole answer (the marked answer as plain pieces)."""
    out, pos = [], 0
    for a, b, label, _n in marked_spans(answer, findings):
        if a > pos:
            out.append((answer[pos:a], None))
        out.append((answer[a:b], label))
        pos = b
    if pos < len(answer):
        out.append((answer[pos:], None))
    return out


def coverage(answer: str, findings: list, check_small_integers: bool = False, check_quotes: bool = True) -> list:
    """[(start, end, checked)] for each sentence of the answer: checked when it has a number or a quote that
    traceground compares with the evidence, or a finding. Claims in words are not checked."""
    points = [n.start for n in _numbers.answer_numbers(answer, check_small_integers)[0]]
    if check_quotes:
        points += [a for a, _b, _t in _quotes.find_quotes(answer)]
    points += [f.start for f in findings]
    out = []
    for a, b in _textnorm.sentence_spans(answer):
        out.append((a, b, any(a <= p < b for p in points)))
    return out


def table(findings: list) -> list:
    """Rows of the findings, as in the report: #, problem, severity, text, why, suggested fix."""
    return [[i, label_of(f), "high" if f.severity == "high" else "minor", f.text, f.message, f.suggestion or ""]
            for i, f in enumerate(findings, 1)]


HEADERS = ["#", "Problem", "Severity", "Text", "Why", "Suggested fix"]

# ------------------------------------------------------------------ HTML for the page
_E = html.escape
_VERDICT = {"ok": ("ok", "✅ Nothing in the answer contradicts the evidence"),
            "problems": ("problems", "❌ Problems found"),
            "unsure": ("unsure", "❔ Unsure: there is no evidence to check against")}
PLACEHOLDER = ('<div class="tg-banner tg-idle">Paste an answer with its sources or tool calls and click '
               '<b>Check</b>, or pick an example below.</div>')


def banner(verdict: str, summary: str) -> str:
    cls, head = _VERDICT[verdict]
    return f'<div class="tg-banner tg-{cls}"><div class="tg-head">{_E(head)}</div><div>{_E(summary)}</div></div>'


def error_banner(message: str) -> str:
    return f'<div class="tg-banner tg-error"><div class="tg-head">⚠️ Cannot check this</div><div>{_E(message)}</div></div>'


def answer_html(answer: str, findings: list, cover: list) -> str:
    """The answer with each finding marked (and numbered like the list of findings), the sentences with
    nothing to check in grey, and a legend of the kinds that occur."""
    spans = marked_spans(answer, findings)
    unchecked = [(a, b) for a, b, ok in cover if not ok]
    cuts = sorted({0, len(answer)} | {p for a, b, _l, _n in spans for p in (a, b)} | {p for a, b in unchecked for p in (a, b)})
    parts = []
    for a, b in zip(cuts, cuts[1:]):
        piece = _E(answer[a:b]).replace("**", "").replace("\n", "<br>")      # Markdown bold marks hidden
        span = next((s for s in spans if s[0] <= a and b <= s[1]), None)
        if span:
            color = COLORS.get(span[2], "#9ca3af")
            piece = (f'<span class="tg-mark" style="background:{color}40;border-bottom:2px solid {color}" '
                     f'title="{_E(span[2])}">{piece}</span>')
            if b == span[1]:
                piece += f'<sup class="tg-num">{span[3]}</sup>'
        elif any(x <= a and b <= y for x, y in unchecked):
            piece = f'<span class="tg-unchecked">{piece}</span>'
        parts.append(piece)
    kinds = list(dict.fromkeys(s[2] for s in spans))
    legend = "".join(f'<span class="tg-key"><span class="tg-swatch" style="background:{COLORS.get(k, "#9ca3af")}"></span>'
                     f'{_E(k)}</span>' for k in kinds)
    n_all, n_un = len(cover), len(unchecked)
    if n_un:
        legend += '<span class="tg-key"><span class="tg-unchecked">grey</span>: nothing in it was checked</span>'
        n_ok = n_all - n_un
        note = (f'{n_ok} of {n_all} sentences {"has" if n_ok == 1 else "have"} numbers or quotes that were compared '
                f'with the evidence (or a finding). '
                + ('The other one, in grey, has' if n_un == 1 else f'The other {n_un}, in grey, have')
                + ' nothing traceground checks: claims made in words are not checked (nor whole numbers from 0 to '
                  '10, unless the box is ticked), so a ✅ says nothing about '
                + ('it.' if n_un == 1 else 'them.'))
    else:
        note = (f"Every sentence ({n_all}) has numbers or quotes that were compared with the evidence (or a "
                f"finding)." if n_all else "")
    return (f'<div class="tg-box"><div class="tg-title">The answer, with each finding marked</div>'
            f'<div class="tg-answer">{"".join(parts)}</div>'
            + (f'<div class="tg-legend">{legend}</div>' if legend else "")
            + (f'<div class="tg-note">{_E(note)}</div>' if note else "") + "</div>")


def evidence_texts(sources: dict, calls: list, question: str) -> dict:
    """{id: full text} of everything a finding can point to: the sources, each tool call, the question."""
    out = dict(sources)
    out.update({c.id: c.render() for c in calls})
    if question:
        out["question"] = question
    return out


def _excerpt(text: str, a: int, b: int, width: int = 180) -> str:
    """The text around [a, b) with that part marked, as HTML."""
    lo, hi = max(0, a - width), min(len(text), b + width)
    if lo:                                   # start and end at a space, not inside a word
        lo = text.find(" ", lo, a) + 1 or lo
    if hi < len(text):
        hi = text.rfind(" ", b, hi) if text.rfind(" ", b, hi) > b else hi
    return ("…" if lo else "") + _E(text[lo:a]) + f"<mark>{_E(text[a:b])}</mark>" + _E(text[b:hi]) + ("…" if hi < len(text) else "")


def _locate(text: str, value: str, message: str):
    """Where in `text` the evidence value is: (start, end) or None."""
    if value:
        i = text.lower().find(value.lower())
        if i >= 0:
            return i, i + len(value)
        m = re.match(r"(?:.*\.)?([^.=\[\]]+?)(?:\[\d+\])*\s*=\s*(.+)$", value)     # "rebounds = 11", "a.b[0].c = 4"
        if m:
            key = re.search(r'"%s"\s*:\s*[^,}\]]+' % re.escape(m.group(1).strip()), text)
            if key:
                return key.start(), key.end()
        words = re.escape(value).replace(r"\ ", r"\s+")
        m = re.search(words, text, re.I)
        if m:
            return m.start(), m.end()
    for arg in re.findall(r"\b(\w+=[^\s,)]+)", message):            # "called with years=3"
        i = text.find(arg.rstrip("."))
        if i >= 0:
            return i, i + len(arg.rstrip("."))
    return None


def evidence_html(f, texts: dict) -> str:
    """What the evidence says for one finding: each source or call it names, with the value marked."""
    items = []
    for ev in f.evidence or []:
        sid, value = ev.get("source", ""), ev.get("value", "")
        text = texts.get(sid) or ev.get("context") or ""
        if not text:
            continue
        where = _locate(text, value, f.message)
        body = _excerpt(text, *where) if where else _E(text[:400]) + ("…" if len(text) > 400 else "")
        items.append(f'<div class="tg-ev"><div class="tg-evsrc">{_E(sid)}</div><div>{body}</div></div>')
    if not items:
        return ""
    return f'<details class="tg-details"><summary>Show the evidence</summary>{"".join(items)}</details>'


def findings_html(findings: list, texts: dict) -> str:
    if not findings:
        return ""
    cards = []
    for i, f in enumerate(findings, 1):
        label = label_of(f)
        color = COLORS.get(label, "#9ca3af")
        sev = "high" if f.severity == "high" else "minor"
        fix = f'<div class="tg-fix">Suggested fix: <code>{_E(f.suggestion)}</code></div>' if f.suggestion else ""
        cards.append(
            f'<div class="tg-card" style="border-left:4px solid {color}">'
            f'<div class="tg-cardhead"><span class="tg-n">{i}</span><b>{_E(label)}</b>'
            f'<span class="tg-sev tg-sev-{sev}">{sev}</span></div>'
            f'<div class="tg-text">“{_E(f.text)}”</div><div class="tg-why">{_E(f.message)}</div>{fix}'
            f'{evidence_html(f, texts)}</div>')
    return f'<div class="tg-title">Findings ({len(findings)})</div>' + "".join(cards)


# ------------------------------------------------------------------ code and report files
def _py(value, indent: int = 0) -> str:
    """A Python literal for `value`: short containers on one line, longer ones one item per line."""
    flat = repr(value)
    if not isinstance(value, (dict, list, tuple)) or len(flat) + indent <= 96:
        return flat
    pad, inner = " " * indent, " " * (indent + 4)
    if isinstance(value, dict):
        items = [f"{inner}{k!r}: {_py(v, indent + 4)}," for k, v in value.items()]
        return "{\n" + "\n".join(items) + f"\n{pad}}}"
    items = [f"{inner}{_py(v, indent + 4)}," for v in value]
    return "[\n" + "\n".join(items) + f"\n{pad}]"


def code_for(kind: str, answer: str, question: str, sources: dict, trace: list, options: dict) -> str:
    """Python code that runs the same check as the page did."""
    args = []
    lines = []
    if kind == "chat":
        lines += ["from traceground import check_messages", "", f"messages = {_py(trace)}"]
        args.append("messages")
    else:
        lines += ["from traceground import check_answer", "", f"answer = {_py(answer)}"]
        args.append("answer")
    if sources:
        lines.append(f"sources = {_py(sources)}")
        args.append("sources=sources")
    if kind != "chat" and question:
        lines.append(f"question = {_py(question)}")
        args.append("question=question")
    if kind != "chat" and trace:
        lines.append(f"trace = {_py(trace)}")
        args.append("trace=trace")
    if options.get("check_small_integers"):
        args.append("check_small_integers=True")
    if not options.get("check_quotes", True):
        args.append("check_quotes=False")
    fn = "check_messages" if kind == "chat" else "check_answer"
    lines += ["", f"result = {fn}({', '.join(args)})", "print(result.to_text())"]
    return "\n".join(lines) + "\n"


REPORTS = os.path.join(tempfile.gettempdir(), "traceground_reports")
KEEP_SECONDS = 3600


def _clean_reports(now: float = None) -> None:
    """Delete report folders older than an hour, so a long-running page does not fill its disk."""
    now = now or time.time()
    try:
        for name in os.listdir(REPORTS):
            path = os.path.join(REPORTS, name)
            if os.path.isdir(path) and now - os.path.getmtime(path) > KEEP_SECONDS:
                shutil.rmtree(path, ignore_errors=True)
    except OSError:
        pass


def report_files(result, folder: str = None) -> list:
    """Write the report as JSON and as Markdown; returns the two paths. Without a folder, a new one is made
    under REPORTS, and folders there older than an hour are deleted."""
    if folder is None:
        os.makedirs(REPORTS, exist_ok=True)
        _clean_reports()
        folder = tempfile.mkdtemp(prefix="report_", dir=REPORTS)
    js = os.path.join(folder, "traceground_report.json")
    md = os.path.join(folder, "traceground_report.md")
    with open(js, "w", encoding="utf-8") as f:
        json.dump(dict(result.to_dict(), version=__version__), f, indent=1, ensure_ascii=False)
    lines = [f"# traceground report ({__version__})", "", f"**{result.verdict.upper()}**: {result.summary}", ""]
    for i, x in enumerate(result.findings, 1):
        lines += [f"{i}. **{label_of(x)}** ({'high' if x.severity == 'high' else 'minor'}): \"{x.text}\"",
                  f"   * in: {x.sentence}", f"   * {x.message}"]
        if x.suggestion:
            lines.append(f"   * suggested fix: {x.suggestion}")
    with open(md, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    return [js, md]


def traceground_check(answer: str = "", sources: str = "", tool_calls: str = "", question: str = "",
                      check_small_whole_numbers: bool = False, check_quotes: bool = True) -> str:
    """Check an AI answer against the evidence it was given (documents, tool calls, or both) and list every number, quote, value or tool argument that the evidence does not support. Deterministic, no language model.

    Args:
        answer: The answer to check. Leave it empty when tool_calls holds a whole chat: then the chat's last answer is checked.
        sources: The documents the answer was written from, as blocks that start with an id in brackets ("[S1] ... [S2] ..."), as blocks separated by a line "---", or as a JSON object {"S1": "...", "S2": "..."}.
        tool_calls: The tool calls as a JSON list [{"name": ..., "args": {...}, "result": ...}], or a whole chat as a JSON list of messages (OpenAI, Anthropic or LangChain format).
        question: The question the answer replies to. Numbers in it count as evidence.
        check_small_whole_numbers: Also check whole numbers from 0 to 10, which are skipped by default.
        check_quotes: Check quotations against the sources (true by default).

    Returns:
        The report as JSON: verdict ("ok", "problems" or "unsure"), summary, findings (each with check, severity, text, sentence, message and evidence), stats, and the same report as plain text; or {"error": ...} when the input cannot be read.
    """
    try:
        src = (sources or "").strip()
        if src.startswith("{"):
            try:
                data = json.loads(src)
            except ValueError as e:
                raise ValueError(f"the sources are not valid JSON: {e}") from None
            src = "\n".join(f"[{k}] {v}" for k, v in data.items())
        r = run(answer, question, src, tool_calls, check_small_integers=check_small_whole_numbers,
                check_quotes=check_quotes)
    except (ValueError, TypeError, AttributeError) as e:
        return json.dumps({"error": str(e)})
    if not r["ok"]:
        msg = html.unescape(re.sub(r"<[^>]+>", " ", r["banner"]).split("Cannot check this", 1)[-1]).strip()
        return json.dumps({"error": msg}, ensure_ascii=False)
    out = dict(r["json"])
    out["report"] = r["text"]
    out["version"] = __version__
    return json.dumps(out, ensure_ascii=False)


def run(answer: str, question: str, sources_text: str, trace_text: str, check_small_integers: bool = False,
        check_quotes: bool = True, files: bool = False) -> dict:
    """Check what was typed. Returns {"ok", "banner", "answer_html", "findings_html", "highlight", "rows",
    "json", "code", "files"}; when the input cannot be read, "ok" is False and "banner" says why."""
    try:
        sources = parse_sources(sources_text)
        kind, trace = parse_trace(trace_text)
        options = dict(check_small_integers=bool(check_small_integers), check_quotes=bool(check_quotes))
        if kind == "chat":
            msgs = list(trace)
            if (answer or "").strip():          # an answer typed in the box replaces the chat's last answer
                msgs.append({"role": "assistant", "content": answer})
            if (question or "").strip() and not any(m.get("role") == "user" for m in msgs):
                msgs.insert(0, {"role": "user", "content": question})
            result = check_messages(msgs, sources or None, **options)
            question, calls, answer = _traces.load_trace(msgs)
            code = code_for("chat", answer, question, sources, msgs, options)
        else:
            if not (answer or "").strip():
                raise ValueError("type or paste the answer to check")
            result = check_answer(answer, sources or None, question or "", trace or None, **options)
            calls = _traces.calls_from_list(trace) if trace else []
            code = code_for("calls", answer, question or "", sources, trace, options)
        _traces.name_calls(calls)
    except (ValueError, TypeError, KeyError) as e:
        return {"ok": False, "banner": error_banner(str(e)), "answer_html": "", "findings_html": "",
                "highlight": [], "rows": [], "json": {}, "code": "", "files": []}
    texts = evidence_texts(sources, calls, question or "")
    cover = coverage(answer, result.findings, check_small_integers, check_quotes)
    return {"ok": True, "banner": banner(result.verdict, result.summary),
            "answer_html": answer_html(answer, result.findings, cover),
            "findings_html": findings_html(result.findings, texts),
            "highlight": highlight(answer, result.findings), "rows": table(result.findings),
            "json": result.to_dict(), "text": result.to_text(), "code": code,
            "files": report_files(result) if files else [],
            "coverage": cover}


# ------------------------------------------------------------------ examples (made up, to show each check)
SOURCE_EXAMPLES = [
    {"title": "A wrong number and a changed quote",
     "question": "What did the council decide about the new library?",
     "sources": "[S1] The city council approved a budget of 4.2 million euros for the new library, which will "
                "open in March 2027 with 120,000 books.\n"
                "[S2] Council member Rao said the library \"will be open seven days a week, from early morning "
                "until late evening\".",
     "answer": "The council approved 4.8 million euros for the library [S1], which opens in March 2027 with "
               "120,000 books. Rao said it \"will be open every day of the week\" [S2]."},
    {"title": "A correct answer",
     "question": "What did the council decide about the new library?",
     "sources": "[S1] The city council approved a budget of 4.2 million euros for the new library, which will "
                "open in March 2027 with 120,000 books.",
     "answer": "The council approved about €4.2 million for the library, which opens in March 2027 with "
               "120,000 books [S1]."},
    {"title": "Says the sources are silent, then answers anyway",
     "question": "When does the library open?",
     "sources": "[S1] The library will open in March 2027 with 120,000 books.",
     "answer": "The sources do not say when the new library will open. The new library will open in March "
               "2027 [S1]."},
]

_GAME = [{"name": "player_game_stats", "args": {"player": "Jordan Reyes", "date": "2026-11-16"},
          "result": {"points": 27, "rebounds": 11, "assists": 7, "minutes": 34}}]
_LOAN_CHAT = [
    {"role": "user", "content": "What is the 5-year cost at 7% interest on a 12,000 loan?"},
    {"role": "assistant", "content": None, "tool_calls": [{"id": "call_1", "type": "function", "function": {
        "name": "loan_cost", "arguments": json.dumps({"principal": 12000, "annual_rate": 0.07, "years": 3})}}]},
    {"role": "tool", "tool_call_id": "call_1",
     "content": json.dumps({"monthly_payment": 370.52, "total_paid": 13338.72, "total_interest": 1338.72})},
    {"role": "assistant", "content": "Over 5 years at 7% you pay 13,338.72 in total, 370.52 a month."}]
_WEATHER_FAIL = [{"name": "get_weather", "args": {"city": "Reykjavik"},
                  "result": "Error: weather service timed out"}]

_LIBRARY_BUDGET = [{"name": "get_library_budget", "args": {"city": "Pune"},
                    "result": {"budget_meur": 4.2, "books": 120000, "opening": "March 2027"}}]

BOTH_EXAMPLES = [
    {"title": "Documents and a tool together",
     "question": "What is the library's budget, and what did Rao say about it?",
     "sources": "[S1] Council member Rao said the library \"will be open seven days a week, from early morning "
                "until late evening\".",
     "trace": json.dumps(_LIBRARY_BUDGET, indent=1),
     "answer": "The library's budget is 4.8 million euros for 120,000 books, and Rao said it \"will be open "
               "seven days a week\" [S1]."},
]

TRACE_EXAMPLES = [
    {"title": "Two values swapped between fields", "question": "How did Jordan Reyes play on 2026-11-16?",
     "trace": json.dumps(_GAME, indent=1),
     "answer": "Jordan Reyes scored 27 points with 7 rebounds and 11 assists in 34 minutes."},
    {"title": "Tool called with other values than asked (a chat)", "question": "",
     "trace": json.dumps(_LOAN_CHAT, indent=1), "answer": ""},
    {"title": "A failed call reported as if it had worked", "question": "What's tomorrow's weather in Reykjavik?",
     "trace": json.dumps(_WEATHER_FAIL, indent=1),
     "answer": "Tomorrow in Reykjavik expect a high of 4 °C with light snow and winds of 30 km/h."},
    {"title": "A web search that never happened", "question": "Is the MX-200 still under warranty after 3 years?",
     "trace": json.dumps([{"name": "get_product", "args": {"sku": "MX-200"}, "result": {"warranty_years": 2}}],
                         indent=1),
     "answer": "I searched the web and found that the MX-200 has a 2-year warranty, so after 3 years it is "
               "no longer covered."},
]

def _load_real(path: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "real_examples.json")) -> tuple:
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    return data["about"], [{"title": e["title"], "model": e["model"], "question": "", "sources": "", "answer": "",
                            "trace": json.dumps(e["messages"], indent=1, ensure_ascii=False)} for e in data["examples"]]


# real chats from the evaluation (real_examples.json): unedited, checked as they are
REAL_ABOUT, REAL_EXAMPLES = _load_real()

ON_SPACE = bool(os.environ.get("SPACE_ID"))        # set by Hugging Face Spaces
WHERE = ("On this online demo, what you paste is checked on the Hugging Face server that runs the page; no "
         "language model or API sees it, and the report files for the download buttons are deleted after an "
         "hour. To keep everything on your own computer, run the page locally (see the GitHub repository)."
         if ON_SPACE else "Nothing you paste leaves this computer.")
WHERE_SHORT = ("What you paste is checked on this Space's server, not sent to any model."
               if ON_SPACE else "Nothing you paste leaves this computer.")

ABOUT = f"""**traceground {__version__}** lists every number, quote, value or tool argument in an AI answer
that its sources or tool calls do not support. It uses no language model: the same input always gives the
same report, in milliseconds. {WHERE}

It checks: numbers (at the precision they are written in), quotes, values attached to the wrong field of a
tool result, tool calls made with other values than the question asked, failed calls reported as success,
tools the answer says it used but never called, and the model thinking aloud or contradicting itself.

It does not judge reasoning: "ACME moved more because it traded more shares" passes when every number is
right. And it needs the evidence: without sources or tool calls it can only say "unsure"."""

HOW_TO = """**How to use this page.** Fill in what you have; every box but the answer is optional.

* **Sources**: the documents the AI answered from (retrieved passages, a report). Give each an id such as
  [S1]; the answer cites them the same way.
* **Tool calls**: what the AI called and what came back, as JSON. Agent frameworks and model APIs keep this
  list anyway. A whole chat works too, in OpenAI, Anthropic or LangChain format; then the question and the
  answer are read from the chat.
* **Both**: an agent that reads documents and calls tools; each number and quote is checked against all of it.
* **Small whole numbers** (0 to 10) are skipped unless you tick the box: "2 options" or "step 3" are everywhere.

**Reading the result.** ✅ nothing contradicts the evidence; ❌ at least one serious problem; ❔ numbers but
no evidence to check them against. On the answer, each finding is marked and numbered; sentences in grey have
nothing traceground checks (claims in words, small whole numbers), so a ✅ says nothing about them. Each finding below says why it was reported; "Show the
evidence" opens the source or tool result with the value it has marked. "Use this check in your code" gives
the Python that produces the same report, and the report can be downloaded as JSON or Markdown."""
