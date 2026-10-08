import pytest
from synthetic import KITCHEN_SINK, PAN, UPI

from kavach import Kavach


@pytest.fixture
def session():
    s = Kavach().session()
    s.mask(f"PAN {PAN}, UPI {UPI}")
    return s


REPLY = "Refund for [PAN_1] goes to [UPI_1]. [Note: 2 days] Done."
EXPECTED = f"Refund for {PAN} goes to {UPI}. [Note: 2 days] Done."


def run(stream, chunks):
    return "".join(stream.feed(c) for c in chunks) + stream.flush()


def test_placeholder_split_across_chunks(session):
    stream = session.stream()
    first = stream.feed("The refund for [PA")
    assert first == "The refund for "
    second = stream.feed("N_1] is")
    assert second == f"{PAN} is"
    assert stream.feed(" being processed") == " being processed"
    assert stream.flush() == ""


def test_every_two_way_split(session):
    for i in range(len(REPLY) + 1):
        assert run(session.stream(), [REPLY[:i], REPLY[i:]]) == EXPECTED, i


def test_character_by_character(session):
    assert run(session.stream(), list(REPLY)) == EXPECTED


def test_never_emits_partial_placeholder(session):
    stream = session.stream()
    emitted = [stream.feed(ch) for ch in REPLY] + [stream.flush()]
    for piece in emitted:
        assert "[PAN" not in piece and "[UPI" not in piece


def test_plain_brackets_are_released(session):
    stream = session.stream()
    assert stream.feed("see [note]") == "see [note]"
    assert stream.feed(" and [1, 2]") == " and [1, 2]"


def test_long_bracket_text_is_released(session):
    stream = session.stream()
    out = stream.feed("[" + "a" * 40)
    assert out == "[" + "a" * 40


def test_newline_after_bracket_releases(session):
    stream = session.stream()
    assert stream.feed("[PA\n") == "[PA\n"


def test_flush_releases_unfinished_fragment(session):
    stream = session.stream()
    assert stream.feed("ends with [PAN_") == "ends with "
    assert stream.flush() == "[PAN_"


def test_unknown_placeholder_passes_through(session):
    assert run(session.stream(), ["[PAN", "_9] ok"]) == "[PAN_9] ok"


def test_tolerant_placeholder_split(session):
    assert run(session.stream(), ["[ pa", "n_1 ]"]) == PAN


def test_empty_stream(session):
    stream = session.stream()
    assert stream.feed("") == ""
    assert stream.flush() == ""


def test_full_round_trip_through_stream():
    s = Kavach().session()
    masked = s.mask(KITCHEN_SINK)
    chunks = [masked[i : i + 7] for i in range(0, len(masked), 7)]
    assert run(s.stream(), chunks) == KITCHEN_SINK


def test_repr_holds_no_text(session):
    stream = session.stream()
    stream.feed("secret [PA")
    assert "secret" not in repr(stream)
