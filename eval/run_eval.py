"""run_eval.py - let a real model answer the evaluation questions with the local tools, and record
each chat (OpenAI-style messages) for score.py.

    python run_eval.py --provider groq                     # all 44 questions, default model
    python run_eval.py --provider hf --max-calls 150       # HF credits: requests capped per run
    python run_eval.py --provider gemini --questions f01,w04
    python run_eval.py --provider groq --model openai/gpt-oss-20b
    python run_eval.py --provider groq --set heldout        # the 20 held-out questions, into runs/heldout/

Writes runs/<date>_<provider>_<model>.jsonl, one line per question. Run it again with the same
provider and model on the same day to continue where it stopped: questions already answered are
skipped, questions that ended in an error are asked again. The run stops by itself after 2 questions
in a row fail at the provider (it is down or overloaded), and Ctrl+C stops it cleanly. Keys come from the environment or from ../.env and are never written anywhere.
"""
import argparse
import json
import re
import sys
import time
from datetime import date
from pathlib import Path

import tools as T
from llm_client import Client, CapReached, load_env

HERE = Path(__file__).resolve().parent
SYSTEM = ("You are a helpful assistant with tools. Use the tools to get every number you report, and say so "
          "plainly if a tool fails or if you cannot do something with the tools you have. Answer in a short "
          "paragraph.")
MAX_ROUNDS = 6


SETS = {   # question set -> (questions file, folder of its runs)
    "dev": (HERE / "questions.json", HERE / "runs"),
    "heldout": (HERE / "questions_heldout.json", HERE / "runs" / "heldout"),
}


def load_questions(path=HERE / "questions.json") -> list:
    """The questions of a file, or of a set name ("dev", "heldout")."""
    path = SETS[path][0] if path in SETS else path
    return json.loads(Path(path).read_text(encoding="utf-8"))["questions"]


def _clean(msg: dict) -> dict:
    """The assistant message as it goes back into the chat and into the record: role, content, tool_calls."""
    out = {"role": "assistant", "content": msg.get("content")}
    if msg.get("tool_calls"):
        out["tool_calls"] = [{"id": tc.get("id") or f"call_{i}", "type": "function",
                              "function": {"name": tc["function"]["name"], "arguments": tc["function"].get("arguments") or "{}"}}
                             for i, tc in enumerate(msg["tool_calls"], 1)]
    return out


def answer_question(question: str, chat) -> dict:
    """Run the tool loop. `chat(messages, tools)` returns an assistant message dict."""
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    for _round in range(MAX_ROUNDS):
        msg = _clean(chat(messages, T.SCHEMAS))
        messages.append(msg)
        if not msg.get("tool_calls"):
            return {"messages": messages, "answer": msg.get("content") or "", "stopped": "answered"}
        for tc in msg["tool_calls"]:
            try:
                args = json.loads(tc["function"]["arguments"] or "{}")
            except json.JSONDecodeError:
                args = None
            result = T.run_tool(tc["function"]["name"], args) if isinstance(args, dict) else \
                {"error": "arguments are not valid JSON"}
            messages.append({"role": "tool", "tool_call_id": tc["id"],
                             "content": result if isinstance(result, str) else json.dumps(result)})
    return {"messages": messages, "answer": "", "stopped": f"no answer after {MAX_ROUNDS} rounds"}


def answered_ids(path: Path) -> set:
    """Questions with an answer in the run file. A question that ended in an error is not answered:
    the next run asks it again (score.py keeps the last record of each question)."""
    if not path.exists():
        return set()
    recs = [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]
    return {r["id"] for r in recs if not r.get("error")}


STOP_AFTER_ERRORS = 2          # questions in a row that fail at the provider: it is down, stop waiting


def run(provider: str, model: str, ids, max_calls: int, out_dir: Path = None, chat=None,
        question_set: str = "dev") -> Path:
    out_dir = out_dir or SETS[question_set][1]
    env = load_env(HERE.parent / ".env")
    client = None if chat else Client(provider, model, env, max_calls=max_calls)
    model = model or (client.model if client else "fake")
    chat = chat or client.chat
    out_dir.mkdir(parents=True, exist_ok=True)
    path = out_dir / f"{date.today().isoformat()}_{provider}_{re.sub(r'[^A-Za-z0-9.-]+', '-', model)}.jsonl"
    done = answered_ids(path)
    questions = [q for q in load_questions(question_set) if (not ids or q["id"] in ids) and q["id"] not in done]
    print(f"{provider} {model}: {len(questions)} questions to answer ({len(done)} already answered in {path.name})",
          flush=True)
    errors_in_a_row = 0
    with path.open("a", encoding="utf-8") as f:
        try:
            for q in questions:
                t0 = time.time()
                try:
                    rec = answer_question(q["question"], chat)
                    error = None
                except CapReached as e:
                    print(f"stopped: {e}")
                    break
                except (RuntimeError, KeyError, IndexError, TypeError) as e:
                    rec, error = {"messages": [], "answer": "", "stopped": "error"}, " ".join(str(e).split())[:300]
                rec.update({"id": q["id"], "provider": provider, "model": model, "error": error,
                            "seconds": round(time.time() - t0, 1)})
                f.write(json.dumps(rec, ensure_ascii=False) + "\n")
                f.flush()
                status = "error: " + error if error else rec["stopped"]
                print(f"  {q['id']}: {status} ({rec['seconds']} s)", flush=True)
                errors_in_a_row = errors_in_a_row + 1 if error else 0
                if errors_in_a_row >= STOP_AFTER_ERRORS:
                    print(f"stopped: {STOP_AFTER_ERRORS} questions in a row failed at {provider}; it seems to be "
                          f"down or overloaded. Run the same command later: the failed questions are asked again.")
                    break
        except KeyboardInterrupt:
            print("stopped by you (Ctrl+C). Run the same command again to continue where it stopped.")
    if client:
        print(f"requests used: {client.calls} of {client.max_calls}")
    return path


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    p = argparse.ArgumentParser(description=__doc__.split("\n\n")[0])
    p.add_argument("--provider", required=True, choices=["groq", "hf", "gemini", "openai"])
    p.add_argument("--model", default="", help="model id (default: the provider's default, see llm_client.py)")
    p.add_argument("--questions", default="", help="comma-separated ids (default: all)")
    p.add_argument("--max-calls", type=int, default=120, help="hard cap on requests in this run (default 120)")
    p.add_argument("--set", default="dev", choices=sorted(SETS), help="question set (default: dev)")
    a = p.parse_args(argv)
    ids = {x.strip() for x in a.questions.split(",") if x.strip()}
    try:
        path = run(a.provider, a.model, ids, a.max_calls, question_set=a.set)
    except PermissionError as e:
        print(f"run_eval: {e}", file=sys.stderr)
        return 2
    print(f"Wrote {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
