"""Email address detector.

A practical subset of RFC 5322: local part of letters, digits and ._%+-, then a
domain of dot-separated labels ending in a 2-24 letter TLD. Quoted local parts
and IP-literal domains are not covered.
Source: https://en.wikipedia.org/wiki/Email_address#Syntax
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

_LABEL = r"[A-Za-z0-9](?:[A-Za-z0-9\-]{0,61}[A-Za-z0-9])?"

_PATTERN = re.compile(
    r"(?<![\w.%+\-])"
    r"[A-Za-z0-9][A-Za-z0-9._%+\-]{0,63}"
    rf"@{_LABEL}(?:\.{_LABEL})*\.[A-Za-z]{{2,24}}"
    # A trailing sentence dot is fine; a dot that starts another label is not.
    r"(?![\w\-@]|\.[A-Za-z0-9])"
)

BASE_SCORE = 0.9


class EmailDetector(Detector):
    entity_type = EntityType.EMAIL
    name = "email"

    def detect(self, text: str) -> list[Detection]:
        return [
            Detection(self.entity_type, m.start(), m.end(), BASE_SCORE, self.name)
            for m in _PATTERN.finditer(text)
        ]

    def normalize(self, value: str) -> str:
        return value.lower()
