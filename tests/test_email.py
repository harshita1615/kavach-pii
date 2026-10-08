import pytest

from kavach.detectors import EmailDetector
from kavach.types import EntityType


@pytest.fixture
def detector():
    return EmailDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "value",
    [
        "rahul@example.com",
        "rahul.sharma@example.co.in",
        "first.last+tag@mail.example.org",
        "RAHUL_99@EXAMPLE.IN",
        "a-b@my-domain.io",
    ],
)
def test_detects_valid(detector, value):
    text = f"Email me at {value} please"
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.EMAIL


def test_trailing_punctuation_and_brackets(detector):
    assert found(detector, "mail rahul@example.com.") == ["rahul@example.com"]
    assert found(detector, "<rahul@example.com>") == ["rahul@example.com"]
    assert found(detector, "(rahul@example.com),") == ["rahul@example.com"]
    assert found(detector, "mailto:rahul@example.com") == ["rahul@example.com"]


def test_multiple(detector):
    text = "a1@example.com; b2@example.in"
    assert found(detector, text) == ["a1@example.com", "b2@example.in"]


def test_hinglish_context(detector):
    assert found(detector, "meri email id rahul@example.com hai") == ["rahul@example.com"]


@pytest.mark.parametrize(
    "text",
    [
        "rahul@okaxis",  # UPI ID, no TLD
        "rahul@example",
        "rahul@.com",
        "@example.com",
        "rahul@example.c",  # 1-letter TLD
        "rahul@-example.com",
        "rahul@example.com-x",
        ".rahul@example.com",
        "",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


def test_long_input_does_not_hang(detector):
    text = "a" * 10_000 + "@" + "b" * 10_000
    assert found(detector, text) == []


def test_normalize(detector):
    assert detector.normalize("Rahul@Example.COM") == "rahul@example.com"
