import random

import pytest

from kavach.detectors import GstinDetector, PanDetector
from kavach.types import EntityType
from kavach.validators import gstin_checksum

_CHARSET = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"


def make_gstin(state: str = "27", pan: str = "ABCPE1234F", entity: str = "1") -> str:
    """Synthetic GSTIN with a correct check character."""
    body = f"{state}{pan}{entity}Z"
    return body + gstin_checksum.check_char(body)


VALID = make_gstin()


# --- checksum ---------------------------------------------------------------


def test_published_example():
    # Example GSTIN used throughout public GST documentation.
    assert gstin_checksum.check_char("27AAPFU0939F1Z") == "V"
    assert gstin_checksum.is_valid("27AAPFU0939F1ZV")


def test_checksum_round_trips_on_random_bodies():
    rng = random.Random(0)
    for _ in range(500):
        body = "".join(rng.choice(_CHARSET) for _ in range(14))
        assert gstin_checksum.is_valid(body + gstin_checksum.check_char(body))


def test_checksum_detects_every_single_character_error():
    for i in range(14):
        for ch in _CHARSET:
            if ch != VALID[i]:
                assert not gstin_checksum.is_valid(VALID[:i] + ch + VALID[i + 1 :])


def test_checksum_is_case_insensitive():
    assert gstin_checksum.is_valid(VALID.lower())


@pytest.mark.parametrize("bad", ["", "27ABCPE1234F1Z", "27ABCPE1234F1Z55", "27ABCPE1234F1Z#"])
def test_checksum_rejects_bad_input_without_echoing_it(bad):
    with pytest.raises(ValueError) as exc:
        gstin_checksum.is_valid(bad)
    if bad:
        assert bad not in str(exc.value)


# --- detector ---------------------------------------------------------------


@pytest.fixture
def detector():
    return GstinDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "value",
    [VALID, VALID.lower(), make_gstin("07"), make_gstin("38"), make_gstin("97"), make_gstin("99")],
)
def test_detects_valid(detector, value):
    text = f"GSTIN: {value}."
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.GSTIN


def test_detects_entity_numbers_and_letters(detector):
    for entity in ("1", "9", "A", "Z"):
        assert found(detector, make_gstin(entity=entity)) == [make_gstin(entity=entity)]


def test_hinglish_context(detector):
    assert found(detector, f"hamara gst number {VALID} hai") == [VALID]


def test_pan_detector_ignores_pan_inside_gstin():
    assert PanDetector().detect(f"GSTIN {VALID}") == []


@pytest.mark.parametrize(
    "text",
    [
        VALID[:-1] + ("A" if VALID[-1] != "A" else "B"),  # wrong check character
        make_gstin("00"),  # invalid state code
        make_gstin("39"),
        make_gstin("96"),
        make_gstin(entity="0"),  # entity number cannot be 0
        make_gstin(pan="ABCDE1234F"),  # invalid PAN holder type
        VALID[:13] + "Y" + VALID[14],  # 14th character must be Z
        "X" + VALID,
        VALID + "1",
        VALID[:-1],
        "",
    ],
)
def test_rejects_invalid(detector, text):
    assert found(detector, text) == []


def test_normalize(detector):
    assert detector.normalize(VALID.lower()) == VALID
