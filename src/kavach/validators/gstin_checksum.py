"""GSTIN check character (15th character).

Each of the first 14 characters maps to a value in base 36 (0-9, A-Z). Values at
odd positions (1-indexed even) are doubled; each product contributes
product // 36 + product % 36. The check value is (36 - sum % 36) % 36.
Source: https://en.wikipedia.org/wiki/Goods_and_Services_Tax_(India)#GSTIN
"""

from __future__ import annotations

_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
_VALUES = {ch: i for i, ch in enumerate(_CHARSET)}


def _require_base36(value: str, length: int) -> str:
    upper = value.upper()
    # Deliberately does not echo the input: it may be a real GSTIN.
    if len(upper) != length or any(ch not in _VALUES for ch in upper):
        raise ValueError(f"expected {length} characters from 0-9 and A-Z")
    return upper


def check_char(first14: str) -> str:
    """Return the check character for the first 14 characters of a GSTIN."""
    total = 0
    for i, ch in enumerate(_require_base36(first14, 14)):
        product = _VALUES[ch] * (2 if i % 2 else 1)
        total += product // 36 + product % 36
    return _CHARSET[(36 - total % 36) % 36]


def is_valid(gstin: str) -> bool:
    """True if the 15th character of gstin is its correct check character."""
    upper = _require_base36(gstin, 15)
    return check_char(upper[:14]) == upper[14]
