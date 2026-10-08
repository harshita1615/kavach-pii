"""Placeholder format shared by masking, unmasking and the stream buffer."""

from __future__ import annotations

import re

from kavach.types import EntityType

_TYPES = "|".join(sorted((e.value for e in EntityType), key=len, reverse=True))

# Tolerates small LLM edits: case changes and stray spaces, e.g. "[ pan_1 ]".
PATTERN = re.compile(rf"\[\s*({_TYPES})\s*_\s*(\d+)\s*\]", re.IGNORECASE)

# Longest a placeholder can plausibly be while still arriving in pieces.
MAX_LENGTH = 32


def make(entity_type: EntityType, number: int) -> str:
    return f"[{entity_type.value}_{number}]"


def key(entity_type_name: str, number: str) -> str:
    """Canonical lookup key for a matched placeholder, whatever its spacing or case."""
    return f"[{entity_type_name.upper()}_{int(number)}]"
