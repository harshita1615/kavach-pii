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
