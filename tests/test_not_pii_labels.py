"""Negative context: a label right before a number says it is not personal data."""

import pytest
from synthetic import AADHAAR

from kavach.context import has_not_pii_label
from kavach.engine import Engine
from kavach.types import EntityType

E = EntityType


def label_before(text: str, value: str) -> bool:
    return has_not_pii_label(text, text.index(value))


@pytest.mark.parametrize(
    "text",
    [
        "Order no. 9876543210",
        "order 9876543210",
        "ORDER ID: 9876543210",
        "my order no is 9876543210",
        "UTR 9876543210",
        "Txn ID - 9876543210",
        "Invoice #9876543210",
        "PNR 9876543210",
        "log entry 9876543210",
        "Log   entry 9876543210",
        "आपका ऑर्डर 9876543210",
        "Mera order 9876543210 abhi tak nahi aaya",
    ],
)
def test_labels_detected(text):
    assert label_before(text, "9876543210")


@pytest.mark.parametrize(
    "text",
    [
        "mobile 9876543210",
        "Order placed. Call me on 9876543210",  # label not directly before
        "OTP sent to 9876543210",
        "reorder 9876543210",  # "order" must be a whole word
        "border 9876543210",
        "9876543210",
    ],
)
def test_no_label(text):
    assert not label_before(text, "9876543210")


@pytest.fixture
def engine():
    return Engine()


def types(engine, text):
    return [d.entity_type for d in engine.analyze(text)]


@pytest.mark.parametrize(
    "text",
    [
        "Order no. 9876543210 cannot be cancelled",
        "Please call me back on 9876543210, my order no is 9123456780",
        "Refund to account number 30012345678, UTR 412345678901",
        f"Transaction {AADHAAR} successful",
    ],
)
def test_labelled_numbers_are_not_masked(engine, text):
    found = engine.analyze(text)
    for d in found:
        before = text[max(0, d.start - 12) : d.start].lower()
        assert not any(w in before for w in ("order", "utr", "transaction"))


def test_phone_with_label_dropped_but_real_phone_kept(engine):
    text = "Please call me back on 9876543210, my order no is 9123456780"
    assert [d.text_in(text) for d in engine.analyze(text)] == ["9876543210"]


def test_strong_context_survives_a_label(engine):
    # +91 prefix and phone context outweigh a nearby label.
    assert types(engine, "Order mobile +91 98765 43210") == [E.PHONE]


def test_phone_and_bank_context_resolves_to_phone(engine):
    text = "Please update my mobile number to 9876543210 on my account."
    assert types(engine, text) == [E.PHONE]


def test_bank_context_alone_resolves_to_bank(engine):
    assert types(engine, "A/c 9876543210") == [E.BANK_ACCOUNT]


def test_labels_do_not_affect_non_numeric_entities(engine):
    assert types(engine, "Order ABCPE1234F") == [E.PAN]
