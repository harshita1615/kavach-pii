"""Bank account number detector.

Indian account numbers have no common format or checksum: they are 9 to 18
digits depending on the bank. Any long number would match, so a context word
("account", "a/c", "khata", "खाता" ...) is required nearby.
Source for length range: https://www.rbi.org.in/ (no single standard; 9-18 is
the range used by Indian banks in practice).
"""

from __future__ import annotations

import re

from kavach.context import has_context
from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

_PATTERN = re.compile(
    # Not glued to a word, a "+" (phone prefix) or a dash-joined number.
    r"(?<![\w+\-])"
    # Contiguous digits, or groups of 3-6 digits split by single spaces/dashes.
    r"(?:[0-9]{9,18}|[0-9]{3,6}(?:[ \-][0-9]{3,6}){1,5})"
    r"(?!\w|[ \-]?[0-9])"
)

_NON_DIGITS = re.compile(r"[^0-9]")

# Context is already required, so the pipeline does not boost this score again.
# Set so that a number with both phone and bank context resolves to PHONE (more
# specific format), and one with only bank context resolves to BANK_ACCOUNT.
BASE_SCORE = 0.8


class BankAccountDetector(Detector):
    entity_type = EntityType.BANK_ACCOUNT
    name = "bank_account"
    requires_context = True

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for m in _PATTERN.finditer(text):
            digits = self.normalize(m.group())
            if 9 <= len(digits) <= 18 and has_context(text, m.start(), m.end(), self.entity_type):
                detections.append(
                    Detection(self.entity_type, m.start(), m.end(), BASE_SCORE, self.name)
                )
        return detections

    def normalize(self, value: str) -> str:
        return _NON_DIGITS.sub("", value)
