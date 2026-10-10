"""Fake identifiers that are valid in format (and checksum, where one exists).

Random values can coincide with real ones; that cannot be avoided for formats
like phone numbers. They are never derived from real people's data.
"""

from __future__ import annotations

import random
import re
import string

from kavach.detectors.gstin import VALID_STATE_CODES
from kavach.detectors.ifsc import KNOWN_BANK_CODES
from kavach.detectors.upi import KNOWN_HANDLES
from kavach.validators import gstin_checksum, verhoeff

UPPER = string.ascii_uppercase
DIGITS = string.digits

# Plausible handles that are deliberately NOT in Kavach's known list, so the
# benchmark measures how Kavach handles UPI IDs it has not been told about.
UNLISTED_HANDLES = ("okbizicici", "timecosmos", "ezeepay", "pockets", "yesfam", "hdfcjd")
UNLISTED_BANK_CODES = ("ABCX", "QRTB", "MZNB", "PLKB")

PAN_HOLDER_WEIGHTS = {
    "P": 70,
    "C": 12,
    "F": 6,
    "H": 4,
    "A": 2,
    "T": 2,
    "B": 1,
    "L": 1,
    "J": 1,
    "G": 1,
}
INVALID_HOLDERS = "".join(sorted(set(UPPER) - set(PAN_HOLDER_WEIGHTS)))

EMAIL_DOMAINS = ("example.com", "example.in", "example.org", "mail.example.com", "test.co.in")
UPI_LIKE_EMAIL_DOMAINS = ("paytm.com", "okaxis.in", "ybl.co", "upi.example.com")


def _digits(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(DIGITS) for _ in range(n))


def _letters(rng: random.Random, n: int) -> str:
    return "".join(rng.choice(UPPER) for _ in range(n))


def _ascii_word(name: str) -> str:
    # Faker names can contain spaces and apostrophes (e.g. D’Souza).
    return re.sub(r"[^a-z0-9]", "", name.lower()) or "user"


def username(rng: random.Random, first: str, last: str) -> str:
    first, last = _ascii_word(first), _ascii_word(last)
    style = rng.randrange(5)
    if style == 0:
        return f"{first}.{last}"
    if style == 1:
        return f"{first}{rng.randint(1, 999)}"
    if style == 2:
        return f"{first}_{last[:3]}{rng.randint(10, 99)}"
    if style == 3:
        return f"{first[0]}{last}"
    return f"{first}{last}{rng.randint(1, 9)}"


# --- valid identifiers ---------------------------------------------------------


def aadhaar(rng: random.Random) -> str:
    body = rng.choice("23456789") + _digits(rng, 10)
    number = body + verhoeff.check_digit(body)
    style = rng.choices(("plain", "spaced", "dashed"), weights=(40, 45, 15))[0]
    if style == "plain":
        return number
    sep = " " if style == "spaced" else "-"
    return sep.join((number[:4], number[4:8], number[8:]))


def pan_raw(rng: random.Random, holder: str | None = None) -> str:
    if holder is None:
        holder = rng.choices(list(PAN_HOLDER_WEIGHTS), weights=PAN_HOLDER_WEIGHTS.values())[0]
    return _letters(rng, 3) + holder + _letters(rng, 1) + _digits(rng, 4) + _letters(rng, 1)


def pan(rng: random.Random) -> str:
    value = pan_raw(rng)
    return value.lower() if rng.random() < 0.12 else value


def upi(rng: random.Random, first: str, last: str) -> str:
    handle = (
        rng.choice(UNLISTED_HANDLES) if rng.random() < 0.1 else rng.choice(sorted(KNOWN_HANDLES))
    )
    if rng.random() < 0.2:
        user = rng.choice("6789") + _digits(rng, 9)  # phone-number UPI IDs are common
    else:
        user = username(rng, first, last)
    return f"{user}@{handle}"


def ifsc(rng: random.Random) -> str:
    code = (
        rng.choice(UNLISTED_BANK_CODES)
        if rng.random() < 0.1
        else rng.choice(sorted(KNOWN_BANK_CODES))
    )
    branch = _digits(rng, 6) if rng.random() < 0.8 else _letters(rng, 2) + _digits(rng, 4)
    return f"{code}0{branch}"


def bank_account(rng: random.Random) -> str:
    length = rng.randint(9, 18)
    return rng.choice("123456789") + _digits(rng, length - 1)


def phone(rng: random.Random) -> str:
    number = rng.choice("6789") + _digits(rng, 9)
    style = rng.choices(
        ("plain", "+91 5-5", "+91-", "+91", "0", "5-5", "91"), weights=(35, 20, 10, 10, 10, 10, 5)
    )[0]
    if style == "plain":
        return number
    if style == "+91 5-5":
        return f"+91 {number[:5]} {number[5:]}"
    if style == "+91-":
        return f"+91-{number}"
    if style == "+91":
        return f"+91{number}"
    if style == "0":
        return f"0{number}"
    if style == "5-5":
        return f"{number[:5]} {number[5:]}"
    return f"91{number}"


def gstin(rng: random.Random) -> str:
    state = rng.choice(sorted(VALID_STATE_CODES - {"97", "99"}))
    holder = rng.choice("CFPHT")
    entity = rng.choice("123456789") if rng.random() < 0.9 else rng.choice(UPPER)
    body = f"{state}{pan_raw(rng, holder)}{entity}Z"
    return body + gstin_checksum.check_char(body)


def email(rng: random.Random, first: str, last: str) -> str:
    return f"{username(rng, first, last)}@{rng.choice(EMAIL_DOMAINS)}"


def email_upi_like(rng: random.Random, first: str, last: str) -> str:
    """An email whose domain starts like a UPI handle. Labeled EMAIL."""
    return f"{username(rng, first, last)}@{rng.choice(UPI_LIKE_EMAIL_DOMAINS)}"


# --- hard negatives: look like PII but are not --------------------------------


def order_id_12(rng: random.Random) -> str:
    return rng.choice("123456789") + _digits(rng, 11)


def utr(rng: random.Random) -> str:
    return rng.choice("123456789") + _digits(rng, 11)


def timestamp(rng: random.Random) -> str:
    stamp = f"2026{rng.randint(1, 12):02d}{rng.randint(1, 28):02d}{rng.randint(0, 23):02d}"
    stamp += f"{rng.randint(0, 59):02d}"
    return stamp + (f"{rng.randint(0, 59):02d}" if rng.random() < 0.5 else "")


def invoice(rng: random.Random) -> str:
    return f"INV-2026-{_digits(rng, 6)}"


def bad_pan(rng: random.Random) -> str:
    """PAN-shaped, but the 4th letter is not a valid holder type."""
    return (
        _letters(rng, 3)
        + rng.choice(INVALID_HOLDERS)
        + _letters(rng, 1)
        + _digits(rng, 4)
        + (_letters(rng, 1))
    )


def bad_aadhaar(rng: random.Random) -> str:
    """Aadhaar-shaped, but with a wrong check digit."""
    body = rng.choice("23456789") + _digits(rng, 10)
    good = int(verhoeff.check_digit(body))
    wrong = str((good + rng.randint(1, 9)) % 10)
    number = body + wrong
    return f"{number[:4]} {number[4:8]} {number[8:]}"


def order_id_10(rng: random.Random) -> str:
    """10 digits starting 6-9: the same shape as a mobile number."""
    return rng.choice("6789") + _digits(rng, 9)


def pnr(rng: random.Random) -> str:
    return rng.choice("123456789") + _digits(rng, 9)


def pincode(rng: random.Random) -> str:
    return rng.choice("12345678") + _digits(rng, 5)


def amount(rng: random.Random) -> str:
    value = rng.randint(100, 500000)
    return rng.choice((f"Rs. {value:,}", f"₹{value:,}", f"INR {value}"))


def tracking(rng: random.Random) -> str:
    return f"{_letters(rng, 2)}{_digits(rng, 9)}IN"


def card_last4(rng: random.Random) -> str:
    return f"XXXX XXXX XXXX {_digits(rng, 4)}"


def otp(rng: random.Random) -> str:
    return _digits(rng, 6)


def ticket(rng: random.Random) -> str:
    return str(rng.randint(10000, 99999))


def small_number(rng: random.Random) -> str:
    return str(rng.randint(10, 99999))
