import pytest

from kavach.detectors import AadhaarDetector
from kavach.types import EntityType
from kavach.validators import verhoeff

# Synthetic numbers built with a correct check digit. Never use real Aadhaar numbers.
VALID = "23456789012" + verhoeff.check_digit("23456789012")
VALID_2 = "98765432109" + verhoeff.check_digit("98765432109")
BAD_CHECK = VALID[:-1] + str((int(VALID[-1]) + 1) % 10)


def spaced(n: str, sep: str = " ") -> str:
    return sep.join([n[0:4], n[4:8], n[8:12]])


@pytest.fixture
def detector():
    return AadhaarDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "value",
    [
        VALID,
        spaced(VALID),
        spaced(VALID, "-"),
        spaced(VALID, " - "),
        spaced(VALID, "  "),
        spaced(VALID, "\n"),
        spaced(VALID, "\r\n"),
    ],
)
def test_detects_formatting_variants(detector, value):
    text = f"My aadhaar is {value}, please update."
    assert found(detector, text) == [value]


def test_detection_fields(detector):
    text = f"aadhaar: {VALID}"
    [d] = detector.detect(text)
    assert d.entity_type is EntityType.AADHAAR
    assert (d.start, d.end) == (9, 21)
    assert d.detector == "aadhaar"
    assert 0 < d.score <= 1


def test_detects_at_start_and_end_of_text(detector):
    assert found(detector, VALID) == [VALID]
    assert found(detector, f"{VALID} is mine") == [VALID]


def test_detects_hinglish_context(detector):
    text = f"mera aadhaar {spaced(VALID)} hai"
    assert found(detector, text) == [spaced(VALID)]


def test_detects_multiple_numbers(detector):
    text = f"Mine is {VALID} and my mother's is {spaced(VALID_2)}."
    assert found(detector, text) == [VALID, spaced(VALID_2)]


def test_detects_number_adjacent_to_punctuation(detector):
    assert found(detector, f"({VALID})") == [VALID]
    assert found(detector, f"UID:{VALID}.") == [VALID]


def test_rejects_wrong_check_digit(detector):
    assert found(detector, f"aadhaar {BAD_CHECK}") == []


@pytest.mark.parametrize("first", ["0", "1"])
def test_rejects_numbers_starting_with_0_or_1(detector, first):
    body = first + VALID[1:11]
    number = body + verhoeff.check_digit(body)
    assert found(detector, f"aadhaar {number}") == []


@pytest.mark.parametrize(
    "text",
    [
        "aadhaar " + VALID[:11],  # 11 digits
        "order " + VALID + "7",  # 13 digits
        "order 7" + VALID,  # 13 digits
        "invoice INV" + VALID,  # glued to letters
        "ref " + VALID + "AB",
        "card " + spaced(VALID) + " 4321",  # first 12 of a 16-digit card
        "card 4321 " + spaced(VALID),  # last 12 of a 16-digit card
        "card 4321-" + spaced(VALID, "-"),
        "",
        "no numbers here",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


def test_does_not_join_numbers_across_blank_lines(detector):
    text = f"{VALID[:4]}\n\n{VALID[4:8]}\n\n{VALID[8:]}"
    assert found(detector, text) == []


def test_normalize_strips_formatting(detector):
    assert detector.normalize(spaced(VALID, " - ")) == VALID
    assert detector.normalize(spaced(VALID, "\n")) == VALID


def test_long_input(detector):
    text = ("filler text " * 5000) + spaced(VALID) + (" more" * 5000)
    assert found(detector, text) == [spaced(VALID)]
