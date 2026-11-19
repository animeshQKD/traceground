"""score.py - run traceground on recorded answers and compare with labels from the known tool results.

    python score.py                         # every run in runs/
    python score.py runs/2026-11-18_groq_openai-gpt-oss-120b.jsonl
    python score.py --set heldout           # every run in runs/heldout/, into score_heldout_<date>.md

Each answer gets an automatic label (the tools are deterministic, so the right values are known):
    correct  every required value is stated (at the precision written) and every required call was made
             with the right arguments; for a question about a failing tool, the answer says it failed
    wrong    a required value is missing or different, a call had wrong arguments, or a failure is hidden
    review   the values are right but a required call is missing (the model may have computed in its head)
The label checks values and calls, not which name a value is attached to: an answer that swaps two
values ("7 rebounds and 11 assists" for 11 and 7) is labelled correct, and shows up in the list of
answers flagged although labelled correct, where a person sees that the label is wrong.
Then traceground checks the recorded chat (check_messages). The report counts false alarms (a correct
answer flagged), catches (a wrong answer flagged) and misses, and lists every one of them, and every
"review", for a person to confirm. Writes results/score_<date>.md and .json.
"""
import argparse
import inspect
import json
import re
import statistics
import sys
import time
from datetime import datetime
from pathlib import Path

import tools as T
from run_eval import SETS, load_questions

from traceground import check_messages
from traceground.numbers import find_numbers

HERE = Path(__file__).resolve().parent
_ACK = re.compile(r"\b(?:fail\w*|error|unable|could\s*n[o']t|couldn['’]t|can\s*not|cannot|can['’]t|unavailable|not\s+available|"
                  r"timed?\s*out|unknown|not\s+found|no\s+(?:such|data|information|record|product|access|tool)|"
                  r"do(?:es)?\s*n[o']t\s+(?:have|exist)|don['’]t\s+have|doesn['’]t\s+(?:have|exist)|not\s+able|isn['’]t\s+(?:a|in))\b", re.I)


def _defaults(name: str) -> dict:
    fn = T.TOOLS[name][0]
    return {k: p.default for k, p in inspect.signature(fn).parameters.items() if p.default is not inspect.Parameter.empty}


def _same(expected, actual) -> bool:
    if isinstance(expected, (int, float)) and isinstance(actual, (int, float)) and not isinstance(actual, bool):
        return abs(expected - actual) <= 1e-6 * max(1.0, abs(expected))
    return str(expected).strip().casefold() == str(actual).strip().casefold()


def _calls(messages: list) -> list:
    out = []
    for m in messages:
        for tc in m.get("tool_calls") or []:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = {}
            out.append((tc["function"]["name"], args if isinstance(args, dict) else {}))
    return out


def _call_made(name, expected_args, made) -> bool:
    for n, args in made:
        if n != name:
            continue
        if expected_args == "any":
            return True
        full = dict(_defaults(name), **args)
        if all(k in full and _same(v, full[k]) for k, v in expected_args.items()):
            return True
    return False


def _stated(value: float, answer: str) -> bool:
    v = abs(value)
    return any(any(abs(c - v) <= t * (1 + 1e-9) + 1e-9 for c, t in n.candidates()) for n in find_numbers(answer))


def expected_values(q: dict) -> list:
    out = []
    for v in q["values"]:
        if "value" in v:
            out.append(float(v["value"]))
        else:
            name, args = q["calls"][v["call"]]
            out.append(float(T.run_tool(name, args)[v["key"]]))
    return out


def label(q: dict, rec: dict) -> tuple:
    """(label, reason)."""
    answer = rec.get("answer") or ""
    if rec.get("error") or not answer.strip():
        return "no answer", rec.get("error") or rec.get("stopped", "")
    if q["kind"] == "acknowledge":
        return ("correct", "says it failed or cannot") if _ACK.search(answer) else ("wrong", "hides the failure")
    made = _calls(rec["messages"])
    missing_values = [v for v in expected_values(q) if not _stated(v, answer)]
    missing_calls = [c for c in q["calls"] if not _call_made(c[0], c[1], made)]
    if missing_values:
        return "wrong", "missing or different values: " + ", ".join(f"{v:g}" for v in missing_values)
    if missing_calls:
        names = {n for n, _a in made}
        wrong_args = [c for c in missing_calls if c[0] in names]
        if wrong_args:
            return "wrong", "called with other arguments than asked: " + "; ".join(f"{c[0]}{c[1]}" for c in wrong_args)
        return "review", "values right but a call is missing: " + ", ".join(c[0] for c in missing_calls)
    return "correct", ""


def score(paths: list) -> dict:
    questions = {q["id"]: q for name in SETS for q in load_questions(name)}     # ids differ between sets
    rows = []
    for path in paths:
        latest = {}                    # a question asked again after an error: its last record counts
        for line in Path(path).read_text(encoding="utf-8").splitlines():
            if line.strip():
                rec = json.loads(line)
                latest[rec["id"]] = rec
        for rec in latest.values():
            q = questions[rec["id"]]
            lab, why = label(q, rec)
            row = {"run": Path(path).name, "id": rec["id"], "model": rec["model"], "provider": rec["provider"],
                   "question": q["question"], "answer": rec.get("answer", ""), "label": lab, "label_reason": why,
                   "flagged": None, "findings": [], "ms": None,
                   "calls": [f"{n}({json.dumps(a, ensure_ascii=False)})" for n, a in _calls(rec.get("messages", []))]}
            if lab != "no answer":
                t0 = time.perf_counter()
                r = check_messages(rec["messages"])
                row["ms"] = round((time.perf_counter() - t0) * 1000, 2)
                row["flagged"] = r.verdict == "problems"
                row["findings"] = [{"check": f.check, "severity": f.severity, "text": f.text, "message": f.message}
                                   for f in r.findings]
            rows.append(row)
    return {"date": datetime.now().isoformat(timespec="seconds"), "runs": [Path(p).name for p in paths], "rows": rows}


def summary(rows: list) -> list:
    out = []
    for model in dict.fromkeys(r["model"] for r in rows):
        rs = [r for r in rows if r["model"] == model]
        lab = {k: [r for r in rs if r["label"] == k] for k in ("correct", "wrong", "review", "no answer")}
        ms = [r["ms"] for r in rs if r["ms"] is not None]
        out.append({"model": model, "answers": len(rs), "correct": len(lab["correct"]), "wrong": len(lab["wrong"]),
                    "review": len(lab["review"]), "no_answer": len(lab["no answer"]),
                    "false_alarms": sum(r["flagged"] for r in lab["correct"]),
                    "caught": sum(r["flagged"] for r in lab["wrong"]),
                    "median_ms": round(statistics.median(ms), 2) if ms else None})
    return out


def markdown(report: dict) -> str:
    rows = report["rows"]
    lines = [f"# Real-answer evaluation, scored {report['date']}", "", "Runs: " + ", ".join(report["runs"]), "",
             "## Summary (automatic labels; every count below is confirmed by hand in the lists that follow)", "",
             "| Model | Answers | Correct | False alarms on correct | Wrong | Caught | Review | No answer | Median ms |",
             "|---|---|---|---|---|---|---|---|---|"]
    for s in summary(rows):
        lines.append(f"| {s['model']} | {s['answers']} | {s['correct']} | {s['false_alarms']} of {s['correct']} | "
                     f"{s['wrong']} | {s['caught']} of {s['wrong']} | {s['review']} | {s['no_answer']} | {s['median_ms']} |")
    checks = {}
    for r in rows:
        for f in r["findings"]:
            checks[f["check"]] = checks.get(f["check"], 0) + 1
    lines += ["", "Findings by check: " + (", ".join(f"{k} {v}" for k, v in sorted(checks.items())) or "none"), ""]

    def block(title, items, ask):
        lines.extend([f"## {title} ({len(items)})", "", ask, ""])
        for r in items:
            lines.extend([f"### {r['id']} · {r['model']} · label {r['label']}" + (f" ({r['label_reason']})" if r['label_reason'] else ""),
                          "", f"* Question: {r['question']}", f"* Calls: {'; '.join(r['calls']) or 'none'}",
                          f"* Answer: {' '.join(r['answer'].split())}"])
            lines.extend([f"* Finding [{f['check']}, {f['severity']}]: {f['message']}" for f in r["findings"]] or ["* Findings: none"])
            lines.extend(["* Confirmed by hand: ", ""])

    block("Flagged although labelled correct: possible false alarms",
          [r for r in rows if r["label"] == "correct" and r["flagged"]],
          "For each: is the finding wrong (a false alarm), or is the label wrong (the answer has a real problem)?")
    block("Labelled wrong but not flagged: possible misses", [r for r in rows if r["label"] == "wrong" and not r["flagged"]],
          "For each: is the answer really wrong, and which check should have caught it?")
    block("Labelled wrong and flagged: catches", [r for r in rows if r["label"] == "wrong" and r["flagged"]],
          "For each: does the finding name the real error?")
    block("Review: values right but a call missing", [r for r in rows if r["label"] == "review"],
          "For each: correct or wrong? Did traceground flag it, and rightly?")
    block("Correct answers with minor findings only", [r for r in rows if r["label"] == "correct" and r["findings"] and not r["flagged"]],
          "For each: is the minor finding right?")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("runs", nargs="*", help="run files (default: every .jsonl in runs/)")
    p.add_argument("--out", default=str(HERE / "results"))
    p.add_argument("--set", default="dev", choices=sorted(SETS), help="where to look for runs when none are given")
    a = p.parse_args(argv)
    paths = a.runs or sorted(str(x) for x in SETS[a.set][1].glob("*.jsonl"))
    if not paths:
        print("score: no run files; run run_eval.py first", file=sys.stderr)
        return 2
    report = score(paths)
    for s in summary(report["rows"]):
        print(f"{s['model']}: {s['answers']} answers; correct {s['correct']} (false alarms {s['false_alarms']}), "
              f"wrong {s['wrong']} (caught {s['caught']}), review {s['review']}, no answer {s['no_answer']}")
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    prefix = "score_" if a.set == "dev" else f"score_{a.set}_"
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
