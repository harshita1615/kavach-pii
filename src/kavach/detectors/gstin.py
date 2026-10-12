"""GSTIN (GST Identification Number) detector.

Format: 15 characters -
  2-digit state code, 10-character PAN of the holder, 1 entity number (1-9, A-Z),
  the letter Z (default), and a base-36 check character.
Source: https://en.wikipedia.org/wiki/Goods_and_Services_Tax_(India)#GSTIN

State codes are 01-38, 97 (other territory) and 99 (centre jurisdiction).
Special GSTINs (TDS/TCS deductors, non-residents, UN bodies) use other
structures and are not covered in v1.
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.detectors.pan import HOLDER_TYPES
from kavach.types import Detection, EntityType
from kavach.validators import gstin_checksum

_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])"
    rf"(?P<state>[0-9]{{2}})[A-Z]{{3}}[{HOLDER_TYPES}][A-Z][0-9]{{4}}[A-Z][1-9A-Z]Z[0-9A-Z]"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

VALID_STATE_CODES = frozenset({f"{n:02d}" for n in range(1, 39)} | {"97", "99"})

BASE_SCORE = 0.95


class GstinDetector(Detector):
    entity_type = EntityType.GSTIN
    name = "gstin"

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for m in _PATTERN.finditer(text):
            if m.group("state") in VALID_STATE_CODES and gstin_checksum.is_valid(m.group()):
                detections.append(
                    Detection(self.entity_type, m.start(), m.end(), BASE_SCORE, self.name)
                )
        return detections

    def normalize(self, value: str) -> str:
        return value.upper()
