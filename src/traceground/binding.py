"""Binding checks: is each value attached to the right thing?

value-to-field  A number the answer attaches to a field name ("concurrence = 0.7", "7 rebounds",
                "a 4% chance of rain") must equal the value some tool result gives for a field of that
                name. Field names come from the JSON keys: "rain_chance_pct" is the words "rain chance"
                (unit suffixes such as _pct, _c, _kmh dropped), matched in any order; "monthly" matches
                "a month". Extra names: field_synonyms={"rain_chance_pct": ["precipitation"]}.
                Only results are checked; arguments with the same name count as support.

argument        The values the question gives must be the values the tools were called with:
                * a question number no call used, where a call used the same digits shifted by a power
                  of ten (asked p = 0.3, called with 0.03: the Kreout case);
                * a question number whose neighbouring word names an argument ("5-year" and "years")
                  that was called with another value (asked 5 years, called with years=3);
                * two values swapped between two calls (asked 120 USD and 80 GBP, called with
                  amount=80 and "USD", amount=120 and "GBP").

When a binding is unsure, nothing is reported: no field word right next to the number (a preposition
such as "for" or "on" starts a new phrase), a number that matches any of the fields its words name, a sentence
with "respectively", or a number written in another unit than the field's ("91.4 °F" for high_c).
A unit can also name the field: "weighs 249 kg" is compared with the results' only kg field, and
reported when 249 is another field of the same call; of several fields in that unit, the one whose word
is in the number's clause ("0.8 km from the train station" for station_km; "a night costs €142" for the
price field rate_eur), and minutes for keys such as delay_min ("running 12 minutes late").
A field named before the number wins over a list's field named after it ("an overall rating of 4.3
stars": rating, not the reviews' stars), and a list's field named for a number its whole holds, with the
list not mentioned, is not compared ("Harbor Noodle House (3.9 stars)" for the restaurant's rating). Also bound: a lone word that only one multi-word
field name has ("€789.52 in interest" for total_interest), the subject of "... is N" ("The total
interest you'll pay on the loan is $3,034.15"), and the two ends of a range ("between $69.80 and
$72.90" for day_low and day_high). A value another call worked out from the field (a calculator's
39.9 * 3) is not compared with the field, nor is a number whose clause says it is worked out ("the
difference in monthly payment is $166.03", but not "a guest rating of 142 is higher than ..."), nor one
the answer works out itself ("€426 for the rooms (3 × €142)"). A field's exact value written in another currency, with no
call that converted it, is reported ("€221.4 million" for net_income_musd). Values are compared as
magnitudes, like numbers ("down 1.2%" for a change of -1.2).
"""
import re

from traceground import numbers as num
from traceground.result import Finding
from traceground.traces import numeric_fields

_UNIT_WORDS = {"c", "f", "k", "pct", "percent", "perc", "kmh", "kph", "mph", "mps", "ms", "s", "sec", "secs", "min",
               "mins", "h", "hr", "hrs", "kg", "g", "lb", "lbs", "km", "m", "cm", "mm", "mi", "usd", "eur", "gbp",
               "inr", "jpy", "cny", "aud", "cad", "chf", "l", "ml", "w", "kw", "kwh", "v", "mb", "gb", "tb", "deg",
               "degc", "degf", "celsius", "fahrenheit", "hz", "khz", "mhz", "ghz", "ppm", "ppb", "hpa", "kpa", "pa",
               "mbar", "bar", "psi", "kcal", "cal", "kj", "mg", "mmhg", "db", "lux", "rpm", "mah", "wh", "musd",
               "meur", "mgbp", "kusd", "keur", "mn", "mln", "bn"}
_GENERIC = {"value", "values", "val", "result", "results", "data", "output", "input", "id", "ids", "index",
            "idx", "status", "code", "type", "name", "key", "n", "x", "y", "z", "arg", "args", "param", "params",
            "number", "num", "query", "text", "item", "items", "state", "count"}
# result fields that say when, not how much: a number is not compared with them ("year‑over‑year")
_WHEN_KEYS = {"year", "date", "timestamp", "time", "datetime"}
_IRREGULAR = {"monthly": "month", "weekly": "week", "daily": "day", "yearly": "year", "hourly": "hour",
              "annually": "year", "annual": "year"}
_LINKS = {"=", ":", "≈", "~", "is", "was", "are", "were", "of", "at", "to", "about", "around", "approximately",
          "approx", "roughly", "nearly", "falls", "fell", "rises", "rose", "drops", "dropped", "reaches", "reached",
          "equals", "equal", "stands", "comes", "becomes", "became", "remains", "be", "will", "would", "now", "by",
          "the", "a", "an", "its", "their", "has", "have", "had", "gives", "gave", "shows", "showed", "goes", "went",
          "increases", "increased", "decreases", "decreased", "climbs", "climbed", "totals", "totaled", "totalled"}
_FILLERS = {"of", "in", "a", "an", "the", "per", "for"}
_STOP_WORDS = {"and", "but", "while", "with", "against", "under", "over", "versus", "vs", "than", "or", "compared",
               "whereas", "so", "then"}
# going back from a number, these start a different phrase: "the monthly payment for a $30,000 loan"
# ("in" is not here: "the total paid in all was 32,126" names the field before it)
_BEFORE_STOP = {"for", "on", "from", "per", "after", "before", "during", "within", "into", "onto", "across",
                "via", "toward", "towards", "versus"}
_QUESTION_STOP = {"of", "the", "a", "an", "at", "for", "with", "and", "to", "in", "on", "is", "by", "my", "me", "i",
                  "what", "how", "much", "many", "if", "be", "will", "it", "its"}

_TIME_NOUNS = {"day", "days", "week", "weeks", "month", "months", "year", "years", "hour", "hours"}
_MIN_MAX = {"min": "minimum", "max": "maximum"}
_LOW_WORDS, _HIGH_WORDS = {"low", "min", "minimum", "lowest"}, {"high", "max", "maximum", "highest"}

_TOKEN = re.compile(r"[^\W\d_]+|[,;.!?()\n]|[=:≈~]")


def stem(word: str) -> str:
    w = word.lower()
    if w in _IRREGULAR:
        return _IRREGULAR[w]
    if w.endswith("ies") and len(w) > 4:
        return w[:-3] + "y"
    if w.endswith("ed") and len(w) >= 6 and not w.endswith("eed"):     # converted, earned: convert, earn
        return w[:-2]
    if w.endswith("s") and not w.endswith("ss") and len(w) > 3:
        return w[:-1]
    return w


def key_words(key: str) -> tuple:
    """'rain_chance_pct' -> ('rain', 'chance'); 'werner_weight' -> ('werner', 'weight'); generic keys -> ()."""
    parts = re.findall(r"[A-Z]?[a-z]+|[A-Z]+(?![a-z])|\d+", key)
    if any(p.lower() in _TIME_NOUNS for p in parts):      # days_min, days_max: minimum and maximum, not minutes
        parts = [_MIN_MAX.get(p.lower(), p) for p in parts]
    words = [stem(p) for p in parts if p.lower() not in _UNIT_WORDS and not p.isdigit()]
    if not words or all(w in _GENERIC for w in words):
        return ()
    return tuple(w for w in words if w not in _GENERIC) or tuple(words)


# ---------------------------------------------------------------- tokens of a text
def _items(text: str) -> list:
    """The text as an ordered list of ("num", Number) and ("tok", word-or-mark, start, end)."""
    nums = num.find_numbers(text)
    items = [("num", n, n.start, n.end) for n in nums]
    for m in _TOKEN.finditer(text):
        if not any(n.start <= m.start() < n.end for n in nums):
            items.append(("tok", m.group(0), m.start(), m.end()))
    return sorted(items, key=lambda it: it[2])


def _is_stop(tok: str) -> bool:
    return tok in ",;.!?()\n" or tok.lower() in _STOP_WORDS


def _words_after(items: list, i: int, k: int = 3) -> list:
    """Up to k content words after item i, stopping at punctuation, a conjunction or a number:
    [(stem, start, end)]."""
    out = []
    for kind, tok, a, b in items[i + 1:]:
        if kind == "num" or _is_stop(tok):
            break
        low = tok.lower()
        if low in _FILLERS or low in _UNIT_WORDS or not tok[0].isalpha():
            continue
        out.append((stem(tok), a, b))
        if len(out) == k:
            break
    return out


def _words_before(items: list, i: int, k: int = 3) -> list:
    """Up to k content words before item i (closest first), skipping link words ("is", "of", "=") and
    stopping at punctuation, a conjunction or a number."""
    out = []
    for j, (kind, tok, a, b) in enumerate(reversed(items[:i])):
        if j == 0 and tok == "(":          # "more points (31)": the bracket opens on the number itself
            continue
        if kind == "num" or _is_stop(tok) or tok.lower() in _BEFORE_STOP:
            break
        if tok.lower() in _LINKS or not (tok[0].isalpha() or tok in "=:≈~"):
            continue
        out.append((stem(tok), a, b))
        if len(out) == k:
            break
    return out


def _matching(words: list, fields: list, slack: int = 1) -> list:
    """Fields all of whose words are among the first len(words) + slack of `words`."""
    hits = []
    for f in fields:
        fw = f["words"]
        window = words[:len(fw) + slack]
        if fw and set(fw) <= {w for w, _a, _b in window}:
            span = [(a, b) for w, a, b in window if w in fw]
            hits.append((f, min(a for a, _b in span), max(b for _a, b in span)))
    return hits


# ---------------------------------------------------------------- value-to-field
def _fields(calls: list, synonyms: dict, which: str) -> list:
    out = []
    for c in calls:
        if c.error:
            continue
        obj = c.result if which == "result" else c.args
        for path, key, value in numeric_fields(obj):
            if which == "result" and key.lower() in _WHEN_KEYS:
                continue
            names = [key_words(key)] + [tuple(stem(w) for w in re.findall(r"[^\W\d_]+", s))
                                        for s in synonyms.get(key, [])]
            for words in names:
                if words:
                    out.append({"call": c, "path": path, "key": key, "value": value, "words": words, "kind": which})
    return out


_UNITS = {   # word or symbol -> (kind, unit)
    **{w: ("temperature", "C") for w in ("c", "celsius", "degc")}, **{w: ("temperature", "F") for w in ("f", "fahrenheit", "degf")},
    **{w: ("length", "km") for w in ("km", "kilometre", "kilometres", "kilometer", "kilometers")},
    **{w: ("length", "mi") for w in ("mi", "mile", "miles")}, **{w: ("length", "m") for w in ("m", "metre", "metres", "meter", "meters")},
    **{w: ("length", "ft") for w in ("ft", "foot", "feet")},
    **{w: ("mass", "kg") for w in ("kg", "kilogram", "kilograms")}, **{w: ("mass", "lb") for w in ("lb", "lbs", "pound", "pounds")},
    **{w: ("mass", "g") for w in ("g", "gram", "grams")},
    **{w: ("money", "USD") for w in ("usd", "$", "dollar", "dollars")}, **{w: ("money", "EUR") for w in ("eur", "€", "euro", "euros")},
    **{w: ("money", "GBP") for w in ("gbp", "£", "pound sterling")}, **{w: ("money", "INR") for w in ("inr", "₹", "rupee", "rupees")},
    **{w: ("money", "JPY") for w in ("jpy", "¥", "yen")}, **{w: ("money", "CHF") for w in ("chf", "franc", "francs")},
    **{w: ("speed", "kmh") for w in ("kmh", "kph", "km/h")}, **{w: ("speed", "mph") for w in ("mph",)},
    **{w: ("time", "hour") for w in ("hour", "hours", "hr", "hrs")},
    **{w: ("time", "minute") for w in ("minute", "minutes", "mins")}, **{w: ("time", "day") for w in ("day", "days")},
    **{w: ("time", "week") for w in ("week", "weeks")}, **{w: ("time", "month") for w in ("month", "months")},
    **{w: ("time", "year") for w in ("year", "years")},
}
_AFTER_UNIT = re.compile(r"\s?(?:°\s?(?P<deg>[CF])\b|(?P<word>km/h|[A-Za-z]+))")


def answer_unit(answer: str, n: num.Number):
    """(kind, unit) written right after the number ("91.4 °F", "42.16 km") or right before it ("$249")."""
    m = _AFTER_UNIT.match(answer, n.end)
    if m:
        w = (m.group("deg") or m.group("word")).lower()
        if w in _UNITS:
            return _UNITS[w]
    before = answer[max(0, n.start - 1):n.start]
    return _UNITS.get(before)


def key_unit(key: str):
    """(kind, unit) of a JSON key's unit suffix: high_c -> temperature C, price_usd -> money USD."""
    parts = re.findall(r"[A-Za-z]+", key.replace("_", " "))
    if len(parts) < 2:
        return None
    last = parts[-1].lower()
    if last not in _UNITS and len(last) == 4 and last[0] in "mkb":       # musd, keur, bgbp: scale + currency
        last = last[1:]
    # delay_min, duration_min: minutes; days_min, days_max: a minimum of days, not minutes
    if last in ("min", "mins") and not any(p.lower() in _TIME_NOUNS for p in parts):
        return ("time", "minute")
    return _UNITS.get(last)


def _hit(n: num.Number, f: dict) -> bool:
    """n states field f's value, also at the scale its key names (revenue_musd 1840.5 as "1.84 billion")."""
    scale = num.key_scale(f["key"])
    return _matches(n, f["value"]) or (scale != 1 and _matches(n, f["value"] * scale))


def _matches(n: num.Number, value: float) -> bool:
    """Magnitudes, as in the number check: "down 1.2%" for a change of -1.2."""
    return any(num._close(c, t, abs(value)) for c, t in n.candidates())


_COPULA = {"is", "was", "are", "were", "be"}
_APPROX_WORDS = {"about", "around", "approximately", "approx", "roughly", "nearly", "some", "just", "only",
                 "exactly", "almost", "the", "a", "an"}
# a subject with one of these names a quantity worked out from a field, not the field itself
_COMPUTED = {"difference", "gap", "increase", "decrease", "growth", "saving", "extra", "ratio", "average", "mean",
             "combined", "sum", "half", "double", "twice", "remaining", "per", "each"}


_COMPARATIVE = {"higher", "lower", "more", "less", "fewer", "warmer", "cooler", "colder", "hotter", "cheaper",
                "dearer", "longer", "shorter", "bigger", "smaller", "greater", "larger", "apart", "than", "extra",
                "difference", "faster", "slower", "heavier", "lighter"}
_YEAR_PREPS = {"in", "of", "for", "since", "from", "until", "till", "by", "during", "to", "before", "after"}


def _computed_clause(items: list, i: int) -> bool:
    """The number is worked out, not a field's value: the clause before it says so ("the difference in
    monthly payment is $166") or a comparative follows it ("3.3 hPa higher than", "7 °C warmer")."""
    for kind, tok, _a, _b in reversed(items[:i]):
        if kind == "tok" and tok in ",;.!?\n":
            break
        if kind == "tok" and stem(tok) in _COMPUTED:
            return True
    for kind, tok, _a, _b in items[i + 1:i + 4]:
        if kind == "num" or (kind == "tok" and (tok in ",;.!?\n" or tok.lower() in _COPULA)):
            break           # "a guest rating of 142 is higher than ...": the comparison is of the field's value
        if tok.lower() in _COMPARATIVE:
            return True
    return False


def _a_year(items: list, i: int, when_values=()) -> bool:
    """ "in 2024", "from 2024 to 2025", "a 2025 revenue": a plain whole number from 1900 to 2100 after such a
    word, or equal to a year the calls give, is a year."""
    n = items[i][1]
    if not (n.integer and 1900 <= n.value <= 2100):
        return False
    if any(abs(n.value - v) < 1e-9 for v in when_values):
        return True
    prev = next((t for t in reversed(items[:i]) if t[0] == "num" or t[1] not in "*_"), None)
    return prev is not None and prev[0] == "tok" and prev[1].lower() in _YEAR_PREPS
_SUBJECT_END = _BEFORE_STOP | {"of", "at", "in", "over", "with", "under", "by", "if", "when", "after", "than"}
_RATE_WORDS = ("pct", "percent", "rate", "margin", "ratio", "share")


def _key_ok(n: num.Number, key: str) -> bool:
    """A percentage is tied by a lone word only to a field that may hold one ("margin_pct", "rate")."""
    return not n.percent or any(w in key.lower() for w in _RATE_WORDS)


def _one_field(cands: list):
    """The field the candidates name, if they name one: the key with the most words, when no other key has as
    many. [(field, start, end)] for every call that has that key, or []."""
    if not cands:
        return []
    most = max(len(f["words"]) for f, _a, _b in cands)
    keys = {f["key"] for f, _a, _b in cands if len(f["words"]) == most}
    return [c for c in cands if c[0]["key"] in keys] if len(keys) == 1 else []


# measure nouns name what is counted, not which field: "after 3 years" is not warranty_years
_MEASURE = {"year", "month", "week", "day", "hour", "minute", "second", "time", "unit", "item", "piece", "people",
            "person", "point", "dollar", "euro", "rupee", "pound", "cent", "night", "seat", "share", "km", "mile",
            "meter", "metre", "gram", "kilo", "litre", "liter", "degree", "percent", "percentage", "number", "total",
            "amount", "value", "level", "count"}


def _distinctive(word, results: list, n, a: int, b: int) -> list:
    """A lone word next to the number that only one multi-word field name has: "€789.52 in interest" when
    total_interest is the only field with "interest" ("total" alone fits total_paid as well; measure nouns
    such as "years" never name a field on their own)."""
    if not word or word in _MEASURE:
        return []
    cands = [(f, a, b) for f in results if word in f["words"]]
    keys = {f["key"] for f, _a, _b in cands}
    if len(keys) != 1 or len(cands[0][0]["words"]) < 2 or not _key_ok(n, cands[0][0]["key"]):
        return []
    return cands


def _after_copula(items: list, i: int) -> bool:
    """The number comes right after "is", "was", ... and the word before that verb ends a phrase that starts
    with a preposition: "the rating for this business according to customer reviews is 3.5", where
    "reviews" is not what the number is."""
    j = i - 1
    while j >= 0 and items[j][0] == "tok" and (items[j][1].lower() in _APPROX_WORDS or items[j][1] in "($*"):
        j -= 1
    if not (j >= 0 and items[j][0] == "tok" and items[j][1].lower() in _COPULA):
        return False
    for kind, tok, _a, _b in reversed(items[:j]):
        if kind == "num" or not (tok[0].isalpha() or tok[0] in "'’"):
            return False
        if tok.lower() in _SUBJECT_END or tok.lower() in ("to", "according"):
            return True
    return False


def _subject(items: list, i: int, results: list, n) -> list:
    """"The total interest you'll pay on a $15,000 loan ... is $300.57": a number right after "is" or "was"
    is the value of the sentence's subject, the words from the sentence start up to a preposition."""
    j = i - 1
    while j >= 0 and items[j][0] == "tok" and (items[j][1].lower() in _APPROX_WORDS or items[j][1] in "($*"):
        j -= 1
    if j < 0 or items[j][0] != "tok" or items[j][1].lower() not in _COPULA:
        return []
    k = j
    while k > 0 and not (items[k - 1][0] == "tok" and items[k - 1][1] in ".!?\n:;"):
        k -= 1
    words = []
    for kind, tok, a, b in items[k:j]:
        if kind == "num" or _is_stop(tok) or tok.lower() in _SUBJECT_END:
            break
        if tok[0].isalpha():
            words.append((stem(tok), a, b))
    if any(w in _COMPUTED for w, _a, _b in words):
        return []
    cands = [c for c in _matching(words, results, slack=len(words)) if _key_ok(n, c[0]["key"])]
    return _one_field(cands)


_RANGE_CUE = {"between", "from", "range", "ranging", "ranges", "spans"}


def _range_pairs(results: list) -> list:
    """[(low fields, high fields)] of result fields whose names differ only by low/high or min/max:
    day_low and day_high, days_min and days_max (for every call that has them)."""
    pairs = []
    for f in results:
        lo = set(f["words"]) & _LOW_WORDS
        if not lo or f["words"] == tuple(lo):
            continue
        rest = set(f["words"]) - lo
        for g in results:
            hi = set(g["words"]) & _HIGH_WORDS
            if g["call"] is f["call"] and hi and set(g["words"]) - hi == rest:
                lows = [x for x in results if x["key"] == f["key"]]
                highs = [x for x in results if x["key"] == g["key"]]
                if (lows, highs) not in pairs:
                    pairs.append((lows, highs))
    return pairs


def _ranges(items: list, answer: str, results: list) -> dict:
    """{item index: [(field, start, end)]} for the two numbers of a range ("between $69.80 and $72.90",
    "a trading range of $69.80 to $72.90", "6-10 days") when the results have exactly one low/high pair."""
    pairs = _range_pairs(results)
    if len(pairs) != 1:
        return {}
    lows, highs = pairs[0]
    out = {}
    for i, (kind, n, a, b) in enumerate(items):
        if kind != "num":
            continue
        j = i + 1
        dash = j < len(items) and items[j][0] == "num" and re.fullmatch(r"\s*[-\u2010-\u2014]\s*", answer[b:items[j][2]])
        word = (j + 1 < len(items) and items[j][0] == "tok" and items[j][1].lower() in ("to", "and")
                and items[j + 1][0] == "num")
        if not (dash or word):
            continue
        k = j if dash else j + 1
        before = [t[1].lower() for t in items[max(0, i - 6):i] if t[0] == "tok"]
        if not dash and not (_RANGE_CUE & set(before)):
            continue
        hi_n = items[k][1]
        out[i] = [(f, n.start, hi_n.end) for f in lows]
        out[k] = [(f, n.start, hi_n.end) for f in highs]
    return out


def list_counts(calls: list) -> list:
    """[(word, length)] for every list in the calls' results: {"reviews": [..3 items..]} gives ("review", 3)."""
    out = []

    def walk(obj):
        if isinstance(obj, dict):
            for k, v in obj.items():
                if isinstance(v, list):
                    for w in key_words(str(k)) or ():
                        out.append((w, len(v)))
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)
    for c in calls:
        walk(c.result)
    return out


def _near_words(items: list, i: int) -> set:
    """The words within six tokens before and three after item i, inside its sentence."""
    near = set()
    for step, stop in ((-1, max(-1, i - 7)), (1, min(len(items), i + 4))):
        for kind, tok, _a, _b in (items[j] for j in range(i + step, stop, step)):
            if kind == "tok" and tok in ".!?\n;":
                break
            if kind == "tok" and tok[0].isalpha():
                near.add(stem(tok))
    return near


# words that stand for a price whichever field holds it: "a night costs €142" for rate_eur
_PRICE_WORDS = {"cost", "costs", "costing", "price", "priced", "rate", "fee", "fare", "charge", "charged"}


def _list_words(path: str) -> set:
    """The words of the list a field belongs to: "reviews[0].stars" -> {"review"}; set() for a field not in a list."""
    return {w for part in re.findall(r"([A-Za-z_]+)\[", path) for w in key_words(part)}


def _segment_words(items: list, i: int, step: int) -> set:
    """The words from item i to the next number (step 1) or the previous one (step -1), within its clause
    (up to a comma, a full stop, "and", "but" ...)."""
    out, j = set(), i + step
    while 0 <= j < len(items):
        kind, tok, _a, _b = items[j]
        if kind == "num" or _is_stop(tok):
            break
        if tok[0].isalpha():
            out.add(stem(tok))
        j += step
    return out


def check_value_to_field(answer: str, calls: list, *, field_synonyms=None, sentence_of=None, worked_out=()) -> tuple:
    synonyms = field_synonyms or {}
    results = _fields(calls, synonyms, "result")
    args = _fields(calls, synonyms, "args")
    if not results:
        return [], {"bindings_checked": 0, "bindings_wrong": 0}
    items = _items(answer)
    question_values = [(c, v) for c in calls for _k, v in _arg_values(c)]
    in_range = _ranges(items, answer, results)
    counts = list_counts(calls)
    counted = {w for w, _n in counts}
    when_values = [float(v) for c in calls for obj in (c.args, c.result) if isinstance(obj, dict)
                   for k, v in obj.items() if k.lower() in _WHEN_KEYS and isinstance(v, (int, float))
                   and not isinstance(v, bool)]
    when_values += [float(y) for c in calls for y in re.findall(r"(?<!\d)((?:19|20)\d\d)-\d\d-\d\d", c.render())]
    skip = num.excluded_spans(answer)
    # "high and low are 9 and 4 respectively": the pairing is by position, not by neighbouring words
    skip += [(m.start(), m.end()) for m in re.finditer(r"[^.!?\n]*\brespectively\b[^.!?\n]*", answer, re.I)]
    used_words = set()
    findings, checked = [], 0
    rendered = " ".join(re.sub(r"\s+", " ", c.render().lower()) for c in calls)
    for i, (kind, n, _a, _b) in enumerate(items):
        if kind != "num" or any(a <= n.start < b for a, b in skip):
            continue
        # "€426 for the rooms (3 × €142)": a number the answer works out itself is not a field's value
        if any(a <= n.start < b for a, b in worked_out):
            continue

        # "4 Eggs & Pizza", "223 Anacapa St": the number with its next or previous word is text in a result
        # (a name, an address), not a value of a field
        nxt = re.match(r"[°'’]?\s+[A-Za-z][\w'’]*", answer[n.end:])
        prv = re.search(r"[A-Za-z][\w'’]*\s+$", answer[max(0, n.start - 40):n.start])
        if (nxt and (n.text.strip() + nxt.group()).lower() in rendered) or \
                (prv and (prv.group() + n.text.strip()).lower() in rendered):
            continue
        after_words = _words_after(items, i)
        after = _matching(after_words, results, slack=0)      # "7 rebounds": the name follows at once
        if after:              # "3 years at 7%": the words a number takes after it are not the next number's
            used_words.update((a2, b2) for _w, a2, b2 in after_words)
        before_words = [w for w in _words_before(items, i) if (w[1], w[2]) not in used_words]
        if (_computed_clause(items, i) and i not in in_range) or _a_year(items, i, when_values):
            continue
        if after_words and after_words[0][0] in counted:
            continue                # "based on 3 reviews": how many items a list has, not a field in it
        if before_words and (before_words[0][0], n.value) in counts:
            continue                # "Number of reviews: 3", and the list has 3 items
        named_before = _matching(before_words, results)
        if after and i not in in_range and any(_hit(n, f) for f, _a, _b in named_before) \
                and not any(_hit(n, f) for f, _a, _b in after):
            continue                # "an overall rating of 4.3 stars": rating holds it; "stars" is what it counts
        # "an overall rating of 3 stars": "stars" after the number is the reviews' stars, but the field named
        # before it (rating, not in a list) is what the number is, when the reviews are not mentioned
        if after and i not in in_range and all("[" in f["path"] for f, _a, _b in after) \
                and any("[" not in f["path"] for f, _a, _b in named_before) \
                and not any(_list_words(f["path"]) & _near_words(items, i) for f, _a, _b in after):
            after = []
        bound = in_range.get(i) or after or named_before
        unit = answer_unit(answer, n)
        if unit and unit[0] == "money":
            # "€221.4 million" for net_income_musd = 221.4: the right number in another currency, and no call
            # converted it
            for f, a2, b2 in bound:
                fu = key_unit(f["key"])
                if fu and fu[0] == "money" and fu != unit and _hit(n, f) and not any(
                        g is not f["call"] and any(abs(v - f["value"]) < 1e-9 for _k, v in _arg_values(g))
                        for g in calls):
                    start, end = min(n.start, a2), max(n.end, b2)
                    findings.append(Finding(
                        check="value-to-field", severity="high", start=start, end=end, text=answer[start:end],
                        sentence=sentence_of(start) if sentence_of else answer,
                        message=(f"\"{answer[start:end]}\": the tool results give {f['key']} = {_fmt(f['value'])} "
                                 f"({f['call'].id}) in {fu[1]}; the answer writes {unit[1]}, and no call converted it."),
                        evidence=[{"source": f["call"].id, "value": f"{f['path']} = {_fmt(f['value'])}",
                                   "context": f["call"].render()}]))
                    checked += 1
                    break
            if findings and findings[-1].start <= n.start < findings[-1].end:
                continue
        if unit:               # "91.4 °F" against high_c: another unit, so the values cannot be compared
            bound = [(f, a, b) for f, a, b in bound
                     if not (key_unit(f["key"]) and key_unit(f["key"])[0] == unit[0] and key_unit(f["key"]) != unit)]
        if not bound and unit:  # "weighs 249 kg": the only kg field of the results names the value
            same_unit = [f for f in results if key_unit(f["key"]) == unit]
            if len({(id(f["call"]), f["key"]) for f in same_unit}) > 1:
                # "0.8 km from the nearest train station": of station_km and airport_km, the one whose word
                # comes after the number (before the next number), or else before it
                for side in (_segment_words(items, i, 1), _segment_words(items, i, -1)):
                    named = [f for f in same_unit if set(f["words"]) & side]
                    if not named and unit[0] == "money" and side & _PRICE_WORDS:
                        named = [f for f in same_unit if set(f["words"]) & _PRICE_WORDS]   # "costs €16": rate
                    if named:
                        same_unit = named
                        break
            if len({(id(f["call"]), f["key"]) for f in same_unit}) == 1:
                f = same_unit[0]
                # only a value of another field of that same call is reported: "$1.35" when weight_kg is 1.35
                swapped = any(g["call"] is f["call"] and g["key"] != f["key"] and _hit(n, g)
                              for g in results)
                if _hit(n, f) or swapped:
                    bound = [(f, n.start, n.end)]
        if not bound and not any(_matches(n, v) for _c, v in question_values):
            # a lone distinctive word right after or right before the number, or the subject of "... is N"
            after1 = after_words[0] if after_words else None
            before1 = before_words[0] if before_words else None
            # "the rating for this business according to customer reviews is 3.5": after "is", the subject
            # names the field, not the word just before "is"
            if _after_copula(items, i):
                before1 = None
            bound = (_distinctive(after1 and after1[0], results, n, *(after1[1:] if after1 else (0, 0)))
                     or _distinctive(before1 and before1[0], results, n, *(before1[1:] if before1 else (0, 0)))
                     or _subject(items, i, results, n))
            if bound and unit:
                bound = [(f, a, b) for f, a, b in bound if not (key_unit(f["key"]) and key_unit(f["key"]) != unit)]
        if not bound:
            continue
        same_name = [f for f, _a, _b in bound]
        # "the price is $119.70" when a calculator turned price_usd 39.9 into 119.7: a value worked out by
        # another call from the field is not the field's
        if any(g["call"] is not f["call"] and _hit(n, g) and
               any(abs(v - f["value"]) < 1e-9 for _k, v in _arg_values(g["call"]))
               for f in same_name for g in results):
            continue
        checked += 1
        names = {f["words"] for f in same_name}
        support = same_name + [f for f in args if f["words"] in names]
        if any(_hit(n, f) for f in support):
            continue
        # "One review gave it 1 star": a more specific field (review_stars) whose other words are close to the
        # number, and which holds it, is the one meant
        near = _near_words(items, i)
        if any(set(f["words"]) < set(g["words"]) and set(g["words"]) - set(f["words"]) <= near and _hit(n, g)
               for f in same_name for g in results):
            continue
        # "This customer gave the business a 5-star rating": one review's review_stars, said of the business
        # (business_stars), or the other way round. When the field that holds the number and the field named
        # share the word near the number ("star"), and one is a field of a list's items and the other is not,
        # the wording does not tell which is meant
        if any(_hit(n, g) and set(f["words"]) & set(g["words"]) & near and ("[" in f["path"]) != ("[" in g["path"])
               for f in same_name for g in results):
            continue
        # "Harbor Noodle House (3.9 stars)": "stars" names the reviews' stars, but the restaurant's own rating
        # (same call, not in a list) holds 3.9 and the reviews are not mentioned near the number
        if any(_hit(n, g) and g["call"] is f["call"] and "[" in f["path"] and "[" not in g["path"]
               and not _list_words(f["path"]) & near for f in same_name for g in results):
            continue
        start = min(n.start, min(a for _f, a, _b in bound))
        end = max(n.end, max(b for _f, _a, b in bound))
        gave = "; ".join(f"{f['key']} = {_fmt(f['value'])} ({f['call'].id})" for f in same_name)
        other = next((f for f in results + args if f["words"] not in names and _hit(n, f)), None)
        shown = n.text.strip()
        message = f"\"{answer[start:end]}\": the tool results give {gave}."
        if other:
            message += f" {shown} is the {other['key']} ({other['call'].id})."
        findings.append(Finding(
            check="value-to-field", severity="high", start=start, end=end, text=answer[start:end],
            sentence=sentence_of(start) if sentence_of else answer, message=message,
            evidence=[{"source": f["call"].id, "value": f"{f['path']} = {_fmt(f['value'])}", "context": f["call"].render()}
                      for f in same_name]))
    return findings, {"bindings_checked": checked, "bindings_wrong": len(findings)}


def _fmt(v: float) -> str:
    return str(int(v)) if v == int(v) and abs(v) < 1e15 else repr(v)


# ---------------------------------------------------------------- argument binding
def _arg_values(call) -> list:
    """[(arg name, value as float)] of a call: numeric args and the numbers written inside string args."""
    out = []

    def walk(name, v):
        if isinstance(v, bool) or v is None:
            return
        if isinstance(v, (int, float)):
            out.append((name, float(v)))
        elif isinstance(v, str):
            for n in num.find_numbers(v):
                out.extend((name, c) for c, _t in n.candidates())
            out.extend((name, float(m.group(0))) for m in num._ANY_DIGITS.finditer(v))
        elif isinstance(v, dict):
            for k, x in v.items():
                walk(k, x)
        elif isinstance(v, list):
            for x in v:
                walk(name, x)
    for k, v in call.args.items():
        walk(k, v)
    return out


def _strings(call) -> list:
    out = []

    def walk(v):
        if isinstance(v, str):
            out.append(v.casefold())
        elif isinstance(v, dict):
            for x in v.values():
                walk(x)
        elif isinstance(v, list):
            for x in v:
                walk(x)
    walk(call.args)
    return out


def _neighbours(items: list, i: int, claimed: set) -> tuple:
    """(words right after the number, words right before it): up to 2 each, small words left out, and
    before it only words that the number before has not taken ("3-year loan at 7%": "year" is the 3's)."""
    def pick(seq):
        out = []
        for kind, tok, a, b in seq:
            if kind == "num" or tok in ",;.!?()\n":
                break
            if tok.lower() in _QUESTION_STOP or not tok[0].isalpha() or (a, b) in claimed:
                continue
            out.append((tok, a, b))
            if len(out) == 2:
                break
        return out
    after = pick(items[i + 1:])
    before = pick(reversed(items[:i]))
    claimed.update((a, b) for _t, a, b in after)
    return [t for t, _a, _b in after], [t for t, _a, _b in before]


def _shifted(q: float, v: float) -> bool:
    if q == 0 or v == 0 or q == v:
        return False
    r = v / q
    return any(abs(r - f) <= 1e-9 * f for f in (10.0, 100.0, 1000.0, 0.1, 0.01, 0.001))


def _answer_span(answer: str, q: num.Number, spans_of_sentences) -> tuple:
    """Where in the answer to point: the first number equal to the question's, else the first sentence."""
    for n in num.find_numbers(answer):
        if any(num._close(c, t, q.value) for c, t in n.candidates()):
            return n.start, n.end
    a, b = spans_of_sentences[0] if spans_of_sentences else (0, len(answer))
    return a, b


def check_arguments(answer: str, question: str, calls: list, *, sentence_spans=(), sentence_of=None) -> tuple:
    calls = [c for c in calls if c.args]
    if not question.strip() or not calls:
        return [], {"question_values": 0, "arguments_wrong": 0}
    items = _items(question)
    skip = num.excluded_spans(question)
    qnums = [(i, it[1]) for i, it in enumerate(items) if it[0] == "num" and not any(a <= it[1].start < b for a, b in skip)]
    argvals = {c.id: _arg_values(c) for c in calls}
    findings = []

    def used(q, call=None):
        pool = [argvals[call.id]] if call else argvals.values()
        return any(any(num._close(c, t, abs(v)) for c, t in q.candidates()) for vals in pool for _name, v in vals)

    def report(q, message, evidence_calls):
        a, b = _answer_span(answer, q, list(sentence_spans))
        findings.append(Finding(
            check="argument", severity="high", start=a, end=b, text=answer[a:b],
            sentence=sentence_of(a) if sentence_of else answer, message=message,
            evidence=[{"source": c.id, "value": "", "context": c.render()} for c in evidence_calls]))

    reported, claimed, neighbours = set(), set(), {}
    for i, _q in qnums:
        neighbours[i] = _neighbours(items, i, claimed)
    for i, q in qnums:
        after, before = neighbours[i]
        near = {stem(w) for w in after + before}
        # (b) a neighbouring word names an argument that was called with another value
        named = [(c, name, v) for c in calls for name, v in argvals[c.id]
                 if near & set(key_words(name)) and _key_ok(q, name)]      # "4% compounded" is not compounds_per_year
        if named and not any(any(num._close(c2, t, abs(v)) for c2, t in q.candidates()) for _c, _n, v in named):
            # the argument the words name best: "5-year" names years before annual_rate ("annual" is yearly too)
            c, name, v = min(named, key=lambda x: (-len(near & set(key_words(x[1]))) / len(key_words(x[1])),
                                                   len(key_words(x[1]))))
            word = next(w for w in after + before if stem(w) in set(key_words(name)))
            a, b = q.start, q.end
            for m in re.finditer(rf"(?<!\w){re.escape(word)}(?!\w)", question):
                if abs(m.start() - q.end) < 15 or abs(q.start - m.end()) < 15:
                    a, b = min(a, m.start()), max(b, m.end())
                    break
            report(q, f"The question asks for {question[a:b]}, but {c.id} was called with {name}={_fmt(v)}.", [c])
            reported.add(i)
            continue
        if used(q):
            continue
        # (a) the same digits shifted by a power of ten
        shifted = [(c, name, v) for c in calls for name, v in argvals[c.id] if _shifted(q.value, abs(v))]
        if shifted:
            c, name, v = shifted[0]
            report(q, f"The question asks for {q.text.strip()}, but {c.id} was called with {name}={_fmt(v)}.", [c])
            reported.add(i)
    # (c) two values swapped between two calls
    tags = {}
    for i, q in qnums:
        after, before = neighbours[i]
        tag = (after or before or [None])[0]
        if tag:
            tags[i] = (q, tag.casefold())
    pairs = list(tags.items())
    for x in range(len(pairs)):
        for y in range(x + 1, len(pairs)):
            (i, (q1, t1)), (j, (q2, t2)) = pairs[x], pairs[y]
            if t1 == t2 or i in reported or j in reported:
                continue
            with_q1 = [c for c in calls if used(q1, c)]
            with_q2 = [c for c in calls if used(q2, c)]

            def has(c, tag):
                return any(re.search(rf"(?<!\w){re.escape(tag)}(?!\w)", s) for s in _strings(c))
            right = any(has(c, t1) for c in with_q1) or any(has(c, t2) for c in with_q2)
            swapped = any(has(c, t2) for c in with_q1) and any(has(c, t1) for c in with_q2)
            if swapped and not right:
                c1 = next(c for c in with_q1 if has(c, t2))
                c2 = next(c for c in with_q2 if has(c, t1))
                report(q1, f"The question pairs {q1.text.strip()} with {t1.upper() if len(t1) <= 4 else t1} and "
                           f"{q2.text.strip()} with {t2.upper() if len(t2) <= 4 else t2}, but the calls swap them: "
                           f"{c1.render().split(' returned')[0]} and {c2.render().split(' returned')[0]}.", [c1, c2])
                reported.update((i, j))
    return findings, {"question_values": len(qnums), "arguments_wrong": len(findings)}
