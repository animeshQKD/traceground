"""ragtruth.py - measure traceground on RAGTruth, a public corpus of real model answers with human-marked
hallucinations (Niu et al., ACL 2024; https://github.com/ParticleMedia/RAGTruth, MIT license).

RAGTruth has 17,790 answers by six models (GPT-3.5, GPT-4, Llama-2 7B/13B/70B, Mistral 7B) to three tasks:
    QA        answer a question from web passages (MS MARCO)
    Summary   summarise a news article (CNN/Daily Mail, Recent News)
    Data2txt  write about a business from its structured data (Yelp), passed here as one tool result
Annotators marked every span that conflicts with the source or adds information the source does not have.
Most marked spans are claims in words ("the restaurant has outdoor seating"), which traceground does not
check. It checks numbers, quotes and values, so the useful questions are:
    * of the marked spans that contain a digit, how many does traceground flag (digit-span recall)?
    * of traceground's high findings, how many fall on a marked span?
    * of the high findings that fall on no marked span, how many are real errors the annotators did not
      mark, and how many are false alarms? Only a person can say: --review writes them out to check.

The data is NOT in this repository. Download the two files into eval/data/ragtruth/ (gitignored), e.g.
in PowerShell:
    mkdir eval\\data\\ragtruth
    $u = "https://raw.githubusercontent.com/ParticleMedia/RAGTruth/main/dataset"
    Invoke-WebRequest "$u/response.jsonl" -OutFile eval\\data\\ragtruth\\response.jsonl
    Invoke-WebRequest "$u/source_info.jsonl" -OutFile eval\\data\\ragtruth\\source_info.jsonl
Then, from the eval folder:
    python ragtruth.py --split train                 # develop on train
    python ragtruth.py --split test                  # measure test once
    python ragtruth.py --split test --review 30      # also write 30 unmarked findings per task to check
Writes results/ragtruth_<split>_<date>.md and .json: numbers and RAGTruth ids only, no texts (the
sources are news articles, web pages and Yelp data, whose terms do not allow redistribution). The
--review file, which has texts, goes to eval/data/ragtruth/ next to the data, so it stays out of git.

Harness: the task's instruction (the question, or "Summarize the following news within 150 words")
is passed as the question, so numbers it contains count as grounded. Only answers RAGTruth rates
"good" are scored (refusals and truncated answers are left out).
"""
import argparse
import collections
import json
import random
import re
import sys
from datetime import date
from pathlib import Path

from traceground import check_answer

HERE = Path(__file__).resolve().parent
DATA = HERE / "data" / "ragtruth"
TASKS = ("QA", "Summary", "Data2txt")


def load(data: Path = DATA) -> tuple:
    """(responses, sources by id) from the two RAGTruth files."""
    for name in ("response.jsonl", "source_info.jsonl"):
        if not (data / name).exists():
            sys.exit(f"{data / name} not found. See the top of ragtruth.py for how to download RAGTruth.")
    with open(data / "response.jsonl", encoding="utf-8") as f:
        responses = [json.loads(line) for line in f if line.strip()]
    with open(data / "source_info.jsonl", encoding="utf-8") as f:
        sources = {s["source_id"]: s for s in map(json.loads, f) if s}
    return responses, sources


def instruction(source: dict) -> str:
    """The task's instruction without the source text: what the model was asked."""
    p, t = source["prompt"], source["task_type"]
    if t == "Summary":
        return p.split("\n", 1)[0]
    if t == "Data2txt":
        return p.split("Structured data:", 1)[0]
    return p.replace(source["source_info"]["passages"], " ")


def check(response: dict, source: dict):
    """traceground's result for one RAGTruth answer."""
    t, info, q = source["task_type"], source["source_info"], instruction(source)
    if t == "Summary":
        return check_answer(response["response"], {"S1": info}, question=q)
    if t == "QA":
        return check_answer(response["response"], {"S1": info["passages"]}, question=q)
    return check_answer(response["response"], question=q,
                        trace=[{"name": "business_data", "args": {}, "result": info}])


def _overlap(a, b) -> bool:
    return a["start"] < b["end"] and b["start"] < a["end"]


def _has_digit(label: dict) -> bool:
    return bool(re.search(r"\d", label["text"]))


def score(responses: list, sources: dict, split: str) -> tuple:
    """(per-task counts, rows of unmarked high findings for review)."""
    out, unmarked = {}, []
    for task in TASKS:
        rows = [r for r in responses if r["split"] == split and r.get("quality", "good") == "good"
                and sources[r["source_id"]]["task_type"] == task]
        c = collections.Counter(dict.fromkeys(("answers", "answers_marked", "flagged", "tp", "fp", "digit_spans",
                                               "digit_spans_flagged", "high_findings", "high_on_marked"), 0))
        kinds_on, kinds_off = collections.Counter(), collections.Counter()
        flagged_unmarked_ids = []
        for r in rows:
            res = check(r, sources[r["source_id"]])
            labels = r["labels"]
            high = [{"start": f.start, "end": f.end, "f": f} for f in res.findings if f.severity == "high"]
            c["answers"] += 1
            c["answers_marked"] += bool(labels)
            c["flagged"] += bool(high)
            c["tp"] += bool(high) and bool(labels)
            c["fp"] += bool(high) and not labels
            for lab in labels:
                if _has_digit(lab):
                    c["digit_spans"] += 1
                    c["digit_spans_flagged"] += any(_overlap(h, lab) for h in high)
            c["high_findings"] += len(high)
            for h in high:
                if any(_overlap(h, lab) for lab in labels):
                    c["high_on_marked"] += 1
                    kinds_on[h["f"].check] += 1
                else:
                    kinds_off[h["f"].check] += 1
                    unmarked.append((task, r, h["f"]))
            if high and not labels:
                flagged_unmarked_ids.append(r["id"])
        p = c["tp"] / c["flagged"] if c["flagged"] else 0.0
        rec = c["tp"] / c["answers_marked"] if c["answers_marked"] else 0.0
        out[task] = {**c, "precision": round(p, 3), "recall": round(rec, 3),
                     "f1": round(2 * p * rec / (p + rec), 3) if p + rec else 0.0,
                     "high_on_marked_by_check": dict(kinds_on), "high_unmarked_by_check": dict(kinds_off),
                     "flagged_unmarked_ids": flagged_unmarked_ids}
    return out, unmarked


def markdown(report: dict, split: str, version: str) -> str:
    lines = [f"# RAGTruth, {split} split ({date.today().isoformat()}, traceground {version})", "",
             "Answers rated good by RAGTruth. A finding is high severity unless stated. \"Marked\" = a span the",
             "RAGTruth annotators marked as a hallucination. Texts are not included: see eval/ragtruth.py.", "",
             "| Task | Answers | With a marked span | Flagged | Flagged and marked | Precision | Recall | F1 |",
             "|---|---|---|---|---|---|---|---|"]
    for t, c in report.items():
        lines.append(f"| {t} | {c['answers']} | {c['answers_marked']} | {c['flagged']} | {c['tp']} | "
                     f"{c['precision']:.3f} | {c['recall']:.3f} | {c['f1']:.3f} |")
    lines += ["", "| Task | Marked spans with a digit | of them flagged | High findings | on a marked span |",
              "|---|---|---|---|---|"]
    for t, c in report.items():
        lines.append(f"| {t} | {c['digit_spans']} | {c['digit_spans_flagged']} | {c['high_findings']} | "
                     f"{c['high_on_marked']} |")
    lines += ["", "High findings by check (on a marked span / on none):", ""]
    for t, c in report.items():
        kinds = sorted(set(c["high_on_marked_by_check"]) | set(c["high_unmarked_by_check"]))
        lines.append(f"* {t}: " + ", ".join(f"{k} {c['high_on_marked_by_check'].get(k, 0)}/"
                                            f"{c['high_unmarked_by_check'].get(k, 0)}" for k in kinds))
    lines += ["", "RAGTruth ids of answers flagged with no marked span (for a person to check):", ""]
    for t, c in report.items():
        lines.append(f"* {t}: " + (", ".join(c["flagged_unmarked_ids"]) or "none"))
    return "\n".join(lines) + "\n"


def write_review(unmarked: list, n: int, path: Path, seed: int = 7) -> int:
    """A random sample of n unmarked high findings per task, with texts, for a person to judge."""
    rng = random.Random(seed)
    k = 0
    with open(path, "w", encoding="utf-8") as f:
        for task in TASKS:
            rows = [u for u in unmarked if u[0] == task]
            for _, r, fd in rng.sample(rows, min(n, len(rows))):
                k += 1
                f.write(f"--- {task} id {r['id']} ({r['model']}) {fd.check}: {fd.text!r}\n"
                        f"    {fd.message}\n    SENTENCE: {fd.sentence}\n\n")
    return k


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    ap.add_argument("--split", choices=["train", "test"], default="train")
    ap.add_argument("--data", type=Path, default=DATA, help="folder with response.jsonl and source_info.jsonl")
    ap.add_argument("--review", type=int, default=0, metavar="N",
                    help="write N unmarked high findings per task, with texts, next to the data")
    ap.add_argument("--out", type=Path, default=HERE / "results")
    a = ap.parse_args(argv)
    import traceground
    responses, sources = load(a.data)
    report, unmarked = score(responses, sources, a.split)
    stem = f"ragtruth_{a.split}_{date.today().isoformat()}"
    a.out.mkdir(exist_ok=True)
    (a.out / f"{stem}.md").write_text(markdown(report, a.split, traceground.__version__), encoding="utf-8")
    (a.out / f"{stem}.json").write_text(json.dumps({"split": a.split, "version": traceground.__version__,
                                                    "tasks": report}, indent=1), encoding="utf-8")
    print(markdown(report, a.split, traceground.__version__).split("\nHigh findings by check")[0])
    print(f"wrote {a.out / stem}.md and .json")
    if a.review:
        path = a.data / f"review_{a.split}.txt"
        print(f"wrote {write_review(unmarked, a.review, path)} findings to check to {path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
