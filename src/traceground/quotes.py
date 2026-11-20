"""Quotes: every quotation of three words or more in the answer must occur in the evidence.

Where it must occur: if the quote's sentence cites sources ([S1], [doc2] ... see citations.py), in one
of those; otherwise in any source (or the question). Compared after textnorm.match_form and with the
punctuation , : ; . ! ? ( ) [ ] removed, so case, accents, dashes, quote marks, spacing and punctuation
do not matter; the words do. A quote with an ellipsis ("a ... b") is checked part by part.

A quote that is not found is reported with the closest wording the sources do contain, and where.
A quote found only in a source the sentence does not cite is reported with the source it is really in.

Editorial insertions in square brackets ("the [new] method") are skipped like an ellipsis.

Not checked: quotes of one or two words (scare quotes, terms), titles ("Attention Is All You Need":
every word but the small ones capitalized, as a title may come from metadata, not the text), quotes
inside code, and quotes in single quote marks (they cannot be told apart from apostrophes).
"""
import re
from difflib import SequenceMatcher

from traceground import citations, textnorm
from traceground.result import Finding

_QUOTE = re.compile(r"[\"“”„«»]([^\"“”„«»\n]{3,600})[\"“”»«]")
_ELLIPSIS = re.compile(r"\s*(?:\.\s?\.\s?\.|…|\[[^\[\]]*\])\s*")      # ... and [editorial insertions]
_SMALL_WORDS = {"a", "an", "the", "of", "and", "or", "in", "on", "for", "to", "with", "at", "by", "from", "into", "onto", "is", "are",
                "n", "this", "that", "these", "those", "my", "your", "his", "her", "its", "our", "their"}
_PUNCT = re.compile(r"[,:;.!?()\[\]…\\*]")     # the backslash of a JSON escape (\\"), and * (emphasis, s**t)
_CODE = re.compile(r"```.*?(?:```|\Z)|`[^`\n]+`", re.S)
FUZZY_WORD_LIMIT = 50_000            # sources longer than this (in words) get no "closest wording" search


def quote_form(text: str) -> str:
    return _PUNCT.sub("", textnorm.match_form(text))


def _word_key(w: str) -> str:
    return quote_form(w)


_EXAMPLE = re.compile(r"(?i)(?:\bsuch\s+as|\be\.g\.,?|\bfor\s+(?:example|instance),?|\bquestion)\s*:?\s*$")


def find_quotes(answer: str, min_words: int = 3) -> list:
    """[(start, end, text)] of the quotations of `min_words` words or more (span inside the marks). Text
    that starts or ends with a space is not a quotation: it lies between two quotations ('the letter "T"
    on their card. Then "X"'). Nor is example text ('a subject line such as "Leave request"') or the
    question in other words ('the answer to the question "What is ...?"')."""
    code = [(m.start(), m.end()) for m in _CODE.finditer(answer)]
    out = []
    for m in _QUOTE.finditer(answer):
        if any(a <= m.start() < b for a, b in code):
            continue
        if m.group(1)[:1].isspace() or m.group(1)[-1:].isspace():
            continue
        if _EXAMPLE.search(answer, max(0, m.start() - 30), m.start()):
            continue
        if len(m.group(1).split()) >= min_words and not looks_like_title(m.group(1)):
            out.append((m.start(1), m.end(1), m.group(1)))
    return out


def looks_like_title(q: str) -> bool:
    """"Attention Is All You Need": every word but the small ones capitalized. A title may come from
    metadata rather than the text, so it is not checked."""
    words = re.findall(r"[^\W\d_][\w'’-]*", q)
    big = [w for w in words if w.lower() not in _SMALL_WORDS]
    return len(big) >= 2 and all(w[0].isupper() for w in big)


def _parts(quote: str, min_words: int) -> list:
    """The parts of a quote to look for: split at ellipses, short parts left out."""
    parts = [p for p in _ELLIPSIS.split(quote) if p.strip()]
    return [p for p in parts if len(p.split()) >= min(min_words, 2)] or [quote]


def _found_in(quote: str, text_form: str, min_words: int) -> bool:
    return all(quote_form(p) in text_form for p in _parts(quote, min_words))


NEAR_RATIO = 0.4      # below the closest-wording bar: shown as "says it differently" when 3 words or more match


def _small_change(quote: str, wording: str) -> bool:
    """The quote and the source's wording differ only in small words (a, the, and, of ...) or punctuation, or
    in the spelling or number of one word."""
    qk = [k for k in (_word_key(w) for w in quote.split()) if k]
    wk = [k for k in (_word_key(w) for w in wording.split()) if k]
    if not qk or qk == wk:
        return bool(qk)
    ops = SequenceMatcher(None, qk, wk, autojunk=False).get_opcodes()
    # words of the source's wording beyond the quote's ends are not changes ("BOMB. Best ever" for "the best ever")
    edits = []
    for tag, a1, a2, b1, b2 in ops:
        if tag == "equal" or (tag == "insert" and (a1 == 0 or a1 == len(qk))):
            continue
        if tag == "replace" and (a1 == 0 or a2 == len(qk)) and all(w in _SMALL_WORDS for w in qk[a1:a2]):
            edits.append((qk[a1:a2], []))              # "the best ever" for "BOMB. Best ever"
        else:
            edits.append((qk[a1:a2], wk[b1:b2]))
    changed = [w for x, y in edits for w in x + y]
    if 0 < len(changed) <= 2 and all(w in _SMALL_WORDS for w in changed):
        return True
    # one word spelled differently: the source's typo corrected ("evrrything" quoted as "everything")
    if not (len(edits) == 1 and len(edits[0][0]) == len(edits[0][1]) == 1):
        return False
    x, y = edits[0][0][0], edits[0][1][0]          # or singular and plural ("best gin" for "best gins")
    return x.rstrip("s") == y.rstrip("s") or (len(x) >= 5 and SequenceMatcher(None, x, y).ratio() >= 0.8)


def _one_letter_off(quote: str, forms: list):
    """The id of the first form (sid, quote form of a source) that has the quote with one letter added, left out or
    changed, inside a word of five letters or more and not in a digit: "experience in itself" for the source's
    "experience in its self". None if there is none."""
    spans, qf = [], ""
    for w in quote.split():
        f = quote_form(w)
        spans.append((len(qf), len(qf) + len(f), f))
        qf += f
    if len(qf) < 10:
        return None
    for i in range(len(qf) + 1):
        word = next((f for a, b, f in spans if a <= i < b or (i == len(qf) and b == i)), "")
        if len(word) < 5 or (i < len(qf) and qf[i].isdigit()):
            continue
        rx = re.compile(re.escape(qf[:i]) + r"(?:[^\d]?" + re.escape(qf[i + 1:]) + "|[^\\d]" + re.escape(qf[i:]) + ")")
        for sid, form in forms:
            if rx.search(form):
                return sid
    return None


def _shared_words(a: str, b: str) -> int:
    """Words of a that b has too (by word key), counted once each."""
    bk = {_word_key(w) for w in b.split()}
    return len({k for k in (_word_key(w) for w in a.split()) if k and k in bk})


def closest_wording(quote: str, sources: list, min_ratio: float = 0.6):
    """(source id, wording as written, similarity 0..1) of the stretch of the sources whose words are
    most like the quote's, or None if nothing reaches min_ratio. Similarity: words in common (in order)
    over the length of the longer of the two."""
    qk = [k for k in (_word_key(w) for w in quote.split()) if k]
    if not qk:
        return None
    total = sum(len(t.split()) for _sid, t in sources)
    if total > FUZZY_WORD_LIMIT:
        return None
    qset = set(qk)
    sm = SequenceMatcher(None, autojunk=False)
    sm.set_seq2(qk)
    best = (0.0, None, None, None)
    for sid, text in sources:
        words = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
        keys = [_word_key(text[a:b]) for a, b in words]
        n = len(qk)
        for length in dict.fromkeys([n, n + 1, max(1, n - 1)]):      # the quote's own length first: wins ties
            for i in range(0, len(words) - length + 1):
                window = keys[i:i + length]
                if not qset.intersection(window):
                    continue
                sm.set_seq1(window)
                if sm.real_quick_ratio() + 0.002 <= best[0] or sm.quick_ratio() + 0.002 <= best[0]:
                    continue
                matched = sum(blk.size for blk in sm.get_matching_blocks())
                r = matched / max(n, length)            # words in common over the longer: a dropped word costs
                # ties go to the stretch that starts and ends where the quote does
                score = r + 0.001 * (window[0] == qk[0]) + 0.001 * (window[-1] == qk[-1])
                if score > best[0]:
                    best = (score, sid, i, length)
    score, sid, i, length = best
    ratio = round(score, 2)
    if sid is None or ratio < min_ratio:
        return None
    text = dict(sources)[sid]
    words = [(m.start(), m.end()) for m in re.finditer(r"\S+", text)]
    first, last = _aligned(qk, [_word_key(text[x:y]) for x, y in words], i, length)
    a, b = words[first][0], words[last][1]
    return sid, text[a:b].strip(" \"'“”‘’,;:.!?"), ratio


def _aligned(qk: list, keys: list, i: int, length: int) -> tuple:
    """First and last word index of the stretch that lines up with the whole quote: the best window,
    widened so that quote words left unmatched at either end ("every [week]" against "every night")
    are covered by the source words in their place."""
    lo = max(0, i - 2)
    region = keys[lo:min(len(keys), i + length + 2)]
    blocks = [blk for blk in SequenceMatcher(None, region, qk, autojunk=False).get_matching_blocks() if blk.size]
    if not blocks:
        return i, i + length - 1
    s0, q0 = blocks[0].a, blocks[0].b
    s1, q1 = blocks[-1].a + blocks[-1].size - 1, blocks[-1].b + blocks[-1].size - 1
    first = lo + max(0, s0 - q0)
    last = min(len(keys) - 1, lo + s1 + (len(qk) - 1 - q1))
    return first, last


def _where(sid: str) -> str:
    return "the question" if sid == "question" else sid


def check_quotes(answer: str, sources: list, question: str = "", *, min_words: int = 3,
                 sentence_of=None) -> tuple:
    """(findings, stats) for the quotes of `answer`. `sources` is [(id, text), ...]."""
    evidence = list(sources) + ([("question", question)] if question.strip() else [])
    forms = {sid: quote_form(t) for sid, t in evidence}
    ids = [sid for sid, _t in sources]
    findings, n_wrong, n_missing = [], 0, 0
    quotes = find_quotes(answer, min_words)
    for start, end, q in quotes:
        sentence = sentence_of(start) if sentence_of else answer
        cite = citations.cited(sentence, ids)
        if q.rstrip().endswith("?") and question.strip() and _shared_words(q, question) >= 0.6 * len(q.split()):
            continue                        # the question asked, restated: 'the answer to "What are the odds ...?"'
        where = [sid for sid in forms if _found_in(q, forms[sid], min_words)]
        if cite and any(sid in where for sid in cite):
            continue
        if not cite and where:
            continue
        if where:                                  # found, but not in what the sentence cites
            n_wrong += 1
            real = where[0]
            near = closest_wording(q, [(real, dict(evidence)[real])], min_ratio=0.0)
            cited_txt = " and ".join(cite)
            findings.append(Finding(
                check="quote", severity="high", start=start, end=end, text=q, sentence=sentence,
                message=(f"The quote is not in {cited_txt}, which this sentence cites. "
                         f"It is in {_where(real)}" + (f": \"{near[1]}\"." if near else ".")),
                evidence=[{"source": real, "value": near[1] if near else q, "context": ""}],
                suggestion=None))
            continue
        n_missing += 1
        pool = [(sid, t) for sid, t in evidence if not cite or sid in cite] or evidence
        near = closest_wording(q, pool) or (closest_wording(q, evidence) if cite else None)
        loose = None if near else (closest_wording(q, pool, min_ratio=NEAR_RATIO) or
                                   (closest_wording(q, evidence, min_ratio=NEAR_RATIO) if cite else None))
        if loose and _shared_words(q, loose[1]) < 3:
            loose = None
        severity = "high"
        letter = None if near and _small_change(q, near[1]) else _one_letter_off(
            q, [(sid, forms[sid]) for sid, _t in pool] if sum(len(t) for _s, t in pool) < 20 * FUZZY_WORD_LIMIT else [])
        if letter:
            severity = "low"            # "experience in itself" for "experience in its self"
            message = (f"The quote differs slightly from {_where(letter)} (one letter): "
                       f"\"{near[1]}\"." if near and near[0] == letter else
                       f"The quote differs slightly from {_where(letter)} (one letter).")
            evidence_list = [{"source": letter, "value": near[1] if near and near[0] == letter else q, "context": ""}]
        elif near and _small_change(q, near[1]):
            severity = "low"            # "dominant and subordinate" for "dominant and a subordinate"
            message = (f"The quote differs slightly from {_where(near[0])} (small words, punctuation or spelling): "
                       f"\"{near[1]}\".")
            evidence_list = [{"source": near[0], "value": near[1], "context": ""}]
        elif near:
            message = (f"The quote is not in the {'cited source' if cite else 'sources'}. "
                       f"The closest wording, in {_where(near[0])}: \"{near[1]}\".")
            evidence_list = [{"source": near[0], "value": near[1], "context": ""}]
        elif loose:
            message = (f"The quote is not in the {'cited source' if cite else 'sources'}. The nearest wording, in "
                       f"{_where(loose[0])}, says it differently: \"{loose[1]}\".")
            evidence_list = [{"source": loose[0], "value": loose[1], "context": ""}]
        else:
            message = f"The quote is not in the {'cited source' if cite else 'sources'}, and nothing there is close to it."
            evidence_list = []
        findings.append(Finding(check="quote", severity=severity, start=start, end=end, text=q, sentence=sentence,
                                message=message, evidence=evidence_list, suggestion=None))
    n_slight = sum(f.check == "quote" and f.severity == "low" for f in findings)
    stats = {"quotes_checked": len(quotes), "quotes_not_found": n_missing - n_slight, "quotes_wrong_source": n_wrong,
             "quotes_changed_slightly": n_slight}
    return findings, stats
