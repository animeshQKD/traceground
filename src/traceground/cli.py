"""The traceground command line.

    traceground --answer answer.txt --sources a.txt b.txt [--question question.txt] [--json]
    traceground --trace chat.json            (OpenAI-style messages: question and answer taken from it)
    traceground --trace calls.json --answer answer.txt --question question.txt

Exit codes, for use in tests and CI:
    0  ok: nothing unsupported (minor findings may be listed)
    1  problems: at least one finding of severity "high" (an unsupported number or quote, a wrong field
       or argument, a failed call reported as a result, a tool claimed but not called, thinking aloud,
       a self-contradiction)
    2  usage error (bad arguments, a file that cannot be read)
    3  unsure: the answer has numbers but no sources or question were given
"""
import argparse
import json
import sys
from pathlib import Path

from traceground import __version__
from traceground.api import check_answer

EXIT = {"ok": 0, "problems": 1, "unsure": 3}


def _read(path: str) -> str:
    if path == "-":
        return sys.stdin.read()
    return Path(path).read_text(encoding="utf-8-sig")      # utf-8-sig: files saved by Notepad start with a BOM


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):              # Windows consoles: print °, ≈, − without crashing
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass
    parser = argparse.ArgumentParser(
        prog="traceground",
        description="Check an AI answer against its sources and tool calls: every number the evidence does not "
                    "support, every quote not in the source it cites, every value attached to the wrong field, "
                    "every tool argument that differs from the question, failed calls reported as results, tools "
                    "claimed but not called, thinking aloud and self-contradictions. "
                    "Exit code 0 ok, 1 problems, 2 usage error, 3 unsure.")
    parser.add_argument("--version", action="version", version=f"traceground {__version__}")
    parser.add_argument("--answer", metavar="FILE", help="the answer to check (a text file, or - for standard input)")
    parser.add_argument("--sources", metavar="FILE", nargs="+", default=[],
                        help="source text files; each file's name is its id in the report")
    parser.add_argument("--question", metavar="FILE", help="the question, as a text file (its numbers count as evidence)")
    parser.add_argument("--trace", metavar="FILE",
                        help="tool calls as JSON: a list of {name, args, result}, or OpenAI-style chat messages "
                             "(then --answer and --question may be left out)")
    parser.add_argument("--json", action="store_true", help="print the result as JSON")
    parser.add_argument("--check-small-integers", action="store_true",
                        help="also check plain integers from 0 to 10 (left out by default)")
    parser.add_argument("--no-percent-as-fraction", action="store_true",
                        help="do not accept 7%% for 0.07 (accepted by default)")
    parser.add_argument("--no-quotes", action="store_true", help="do not check quotes")
    parser.add_argument("--no-wording", action="store_true",
                        help="do not check the wording (thinking aloud, self-contradiction)")
    args = parser.parse_args(argv)
    if not args.answer and not args.trace:
        parser.print_help()
        return 0
    try:
        answer = _read(args.answer) if args.answer else None
        trace = json.loads(_read(args.trace)) if args.trace else None
        sources = {}
        for p in args.sources:
            sid = Path(p).name
            if sid in sources:
                parser.error(f"two sources have the same file name: {sid}")
            sources[sid] = _read(p)
        question = _read(args.question) if args.question else ""
    except OSError as e:
        print(f"traceground: cannot read {e.filename}: {e.strerror}", file=sys.stderr)
        return 2
    except json.JSONDecodeError as e:
        print(f"traceground: {args.trace} is not valid JSON: {e}", file=sys.stderr)
        return 2
    try:
        result = check_answer(answer, sources, question, trace, percent_as_fraction=not args.no_percent_as_fraction,
                              check_small_integers=args.check_small_integers, check_quotes=not args.no_quotes,
                              check_wording=not args.no_wording)
    except (TypeError, ValueError) as e:
        print(f"traceground: {e}", file=sys.stderr)
        return 2
    print(result.to_json() if args.json else result.to_text())
    return EXIT[result.verdict]


if __name__ == "__main__":
    sys.exit(main())
