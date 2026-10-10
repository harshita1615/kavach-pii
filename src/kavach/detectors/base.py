"""Interface every entity detector implements."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import ClassVar

from kavach.types import Detection, EntityType


class Detector(ABC):
    """Finds candidate spans of one entity type and keeps only those that validate.

    Detectors must be pure: no logging, no I/O, and no raw text in exceptions.
    """

    entity_type: ClassVar[EntityType]
    name: ClassVar[str]
    # True if the detector only reports matches that already have context, in
    # which case the pipeline does not add the context boost a second time.
    requires_context: ClassVar[bool] = False

    @abstractmethod
    def detect(self, text: str) -> list[Detection]:
        """Return validated detections in order of position."""

    def normalize(self, value: str) -> str:
        """Canonical form of a detected value, so formatting variants of the
        same value (e.g. spaced vs unspaced Aadhaar) share one placeholder."""
        return value
