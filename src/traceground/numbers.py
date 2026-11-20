"""Numbers: find them in an answer, find them in the evidence, and say which answer numbers the
evidence does not support.

A number in the answer is supported when some number in the evidence (the sources, and the question)
equals it at the precision the answer wrote it with (project 1's rule): "1.98" is supported by
1.9799, "24" by 23.7, "12,250" by 12250.43. Also accepted:
  * thousands separators, including Indian grouping: 12,250 = 12250; 1,23,456 = 123456;
  * scientific notation: 3.2e-4 = 3.2×10⁻⁴ = 3.2 x 10^-4;
  * scale words: "41.2 million" = 41,200,000 ("k", "M", "bn", lakh, crore too);
  * a percentage and its fraction, 7% = 0.07 (percent_as_fraction, on by default);
  * an approximate round number: "about 12,000" for 12,250 (only after about, around, roughly, ~ ...);
  * number words and fractions in the evidence: "twenty" supports 20, "half" and "1/2" support 0.5 or 50%;
  * a number computed from numbers the answer itself states and the evidence supports, when its
    sentence says so ("315 EUR and 234 EUR, a total of 549 EUR"): a sum or difference of two of them or
    the sum of all (with "total", "together", "extra", "warmer" ...), or a stated number times or
    divided by a count from the question (with "each", "per", "times"), at the written precision.
    Wrong arithmetic ("a total of 550") stays unsupported;
  * a source number times or divided by a whole count from the question ("3 lamps" at 39.9 is 119.70)
    is reported as minor: worked out in the answer, not by a tool;
  * a duration written in two units whose total is a source number ("535 minutes, 8 hours 55 minutes");
  * a unit conversion next to a supported number, "350°F (175°C)", is listed as minor (worked out in the
    answer); when neither number is in the evidence, only the first is reported;
  * a scale in a key name: revenue_musd = 1840.5 supports "1.84 billion";
  * a thin or narrow no-break space as thousands separator ("40\u202f983.61").
Signs are not compared (a model writes "−0.11" with any kind of minus, ranges "5-10" look like signs).

Not checked in the answer (when unsure, stay silent):
  * numbers inside citation markers ([1], [S1], [doc2], [P1-p4-2]) and reference labels (Eq. (3),
    Fig. 2, Table 1, Section 4, Step 2, page 7, No. 5, Passage 2, Review 3);
  * list numbering at the start of a line ("1. ", "2) ");
  * URLs, e-mail addresses and code (`inline` or in ``` blocks);
  * years in citations ("Smith et al. 2020", "Hradil (1997)");
  * digits glued to a word: symbol indices (rho_1, λ_1), names (Q3, CO2, COVID-19, MX-200, GPT-4),
    ordinals (1st, 3rd; but the day of a date, "April 11th", is checked) and glued units (5km);
  * plain integers from 0 to 10 (check_small_integers=False by default): "3 options", "2 steps" are
    too often not written as digits in the evidence.
"""
import re
from dataclasses import dataclass

from traceground.result import Finding

_SUPERSCRIPT = str.maketrans("⁰¹²³⁴⁵⁶⁷⁸⁹⁻⁺", "0123456789-+")
_SCALE_WORDS = {"thousand": 1e3, "million": 1e6, "billion": 1e9, "trillion": 1e12,
                "lakh": 1e5, "lakhs": 1e5, "crore": 1e7, "crores": 1e7}
_SCALE_SUFFIX = {"k": 1e3, "K": 1e3, "M": 1e6, "mn": 1e6, "bn": 1e9}
_SUP = "[⁻⁺]?[⁰¹²³⁴⁵⁶⁷⁸⁹]+"

_NUM = re.compile(rf"""
    (?<![\w.])                                   # not glued to a word or a decimal point
    (?<![A-Za-z][-‐‑])                 # not COVID-19, MX-200, GPT-4
    (?P<sign>[-−+])?
    (?:
        (?P<pow10>10)\s?(?:\^\s?\(?(?P<pe1>[-−+]?\d+)\)?|(?P<pe2>{_SUP}))      # 10^-4, 10⁻⁴
      |
        (?P<int>\d{{1,3}}(?:,\d{{2,3}})*,\d{{3}}(?!\d)                              # 12,250 · 1,23,456
               |\d{{1,3}}(?:[\u202f\u2009\u00a0]\d{{3}})+(?!\d)                    # 40\u202f983 (SI style)
               |\d+)                                                            # 42
        (?:\.(?P<frac>\d+))?
        (?:\s?[eE](?P<e1>[-−+]?\d+)
          |\s?[×xX·*]\s?10\s?(?:\^\s?\(?(?P<e2>[-−+]?\d+)\)?|(?P<e3>{_SUP}))
        )?
    )
    (?P<pct>\s?%|\s?(?:per\s?cent|percent)\b)?
    (?P<sfx>(?:k|K|M|mn|bn)(?![A-Za-z]))?
    (?![A-Za-z\d])                               # not 5km, 1st, 3D
    (?:\s(?P<word>thousand|million|billion|trillion|lakhs?|crores?)\b)?
""", re.X)

# every run of digits, for the evidence only: more evidence numbers can only mean fewer false alarms
_ANY_DIGITS = re.compile(r"\d+(?:\.\d+)?")
_FRACTION = re.compile(r"(?<![\d/.])(\d{1,4})\s?/\s?(\d{1,4})(?![\d/])")

_UNITS = ["zero", "one", "two", "three", "four", "five", "six", "seven", "eight", "nine", "ten", "eleven",
          "twelve", "thirteen", "fourteen", "fifteen", "sixteen", "seventeen", "eighteen", "nineteen"]
_TENS = {"twenty": 20, "thirty": 30, "forty": 40, "fifty": 50, "sixty": 60, "seventy": 70, "eighty": 80,
         "ninety": 90}
_WORD_VALUES = {w: float(i) for i, w in enumerate(_UNITS)} | {w: float(v) for w, v in _TENS.items()} | {
    "hundred": 100.0, "dozen": 12.0, "half": 0.5, "quarter": 0.25}
_NUMBER_WORD = re.compile(
    r"\b(?P<tens>" + "|".join(_TENS) + r")[-\s](?P<unit>" + "|".join(_UNITS[1:10]) + r")\b"
    r"|\b(?P<word>" + "|".join(sorted(_WORD_VALUES, key=len, reverse=True)) + r")\b"
    r"(?:\s(?P<scale>hundred|thousand|million|billion|trillion|lakhs?|crores?)\b)?", re.I)

# ---- what the answer check leaves out
_CITATION = re.compile(r"\[[A-Za-z]{0,12}[-_]?\d+[\w\-]*(?:\s*[,;–-]\s*[A-Za-z]{0,12}[-_]?\d+[\w\-]*)*\]")
_LABEL = re.compile(r"(?:\b(?:Eqs?\.?|Equations?|Figs?\.?|Figures?|Tables?|Tab\.|Refs?\.?|References?|Sections?|"
                    r"Secs?\.|Appendix|Chapters?|Ch\.|Steps?|Options?|Items?|Pages?|pp?\.|No\.|Nos\.|Lines?|"
                    r"Rows?|Columns?|Rules?|Articles?|Art\.|Clauses?|Passages?|Reviews?|Reviewers?|Examples?|Parts?|Cases?)|[§#])"
                    r"\s*\(?[A-Z]?\d+[a-z]?(?:\.\d+)*\)?"
                    r"(?:\s*(?:,|and|&|–|-|to)\s*\(?[A-Z]?\d+[a-z]?(?:\.\d+)*\)?)*", re.I)
_LIST_NUMBER = re.compile(r"(?m)^[ \t]*\d+[.)](?=\s)")
_URL_OR_EMAIL = re.compile(r"\bhttps?://\S+|\bwww\.\S+|\b[\w.+-]+@[\w-]+\.[\w.-]+")
_CODE = re.compile(r"```.*?(?:```|\Z)|`[^`\n]+`", re.S)        # fenced blocks and inline code
_CITED_YEAR = re.compile(r"\bet\s+al\.?,?\s*\(?(?:19|20)\d{2}[a-z]?\)?"
                         r"|\b[A-Z][\w'’-]+(?:\s(?:and|&)\s[A-Z][\w'’-]+)?,?\s\((?:19|20)\d{2}[a-z]?\)"
                         r"|\((?:[A-Z][\w'’-]+(?:\s+et\s+al\.)?,?\s(?:19|20)\d{2}[a-z]?;?\s*)+\)")
_APPROX = re.compile(r"(?:\b(?:about|around|approximately|approx\.|roughly|nearly|almost|some|close\s+to|"
                     r"over|under|more\s+than|less\s+than|up\s+to|at\s+least|at\s+most)|[~≈∼])"
                     r"\s*[$€£₹¥]?\s*$", re.I)


@dataclass(frozen=True)
class Number:
    start: int
    end: int
    text: str
    value: float          # magnitude, exponent applied, scale word NOT applied
    decimals: int         # digits after the decimal point, as written
    exponent: int         # power of ten written with it (3.2×10⁻⁴: -4)
    scale: float          # 1, or 1e6 for "million" ...
    percent: bool
    integer: bool         # written as a plain integer: no decimals, exponent, percent or scale
    approx: bool = False  # preceded by "about", "~" ...

    @property
    def tolerance(self) -> float:
        """Half a unit of the last digit written; for "about 12,000" half of the rounded place."""
        tol = 0.5 * 10.0 ** (self.exponent - self.decimals)
        if self.approx and self.decimals == 0 and self.value >= 10:
            digits = re.sub(r"\D", "", self.text.split(".")[0].split("e")[0].split("E")[0])
            zeros = len(digits) - len(digits.rstrip("0"))
            tol = max(tol, 0.5 * 10.0 ** zeros)
        return tol

    def candidates(self, percent_as_fraction: bool = True) -> list:
        """(value, tolerance) pairs this number may stand for."""
        out = [(self.value, self.tolerance)]
        if self.scale != 1:
            out.append((self.value * self.scale, self.tolerance * self.scale))
        if self.percent and percent_as_fraction:
            out.append((self.value / 100, self.tolerance / 100))
        return out


def _exp(s) -> int:
    return int(s.translate(_SUPERSCRIPT).replace("−", "-")) if s else 0


def _parse(m: re.Match, text: str) -> Number:
    g = m.groupdict()
    if g["pow10"]:
        exponent, mantissa, decimals = _exp(g["pe1"] or g["pe2"]), 1.0, 0
    else:
        exponent = _exp(g["e1"] or g["e2"] or g["e3"])
        int_s = re.sub(r"[,\u202f\u2009\u00a0]", "", g["int"])
        mantissa = float(f"{int_s}.{g['frac']}" if g["frac"] else int_s)
        decimals = len(g["frac"] or "")
    scale = _SCALE_WORDS.get((g["word"] or "").lower()) or _SCALE_SUFFIX.get(g["sfx"] or "", 1.0)
    has_exp = bool(g["pow10"] or g["e1"] or g["e2"] or g["e3"])
    return Number(start=m.start(), end=m.end(), text=m.group(0), value=abs(mantissa) * 10.0 ** exponent,
                  decimals=decimals, exponent=exponent, scale=scale, percent=bool(g["pct"]),
                  integer=not (g["frac"] or has_exp or g["pct"] or scale != 1),
                  approx=bool(_APPROX.search(text[max(0, m.start() - 30):m.start()])))


# what is left when a number glued to a unit was cut short: "29" of "29,200km", "3" of "3.5km"
_CUT_FROM_GLUED = re.compile(r"(?:[,.]\d+)+[A-Za-z]")


def find_numbers(text: str) -> list:
    """Every number written in digits in `text`, with its span. A number glued to a unit ("5km") is not
    one, and neither is a part of one ("29" of "29,200km")."""
    return [_parse(m, text) for m in _NUM.finditer(text) if not _CUT_FROM_GLUED.match(text, m.end())]


# a rating scale, not a claim: "4.0 out of 5.0 stars", "8/10"
_SCALE = re.compile(r"(?i)\bout\s+of\s+(?:5|10|100)(?:\.0)?\b|(?<=\d)\s?/\s?(?:5|10)(?:\.0)?\b(?!\s*[-/]?\d)"
                    r"|\b24\s*/\s*7\b|\b24x7\b")       # and "open 24/7"

# the answer counting itself: "Here is a summary in 150 words", "(98 words)", "Word count: 98", "a 98-word summary"
_OWN_LENGTH = re.compile(
    r"(?i)\b(?:summary|summari[sz]ed|overview|answer|response|description|paragraph|version|reply|text|recap)\b"
    r"[^.!?\n]{0,80}?\b(?:in|within|under|of|at|to)\s+(?:about\s+|around\s+|approximately\s+|exactly\s+|"
    r"roughly\s+|just\s+|fewer\s+than\s+|less\s+than\s+|under\s+)?\d{1,4}(?:\s*[-\u2013]\s*\d{1,4})?\s+"
    r"(?:words?|sentences?|characters?|paragraphs?|bullet\s+points?|lines?)\b"
    r"|\(\s*\d{1,4}\s+words?\s*\)|\bword\s+count\s*:?\s*\d{1,4}"
    r"|\b\d{1,4}[-\s]words?\s+(?:summary|overview|answer|response|description|paragraph|version|recap)\b")


def excluded_spans(answer: str) -> list:
    """Spans of the answer whose numbers are not checked (citations, labels, list numbers, cited years,
    the answer counting its own words, a rating scale)."""
    spans = []
    for rx in (_CITATION, _LABEL, _LIST_NUMBER, _CITED_YEAR, _URL_OR_EMAIL, _CODE, _OWN_LENGTH, _SCALE):
        spans += [(m.start(), m.end()) for m in rx.finditer(answer)]
    return spans


_MONTHS = r"(?:Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|June?|July?|Aug(?:ust)?|Sep(?:t(?:ember)?)?|" \
          r"Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)"
_DATE_ORDINAL = re.compile(rf"\b{_MONTHS}\.?\s+\d{{1,2}}(st|nd|rd|th)\b|\b\d{{1,2}}(st|nd|rd|th)\s+(?:of\s+)?{_MONTHS}\b",
                           re.I)


def unglue_date_ordinals(text: str) -> str:
    """"April 11th" -> "April 11  ": the day of a date is checked like any number (other ordinals, "1st
    place", stay glued and are not checked). Same length, so positions do not move."""
    if not re.search(r"\d(?:st|nd|rd|th)\b", text):
        return text
    out = list(text)
    for m in _DATE_ORDINAL.finditer(text):
        g = 1 if m.group(1) else 2
        out[m.start(g):m.end(g)] = "  "
    return "".join(out)


def answer_numbers(answer: str, check_small_integers: bool = False) -> tuple:
    """(numbers to check, numbers left out) of the answer."""
    skip = excluded_spans(answer)
    keep, left = [], []
    for n in find_numbers(unglue_date_ordinals(answer)):
        small = n.integer and n.value <= 10 and not check_small_integers
        (left if small or any(a <= n.start < b for a, b in skip) else keep).append(n)
    return keep, left


# ---------------------------------------------------------------- evidence
@dataclass(frozen=True)
class EvidenceNumber:
    source: str           # source id, or "question"
    text: str             # as written there
    start: int
    end: int
    values: tuple         # every value it may stand for
    shown: bool = True    # may be offered as a "closest value" (False for number words and loose digits)
    pct: bool = True      # may support "x%" by its plain value: written with %, at least 1, or a pct key


_KEY_BEFORE = re.compile(r"[\"']([A-Za-z][\w ]*)[\"']\s*:\s*[-\u2212+]?$")
_CURRENCIES = ("usd", "eur", "gbp", "inr", "jpy", "chf", "cny", "aud", "cad")
_KEY_SCALES = {"thousand": 1e3, "thousands": 1e3, "k": 1e3, "m": 1e6, "mn": 1e6, "mln": 1e6, "mio": 1e6,
               "million": 1e6, "millions": 1e6, "b": 1e9, "bn": 1e9, "billion": 1e9, "billions": 1e9}


def key_scale(key: str) -> float:
    """revenue_musd, sales_eur_mn, users_millions -> 1e6; cost_kusd -> 1e3; 1 when the key gives no scale.
    A lone "m" or "k" counts only next to a currency (distance_m is metres)."""
    parts = re.findall(r"[a-z]+", key.lower())
    if not parts:
        return 1.0
    last = parts[-1]
    if last in _KEY_SCALES and (len(last) > 1 or (len(parts) > 1 and parts[-2] in _CURRENCIES)):
        return _KEY_SCALES[last]
    for cur in _CURRENCIES:
        if last.endswith(cur) and last[:-len(cur)] in _KEY_SCALES:
            return _KEY_SCALES[last[:-len(cur)]]
    return 1.0


_PCT_KEY = re.compile(r"(?i)(?:pct|percent(?:age)?)[\w ]*[\"']?\s*[:=]\s*[-\u2212+]?$")


def evidence_numbers(source_id: str, text: str, percent_as_fraction: bool = True) -> list:
    out, seen = [], set()
    for n in find_numbers(unglue_date_ordinals(text)):
        vals = [n.value] + ([n.value * n.scale] if n.scale != 1 else []) + \
               ([n.value / 100] if n.percent and percent_as_fraction else [])
        pct = n.percent or abs(n.value * n.scale) >= 1 or bool(_PCT_KEY.search(text, max(0, n.start - 40), n.start))
        key = _KEY_BEFORE.search(text, max(0, n.start - 60), n.start)
        scale = key_scale(key.group(1)) if key else 1.0
        if scale != 1.0:                           # "revenue_musd": 1840.5 supports "1.84 billion"
            vals = vals + [v * scale for v in vals]
        out.append(EvidenceNumber(source_id, n.text.strip(), n.start, n.end, tuple(vals), True, pct))
        seen.add(n.start)
    for m in _ANY_DIGITS.finditer(text):           # digits the precise pattern leaves out (MX-200, Q3, x2)
        if not any(e.start <= m.start() < e.end for e in out):
            out.append(EvidenceNumber(source_id, m.group(0), m.start(), m.end(), (float(m.group(0)),), False))
    for m in _FRACTION.finditer(text):             # "1/2" supports 0.5 and 50%
        a, b = float(m.group(1)), float(m.group(2))
        if b:
            vals = (a / b, 100 * a / b) if percent_as_fraction else (a / b,)
            out.append(EvidenceNumber(source_id, m.group(0), m.start(), m.end(), vals, False))
    for m in _NUMBER_WORD.finditer(text):
        if m.group("tens"):
            v = _TENS[m.group("tens").lower()] + _UNITS.index(m.group("unit").lower())
        else:
            v = _WORD_VALUES[m.group("word").lower()]
        scale = m.group("scale")
        vals = [v] + ([v * (_SCALE_WORDS.get(scale.lower()) or 100.0)] if scale else [])
        if m.group("word") and m.group("word").lower() in ("half", "quarter") and percent_as_fraction:
            vals.append(v * 100)                   # "half" supports 50%
        out.append(EvidenceNumber(source_id, m.group(0), m.start(), m.end(), tuple(float(x) for x in vals), False))
    return out


def _context(text: str, start: int, end: int, width: int = 50) -> str:
    a, b = max(0, start - width), min(len(text), end + width)
    return ("..." if a else "") + " ".join(text[a:b].split()) + ("..." if b < len(text) else "")


def _close(c: float, tol: float, v: float) -> bool:
    return abs(c - v) <= tol * (1 + 1e-9) + 1e-12 * max(1.0, abs(v))


def _supported(n: Number, evidence: list, percent_as_fraction: bool) -> bool:
    """`n` at its precision matches an evidence value. "0.075%" is not supported by a bare 0.075 (a
    fraction, so 7.5%): a percentage matches by its plain value only evidence that may be a percentage."""
    for i, (c, t) in enumerate(n.candidates(percent_as_fraction)):
        plain = n.percent and i == 0
        if plain:   # against the number as written there, not its fraction form (7.5% is not 0.075%)
            if any(_close(c, t, e.values[0]) for e in evidence if e.pct):
                return True
        elif any(_close(c, t, v) for e in evidence for v in e.values):
            return True
    return False


def _cut_short(n: Number, evidence: list):
    """The evidence value that `n` is a truncation of (1.97 for 1.9799), if any."""
    if n.decimals == 0 or n.percent:
        return None
    step = 10.0 ** (n.exponent - n.decimals)
    for e in evidence:
        for v in e.values:
            if n.value - 1e-12 <= v < n.value + step - 1e-12 and not _close(n.value, n.tolerance, v):
                return e, v
    return None


_STAMP = re.compile(r"\d{4}-\d\d-\d\d(?:[ T]\d\d:\d\d(?::\d\d(?:\.\d+)?)?)?|(?<![\d.])\d{1,2}:\d\d(?::\d\d)?")
_MONTH_BEFORE = re.compile(rf"(?i)\b{_MONTHS}\.?\s+$")
_MONTH_AFTER = re.compile(rf"(?i)(?:st|nd|rd|th)?\s+(?:of\s+)?{_MONTHS}\b")


def number_kind(text: str, start: int, end: int) -> str:
    """What a number is, for offering a close value of the same kind: "stamp" (a part of a date or time
    stamp, "2015-12-13 17:03:39"), "day" (of a month: "May 18", "22nd of May"), "year" (1800 to 2100, digits
    only) or "other"."""
    if any(m.start() <= start < m.end() for m in _STAMP.finditer(text, max(0, start - 20), min(len(text), end + 20))):
        return "stamp"
    if _MONTH_BEFORE.search(text[max(0, start - 12):start]) or _MONTH_AFTER.match(text, end):
        return "day"
    if re.fullmatch(r"\d{4}", text[start:end].strip()) and 1800 <= int(text[start:end]) <= 2100:
        return "year"
    return "other"


def _nearest(n: Number, evidence: list, k: int = 2, within: float = 0.5, answer: str = "", texts=None) -> list:
    """Up to k source numbers close to n (relative difference at most `within`), closest first. With the
    answer and the texts, only numbers of the same kind (number_kind) are offered: a year is not close to a
    price, and a part of a time stamp is never offered."""
    kind = number_kind(answer, n.start, n.end) if answer and texts else None
    if kind is not None:
        evidence = [e for e in evidence if e.source in texts
                    and number_kind(texts[e.source], e.start, e.end) == kind != "stamp"]
    pairs = [(c, False) for c, _t in n.candidates(percent_as_fraction=False)]
    if n.percent:
        pairs.append((n.value / 100, True))       # 70% as 0.70: compared only with decimals, not with "1"

    def dist(e):
        return min((abs(c - v) / max(abs(c), abs(v), 1e-300) for c, frac in pairs for v in e.values
                    if not (frac and v == int(v))), default=float("inf"))
    ranked, seen = [], set()
    for e in sorted((e for e in evidence if e.source != "question" and e.shown and dist(e) <= within), key=dist):
        if e.text not in seen:
            seen.add(e.text)
            ranked.append(e)
        if len(ranked) == k:
            break
    return ranked


def _fmt_round(v: float, n: Number) -> str:
    if n.exponent:
        return f"{v / 10.0 ** n.exponent:.{n.decimals}f}"
    return f"{v:,.{n.decimals}f}" if "," in n.text else f"{v:.{n.decimals}f}"


def _suggest(n: Number, right: str):
    """The corrected text for the span, only for a plain decimal written the usual way (certain)."""
    shown = n.text.strip()
    if n.exponent or n.scale != 1 or re.search(r",\d{2},", shown):
        return None
    sign = shown[0] if shown[0] in "-\u2212+" else ""
    return n.text.replace(shown, sign + right)


_SUM_CUE = re.compile(r"(?i)\b(?:total(?:s|ling)?|altogether|together|combined|sum|overall|in all|difference|"
                      r"differs?|extra|additional|adds?|added|sav(?:e|es|ing|ings)|gap|apart|net|remaining|left over|"
                      r"warmer|cooler|colder|hotter|higher|lower|longer|shorter|cheaper|more than|less than|"
                      r"fewer than|increased?|decreased?|rises?|drops?|minus|plus|makes|comes? to|all told|in sum)\b")
_PRODUCT_CUE = re.compile(r"(?i)\b(?:each|apiece|per|times|every)\b|[\u00d7*]|\bx\s?\d")


def derived_from(n: Number, stated: list, question_numbers: list, sentence: str = ""):
    """How `n` follows from numbers the answer itself states (and the evidence supports), if it does,
    when its sentence says it is worked out: "315 EUR and 234 EUR, a total of 549 EUR" (a sum or a
    difference of two of them, or the sum of all, with a word such as "total", "together", "extra",
    "warmer"); a stated number times or divided by a whole count from the question ("3 lamps at 39.90
    each cost 119.70", with "each", "per", "times"). The numbers are taken as written and the result
    must round to `n` at the precision `n` is written in, so wrong arithmetic ("a total of 550") stays
    unsupported. Returns a short description ("315 + 234"), or None."""
    ops = [x for x in stated if x is not n and not x.percent]
    counts = [q for q in question_numbers if q.integer and not q.percent and 2 <= q.value <= 1000]
    # a percentage is the fraction it stands for: "0.15%" is 0.0015, not 36 / 240
    targets = [(n.value / 100, n.tolerance / 100)] if n.percent else n.candidates(percent_as_fraction=False)

    def hit(r):
        return any(abs(c - r) <= t + 1e-9 * max(1.0, abs(r)) for c, t in targets)

    if _SUM_CUE.search(sentence):
        for i, x in enumerate(ops):
            a = x.value * x.scale
            for y in ops[i + 1:]:
                b = y.value * y.scale
                if hit(a + b):
                    return f"{x.text.strip()} + {y.text.strip()}"
                if hit(abs(a - b)):
                    return f"{x.text.strip()} - {y.text.strip()}"
        if len(ops) >= 3 and hit(sum(x.value * x.scale for x in ops)):
            return " + ".join(x.text.strip() for x in ops)
    if _PRODUCT_CUE.search(sentence):
        for x in ops:
            a = x.value * x.scale
            for q in counts:
                if hit(a * q.value):
                    return f"{x.text.strip()} \u00d7 {q.text.strip()}"
                if hit(a / q.value):
                    return f"{x.text.strip()} / {q.text.strip()}"
    return None


COMPUTED_NOTE = "worked out in the answer rather than by a tool"

_UNIT_WORDS = {
    "F": ("°f", "° f", "°fahrenheit", "f", "degrees f", "degrees fahrenheit", "fahrenheit", "deg f"),
    "C": ("°c", "° c", "°celsius", "c", "degrees c", "degrees celsius", "celsius", "deg c"),
    "km": ("km", "kilometers", "kilometres", "kilometer", "kilometre"), "mi": ("mi", "miles", "mile"),
    "kg": ("kg", "kilograms", "kilogram", "kilos"), "lb": ("lb", "lbs", "pounds", "pound"),
    "m": ("m", "meters", "metres", "meter", "metre"), "ft": ("ft", "feet", "foot"),
    "cm": ("cm", "centimeters", "centimetres"), "in": ("in", "inches", "inch"),
    "g": ("g", "grams", "gram"), "oz": ("oz", "ounces", "ounce"),
    "l": ("l", "liters", "litres", "liter", "litre"), "gal": ("gal", "gallons", "gallon"),
}
_UNIT_OF = {w: u for u, ws in _UNIT_WORDS.items() for w in ws}
_CONVERT = {("F", "C"): lambda x: (x - 32) * 5 / 9, ("C", "F"): lambda x: x * 9 / 5 + 32,
            ("km", "mi"): lambda x: x / 1.609344, ("mi", "km"): lambda x: x * 1.609344,
            ("kg", "lb"): lambda x: x * 2.20462, ("lb", "kg"): lambda x: x / 2.20462,
            ("m", "ft"): lambda x: x * 3.28084, ("ft", "m"): lambda x: x / 3.28084,
            ("cm", "in"): lambda x: x / 2.54, ("in", "cm"): lambda x: x * 2.54,
            ("g", "oz"): lambda x: x / 28.3495, ("oz", "g"): lambda x: x * 28.3495,
            ("l", "gal"): lambda x: x / 3.78541, ("gal", "l"): lambda x: x * 3.78541}
_UNIT_RX = "|".join(sorted((re.escape(w) for w in _UNIT_OF), key=len, reverse=True))
_CONVERSION = re.compile(rf"(?i)(?<![\w.])(-?\d[\d,]*(?:\.\d+)?)\s*({_UNIT_RX})(?![a-z])\s*[(/]\s*(?:about\s+|approx\.?\s+|"
                         rf"approximately\s+|~|≈\s*)?(-?\d[\d,]*(?:\.\d+)?)\s*({_UNIT_RX})(?![a-z])\s*\)?")


def conversion_pairs(answer: str) -> list:
    """[(first, second, (from, to))] spans of "350°F (175°C)" or "5 km (3.1 miles)" where the second number
    is the first converted (within 3%, or 6 degrees for temperatures: 400°F is written 200°C)."""
    out = []
    for m in _CONVERSION.finditer(answer):
        u1, u2 = _UNIT_OF.get(m.group(2).lower().replace(" ", " ")), _UNIT_OF.get(m.group(4).lower())
        f = _CONVERT.get((u1, u2))
        if not f:
            continue
        x, y = float(m.group(1).replace(",", "")), float(m.group(3).replace(",", ""))
        tol = 6.0 if u1 in ("F", "C") else max(0.03 * abs(f(x)), 0.05)
        if abs(f(x) - y) <= tol:
            out.append(((m.start(1), m.end(1)), (m.start(3), m.end(3)), (u1, u2)))
    return out


def computed_from_question(n: Number, evidence: list, question_numbers: list):
    """(evidence number, question number, operator) when `n` is an evidence number times or divided by a
    whole count from the question (2 to 1000): "3 lamps" and price_usd 39.9 give 119.70. None otherwise."""
    counts = [q for q in question_numbers if q.integer and not q.percent and 2 <= q.value <= 1000]
    # a percentage is the fraction it stands for: "0.15%" is 0.0015, not 36 / 240
    targets = [(n.value / 100, n.tolerance / 100)] if n.percent else n.candidates(percent_as_fraction=False)
    for e in evidence:
        if e.source == "question" or not e.shown:
            continue
        for q in counts:
            for r, op in ((e.values[0] * q.value, "\u00d7"), (e.values[0] / q.value, "/")):
                if any(abs(c - r) <= t + 1e-9 * max(1.0, abs(r)) for c, t in targets):
                    return e, q, op
    return None


_DURATION = re.compile(r"(?i)\b(\d+)\s*(?:hours?|hrs?|h)\s*(?:and\s+)?(\d+)\s*(?:minutes?|mins?|min|m)\b"
                       r"|\b(\d+)\s*(?:days?|d)\s*(?:and\s+)?(\d+)\s*(?:hours?|hrs?|h)\b")


def duration_parts(answer: str, values: list) -> list:
    """[(start, end)] of "8 hours 55 minutes" or "2 days 4 hours" whose total, in the smaller unit, is one of
    `values` (535 minutes): the parts are the same quantity written another way."""
    out = []
    for m in _DURATION.finditer(answer):
        big, small, factor = (m.group(1), m.group(2), 60) if m.group(1) else (m.group(3), m.group(4), 24)
        total = int(big) * factor + int(small)
        if any(abs(v - total) < 1e-9 for v in values):
            out.append((m.start(), m.end()))
    return out


_TIME_12 = re.compile(r"(?i)(?<![\d:.])(\d{1,2})(?::(\d{1,2}))?\s*([ap])(?:\.\s?m\.|\s?m\b)")    # 2 pm, 2:30 p.m., 11:0 PM
_TIME_24 = re.compile(r"(?<![\d:.])(\d{1,2}):(\d{1,2})(?![\d:])")
_TIME_WORDS = {"noon": 720, "midday": 720, "midnight": 0}


def _minutes(m, twelve: bool):
    h, mm = int(m.group(1)), int(m.group(2) or 0)
    if mm > 59 or h > (12 if twelve else 24):
        return None
    if twelve:
        h = h % 12 + (12 if m.group(3).lower() == "p" else 0)
    return (h * 60 + mm) % 1440


def clock_times(text: str, twelve_only: bool = False) -> list:
    """[(start, end, minutes after midnight)] of the times in a text: "11:00 PM", "7 am", "23:0", "noon"."""
    out = [(m.start(), m.end(), t) for m in _TIME_12.finditer(text) if (t := _minutes(m, True)) is not None]
    taken = [(a, b) for a, b, _t in out]
    if not twelve_only:
        out += [(m.start(), m.end(), t) for m in _TIME_24.finditer(text) if (t := _minutes(m, False)) is not None
                and not any(a <= m.start() < b for a, b in taken)]
    out += [(m.start(), m.end(), _TIME_WORDS[m.group(0).lower()])
            for m in re.finditer(r"(?i)\b(?:noon|midday|midnight)\b", text)]
    return out


def check_numbers(answer: str, sources: list, question: str = "", *, percent_as_fraction: bool = True,
                  check_small_integers: bool = False, sentence_of=None,
                  evidence_name: str = "the sources or the question") -> tuple:
    """(findings, stats) for the numbers of `answer`. `sources` is [(id, text), ...]; `evidence_name`
    is how messages name the evidence ("the tool results or the question")."""
    texts = dict(sources)
    evidence = [e for sid, t in sources for e in evidence_numbers(sid, t, percent_as_fraction)]
    if question:
        texts["question"] = question
        evidence += evidence_numbers("question", question, percent_as_fraction)
    keep, left = answer_numbers(answer, check_small_integers)
    # clock times are checked as times: "11 pm" against "23:0"; their digits are not checked one by one
    ev_times = {t for _sid, text in sources for _a, _b, t in clock_times(text)}
    if question:
        ev_times |= {t for _a, _b, t in clock_times(question)}
    times = [(a, b, t) for a, b, t in clock_times(answer) if re.search(r"\d", answer[a:b])]
    findings, times_checked = [], 0
    if ev_times:
        for a, b, t in times:
            inside = [n for n in keep if a <= n.start < b]
            keep = [n for n in keep if not a <= n.start < b]
            times_checked += bool(inside)
            if t not in ev_times and inside:
                findings.append(Finding(
                    check="number", severity="high", start=a, end=b, text=answer[a:b],
                    sentence=sentence_of(a) if sentence_of else answer,
                    message=f"\"{answer[a:b].strip()}\" is not a time given in {evidence_name}.",
                    evidence=[], suggestion=None))
    supported = [n for n in keep + left if _supported(n, evidence, percent_as_fraction)]
    conversions = conversion_pairs(answer)
    durations = duration_parts(answer, [v for e in evidence for v in e.values] +
                               [n.value * n.scale for n in supported])
    supported += [n for n in keep if n not in supported and any(a <= n.start < b for a, b in durations)]
    question_numbers = find_numbers(question) if question else []
    derived, computed_n = 0, 0
    for n in keep:
        if n in supported:
            continue
        sentence = sentence_of(n.start) if sentence_of else answer
        if derived_from(n, supported, question_numbers, sentence):
            derived += 1
            continue
        pair = next(((a, b, u) for a, b, u in conversions if (n.start, n.end) in (a, b) or a[0] <= n.start < b[1]), None)
        if pair:
            a, b, (u1, u2) = pair
            other = a if b[0] <= n.start < b[1] else b
            partner = next((x for x in keep + left if x.start == other[0]), None)
            if b[0] <= n.start < b[1] or (partner is not None and partner in supported):
                # "350°F (175°C)": the bracketed number is the other converted; it is listed, as minor
                if partner is not None and partner in supported:
                    computed_n += 1
                    findings.append(Finding(
                        check="number", severity="low", start=n.start, end=n.end, text=n.text, sentence=sentence,
                        message=(f"\"{n.text.strip()}\" is not in {evidence_name}; it is {partner.text.strip()} "
                                 f"converted ({u1 if other == a else u2} to {u2 if other == a else u1}), "
                                 f"{COMPUTED_NOTE}."),
                        evidence=[], suggestion=None))
                    continue
                if b[0] <= n.start < b[1]:
                    continue            # neither is in the evidence: the first number is reported, not both
        computed = computed_from_question(n, evidence, question_numbers)
        if computed:
            computed_n += 1
            e, q, op = computed
            findings.append(Finding(
                check="number", severity="low", start=n.start, end=n.end, text=n.text, sentence=sentence,
                message=(f"\"{n.text.strip()}\" is not in {evidence_name}; it is {e.text} ({_where(e)}) {op} "
                         f"{q.text.strip()} (the question), {COMPUTED_NOTE}."),
                evidence=[{"source": e.source, "value": e.text, "context": _context(texts[e.source], e.start, e.end)}],
                suggestion=None))
            continue
        shown = n.text.strip()
        cut = _cut_short(n, evidence)
        if cut:
            e, v = cut
            right = _fmt_round(v, n)
            findings.append(Finding(
                check="number", severity="low", start=n.start, end=n.end, text=n.text, sentence=sentence,
                message=(f"\"{shown}\" looks like {e.text} ({_where(e)}) cut short: rounded to "
                         f"{n.decimals} decimal{'s' if n.decimals > 1 else ''} it is {right}."),
                evidence=[{"source": e.source, "value": e.text, "context": _context(texts[e.source], e.start, e.end)}],
                suggestion=_suggest(n, right)))
            continue
        near = _nearest(n, evidence, answer=answer, texts=texts)
        if near:
            closest = " or ".join(f"{e.text} ({_where(e)})" for e in near)
            message = f"\"{shown}\" is not in {evidence_name}. The closest values they give: {closest}."
        else:
            message = f"\"{shown}\" is not in {evidence_name}, and they give no value close to it."
        findings.append(Finding(
            check="number", severity="high", start=n.start, end=n.end, text=n.text, sentence=sentence,
            message=message,
            evidence=[{"source": e.source, "value": e.text, "context": _context(texts[e.source], e.start, e.end)}
                      for e in near]))
    stats = {"numbers_checked": len(keep) + times_checked, "numbers_not_checked": len(left), "numbers_derived": derived,
             "numbers_unsupported": sum(f.severity == "high" for f in findings),
             "numbers_cut_short": sum(f.severity == "low" for f in findings) - computed_n,
             "numbers_computed_in_answer": computed_n}
    return findings, stats


def _where(e: EvidenceNumber) -> str:
    return "the question" if e.source == "question" else e.source
