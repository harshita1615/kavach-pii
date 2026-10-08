"""Hindi context words, in romanised Hinglish and in Devanagari.

Romanised words are matched on word boundaries; Devanagari words are matched as
substrings, because vowel signs break Python's \\b inside Devanagari words.
"""

from kavach.types import EntityType

KEYWORDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.AADHAAR: ("aadhaar card", "aadhar card", "आधार", "आधार कार्ड"),
    EntityType.PAN: ("pan card", "पैन", "पैन कार्ड"),
    EntityType.UPI: ("upi id", "यूपीआई"),
    EntityType.IFSC: ("आईएफएससी",),
    EntityType.BANK_ACCOUNT: (
        "khata",
        "khaata",
        "khate",
        "khaate",
        "khata number",
        "khata sankhya",
        "खाता",
        "खाते",
        "बैंक",
        "अकाउंट",
        "खाता संख्या",
    ),
    EntityType.PHONE: (
        "mobile number",
        "phone number",
        "nambar",
        "numbar",
        "fone",
        "मोबाइल",
        "फ़ोन",
        "फोन",
        "नंबर",
    ),
    EntityType.GSTIN: ("जीएसटी",),
    EntityType.EMAIL: ("ईमेल",),
}
