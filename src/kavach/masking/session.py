"""Reversible masking scoped to one session.

The placeholder <-> value mapping lives only in this object's memory. It is
never logged, written to disk or included in repr/str. Drop the session (or
call clear()) when the conversation ends.
"""

from __future__ import annotations

from collections import Counter
from typing import Literal

from kavach.engine import Engine
from kavach.masking import placeholders
from kavach.masking.stream_buffer import StreamUnmasker
from kavach.types import Detection, EntityType

Mode = Literal["mask", "redact", "scan"]
MODES: tuple[str, ...] = ("mask", "redact", "scan")


class MaskingSession:
    """Masks text before the LLM call and restores it afterwards.

    mode="mask"   placeholders, restorable with unmask()
    mode="redact" the same placeholders, but no mapping is kept
    mode="scan"   text is returned unchanged; only counts are recorded
    """

    def __init__(self, engine: Engine, mode: Mode = "mask") -> None:
        if mode not in MODES:
            raise ValueError(f"mode must be one of {', '.join(MODES)}; got {mode!r}")
        self._engine = engine
        self._mode = mode
        self._value_to_placeholder: dict[tuple[EntityType, str], str] = {}
        self._placeholder_to_value: dict[str, str] = {}
        self._next_number: Counter[EntityType] = Counter()
        self._counts: Counter[EntityType] = Counter()

    @property
    def mode(self) -> str:
        return self._mode

    @property
    def counts(self) -> dict[str, int]:
        """Detections per entity type so far. Safe to log: no values."""
        return {entity_type.value: n for entity_type, n in self._counts.items()}

    def mask(self, text: str) -> str:
        detections = self._engine.analyze(text)
        for detection in detections:
            self._counts[detection.entity_type] += 1
        if self._mode == "scan" or not detections:
            return text

        # Placeholder-like strings already in the input (e.g. pasted from an earlier
        # masked message) are never reused, so they can't be confused on unmask.
        taken = {placeholders.key(*m.groups()) for m in placeholders.PATTERN.finditer(text)}
        parts = []
        last = 0
        for detection in detections:
            parts.append(text[last : detection.start])
            parts.append(self._placeholder_for(detection, text, taken))
            last = detection.end
        parts.append(text[last:])

        if self._mode == "redact":
            self._forget_mapping()
        return "".join(parts)

    def unmask(self, text: str) -> str:
        """Replace known placeholders with their original values. Unknown
        placeholders (e.g. invented by the LLM) are left unchanged."""
        if not self._placeholder_to_value:
            return text

        def restore(match):
            canonical = placeholders.key(match.group(1), match.group(2))
            return self._placeholder_to_value.get(canonical, match.group(0))

        return placeholders.PATTERN.sub(restore, text)

    def stream(self) -> StreamUnmasker:
        """Unmasker for a streamed response: feed() each chunk, then flush()."""
        return StreamUnmasker(self.unmask)

    def clear(self) -> None:
        """Forget all mappings and counts."""
        self._forget_mapping()
        self._counts.clear()

    def _placeholder_for(self, detection: Detection, text: str, taken: set[str]) -> str:
        entity_type = detection.entity_type
        key = (entity_type, self._engine.normalize(detection, text))
        existing = self._value_to_placeholder.get(key)
        if existing is not None:
            return existing
        while True:
            self._next_number[entity_type] += 1
            placeholder = placeholders.make(entity_type, self._next_number[entity_type])
            if placeholder not in taken:
                break
        self._value_to_placeholder[key] = placeholder
        self._placeholder_to_value[placeholder] = detection.text_in(text)
        return placeholder

    def _forget_mapping(self) -> None:
        self._value_to_placeholder.clear()
        self._placeholder_to_value.clear()
        self._next_number.clear()

    def __repr__(self) -> str:
        return f"<MaskingSession mode={self._mode} counts={self.counts}>"
