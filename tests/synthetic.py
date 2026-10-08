"""Synthetic, format-valid test values. Never replace these with real data."""

from kavach.validators import gstin_checksum, verhoeff

AADHAAR = "23456789012" + verhoeff.check_digit("23456789012")
AADHAAR_SPACED = f"{AADHAAR[:4]} {AADHAAR[4:8]} {AADHAAR[8:]}"
AADHAAR_2 = "98765432109" + verhoeff.check_digit("98765432109")
PAN = "ABCPE1234F"
PAN_2 = "AAAPZ9876K"
UPI = "rahul@okaxis"
IFSC = "SBIN0001234"
BANK = "30012345678"
PHONE = "+91 98765 43210"
GSTIN = "27ABCPE1234F1Z" + gstin_checksum.check_char("27ABCPE1234F1Z")
EMAIL = "rahul@example.com"

KITCHEN_SINK = (
    f"Hi, mera aadhaar {AADHAAR_SPACED} hai aur PAN {PAN}. "
    f"Refund to UPI {UPI} or a/c {BANK} (IFSC {IFSC}). "
    f"Call {PHONE} or email {EMAIL}. GSTIN {GSTIN}."
)
