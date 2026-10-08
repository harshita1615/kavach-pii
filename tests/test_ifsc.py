import pytest

from kavach.detectors import IfscDetector
from kavach.detectors.ifsc import KNOWN_BANK_SCORE, UNKNOWN_BANK_SCORE
from kavach.types import EntityType


@pytest.fixture
def detector():
    return IfscDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize("value", ["SBIN0001234", "HDFC0ABC123", "UTIB0000001", "sbin0001234"])
def test_detects_known_banks(detector, value):
    text = f"IFSC: {value}."
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.IFSC
    assert d.score == KNOWN_BANK_SCORE


def test_unknown_bank_code_scores_lower(detector):
    [d] = detector.detect("code ABCD0123456")
    assert d.score == UNKNOWN_BANK_SCORE


def test_with_account_and_hinglish(detector):
    text = "khata 30012345678, ifsc SBIN0001234 hai"
    assert found(detector, text) == ["SBIN0001234"]


@pytest.mark.parametrize(
    "text",
    [
        "SBIN1001234",  # 5th character must be 0
        "SBIN000123",  # 10 characters
        "SBIN00012345",  # 12 characters
        "XSBIN0001234",
        "1SBIN0001234",
        "SBIN0001234X",
        "SB1N0001234",  # digit in bank code
        "SBIN 0001234",
        "",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


def test_normalize(detector):
    assert detector.normalize("sbin0001234") == "SBIN0001234"
