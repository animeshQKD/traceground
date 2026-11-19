"""Text clean-up, a form for comparing, and sentence spans.

Ported from "Ask Your Quantum Physics Research Papers" (textnorm.py, 2026-11-13a) and generalized:
the rules that only physics PDFs need (TeX's epsilon misread, negated relations, lone capitals) are
left out; ligatures, invisible characters, spacing accents and odd spaces, which any PDF text can
have, stay.

* clean(text): what a reader sees, tidied. Nothing that changes the wording.
* match_form(text): only for comparing (quotes): NFKC, case folded, dashes, quote marks, whitespace
  and the script marks ^ _ { } removed.
* sentence_spans(text): (start, end) of each sentence in the ORIGINAL text, so a finding can point at
  its sentence. Conservative: when unsure, it does not split.
"""
import html
import re
import unicodedata

LIGATURES = {"ﬀ": "ff", "ﬁ": "fi", "ﬂ": "fl", "ﬃ": "ffi", "ﬄ": "ffl", "ﬅ": "st", "ﬆ": "st"}
_INVISIBLE = dict.fromkeys(map(ord, "­​‌‍⁠﻿"), None)   # soft hyphen, zero-width
_CONTROL = dict.fromkeys(c for c in range(0x20) if chr(c) not in "\t\n\r")
_SPACES = re.compile(r"[\s  -   　]+")
DASHES = "-‐‑‒–—―−﹣－"
QUOTES = "\"'`‘’‚‛“”„‟′″´"
_DROP_FOR_MATCH = dict.fromkeys(map(ord, DASHES + QUOTES + "^_{}"), None)

# spacing accents that PDF text extraction leaves as separate glyphs next to the letter ("fu¨r")
_ACCENTS = {"¨": "̈", "´": "́", "˜": "̃", "ˆ": "̂", "¸": "̧",
            "ˇ": "̌", "˘": "̆", "˙": "̇", "¯": "̄", "˚": "̊",
            "˝": "̋", "˛": "̨"}
_ACC = "".join(_ACCENTS)
_ACC_AFTER = re.compile(rf"([A-Za-zıȷ])([{_ACC}])")


def _combine_accents(text: str) -> str:
    if not any(a in text for a in _ACCENTS):
        return text
    text = _ACC_AFTER.sub(lambda m: m.group(1).replace("ı", "i").replace("ȷ", "j")
                          + _ACCENTS[m.group(2)], text)
    return unicodedata.normalize("NFC", text)


def clean(text: str) -> str:
    """Readable form: ligatures expanded, spacing accents joined to their letters, invisible and
    control characters removed, every kind of space a plain space, whitespace collapsed."""
    if not text:
        return ""
    for lig, rep in LIGATURES.items():
        text = text.replace(lig, rep)
    text = _combine_accents(text.translate(_INVISIBLE).translate(_CONTROL))
    return _SPACES.sub(" ", text).strip()


def match_form(text: str) -> str:
    """Form used only for comparing two texts: differences of case, accents' encoding, HTML entities
    (&amp;), dashes, hyphens, quote marks, spacing and line-break hyphens disappear."""
    t = unicodedata.normalize("NFKC", clean(html.unescape(text))).casefold().translate(_DROP_FOR_MATCH)
    return re.sub(r"\s+", "", t)


def fold_accents(text: str) -> str:
    """'Řeháček' -> 'Rehacek' (for comparing names, never for display)."""
    return "".join(c for c in unicodedata.normalize("NFKD", text) if not unicodedata.combining(c))


# ---------------------------------------------------------------- sentences
_ABBREV = {
    "al", "fig", "figs", "eq", "eqs", "ref", "refs", "sec", "secs", "tab", "app", "ch", "chap", "vol",
    "no", "nos", "pp", "p", "e.g", "i.e", "cf", "vs", "etc", "approx", "resp", "viz", "dr", "prof",
    "mr", "mrs", "ms", "st", "jr", "sr", "inc", "ltd", "co", "corp", "dept", "univ", "est", "max", "min",
    "a.m", "p.m", "u.s", "u.k", "jan", "feb", "mar", "apr", "jun", "jul", "aug", "sep", "sept", "oct",
    "nov", "dec", "mt", "ft", "avg",
}
# a sentence ends at . ! or ? (perhaps followed by closing quotes or brackets) and whitespace, at a
# blank line, or at a line break before a list item
_BOUNDARY = re.compile(r"([.!?])([\"'”’)\]]*)(\s+)"
                       r"|\n[ \t]*\n\s*"
                       r"|\n(?=[ \t]*(?:[-*•]|\d+[.)])\s)")


def _word_before(text: str, end: int) -> str:
    m = re.search(r"([A-Za-z][A-Za-z.]*)$", text[:end])
    return m.group(1).lower().rstrip(".") if m else ""


def _trimmed(text: str, a: int, b: int):
    while a < b and text[a].isspace():
        a += 1
    while b > a and text[b - 1].isspace():
        b -= 1
    return a, b


def sentence_spans(text: str) -> list:
    """[(start, end), ...] of the sentences of `text`, as offsets into `text` itself."""
    spans, start = [], 0
    for m in _BOUNDARY.finditer(text):
        if m.group(1):
            if m.end() >= len(text):
                continue
            nxt = text[m.end()]
            if m.group(1) == ".":
                if _word_before(text, m.start()) in _ABBREV:
                    continue
                if re.search(r"(?:^|[\s(\[])[A-Z]$", text[:m.start()]):       # an initial: "A. Einstein"
                    continue
                if nxt.islower():                     # "approx. two": the period was inside the sentence
                    continue
            end = m.start(3)
        else:
            end = m.start()
        a, b = _trimmed(text, start, end)
        if a < b:
            spans.append((a, b))
        start = m.end()
    a, b = _trimmed(text, start, len(text))
    if a < b:
        spans.append((a, b))
    merged = []                       # "... every night. [S1]": markers alone belong to the sentence before
    for a, b in spans:
        if merged and _ONLY_MARKERS.match(text[a:b]):
            merged[-1] = (merged[-1][0], b)
        else:
            merged.append((a, b))
    return merged


_ONLY_MARKERS = re.compile(r"^(?:\s*\[[^\[\]\n]{1,80}\])+\s*[.!?]?$")


def split_sentences(text: str) -> list:
    return [text[a:b] for a, b in sentence_spans(text)]


def sentence_at(text: str, pos: int, spans=None) -> str:
    """The sentence of `text` that contains offset `pos`."""
    for a, b in spans if spans is not None else sentence_spans(text):
        if a <= pos < b:
            return text[a:b]
    return text.strip()
