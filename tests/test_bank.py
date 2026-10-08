import pytest

from kavach.detectors import BankAccountDetector
from kavach.types import EntityType


@pytest.fixture
def detector():
    return BankAccountDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "text,value",
    [
        ("My account number is 50100123456789", "50100123456789"),
        ("A/C No. 123456789 at HDFC", "123456789"),
        ("Acct: 123456789012345678", "123456789012345678"),
        ("account 50100 12345 6789", "50100 12345 6789"),
        ("account 5010-0123-4567", "5010-0123-4567"),
        ("NEFT to 30012345678, IFSC SBIN0001234", "30012345678"),
        ("mera khata number 001234567890 hai", "001234567890"),
        ("मेरा खाता संख्या 001234567890 है", "001234567890"),
        ("30012345678 is my savings account", "30012345678"),
    ],
)
def test_detects_with_context(detector, text, value):
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.BANK_ACCOUNT


@pytest.mark.parametrize(
    "text",
    [
        "Order 50100123456789 has shipped",  # no context
        "Invoice 123456789 dated today",
        "Accepted 123456789",
        "account 12345678",  # 8 digits
        "account 1234567890123456789",  # 19 digits
        "account +919876543210",  # phone with country code
        "account ABC123456789",  # glued to letters
        "account 123456789XYZ",
        "account 12-123456789",  # 2-digit group
        "account " + "x" * 60 + " 50100123456789",  # keyword too far away
        "account",
        "",
    ],
)
def test_rejects_without_context_or_wrong_shape(detector, text):
    assert found(detector, text) == []


def test_multiple_accounts(detector):
    text = "From a/c 30012345678 to a/c 50100123456789"
    assert found(detector, text) == ["30012345678", "50100123456789"]


def test_normalize(detector):
    assert detector.normalize("50100 12345-6789") == "50100123456789"
