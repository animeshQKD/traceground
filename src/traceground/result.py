"""What a check returns: a Result with a verdict and a list of Findings, each pointing at a span of the
answer. Plain dataclasses, convertible to a dict and to JSON."""
import json
from dataclasses import asdict, dataclass, field
from typing import Optional

VERDICTS = ("ok", "problems", "unsure")
SEVERITIES = ("high", "low")        # high: wrong, fix before the answer is shown; low: imprecise (e.g. cut short)


@dataclass
class Finding:
    check: str                      # number, quote, value-to-field, argument, failed-call, tool-not-called,
                                    # self-talk or self-contradiction
    severity: str                   # "high" or "low"
    start: int                      # span in the answer: answer[start:end] == text
    end: int
    text: str
    sentence: str                   # the sentence of the answer that contains the span
    message: str                    # plain words, for the person reading the report
    evidence: list = field(default_factory=list)    # what the evidence actually says: [{"source", "value", "context"}]
    suggestion: Optional[str] = None                # a replacement for `text`, only when it is certain

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class Result:
    verdict: str                    # "ok", "problems" (a high finding) or "unsure" (no evidence, nothing found)
    findings: list
    summary: str
    stats: dict = field(default_factory=dict)
    corrected_answer: Optional[str] = None          # only when every fix is certain (not produced yet)

    @property
    def ok(self) -> bool:
        return self.verdict == "ok"

    def to_dict(self) -> dict:
        return {"verdict": self.verdict, "summary": self.summary,
                "findings": [f.to_dict() for f in self.findings],
                "corrected_answer": self.corrected_answer, "stats": dict(self.stats)}

    def to_json(self, indent: int = 2) -> str:
        return json.dumps(self.to_dict(), indent=indent, ensure_ascii=False)

    def to_text(self) -> str:
        """A short plain-text report: the verdict, then one numbered block per finding."""
        lines = [f"{self.verdict.upper()}: {self.summary}"]
        for i, f in enumerate(self.findings, 1):
            tag = "" if f.severity == "high" else " (minor)"
            lines.append(f"{i}. [{f.check}{tag}] \"{f.text}\" in: {f.sentence}")
            lines.append(f"   {f.message}")
        return "\n".join(lines)
