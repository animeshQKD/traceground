# Contributing

Thank you for helping. The most useful contributions are real cases: an AI answer that traceground
flagged although it was correct, or an error it missed. Please open an issue with one of the templates.

## Rules every check follows

1. **When a check is unsure, it stays silent.** A false alarm on a correct answer counts as much as a
   missed error.
2. Every check has tests for errors it must catch **and** for correct answers it must pass, taken from
   real answers wherever possible.
3. Nothing is deleted or rewritten silently. Automatic fixes are opt-in and only where the fix is certain.
4. The core uses the standard library only. Tests run offline: no network, no API keys, no models.
5. Every number in the README comes from a run, with its date.

## Development setup

```
conda create -n traceground python=3.11 -y
conda activate traceground
pip install -e ".[test]"
python -m pytest
```

## Pull requests

Keep a pull request to one change, with its tests, and add a line to `CHANGELOG.md`.
