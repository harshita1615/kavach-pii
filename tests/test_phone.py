import pytest

from kavach.detectors import PhoneDetector
from kavach.detectors.phone import BASE_SCORE, INTERNATIONAL_PREFIX_SCORE
from kavach.types import EntityType


@pytest.fixture
def detector():
    return PhoneDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "value",
    [
        "+919876543210",
        "+91 98765 43210",
        "+91-9876543210",
        "+91 987-654-3210",
        "0091 9876543210",
        "(+91) 98765 43210",
    ],
)
def test_international_prefix_scores_high(detector, value):
    text = f"Call me on {value} today"
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.PHONE
    assert d.score == INTERNATIONAL_PREFIX_SCORE


@pytest.mark.parametrize(
    "value",
    ["9876543210", "6123456789", "98765 43210", "987-654-3210", "09876543210", "919876543210"],
)
def test_domestic_formats(detector, value):
    text = f"mobile: {value}"
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.score == BASE_SCORE


def test_hinglish_context(detector):
    assert found(detector, "mera number 9876543210 hai") == ["9876543210"]


def test_multiple(detector):
    text = "9876543210, +91 91234 56789"
    assert found(detector, text) == ["9876543210", "+91 91234 56789"]


@pytest.mark.parametrize(
    "text",
    [
        "5876543210",  # starts with 5
        "987654321",  # 9 digits
        "98765432101",  # 11 digits
        "98765 432101",
        "INV9876543210",
        "9876543210ABC",
        "+9198765432101",
        "",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


@pytest.mark.parametrize("value", ["+91 98765 43210", "09876543210", "919876543210"])
def test_normalize_to_ten_digits(detector, value):
    assert detector.normalize(value) == "9876543210"
