"""mutate.py - plant grounding errors in real answers that were checked by hand and found correct, and
count how many traceground reports.

    python mutate.py                       # every run in runs/
    python mutate.py runs\\2026-11-17_groq_openai-gpt-oss-20b.jsonl
    python mutate.py --set heldout         # every run in runs\\heldout, into mutations_heldout_<date>.md

The errors are planted, not made by a model: what this measures is how often traceground reports an
error of a known kind in real wording, not how often models make such errors. Each answer's final text
is changed in one place, and nothing else in the chat (question, calls, results) is changed:

  digits swapped         two neighbouring digits of a number swapped        892.41 -> 892.14
  last digit off by one  the last digit of a number one higher or lower     469.70 -> 469.71
  value of another field a number replaced by another field of its result  469.70 -> 2,545.63
  two values swapped     two numbers of one sentence, of different fields  27 points, 11 rebounds -> 11 points, 27 rebounds
  fraction as percent    a percentage divided by 100, as if 0.522 were %   52.2% -> 0.522%

Only answers that are correct by hand (hand_labels.json lists the wrong ones) and that traceground
passes ("ok") are used, so every report on a changed answer comes from the planted error. A planted
error is "caught" when a high-severity finding covers the changed text, "flagged elsewhere" when the
answer is reported but not at the changed text, and "missed" otherwise. Writes
results/mutations_<date>.md and .json; every miss is listed for review by hand.
"""
import argparse
import glob
import json
import re
import sys
from datetime import datetime
from pathlib import Path

from run_eval import SETS
from traceground import check_messages
from traceground.numbers import answer_numbers
from traceground.textnorm import sentence_spans

HERE = Path(__file__).resolve().parent
KINDS = ["digits swapped", "last digit off by one", "value of another field", "two values swapped",
         "fraction as percent"]
MAX_FIELDS_PER_NUMBER = 2      # "value of another field": at most this many replacements for one number
MAX_SWAPS_PER_ANSWER = 3
_DIGITS = re.compile(r"\d[\d,   ]*(?:\.\d+)?")


def load_wrong(path: Path = HERE / "hand_labels.json") -> set:
    """(model, id) of the answers found wrong by hand."""
    if not path.exists():
        return set()
    data = json.loads(path.read_text(encoding="utf-8"))
    return {(w["model"], w["id"]) for w in data.get("wrong", [])}


def records(paths: list) -> list:
    out = []
    for path in paths:
        latest = {}
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                latest[rec["id"]] = rec
        out += [dict(r, run=Path(path).name) for r in latest.values() if not r.get("error") and r.get("answer")]
    return out


def result_fields(messages: list) -> list:
    """[(call, key, value)] of every number in the tool results (JSON objects); call is "name (call id)"."""
    names = {}
    for m in messages:
        for tc in m.get("tool_calls") or []:
            names[tc["id"]] = tc["function"]["name"]
    out = []
    for m in messages:
        if m.get("role") != "tool":
            continue
        try:
            data = json.loads(m.get("content") or "")
        except ValueError:
            continue
        if isinstance(data, dict):
            call = f"{names.get(m.get('tool_call_id'), '?')} ({m.get('tool_call_id')})"
            out += [(call, k, float(v)) for k, v in data.items()
                    if isinstance(v, (int, float)) and not isinstance(v, bool)]
    return out


def _field_of(n, fields: list):
    """The (call, key, value) whose value the number states, if any (52.2% states 0.522)."""
    for f in fields:
        if any(abs(c - f[2]) <= t + 1e-9 for c, t in n.candidates(percent_as_fraction=True)):
            return f
    return None


def _numeric_part(n) -> tuple:
    """(start, end) of the digits of number n in the answer: "$1,234.50" -> the "1,234.50"."""
    m = _DIGITS.search(n.text)
    return n.start + m.start(), n.start + m.end()


def _fmt(value: float, like: str) -> str:
    """`value` as the model would copy it from the results (its own decimals: 1.05, 36), with the
    thousands separator of `like`."""
    text = repr(value)
    decimals = 0 if value == int(value) else len(text.split(".")[1]) if "." in text and "e" not in text else 2
    sep = "," if "," in like else next((c for c in "   " if c in like), "")
    s = f"{value:,.{decimals}f}"
    return s.replace(",", sep) if sep != "," else s


_DATE = re.compile(r"\b\d{4}[-\u2010-\u2014/.]\d{1,2}[-\u2010-\u2014/.]\d{1,2}\b")


def mutations(answer: str, fields: list) -> list:
    """[(kind, new answer, [(start, end) of the changed text in the new answer], what changed)]. Numbers
    inside a date (2026-11-16) are left alone: changing them is not a wrong value of a field."""
    dates = [(m.start(), m.end()) for m in _DATE.finditer(answer)]
    keep = [n for n in answer_numbers(answer)[0] if not any(a <= n.start < b for a, b in dates)]
    out = []

    def one(kind, a, b, new, what):
        out.append((kind, answer[:a] + new + answer[b:], [(a, a + len(new))], what))

    for n in keep:
        a, b = _numeric_part(n)
        digits = [i for i in range(a, b) if answer[i].isdigit()]
        old = answer[a:b]
        # digits swapped: the last neighbouring pair that differs
        for i, j in reversed(list(zip(digits, digits[1:]))):
            if answer[i] != answer[j]:
                new = list(old)
                new[i - a], new[j - a] = new[j - a], new[i - a]
                if new[0] != "0" or old[0] == "0":
                    one("digits swapped", a, b, "".join(new), f"{old} -> {''.join(new)}")
                break
        # last digit off by one
        k = digits[-1]
        d = int(answer[k])
        new = old[:k - a] + str(d + 1 if d < 9 else d - 1) + old[k - a + 1:]
        one("last digit off by one", a, b, new, f"{old} -> {new}")
        # value of another field of the same call
        f = _field_of(n, fields)
        if f and not n.percent:
            others = [g for g in fields if g[0] == f[0] and g[1] != f[1] and abs(g[2] - f[2]) > 1e-9]
            for g in others[:MAX_FIELDS_PER_NUMBER]:
                new = _fmt(g[2], old)
                one("value of another field", a, b, new, f"{old} ({f[1]}) -> {new} ({g[1]})")
        # fraction as percent
        if n.percent:
            decimals = (len(old.split(".")[1]) if "." in old else 0) + 2
            new = f"{n.value / 100:.{decimals}f}"
            one("fraction as percent", a, b, new, f"{old}% -> {new}%")
    # two values swapped: two numbers of one sentence that state different fields
    swaps = 0
    for s_start, s_end in sentence_spans(answer):
        bound = [(n, _field_of(n, fields)) for n in keep if s_start <= n.start < s_end]
        bound = [(n, f) for n, f in bound if f and not n.percent]
        for i in range(len(bound)):
            for j in range(i + 1, len(bound)):
                (n1, f1), (n2, f2) = bound[i], bound[j]
                if swaps >= MAX_SWAPS_PER_ANSWER or f1[1] == f2[1] or abs(f1[2] - f2[2]) < 1e-9:
                    continue
                (a1, b1), (a2, b2) = _numeric_part(n1), _numeric_part(n2)
                t1, t2 = answer[a1:b1], answer[a2:b2]
                new = answer[:a1] + t2 + answer[b1:a2] + t1 + answer[b2:]
                shift = len(t2) - len(t1)
                out.append(("two values swapped", new, [(a1, a1 + len(t2)), (a2 + shift, a2 + shift + len(t1))],
                            f"{t1} ({f1[1]}) <-> {t2} ({f2[1]})"))
                swaps += 1
    return out


def _overlaps(f, spans) -> bool:
    return any(f.start < b and a < f.end for a, b in spans)


def run(paths: list, wrong: set) -> dict:
    rows, skipped = [], []
    for rec in records(paths):
        key = (rec["model"], rec["id"])
        if key in wrong:
            skipped.append({"model": rec["model"], "id": rec["id"], "why": "wrong by hand"})
            continue
        base = check_messages(rec["messages"])
        if base.verdict != "ok":
            skipped.append({"model": rec["model"], "id": rec["id"], "why": f"traceground says {base.verdict}"})
            continue
        answer = rec["messages"][-1]["content"]
        for kind, new_answer, spans, what in mutations(answer, result_fields(rec["messages"])):
            msgs = json.loads(json.dumps(rec["messages"]))
            msgs[-1]["content"] = new_answer
            r = check_messages(msgs)
            high = [f for f in r.findings if f.severity == "high"]
            hit = [f for f in high if _overlaps(f, spans)]
            outcome = "caught" if hit else ("flagged elsewhere" if r.verdict == "problems" else "missed")
            rows.append({"model": rec["model"], "id": rec["id"], "kind": kind, "change": what,
                         "answer": new_answer, "outcome": outcome,
                         "checks": sorted({f.check for f in hit}),
                         "findings": [f.message for f in r.findings]})
    return {"date": datetime.now().isoformat(timespec="seconds"), "runs": [Path(p).name for p in paths],
            "rows": rows, "skipped": skipped}


def summary(rows: list) -> list:
    out = []
    for kind in KINDS + ["all"]:
        rs = [r for r in rows if kind == "all" or r["kind"] == kind]
        if not rs:
            continue
        c = {o: sum(r["outcome"] == o for r in rs) for o in ("caught", "flagged elsewhere", "missed")}
        checks = {}
        for r in rs:
            for ch in r["checks"]:
                checks[ch] = checks.get(ch, 0) + 1
        out.append({"kind": kind, "planted": len(rs), **c, "checks": checks})
    return out


def markdown(report: dict) -> str:
    rows = report["rows"]
    answers = len({(r["model"], r["id"]) for r in rows})
    lines = [f"# Planted errors in real answers, {report['date']}", "",
             f"Runs: {', '.join(report['runs'])}", "",
             f"{len(rows)} planted errors in {answers} real answers that are correct by hand and that "
             "traceground passes. The errors are planted, not made by the models.", "",
             "| Kind | Planted | Caught | Flagged elsewhere | Missed | Caught by |", "|---|---|---|---|---|---|"]
    for s in summary(rows):
        by = ", ".join(f"{k} {v}" for k, v in sorted(s["checks"].items()))
        pct = f" ({100 * s['caught'] / s['planted']:.0f}%)"
        lines.append(f"| {s['kind']} | {s['planted']} | {s['caught']}{pct} | {s['flagged elsewhere']} | "
                     f"{s['missed']} | {by} |")
    if report["skipped"]:
        lines += ["", "Answers not used: " + "; ".join(f"{s['id']} ({s['model']}): {s['why']}"
                                                       for s in report["skipped"])]
    for outcome in ("missed", "flagged elsewhere"):
        rs = [r for r in rows if r["outcome"] == outcome]
        lines += ["", f"## {outcome.capitalize()} ({len(rs)})", ""]
        for r in rs:
            lines += [f"* **{r['id']}** · {r['model']} · {r['kind']}: {r['change']}",
                      f"  * Answer: {r['answer']}"]
            lines += [f"  * Finding: {m}" for m in r["findings"]]
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("runs", nargs="*", help="run files or patterns (default: every .jsonl in runs/)")
    p.add_argument("--out", default=str(HERE / "results"))
    p.add_argument("--set", default="dev", choices=sorted(SETS), help="where to look for runs when none are given")
    a = p.parse_args(argv)
    missing = [pat for pat in a.runs if not glob.glob(pat)]
    if missing:
        print(f"mutate: no file matches {', '.join(missing)}", file=sys.stderr)
        return 2
    paths = sorted({x for pat in a.runs for x in glob.glob(pat)}) if a.runs else \
        sorted(str(x) for x in SETS[a.set][1].glob("*.jsonl"))
    if not paths:
        print("mutate: no run files; run run_eval.py first", file=sys.stderr)
        return 2
    report = run(paths, load_wrong())
    for s in summary(report["rows"]):
        print(f"{s['kind']}: {s['planted']} planted, caught {s['caught']}, "
              f"flagged elsewhere {s['flagged elsewhere']}, missed {s['missed']}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prefix = "mutations_" if a.set == "dev" else f"mutations_{a.set}_"
    stem, k = out / f"{prefix}{report['date'][:10]}", 1
    while stem.with_suffix(".md").exists():
        k += 1
        stem = out / f"{prefix}{report['date'][:10]}_{k}"
    stem.with_suffix(".json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    stem.with_suffix(".md").write_text(markdown(report), encoding="utf-8")
    print(f"Wrote {stem.with_suffix('.md')} and {stem.with_suffix('.json')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
