"""Smoke tests of the 0.0.1 skeleton: the installed package, its version and its command line."""
import re
import subprocess
import sys
from importlib.metadata import entry_points
from pathlib import Path

import pytest

import traceground
from traceground.cli import main

ROOT = Path(__file__).resolve().parents[1]


def _pyproject_version() -> str:
    text = (ROOT / "pyproject.toml").read_text(encoding="utf-8")
    return re.search(r'^version = "([^"]+)"', text, re.M).group(1)


def test_version_is_the_one_in_pyproject():
    assert traceground.__version__ == _pyproject_version()


def test_cli_version(capsys):
    with pytest.raises(SystemExit) as e:
        main(["--version"])
    assert e.value.code == 0
    assert capsys.readouterr().out.strip() == f"traceground {traceground.__version__}"


def test_cli_without_arguments_prints_help_and_exits_0(capsys):
    assert main([]) == 0
    assert "usage: traceground" in capsys.readouterr().out


def test_python_dash_m():
    out = subprocess.run([sys.executable, "-m", "traceground", "--version"],
                         capture_output=True, text=True, check=True).stdout
    assert out.strip() == f"traceground {traceground.__version__}"


def test_console_script_is_registered():
    scripts = {ep.name: ep.value for ep in entry_points(group="console_scripts")}
    assert scripts.get("traceground") == "traceground.cli:main"


def test_core_imports_only_the_standard_library():
    code = ("import sys; before = set(sys.modules); import traceground, traceground.cli, traceground.numbers; "
            "print('\\n'.join(sorted(set(sys.modules) - before)))")
    new = subprocess.run([sys.executable, "-c", code], capture_output=True, text=True, check=True).stdout.split()
    third_party = [m for m in new
                   if m.split(".")[0] not in sys.stdlib_module_names and m.split(".")[0] != "traceground"]
    assert third_party == []


def test_package_is_typed():
    assert (Path(traceground.__file__).parent / "py.typed").exists()
