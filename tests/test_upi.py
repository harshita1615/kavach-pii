import pytest

from kavach.detectors import UpiDetector
from kavach.detectors.upi import KNOWN_HANDLE_SCORE, UNKNOWN_HANDLE_SCORE
from kavach.types import EntityType


@pytest.fixture
def detector():
    return UpiDetector()


def found(detector, text):
    return [d.text_in(text) for d in detector.detect(text)]


@pytest.mark.parametrize(
    "value",
    [
        "rahul@okaxis",
        "rahul.sharma99@ybl",
        "rahul_s-1@oksbi",
        "RAHUL@OKHDFCBANK",
        "9876543210@paytm",
        "priya@upi",
    ],
)
def test_detects_known_handles(detector, value):
    text = f"Refund to {value} please"
    [d] = detector.detect(text)
    assert d.text_in(text) == value
    assert d.entity_type is EntityType.UPI
    assert d.score == KNOWN_HANDLE_SCORE


def test_unknown_handle_scores_low(detector):
    [d] = detector.detect("pay rahul@somenewbank")
    assert d.score == UNKNOWN_HANDLE_SCORE


def test_trailing_sentence_punctuation(detector):
    assert found(detector, "Pay rahul@okaxis.") == ["rahul@okaxis"]
    assert found(detector, "(rahul@okaxis)") == ["rahul@okaxis"]
    assert found(detector, "UPI:rahul@okaxis, thanks") == ["rahul@okaxis"]


def test_hinglish_context(detector):
    assert found(detector, "mera upi id rahul@ybl hai") == ["rahul@ybl"]


def test_multiple(detector):
    text = "rahul@okaxis or priya@ybl or rahul@okaxis"
    assert found(detector, text) == ["rahul@okaxis", "priya@ybl", "rahul@okaxis"]


@pytest.mark.parametrize(
    "text",
    [
        "rahul@gmail.com",  # email
        "rahul@okaxis.com",  # email with a UPI-like domain
        "rahul@okaxis-bank.in",
        "@okaxis",  # no username
        "r@okaxis",  # one-character username
        "rahul@okaxis@foo",
        "rahul@1abc",  # handle must start with a letter
        ".rahul@okaxis",  # continuation of a longer token
        "",
        "no handle here",
    ],
)
def test_rejects_look_alikes(detector, text):
    assert found(detector, text) == []


def test_normalize(detector):
    assert detector.normalize("Rahul@OKAXIS") == "rahul@okaxis"
