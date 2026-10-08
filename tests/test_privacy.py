"""Guards for the rule that the package never logs or prints input text."""

from pathlib import Path

import pytest

SRC = Path(__file__).parent.parent / "src" / "kavach"
# cli.py will print results to the user's terminal, but only placeholders/counts.
EXEMPT = {"cli.py"}


@pytest.mark.parametrize(
    "path", [p for p in SRC.rglob("*.py") if p.name not in EXEMPT], ids=lambda p: p.name
)
def test_no_logging_or_printing(path):
    source = path.read_text(encoding="utf-8")
    for forbidden in ("import logging", "print(", "warnings.warn(", "open("):
        assert forbidden not in source, f"{path.name} contains {forbidden!r}"
