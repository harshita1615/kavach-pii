"""Detection pipeline: detect -> validate -> context score -> resolve overlaps.

Detectors already validate (checksums, structure). The engine adds the context
boost, applies the confidence threshold, and resolves overlapping spans so the
result is a clean, non-overlapping list ordered by position.
"""

from __future__ import annotations

import dataclasses
from collections.abc import Iterable

from kavach.context import has_context
from kavach.detectors import ALL_DETECTORS, Detector
from kavach.types import Detection, EntityType

DEFAULT_THRESHOLD = 0.5
CONTEXT_BOOST = 0.2

# Tie-break when score and length are equal: more specific entity types first.
SPECIFICITY = (
    EntityType.GSTIN,
    EntityType.UPI,
    EntityType.EMAIL,
    EntityType.IFSC,
    EntityType.PAN,
    EntityType.AADHAAR,
    EntityType.PHONE,
    EntityType.BANK_ACCOUNT,
)
_SPECIFICITY_RANK = {entity_type: rank for rank, entity_type in enumerate(SPECIFICITY)}


def parse_entities(entities: Iterable[EntityType | str] | None) -> frozenset[EntityType]:
    """Turn user-supplied entity names into EntityTypes; None means all."""
    if entities is None:
        return frozenset(EntityType)
    parsed = set()
    for entity in entities:
        if isinstance(entity, EntityType):
            parsed.add(entity)
            continue
        try:
            parsed.add(EntityType(str(entity).upper()))
        except ValueError:
            valid = ", ".join(e.value for e in EntityType)
            raise ValueError(f"unknown entity {entity!r}; expected one of: {valid}") from None
    return frozenset(parsed)


def resolve_overlaps(detections: Iterable[Detection]) -> list[Detection]:
    """Keep a non-overlapping subset, preferring higher score, then longer span,
    then the more specific entity type. Returned in order of position."""
    ranked = sorted(
        detections,
        key=lambda d: (-d.score, -(d.end - d.start), _SPECIFICITY_RANK[d.entity_type], d.start),
    )
    kept: list[Detection] = []
    for candidate in ranked:
        if all(candidate.end <= k.start or candidate.start >= k.end for k in kept):
            kept.append(candidate)
    return sorted(kept, key=lambda d: d.start)


class Engine:
    def __init__(
        self,
        entities: Iterable[EntityType | str] | None = None,
        threshold: float = DEFAULT_THRESHOLD,
    ) -> None:
        if not 0.0 <= threshold <= 1.0:
            raise ValueError(f"threshold must be in [0, 1], got {threshold}")
        self.entities = parse_entities(entities)
        self.threshold = threshold
        self._detectors: dict[EntityType, Detector] = {
            cls.entity_type: cls() for cls in ALL_DETECTORS if cls.entity_type in self.entities
        }

    def analyze(self, text: str) -> list[Detection]:
        """Detect all enabled entities in text."""
        if not text:
            return []
        candidates = []
        for detector in self._detectors.values():
            for detection in detector.detect(text):
                detection = self._apply_context(text, detection)
                if detection.score >= self.threshold:
                    candidates.append(detection)
        return resolve_overlaps(candidates)

    def normalize(self, detection: Detection, text: str) -> str:
        """Canonical form of a detected value, used to give repeats one placeholder."""
        return self._detectors[detection.entity_type].normalize(detection.text_in(text))

    @staticmethod
    def _apply_context(text: str, detection: Detection) -> Detection:
        if has_context(text, detection.start, detection.end, detection.entity_type):
            boosted = min(1.0, round(detection.score + CONTEXT_BOOST, 4))
            return dataclasses.replace(detection, score=boosted)
        return detection
