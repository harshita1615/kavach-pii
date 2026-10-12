"""PAN (Permanent Account Number) detector.

Format: 5 letters, 4 digits, 1 letter (e.g. ABCPE1234F). The 4th letter is the
holder type:
  P person, C company, H HUF, F firm, A association of persons, T trust,
  B body of individuals, L local authority, J artificial juridical person,
  G government.
The 10th letter is an alphabetic check character whose algorithm is not
published, so it is not validated.
Source: https://en.wikipedia.org/wiki/Permanent_account_number

Case-insensitive, and tolerant of a single space or dash between the letter,
digit and final-letter blocks.
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

HOLDER_TYPES = "ABCFGHJLPT"

_PATTERN = re.compile(
    # Not part of a longer alphanumeric token, e.g. the PAN inside a GSTIN.
    r"(?<![A-Za-z0-9])"
    rf"[A-Z]{{3}}[{HOLDER_TYPES}][A-Z][ -]?[0-9]{{4}}[ -]?[A-Z]"
    r"(?![A-Za-z0-9])",
    re.IGNORECASE,
)

_SEPARATORS = re.compile(r"[ -]")

BASE_SCORE = 0.85


class PanDetector(Detector):
    entity_type = EntityType.PAN
    name = "pan"

    def detect(self, text: str) -> list[Detection]:
        return [
            Detection(self.entity_type, m.start(), m.end(), BASE_SCORE, self.name)
            for m in _PATTERN.finditer(text)
        ]

    def normalize(self, value: str) -> str:
        return _SEPARATORS.sub("", value).upper()
