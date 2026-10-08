"""Aadhaar number detector.

Format: 12 digits, first digit 2-9 (UIDAI does not issue numbers starting with
0 or 1), last digit a Verhoeff check digit. Usually written 4-4-4, separated by
spaces, dashes or (in pasted text) line breaks.
Sources: https://en.wikipedia.org/wiki/Aadhaar,
https://en.wikipedia.org/wiki/Verhoeff_algorithm

A random 12-digit number starting 2-9 passes the checksum about 1 time in 10,
so context scoring (later in the pipeline) is still needed for precision.
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType
from kavach.validators import verhoeff

# Between groups: a dash with optional spaces, runs of spaces/tabs, or one line break.
_SEP = r"(?:[ \t]*-[ \t]*|[ \t]+|\r?\n)?"

_PATTERN = re.compile(
    # Not glued to other word characters, and not preceded by a 4-digit group
    # (which would make this the tail of a 16-digit card number).
    r"(?<!\w)(?<!\b\d{4}[ -])"
    rf"[2-9]\d{{3}}{_SEP}\d{{4}}{_SEP}\d{{4}}"
    # Not followed by another 4-digit group (card number) or word character.
    r"(?![ -]?\d{4}\b)(?!\w)"
)

_NON_DIGITS = re.compile(r"\D")

BASE_SCORE = 0.85


class AadhaarDetector(Detector):
    entity_type = EntityType.AADHAAR
    name = "aadhaar"

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for match in _PATTERN.finditer(text):
            digits = self.normalize(match.group())
            if len(digits) == 12 and verhoeff.is_valid(digits):
                detections.append(
                    Detection(self.entity_type, match.start(), match.end(), BASE_SCORE, self.name)
                )
        return detections

    def normalize(self, value: str) -> str:
        return _NON_DIGITS.sub("", value)
