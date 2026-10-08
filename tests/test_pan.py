import pytest

from kavach.detectors import PanDetector
from kavach.detectors.pan import HOLDER_TYPES
from kavach.types import EntityType

# Synthetic PAN. Note the plan's example ABCDE1234F is NOT a valid PAN:
# its 4th letter, D, is not a holder type.
VALID = "ABCPE1234F"


@pytest.fixture
def detector():
    return PanDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize("holder", list(HOLDER_TYPES))
def test_accepts_every_holder_type(detector, holder):
    pan = f"ABC{holder}E1234F"
    assert found(detector, f"PAN {pan}") == [pan]


@pytest.mark.parametrize("holder", sorted(set("ABCDEFGHIJKLMNOPQRSTUVWXYZ") - set(HOLDER_TYPES)))
def test_rejects_invalid_holder_type(detector, holder):
    assert found(detector, f"PAN ABC{holder}E1234F") == []


@pytest.mark.parametrize(
    "value",
    [VALID, "abcpe1234f", "AbCpE1234f", "ABCPE 1234 F", "ABCPE-1234-F", "ABCPE 1234F"],
)
def test_detects_formatting_variants(detector, value):
    text = f"My PAN is {value}, refund please"
    assert found(detector, text) == [value]


def test_detection_fields(detector):
    text = f"PAN: {VALID}"
    [d] = detector.detect(text)
    assert d.entity_type is EntityType.PAN
    assert (d.start, d.end) == (5, 15)
    assert d.detector == "pan"


def test_detects_hinglish_context(detector):
    assert found(detector, f"mera pan card number {VALID} hai") == [VALID]


def test_detects_multiple_and_repeated(detector):
    text = f"{VALID}, AAAPZ9876K and again {VALID}"
    assert found(detector, text) == [VALID, "AAAPZ9876K", VALID]


def test_detects_adjacent_to_punctuation(detector):
    assert found(detector, f"(PAN:{VALID}).") == [VALID]


@pytest.mark.parametrize(
    "text",
    [
        "27ABCPE1234F1Z5",  # PAN embedded in a GSTIN
        "X" + VALID,
        VALID + "G",
        VALID + "9",
        "ABCPE12345F",  # 5 digits
        "ABCPE123F",  # 3 digits
        "ABCP1234F",  # 4 letters
        "ABCPE  1234F",  # two spaces
        "ABCPE1234 5",  # ends in a digit
        "",
        "PASSWORD12",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


def test_normalize(detector):
    assert detector.normalize("abcpe-1234 f") == VALID
