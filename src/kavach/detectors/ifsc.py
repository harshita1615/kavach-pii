"""IFSC (Indian Financial System Code) detector.

Format: 11 characters - 4-letter bank code, a 0 (reserved), then a 6-character
branch code of letters or digits, e.g. SBIN0001234.
Source: https://www.rbi.org.in/Scripts/FAQView.aspx?Id=60

Known bank codes score higher; the list is not exhaustive.
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

KNOWN_BANK_CODES = frozenset(
    {
        "SBIN",  # State Bank of India
        "HDFC",  # HDFC Bank
        "ICIC",  # ICICI Bank
        "UTIB",  # Axis Bank
        "KKBK",  # Kotak Mahindra Bank
        "PUNB",  # Punjab National Bank
        "BARB",  # Bank of Baroda
        "CNRB",  # Canara Bank
        "UBIN",  # Union Bank of India
        "BKID",  # Bank of India
        "IOBA",  # Indian Overseas Bank
        "IDIB",  # Indian Bank
        "UCBA",  # UCO Bank
        "CBIN",  # Central Bank of India
        "MAHB",  # Bank of Maharashtra
        "PSIB",  # Punjab & Sind Bank
        "IBKL",  # IDBI Bank
        "YESB",  # Yes Bank
        "INDB",  # IndusInd Bank
        "IDFB",  # IDFC First Bank
        "FDRL",  # Federal Bank
        "KARB",  # Karnataka Bank
        "KVBL",  # Karur Vysya Bank
        "SIBL",  # South Indian Bank
        "CIUB",  # City Union Bank
        "DCBL",  # DCB Bank
        "RATN",  # RBL Bank
        "AUBL",  # AU Small Finance Bank
        "ESFB",  # Equitas Small Finance Bank
        "UJVN",  # Ujjivan Small Finance Bank
        "JAKA",  # Jammu & Kashmir Bank
        "TMBL",  # Tamilnad Mercantile Bank
        "CSBK",  # CSB Bank
        "DBSS",  # DBS Bank India
        "HSBC",  # HSBC
        "SCBL",  # Standard Chartered
        "CITI",  # Citibank
        "DEUT",  # Deutsche Bank
        "PYTM",  # Paytm Payments Bank
        "AIRP",  # Airtel Payments Bank
        "FINO",  # Fino Payments Bank
        "IPOS",  # India Post Payments Bank
    }
)

_PATTERN = re.compile(
    r"(?<![A-Za-z0-9])[A-Z]{4}0[A-Z0-9]{6}(?![A-Za-z0-9])",
    re.IGNORECASE,
)

KNOWN_BANK_SCORE = 0.9
UNKNOWN_BANK_SCORE = 0.7


class IfscDetector(Detector):
    entity_type = EntityType.IFSC
    name = "ifsc"

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for m in _PATTERN.finditer(text):
            known = m.group()[:4].upper() in KNOWN_BANK_CODES
            score = KNOWN_BANK_SCORE if known else UNKNOWN_BANK_SCORE
            detections.append(Detection(self.entity_type, m.start(), m.end(), score, self.name))
        return detections

    def normalize(self, value: str) -> str:
        return value.upper()
