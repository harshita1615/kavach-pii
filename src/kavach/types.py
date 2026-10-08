"""Core data structures shared by detectors, the pipeline and masking.

Privacy rule: a Detection never holds the matched text, only its position.
Its repr, str and any error raised from it are therefore safe to log.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class EntityType(str, Enum):
    """Entity types supported in v1. The value doubles as the placeholder prefix."""

    AADHAAR = "AADHAAR"
    PAN = "PAN"
    UPI = "UPI"
    IFSC = "IFSC"
    BANK_ACCOUNT = "BANK_ACCOUNT"
    PHONE = "PHONE"
    GSTIN = "GSTIN"
    EMAIL = "EMAIL"

    def __str__(self) -> str:
        return self.value


@dataclass(frozen=True, slots=True)
class Detection:
    """One detected entity: the span text[start:end] of type entity_type.

    score is a confidence in [0, 1]. Detectors set a base score from format and
    checksum validation; the context scorer adjusts it later in the pipeline.
    """

    entity_type: EntityType
    start: int
    end: int
    score: float
    detector: str

    def __post_init__(self) -> None:
        if not 0 <= self.start < self.end:
            raise ValueError(f"invalid span: start={self.start}, end={self.end}")
        if not 0.0 <= self.score <= 1.0:
            raise ValueError(f"score must be in [0, 1], got {self.score}")

    def text_in(self, text: str) -> str:
        """Return the detected value from the text it was found in."""
        return text[self.start : self.end]
