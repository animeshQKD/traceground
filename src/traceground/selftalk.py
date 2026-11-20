"""Checks of the answer's own wording.

self-talk           The model thinking aloud or talking to a checker, left in the final answer:
                    "Wait, let me check:", "Hmm, ...", "Let me report the tool's numbers:", "These are the
                    actual computed values.", a paragraph that takes back what came before ("Let me
                    reconsider.", "I made a mistake"), "2.26 > 2.83? No - ...". Ported from the Quantum
                    Information Agent (graph.py), where these leaked from DeepSeek V4 Flash and
                    gpt-oss-120b. Ordinary openers ("Let me explain", "Let me summarize") are fine.
self-contradiction  The answer says the sources do not give something ("The passages do not say how long
                    the warranty lasts.") and another sentence then gives it from them: it shares most of
                    that sentence's topic words, and it cites a source or its words are a source's words.
                    Ported from "Ask Your Quantum Physics Research Papers" (checker.py).
"""
import re

from traceground import citations
from traceground.binding import stem
from traceground.result import Finding

_SELF_CHECK = re.compile(r"\b(?:wait|hmm+)\b\s*[,.!—–-]+\s*(?:let\s+me\s+(?:re-?)?check(?:\s+(?:this|that|again))?\s*[:,.]?\s*"
                         r"|(?=that['’]?s\s+(?:not|wrong)|this\s+is\s+(?:not|wrong)|actually\b|no\b|i\s+(?:made|was|need\s+to\s+(?:re)?check)))"
                         r"|\blet\s+me\s+(?:re-?)?check(?:\s+(?:this|that|again))?\s*:\s*"
                         r"|\blet\s+me\s+(?:recompute|re-?calculate|verify|be\s+precise|correct\s+(?:this|that))"
                         r"(?:\s+(?:the\s+)?(?:actual\s+|exact\s+|correct\s+)?(?:numbers|values|this|that))?(?:\s+again)?\s*:\s*", re.I)
_RESTATE = re.compile(r"\blet\s+me\s+(?:report|quote|restate|repeat|stick\s+to)\s+(?:only\s+)?(?:the\s+)?"
                      r"(?:tool['’]?s?\s+|computed\s+|actual\s+|exact\s+|correct\s+)*(?:numbers|values|results)\b\s*:?"
                      r"|\b(?:these|those)\s+are\s+the\s+(?:tool['’]?s?\s+)?(?:actual|exact|correct|real|true)\s+"
                      r"(?:computed\s+)?(?:numbers|values|results)\s*\.", re.I)
_RETRACTION = re.compile(r"(?m)^[ \t]*(?:\*\*)?(?:let\s+me\s+(?:reconsider|re-?think|re-?examine|re-?do|correct\s+(?:myself|this|that))\b"
                         r"|on\s+second\s+thought\b|correction\s*:"
                         r"|actually\s*,?\s+i\s+(?:made|was\s+wrong|misread|mis-?stated)\b"
                         r"|i\s+(?:made|have\s+made)\s+an?\s+(?:error|mistake)\b|i\s+misspoke\b|scratch\s+that\b)[^\n]*", re.I)
_ASKED_AND_DENIED = re.compile(r"[^?!:\n()]{0,30}[<>≤≥][^?!:\n()]{0,15}\?\s*No\s*[—–-]+\s*")

_TELL = (r"(?:say|state|mention|give|provide|discuss|explain|describe|contain|specify|address|cover|answer|define|include|"
         r"report|tell|show|offer|list|detail|indicate|identify|clarify|confirm|specif|quantify|reveal|note|record)\w*")
_NOUN = r"(?:passages?|papers?|sources?|documents?|docs|context|texts?|articles?|search\s+results|results|data|records|files?|manual|reports?)"
_NO_ANSWER = re.compile(rf"\b{_NOUN}\b[^.]{{0,60}}\b(?:do(?:es)?\s+not|don['’]t|doesn['’]t|never)\s+(?:\w+ly\s+)?{_TELL}\b"
                        rf"|\bnot\s+(?:\w+\s+)?(?:stated|given|found|mentioned|specified|provided|included|covered|listed)\b[^.]{{0,40}}\b{_NOUN}\b"
                        rf"|\b{_NOUN}\b[^.]{{0,40}}\bno\s+(?:information|mention|details?)\b", re.I)
_QUOTED = re.compile(r"[\"“][^\"“”\n]*[\"”]")
_STOP = {"the", "and", "for", "with", "that", "this", "these", "those", "from", "how", "what", "when", "where", "which",
         "who", "why", "does", "not", "say", "says", "state", "states", "mention", "give", "provide", "are", "was", "were",
         "has", "have", "had", "its", "their", "there", "they", "them", "any", "about", "into", "than", "then", "also",
         "only", "but", "your", "our", "can", "will", "would", "should", "could", "may", "might", "is", "be", "it",
         "don", "doesn", "didn", "isn", "aren", "wasn", "weren", "won", "dont", "doesnt", "didnt"}
# words about the sources, not the topic: "Based on the given passages, ..." shares no topic with a denial
_SOURCE_TALK = {stem(w) for w in ("given", "based", "provided", "mentioned", "stated", "according")}
_NOUN_WORDS = {"passage", "paper", "source", "document", "doc", "context", "text", "article", "search", "result", "data",
               "record", "file", "manual", "report", "information", "mention", "detail"}


_MESSAGES = {"think": "This is the model thinking aloud, left in the final answer",
             "checker": "These are words the model addressed to a checker, left in the final answer",
             "retract": "This is the model taking back what it wrote, left in the final answer"}


def check_self_talk(answer: str, *, sentence_of=None) -> tuple:
    findings, seen = [], []
    quoted = [(m.start(), m.end()) for m in _QUOTED.finditer(answer)]       # someone else's words: not self-talk
    for kind, rx in (("think", _SELF_CHECK), ("think", _ASKED_AND_DENIED),
                     ("checker", _RESTATE), ("retract", _RETRACTION)):
        for m in rx.finditer(answer):
            a, b = m.start(), m.end()
            while b > a and answer[b - 1].isspace():
                b -= 1
            while a < b and answer[a].isspace():
                a += 1
            if a == b or any(x < b and a < y for x, y in seen) or any(x <= a < y for x, y in quoted):
                continue
            seen.append((a, b))
            findings.append(Finding(
                check="self-talk", severity="high", start=a, end=b, text=answer[a:b],
                sentence=sentence_of(a) if sentence_of else answer,
                message=f"{_MESSAGES[kind]}: \"{answer[a:b]}\".",
                evidence=[], suggestion="" if rx is _SELF_CHECK else None))
    findings.sort(key=lambda f: f.start)
    return findings, {"self_talk": len(findings)}


def _content(text: str) -> list:
    return [stem(w) for w in re.findall(r"[^\W\d_]{3,}|\d+", text.casefold()) if w not in _STOP]


# a statement about one source only: "Passage 3 does not ...", "this passage does not ...", "S2 does not ..."
_ONE_SOURCE = re.compile(r"(?i)\b(?:(?:passage|source|document|doc|result|article|snippet)\s*#?\d+|S\d+|"
                         r"(?:this|that|the\s+(?:first|second|third|fourth|fifth|last|other))\s+"
                         r"(?:passage|source|document|article|snippet|result))\b")


def check_self_contradiction(answer: str, sentence_spans: list, evidence: list, *, sentence_of=None) -> tuple:
    """`evidence`: [(id, text)] of the sources and tool results."""
    findings = []
    ids = [sid for sid, _t in evidence]
    ev_words = {sid: set(_content(t)) for sid, t in evidence}
    for a, b in sentence_spans:
        s = answer[a:b]
        if not _NO_ANSWER.search(_QUOTED.sub(" ", s)):
            continue
        if _ONE_SOURCE.search(s):
            continue        # "Passage 3 does not mention nausea": one source, while another may give it
        topic = [w for w in dict.fromkeys(_content(s)) if w not in _NOUN_WORDS]
        if len(topic) < 2:
            continue
        for c, d in sentence_spans:
            if (c, d) == (a, b):
                continue
            t = answer[c:d]
            if _NO_ANSWER.search(_QUOTED.sub(" ", t)) or t.rstrip().endswith(("?", ":")):
                continue        # a question or a heading ("follow these steps:") gives nothing yet
            shared = [w for w in topic if w in set(_content(t)) and w not in _SOURCE_TALK]
            if len(shared) < 2 or len(shared) < 2 * len(topic) / 3:
                continue
            words = [w for w in _content(t) if not re.fullmatch(r"s\d+", w)]
            cited = citations.cited(t, ids)
            backed = cited or any(words and sum(w in ev for w in words) >= 0.6 * len(words) for ev in ev_words.values())
            if not backed:
                continue
            where = (", which cites " + " and ".join(cited)) if cited else ""
            findings.append(Finding(
                check="self-contradiction", severity="high", start=a, end=b, text=s,
                sentence=sentence_of(a) if sentence_of else s,
                message=f"The answer says the sources do not give this, then gives it from them: \"{t.rstrip('.')}\"{where}.",
                evidence=[{"source": sid, "value": "", "context": ""} for sid in cited]))
            break
    return findings, {"self_contradictions": len(findings)}
