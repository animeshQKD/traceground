"""
run_survey.py - Phase 0: run existing answer checkers on the 20 cases of cases.json.

Question it answers: where do GroundLens, LongTracer, RAGGround and halluguard already catch the
errors of handoff section 5, where do they raise false alarms on correct answers, and how does our own
checker (traceground, installed from this folder) do on the same cases?

    python run_survey.py                       # every tool that is installed
    python run_survey.py --tools traceground   # only some (comma-separated)

Writes results/survey_<date>.json (everything) and results/survey_<date>.md (tables). Nothing is sent
anywhere except the model downloads the tools do themselves from Hugging Face on first use.

How the cases are given to the tools (all four take an answer and a list of passages):
  * "sources" cases: each source is one passage.
  * "trace" cases: each tool call is one passage, "Tool call 1: loan_cost(rate=0.07, years=3)" and
    its result as JSON (render_passages). None of the four reads a tool trace itself.
  * every tool also gets the user's question as one more passage ("User question: ..."), since the
    question is evidence too (a number the user gave may be repeated); tools that take a question
    parameter get it there as well.
  * citation markers such as [S1] are taken out of the answer (none of the four reads an answer's own
    markers, as far as their documentation says, and a marker's digit would otherwise count as an
    unsupported number). So q2, a quote cited to the wrong passage, is an error these tools cannot see.
    --markers keep runs with the markers left in, to see what they do with them.

A "flag" is any verdict other than a clean pass (GroundLens REVIEW counts as a flag). Whether a flag
points at the real error is NOT decided here: the .md lists each tool's reasons, and the column
"right reason?" is filled in by hand.
"""
import argparse
import datetime as dt
import json
import platform
import re
import statistics
import sys
import tempfile
import time
import traceback
from importlib import metadata
from pathlib import Path

FILES_VERSION = "2026-11-17c"
HERE = Path(__file__).resolve().parent
TOOLS = ["traceground", "groundlens", "longtracer", "ragground", "halluguard"]
PIP_NAMES = {"traceground": "traceground", "groundlens": "groundlens", "longtracer": "longtracer",
             "ragground": "ragground", "halluguard": "halluguard"}


# ------------------------------------------------------------------ cases
def load_cases(path=HERE / "cases.json") -> list:
    with open(path, encoding="utf-8") as f:
        return json.load(f)["cases"]


_MARKER = re.compile(r"\s*\[S\d+(?:\s*,\s*S\d+)*\]")


def answer_for_tools(answer: str, markers: str = "strip") -> str:
    """The answer as the tools get it: without citation markers, unless markers == 'keep'."""
    return answer if markers == "keep" else _MARKER.sub("", answer)


def _args(args: dict) -> str:
    return ", ".join(f"{k}={json.dumps(v, ensure_ascii=False)}" for k, v in args.items())


def render_passages(case: dict) -> list:
    """[(id, text), ...]: the evidence of a case as plain passages, the question last."""
    if case["kind"] == "sources":
        out = [(s["id"], s["text"]) for s in case["sources"]]
    else:
        out = []
        for i, call in enumerate(case["trace"], 1):
            res = call["result"]
            res = res if isinstance(res, str) else json.dumps(res, ensure_ascii=False)
            out.append((f"T{i}", f"Tool call {i}: {call['name']}({_args(call['args'])})\nResult: {res}"))
    out.append(("Q", f"User question: {case['question']}"))
    return out


# ------------------------------------------------------------------ adapters
class Adapter:
    """setup() loads models (timed separately); check() returns (verdict, reason), verdict 'flag' or 'pass'."""
    name = ""

    def version(self) -> str:
        try:
            return metadata.version(PIP_NAMES[self.name])
        except metadata.PackageNotFoundError:
            return ""

    def setup(self) -> None:
        pass

    def check(self, case: dict, passages: list) -> tuple:
        raise NotImplementedError


class TraceGround(Adapter):
    """Our own checker. Sources cases: the same passages as the others. Trace cases: the trace itself,
    which traceground reads (the others get it as passages, as they cannot read a trace)."""
    name = "traceground"

    def setup(self):
        from traceground import check_answer
        self.check_answer = check_answer

    def check(self, case, passages):
        if case["kind"] == "trace":
            r = self.check_answer(case["answer"], None, case["question"], trace=case["trace"])
        else:
            r = self.check_answer(case["answer"], [p for p in passages if p[0] != "Q"], case["question"])
        verdict = "flag" if r.verdict == "problems" else "pass"
        return verdict, (f"[{r.verdict}] " + " | ".join(f.message for f in r.findings)).strip()


class GroundLens(Adapter):
    name = "groundlens"

    def setup(self):
        import groundlens as gl
        self.gl = gl
        self.records = tempfile.mkdtemp(prefix="groundlens_records_")      # its signed records go here
        self.v = gl.Verifier(sink=gl.sinks.jsonl(self.records))

    def check(self, case, passages):
        kw = dict(answer=case["answer"], question=case["question"])
        try:
            rec = self.v.check(passages=[(pid, text, "survey") for pid, text in passages], **kw)
        except (TypeError, ValueError):                 # if the (id, text, provenance) form is refused
            rec = self.v.check(passages=[text for _pid, text in passages], **kw)
        decision = str(getattr(rec.decision, "name", rec.decision)).upper()
        verdict = "pass" if decision.endswith("PASS") else "flag"
        reasons = "; ".join(str(r) for r in (rec.reasons or []))
        return verdict, f"[{decision}] {reasons}".strip()


class LongTracer(Adapter):
    name = "longtracer"

    def setup(self):
        from longtracer import CitationVerifier
        self.v = CitationVerifier(threshold=0.5)        # the default of longtracer.check()

    def check(self, case, passages):
        res = self.v.verify_parallel(case["answer"], [t for _p, t in passages])
        verdict = "pass" if res.verdict == "PASS" else "flag"
        flagged = [str(c.get("claim", ""))[:150] for c in (res.flagged_claims or [])]
        return verdict, (f"[{res.verdict}] {res.summary} " + " | ".join(flagged)).strip()


class RAGGround(Adapter):
    name = "ragground"

    def setup(self):
        from ragground import RAGGround as RG
        self.g = RG(require_model=True)                 # fail loudly instead of a silent heuristic fallback
        self.g.prepare()

    def check(self, case, passages):
        rep = self.g.verify(context=dict(passages), answer=case["answer"])
        verdict = "pass" if rep.is_grounded else "flag"
        bad = [f"{getattr(c.status, 'value', c.status)}: {c.text[:120]}" for c in rep.claims
               if str(getattr(c.status, "value", c.status)).upper() != "VERIFIED"]
        return verdict, (f"[grounded={rep.is_grounded}, neural={rep.used_neural_model}] " + " | ".join(bad)).strip()


class HalluGuard(Adapter):
    name = "halluguard"

    def setup(self):
        from halluguard import Guard
        from halluguard.verifier import NLIVerifier
        from sentence_transformers import SentenceTransformer
        self.Guard = Guard
        self.encoder = SentenceTransformer("all-MiniLM-L6-v2")   # the encoder of its README
        self.nli = NLIVerifier()                                  # its default NLI model, as its README advises
        self.nli._ensure_model()                                  # load now, so setup time is not in the first check

    def check(self, case, passages):
        guard = self.Guard.from_documents(documents=[t for _p, t in passages], encoder=self.encoder,
                                          verifier=self.nli)
        rep = guard.check(case["answer"], question=case["question"])
        verdict = "flag" if rep.n_flagged else "pass"
        bad = [f"{c.text[:120]} (support {c.support_score:.2f})" for c in rep.claims
               if str(getattr(c.status, "value", c.status)) != "SUPPORTED"]
        return verdict, (f"[{rep.n_flagged} of {len(rep.claims)} claims flagged] " + " | ".join(bad)).strip()


ADAPTERS = {a.name: a for a in (TraceGround, GroundLens, LongTracer, RAGGround, HalluGuard)}


# ------------------------------------------------------------------ running
def run_tool(adapter: Adapter, cases: list, markers: str = "strip") -> dict:
    out = {"tool": adapter.name, "version": adapter.version(), "setup_s": None, "setup_error": "",
           "results": []}
    if not out["version"]:
        out["setup_error"] = f"not installed (pip install {PIP_NAMES[adapter.name]})"
        return out
    t0 = time.perf_counter()
    try:
        adapter.setup()
    except Exception as e:  # noqa: BLE001 - a tool that cannot start is a result, not a crash
        out["setup_error"] = f"{type(e).__name__}: {e}"[:500]
        return out
    out["setup_s"] = round(time.perf_counter() - t0, 2)
    for k, case in enumerate(cases):
        passages = render_passages(case)
        given = dict(case, answer=answer_for_tools(case["answer"], markers))
        t = time.perf_counter()
        try:
            verdict, reason = adapter.check(given, passages)
        except Exception as e:  # noqa: BLE001
            verdict, reason = "error", f"{type(e).__name__}: {e} | {traceback.format_exc(limit=2)[-300:]}"
        ms = (time.perf_counter() - t) * 1000
        out["results"].append({"id": case["id"], "verdict": verdict, "reason": reason[:600],
                               "ms": round(ms, 2), "warmup": k == 0})
    return out


def summarize(run: dict, cases: list) -> dict:
    expect = {c["id"]: c["expect"] for c in cases}
    res = run["results"]
    flags = [r for r in res if expect[r["id"]] == "flag"]
    passes = [r for r in res if expect[r["id"]] == "pass"]
    times = [r["ms"] for r in res if not r["warmup"] and r["verdict"] != "error"]
    return {"flagged_errors": sum(r["verdict"] == "flag" for r in flags), "errors_total": len(flags),
            "false_alarms": sum(r["verdict"] == "flag" for r in passes), "correct_total": len(passes),
            "crashes": sum(r["verdict"] == "error" for r in res),
            "median_ms": round(statistics.median(times), 2) if times else None}


def markdown(report: dict, cases: list) -> str:
    runs = [r for r in report["runs"] if not r["setup_error"]]
    lines = [f"# Survey run {report['date']}", "",
             f"Python {report['python']} on {report['platform']}; cases.json {report['cases_version']}; "
             f"run_survey.py {FILES_VERSION}; citation markers: {report.get('markers', 'strip')}.", ""]
    for r in report["runs"]:
        if r["setup_error"]:
            lines.append(f"* **{r['tool']}**: not run: {r['setup_error']}")
    if runs:
        lines += ["", "## Summary (verdicts only; reasons not yet checked by hand)", "",
                  "| Tool | Version | Errors flagged | False alarms on correct answers | Crashes | Median ms per check | Setup s |",
                  "|---|---|---|---|---|---|---|"]
        for r in runs:
            s = r["summary"]
            lines.append(f"| {r['tool']} | {r['version']} | {s['flagged_errors']} of {s['errors_total']} | "
                         f"{s['false_alarms']} of {s['correct_total']} | {s['crashes']} | {s['median_ms']} | {r['setup_s']} |")
        lines += ["", "Median time leaves out the first check of each tool (warm-up).", "",
                  "## Per case", "",
                  "| Case | Type | Expected | " + " | ".join(r["tool"] for r in runs) + " |",
                  "|---|---|---|" + "---|" * len(runs)]
        by = {r["tool"]: {x["id"]: x for x in r["results"]} for r in runs}
        for c in cases:
            cells = []
            for r in runs:
                v = by[r["tool"]][c["id"]]["verdict"]
                cells.append(v + ("" if v == "error" else (" ✓" if v == c["expect"] else " ✗")))
            lines.append(f"| {c['id']} | {c['error_type']} | {c['expect']} | " + " | ".join(cells) + " |")
        lines += ["", "## Reasons (fill in 'right reason?' by hand for every flag)", ""]
        for c in cases:
            lines += [f"### {c['id']}: {c['error_type']}, expected {c['expect']}", "",
                      f"* Answer: {c['answer']}", f"* Why: {c['why']}", "",
                      "| Tool | Verdict | Reason given | Right reason? |", "|---|---|---|---|"]
            for r in runs:
                x = by[r["tool"]][c["id"]]
                reason = x["reason"].replace("|", "/").replace("\n", " ")
                lines.append(f"| {r['tool']} | {x['verdict']} | {reason} |  |")
            lines.append("")
    return "\n".join(lines) + "\n"


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):              # Windows consoles: never crash on °, ✓, ≈
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--tools", default=",".join(TOOLS), help="comma-separated, from: " + ", ".join(TOOLS))
    p.add_argument("--cases", default=str(HERE / "cases.json"))
    p.add_argument("--out", default=str(HERE / "results"))
    p.add_argument("--markers", choices=["strip", "keep"], default="strip",
                   help="take citation markers like [S1] out of the answers (default) or keep them")
    a = p.parse_args(argv)
    names = [t.strip() for t in a.tools.split(",") if t.strip()]
    unknown = [t for t in names if t not in ADAPTERS]
    if unknown:
        p.error(f"unknown tool(s): {', '.join(unknown)}")
    cases = load_cases(a.cases)
    with open(a.cases, encoding="utf-8") as f:
        cases_version = json.load(f)["version"]
    report = {"date": dt.datetime.now().isoformat(timespec="seconds"), "python": platform.python_version(),
              "platform": platform.platform(), "cases_version": cases_version, "files_version": FILES_VERSION, "markers": a.markers,
              "runs": []}
    for name in names:
        print(f"{name}: starting ...", flush=True)
        run = run_tool(ADAPTERS[name](), cases, a.markers)
        if not run["setup_error"]:
            run["summary"] = summarize(run, cases)
            s = run["summary"]
            print(f"{name} {run['version']}: flagged {s['flagged_errors']} of {s['errors_total']} errors, "
                  f"false alarms on {s['false_alarms']} of {s['correct_total']} correct answers, "
                  f"{s['crashes']} crashes, median {s['median_ms']} ms per check (setup {run['setup_s']} s)")
        else:
            print(f"{name}: not run: {run['setup_error']}")
        report["runs"].append(run)
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = out / (f"survey_{report['date'][:10]}" + ("" if names == TOOLS else "_" + "-".join(names))
                  + ("_markers" if a.markers == "keep" else ""))
    base, k = stem, 1
    while stem.with_suffix(".json").exists() or stem.with_suffix(".md").exists():   # never overwrite a run
        k += 1
        stem = base.with_name(f"{base.name}_{k}")
    stem.with_suffix(".json").write_text(json.dumps(report, indent=1, ensure_ascii=False), encoding="utf-8")
    stem.with_suffix(".md").write_text(markdown(report, cases), encoding="utf-8")
    print(f"Wrote {stem.with_suffix('.json')} and {stem.with_suffix('.md')}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
