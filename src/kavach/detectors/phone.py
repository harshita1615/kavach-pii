"""Indian mobile number detector.

Format: 10 digits starting 6-9, optionally prefixed with +91, 0091, (+91), 91
or a trunk 0. Commonly written contiguous, 5-5 or 3-3-4.
Source: https://en.wikipedia.org/wiki/Telephone_numbers_in_India

Numbers with an international prefix score higher. Bare 10-digit numbers score
lower because order IDs and amounts can look the same; context decides.
Landlines are not covered in v1.
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

_PATTERN = re.compile(
    r"(?<![\w+])"
    r"(?P<prefix>(?:\+|00)91[ \-]?|\(\+?91\)[ \-]?|91[ \-]?|0)?"
    r"(?:[6-9]\d{9}|[6-9]\d{4}[ \-]\d{5}|[6-9]\d{2}[ \-]\d{3}[ \-]\d{4})"
    r"(?!\w|[ \-]?\d)"
)

_NON_DIGITS = re.compile(r"\D")

INTERNATIONAL_PREFIX_SCORE = 0.85
BASE_SCORE = 0.6


class PhoneDetector(Detector):
    entity_type = EntityType.PHONE
    name = "phone"

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for m in _PATTERN.finditer(text):
            international = (m.group("prefix") or "").startswith(("+", "00", "(+"))
            score = INTERNATIONAL_PREFIX_SCORE if international else BASE_SCORE
            detections.append(Detection(self.entity_type, m.start(), m.end(), score, self.name))
        return detections

    def normalize(self, value: str) -> str:
        return _NON_DIGITS.sub("", value)[-10:]
