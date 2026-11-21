"""traceground: checks an AI answer against its sources or its tool-call trace.

    from traceground import check_answer
    result = check_answer(answer, sources=["...", "..."], question="...")
    print(result.verdict, result.summary)
    for f in result.findings:
        print(f.text, f.message)

    # or with a tool-call trace: a list of {"name", "args", "result"}, or OpenAI-style chat messages
    result = check_answer(answer, question="...", trace=[{"name": "loan_cost", "args": {...}, "result": {...}}])
    result = check_messages(messages)

Beta (0.2.0): numbers, quotes, value-to-field and argument binding, failed calls, tools
never called, thinking aloud and self-contradiction. See https://github.com/animeshQKD/traceground.
"""
from importlib.metadata import PackageNotFoundError, version

from traceground.api import check_answer, check_messages, normalize_sources
from traceground.result import Finding, Result

try:
    __version__ = version("traceground")
except PackageNotFoundError:          # running from a source tree that was not installed
    __version__ = "0.0.0+unknown"

__all__ = ["__version__", "check_answer", "check_messages", "normalize_sources", "Finding", "Result"]
