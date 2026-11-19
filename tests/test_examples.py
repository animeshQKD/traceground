"""The files in examples/ must keep showing what examples/README.md says they show."""
from pathlib import Path

import pytest

from traceground.cli import main

EX = Path(__file__).resolve().parents[1] / "examples"
if not EX.exists():
    pytest.skip("no examples folder (e.g. in the source distribution)", allow_module_level=True)


def test_loan_chat(capsys):
    assert main(["--trace", str(EX / "loan_chat.json")]) == 1
    assert "The question asks for 5-year, but loan_cost was called with years=3." in capsys.readouterr().out


def test_game_calls(capsys):
    assert main(["--trace", str(EX / "game_calls.json"), "--answer", str(EX / "game_answer.txt")]) == 1
    out = capsys.readouterr().out
    assert '"7 rebounds": the tool results give rebounds = 11' in out and '"11 assists"' in out
