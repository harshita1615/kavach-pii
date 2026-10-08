"""English context words that suggest a nearby value is a given entity type.

Matched case-insensitively on word boundaries.
"""

from kavach.types import EntityType

KEYWORDS: dict[EntityType, tuple[str, ...]] = {
    EntityType.AADHAAR: ("aadhaar", "aadhar", "adhaar", "adhar", "uid", "uidai", "uid number"),
    EntityType.PAN: ("pan", "pan card", "pan number", "permanent account number", "income tax"),
    EntityType.UPI: ("upi", "upi id", "vpa", "gpay", "google pay", "phonepe", "paytm", "bhim"),
    EntityType.IFSC: ("ifsc", "ifsc code", "branch code", "branch"),
    EntityType.BANK_ACCOUNT: (
        "account",
        "account no",
        "account number",
        "acct",
        "acc",
        "acc no",
        "a/c",
        "a/c no",
        "bank",
        "savings",
        "current account",
        "beneficiary",
        "neft",
        "imps",
        "rtgs",
        "ifsc",
        "deposit",
        "credit to",
        "transfer to",
    ),
    EntityType.PHONE: (
        "phone",
        "mobile",
        "mob",
        "ph",
        "cell",
        "call",
        "contact",
        "whatsapp",
        "sms",
        "otp",
        "number",
    ),
    EntityType.GSTIN: ("gst", "gstin", "gst no", "gst number", "gstn"),
    EntityType.EMAIL: ("email", "e-mail", "mail", "mail id"),
}
