"""Context lookup: is there a keyword for an entity type near a span?

Kept independent of the detectors. The bank-account detector requires context;
the pipeline uses it to raise confidence for other entity types.
"""

from __future__ import annotations

import re
from functools import cache

from kavach.context import keywords_en, keywords_hi
from kavach.types import EntityType

WINDOW_BEFORE = 50
WINDOW_AFTER = 30


def keywords_for(entity_type: EntityType) -> tuple[str, ...]:
    """All context words (English, Hinglish, Devanagari) for an entity type."""
    return keywords_en.KEYWORDS.get(entity_type, ()) + keywords_hi.KEYWORDS.get(entity_type, ())


@cache
def _keyword_pattern(entity_type: EntityType) -> re.Pattern[str]:
    parts = []
    # Longest first, so "account number" wins over "account" in the alternation.
    for keyword in sorted(set(keywords_for(entity_type)), key=len, reverse=True):
        escaped = re.escape(keyword)
        if keyword.isascii():
            escaped = rf"(?<![a-z0-9]){escaped}(?![a-z0-9])"
        parts.append(escaped)
    return re.compile("|".join(parts), re.IGNORECASE)


def _alternation(words: tuple[str, ...]) -> str:
    parts = []
    for word in sorted(set(words), key=len, reverse=True):
        escaped = r"\s+".join(re.escape(part) for part in word.split())
        parts.append(rf"(?<![a-z0-9]){escaped}" if word.isascii() else escaped)
    return "|".join(parts)


# A not-PII label, an optional "no./number/id/#", an optional "is/hai/was",
# optional punctuation, then the span. Must end exactly where the span starts.
_NOT_PII_LABEL = re.compile(
    rf"(?:{_alternation(keywords_en.NOT_PII_LABELS + keywords_hi.NOT_PII_LABELS)})"
    r"(?:\s*(?:no\.?|number|num|id|#))?"
    r"(?:\s+(?:is|hai|was))?"
    r"\s*[:#.\-]?\s*$",
    re.IGNORECASE,
)

LABEL_WINDOW = 30


def has_not_pii_label(text: str, start: int) -> bool:
    """True if text[start:] is directly preceded by a label such as "Order no."
    or "UTR", which says the value that follows is not personal data."""
    return _NOT_PII_LABEL.search(text[max(0, start - LABEL_WINDOW) : start]) is not None


def has_context(
    text: str,
    start: int,
    end: int,
    entity_type: EntityType,
    before: int = WINDOW_BEFORE,
    after: int = WINDOW_AFTER,
) -> bool:
    """True if a context word for entity_type appears within the window
    around text[start:end]. The span itself is not searched."""
    left = text[max(0, start - before) : start]
    right = text[end : end + after]
    pattern = _keyword_pattern(entity_type)
    # Searched separately so a keyword can't be formed across the span.
    return pattern.search(left) is not None or pattern.search(right) is not None
