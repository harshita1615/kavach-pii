"""UPI ID (Virtual Payment Address) detector.

Format: username@handle, where handle names the payment app or bank (PSP).
Unlike an email address, the handle has no dot-separated domain after it.
IDs with a known handle score high; unknown handles score low so that context
scoring decides. The handle list is not exhaustive.
Sources: https://www.npci.org.in/what-we-do/upi/3rd-party-apps,
https://www.npci.org.in/what-we-do/upi/live-members
"""

from __future__ import annotations

import re

from kavach.detectors.base import Detector
from kavach.types import Detection, EntityType

KNOWN_HANDLES = frozenset(
    {
        # Google Pay
        "okaxis",
        "okhdfcbank",
        "okicici",
        "oksbi",
        # PhonePe
        "ybl",
        "ibl",
        "axl",
        # Paytm
        "paytm",
        "pthdfc",
        "ptsbi",
        "ptyes",
        "ptaxis",
        # Amazon Pay
        "apl",
        "yapl",
        "rapl",
        # WhatsApp
        "waaxis",
        "wahdfcbank",
        "waicici",
        "wasbi",
        # BHIM and generic
        "upi",
        # Other apps
        "axisbank",
        "axisb",
        "freecharge",
        "ikwik",
        "jupiteraxis",
        "naviaxis",
        "fam",
        "superyes",
        "slc",
        "kbaxis",
        "abfspay",
        "pingpay",
        "yesg",
        "goaxb",
        "payzapp",
        "airtel",
        "jio",
        "jiopay",
        "cred",
        "cnrb",
        "barodampay",
        "mahb",
        "pnb",
        # Bank handles
        "sbi",
        "hdfcbank",
        "icici",
        "kotak",
        "kmbl",
        "yesbank",
        "yesbankltd",
        "idfcfirst",
        "idfcbank",
        "indus",
        "federal",
        "fbl",
        "rbl",
        "aubank",
        "dbs",
        "hsbc",
        "sc",
        "citi",
        "citigold",
        "unionbank",
        "unionbankofindia",
        "uboi",
        "boi",
        "cbin",
        "centralbank",
        "indianbank",
        "idbi",
        "iob",
        "uco",
        "equitas",
        "kbl",
        "kvb",
        "dcb",
        "jkb",
        "tjsb",
        "sib",
    }
)

_PATTERN = re.compile(
    # Not a continuation of a longer token or address.
    r"(?<![\w.\-@])"
    r"[a-z0-9][a-z0-9._\-]{1,255}@(?P<handle>[a-z][a-z0-9]{1,63})"
    # Not followed by a domain (".com"), another word character or a second "@".
    r"(?![\w@]|[.\-][a-z0-9])",
    re.IGNORECASE,
)

KNOWN_HANDLE_SCORE = 0.9
UNKNOWN_HANDLE_SCORE = 0.4


class UpiDetector(Detector):
    entity_type = EntityType.UPI
    name = "upi"

    def detect(self, text: str) -> list[Detection]:
        detections = []
        for m in _PATTERN.finditer(text):
            known = m.group("handle").lower() in KNOWN_HANDLES
            score = KNOWN_HANDLE_SCORE if known else UNKNOWN_HANDLE_SCORE
            detections.append(Detection(self.entity_type, m.start(), m.end(), score, self.name))
        return detections

    def normalize(self, value: str) -> str:
        return value.lower()
