"""Checks of what the answer says about the tool calls themselves.

failed-call       A call failed, was not called again successfully (nor replaced by another tool called
                  about the same thing, e.g. the same city), and the answer reads as if it had worked: it
                  does not mention the failure, and it speaks of what the failed call was about (its
                  argument values, e.g. "Oslo").
tool-not-called   The answer claims an action no call matches: "I searched the web" with no search
                  tool, "I ran the code" with no code tool, "I queried the database" with no database
                  tool, "I used the X tool" with no tool X. Offers ("I can search the web") and advice
                  ("you can search online") are not claims.
"""
import re

from traceground.result import Finding

_ACKNOWLEDGED = re.compile(r"\b(?:fail\w*|error\w*|unable|could\s*n[o']t|couldn['’]t|cannot|can['’]t|unavailable|not\s+available|"
                           r"timed?\s*out|time-?out|try\s+again|did\s*n[o']t\s+work|didn['’]t\s+work|no\s+data|not\s+possible|"
                           r"went\s+wrong|problem\s+(?:with|reaching|getting)|issue\s+(?:with|reaching|getting))", re.I)

_CLAIMS = [
    ("a web search",
     re.compile(r"\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+|also\s+)?(?:searched|looked\s+(?:it\s+|this\s+|that\s+)?up|checked|browsed)"
                r"\s+(?:on\s+)?(?:the\s+)?(?:web|internet|online|google|bing)\b"
                r"|\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+)?googled\b"
                r"|\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+)?(?:did|ran|performed|conducted)\s+an?\s+(?:quick\s+)?(?:web|online|internet|google)\s+search\b"
                r"|\baccording\s+to\s+(?:my|our|a)\s+(?:quick\s+)?(?:web|online|internet|google)\s+search\b", re.I),
     ("search", "web", "browse", "browser", "google", "bing", "internet", "serp", "tavily", "duckduckgo", "ddg", "exa",
      "brave", "perplexity", "fetch", "url", "http", "crawl", "scrape")),
    ("running code",
     re.compile(r"\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+)?(?:ran|executed|tested|run)\s+(?:the\s+|this\s+|your\s+|a\s+|some\s+)?"
                r"(?:python\s+)?(?:code|script|program|snippet|notebook)\b", re.I),
     ("python", "code", "exec", "execute", "run", "interpreter", "sandbox", "shell", "bash", "repl", "jupyter", "notebook")),
    ("a database query",
     re.compile(r"\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+)?(?:queried|checked|searched|looked\s+(?:it\s+)?up\s+in)\s+"
                r"(?:the\s+|your\s+|our\s+)?(?:database|db|crm|inventory\s+system)\b", re.I),
     ("db", "database", "sql", "query", "crm", "inventory", "lookup", "records")),
]
_NAMED = re.compile(r"\b(?:I|we)\s+(?:have\s+|['’]ve\s+|just\s+)?(?:called|used|ran|invoked|run)\s+(?:the\s+)?`?(?P<tool>[A-Za-z_][\w.\-]*)`?\s+tool\b", re.I)


def _tokens(name: str) -> set:
    return {t for t in re.split(r"[^a-z0-9]+", re.sub(r"([a-z])([A-Z])", r"\1_\2", name).lower()) if t}


def _topic(call) -> set:
    """What a call was about: its string argument words (3+ letters) and its numeric arguments."""
    out = set()

    def walk(v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            out.add(str(v))
        elif isinstance(v, str):
            out.update(w.casefold() for w in re.findall(r"[^\W\d_]{3,}", v))
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(call.args)
    return out


def _render_words(call) -> set:
    return {w.casefold() for w in re.findall(r"[^\W\d_]{3,}|\d+(?:\.\d+)?", call.render())}


def check_failed_calls(answer: str, calls: list, *, sentence_spans=(), sentence_of=None) -> tuple:
    findings = []
    if _ACKNOWLEDGED.search(answer):
        return findings, {"tool_calls_failed_unreported": 0}
    answer_words = {w.casefold() for w in re.findall(r"[^\W\d_]{3,}|\d+(?:\.\d+)?", answer)}
    for k, c in enumerate(calls):
        if not c.error:
            continue
        later_ok = [d for d in calls[k + 1:] if not d.error]
        if any(d.name == c.name for d in later_ok):
            continue                                          # called again and it worked
        if any(_topic(d) & _topic(c) for d in calls if not d.error and d is not c):
            continue                                          # another tool did the same job ("Oslo" either way)
        covered = set().union(*(_render_words(d) for d in calls if not d.error)) if later_ok or any(
            not d.error for d in calls) else set()
        about = (_topic(c) & answer_words) - covered
        if not about and (c.args or any(not d.error for d in calls)):
            continue                                          # the answer is about something a working call gave
        spans = list(sentence_spans) or [(0, len(answer))]
        a, b = next(((x, y) for x, y in spans if any(w in answer[x:y].casefold() for w in about)), spans[0])
        what = c.result if isinstance(c.result, str) else str(c.result)
        call_txt = c.render().split(" failed:")[0]
        findings.append(Finding(
            check="failed-call", severity="high", start=a, end=b, text=answer[a:b],
            sentence=sentence_of(a) if sentence_of else answer[a:b],
            message=(f"{call_txt} failed (\"{what[:120]}\") and was not called again successfully, but the answer "
                     f"reads as if it had worked."),
            evidence=[{"source": c.id, "value": what[:200], "context": c.render()}]))
    return findings, {"tool_calls_failed_unreported": len(findings)}


def check_tools_not_called(answer: str, calls: list, *, sentence_of=None) -> tuple:
    findings = []
    names = [c.name for c in calls]
    name_tokens = set().union(*(_tokens(n) for n in names)) if names else set()
    called = ", ".join(dict.fromkeys(names)) if names else "no tool was called"

    def add(m, what):
        a, b = m.start(), m.end()
        findings.append(Finding(
            check="tool-not-called", severity="high", start=a, end=b, text=answer[a:b],
            sentence=sentence_of(a) if sentence_of else answer,
            message=f"The answer says \"{answer[a:b]}\", but no tool for {what} was called "
                    f"({'calls: ' + called if names else called}).",
            evidence=[]))

    for what, rx, tokens in _CLAIMS:
        if name_tokens & set(tokens):
            continue
        for m in rx.finditer(answer):
            add(m, what)
    for m in _NAMED.finditer(answer):
        tool = m.group("tool")
        norm = re.sub(r"[\s\-.]+", "_", tool.casefold())
        if norm in {n.casefold() for n in names} or _tokens(tool) <= name_tokens:
            continue
        if any(rx.search(m.group(0)) for _w, rx, _t in _CLAIMS):
            continue
        add(m, f"\"{tool}\"")
    findings.sort(key=lambda f: f.start)
    return findings, {"tool_claims_unbacked": len(findings)}
