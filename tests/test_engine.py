from itertools import pairwise

import pytest
from synthetic import AADHAAR, BANK, EMAIL, GSTIN, IFSC, KITCHEN_SINK, PAN, PHONE, UPI

from kavach.engine import CONTEXT_BOOST, Engine, parse_entities, resolve_overlaps
from kavach.types import Detection, EntityType

E = EntityType


def types_and_values(engine, text):
    return [(d.entity_type, d.text_in(text)) for d in engine.analyze(text)]


@pytest.fixture
def engine():
    return Engine()


def test_kitchen_sink_finds_every_entity_once(engine):
    found = types_and_values(engine, KITCHEN_SINK)
    assert [t for t, _ in found] == [
        E.AADHAAR,
        E.PAN,
        E.UPI,
        E.BANK_ACCOUNT,
        E.IFSC,
        E.PHONE,
        E.EMAIL,
        E.GSTIN,
    ]
    values = [v for _, v in found]
    for value in (PAN, UPI, BANK, IFSC, PHONE, EMAIL, GSTIN):
        assert value in values


def test_results_never_overlap(engine):
    detections = engine.analyze(KITCHEN_SINK)
    for a, b in pairwise(detections):
        assert a.end <= b.start


def test_empty_text(engine):
    assert engine.analyze("") == []
    assert engine.analyze("nothing sensitive here") == []


# --- overlap resolution on real text ---------------------------------------


def test_account_context_beats_phone(engine):
    assert types_and_values(engine, "A/c 9876543210") == [(E.BANK_ACCOUNT, "9876543210")]


def test_phone_context_without_bank_context(engine):
    assert types_and_values(engine, "mobile 9876543210") == [(E.PHONE, "9876543210")]


def test_upi_beats_phone_digits_inside_it(engine):
    text = "a/c holder, pay 9876543210@paytm"
    assert types_and_values(engine, text) == [(E.UPI, "9876543210@paytm")]


def test_email_beats_phone_digits_inside_it(engine):
    text = "write to 9876543210@example.com"
    assert types_and_values(engine, text) == [(E.EMAIL, "9876543210@example.com")]


def test_gstin_not_split_into_pan(engine):
    assert types_and_values(engine, f"GST {GSTIN}") == [(E.GSTIN, GSTIN)]


def test_aadhaar_with_context(engine):
    [d] = engine.analyze(f"aadhaar {AADHAAR}")
    assert d.entity_type is E.AADHAAR
    assert d.score == 1.0  # 0.85 + boost, capped


# --- context and threshold -------------------------------------------------


def test_context_boost_applied(engine):
    [plain] = engine.analyze("9876543210")
    [boosted] = engine.analyze("mobile 9876543210")
    assert boosted.score == pytest.approx(plain.score + CONTEXT_BOOST)


def test_unknown_upi_handle_needs_context(engine):
    assert engine.analyze("send to rahul@newbank") == []
    assert types_and_values(engine, "upi id rahul@newbank") == [(E.UPI, "rahul@newbank")]


def test_threshold_filters():
    assert Engine(threshold=0.95).analyze("9876543210") == []
    assert Engine(threshold=0.0).analyze("9876543210") != []


@pytest.mark.parametrize("threshold", [-0.1, 1.5])
def test_invalid_threshold(threshold):
    with pytest.raises(ValueError):
        Engine(threshold=threshold)


# --- entity selection --------------------------------------------------------


def test_entity_filter():
    engine = Engine(entities=["PAN"])
    assert [t for t, _ in types_and_values(engine, KITCHEN_SINK)] == [E.PAN]


def test_entities_accept_lowercase_and_enum():
    assert parse_entities(["pan", E.UPI]) == {E.PAN, E.UPI}
    assert parse_entities(None) == set(E)


def test_unknown_entity_raises():
    with pytest.raises(ValueError, match="AADHAAR"):
        parse_entities(["PASSPORT"])


def test_disabled_entity_does_not_block_others():
    # With PHONE disabled, the account context still yields a bank account.
    engine = Engine(entities=["BANK_ACCOUNT"])
    assert types_and_values(engine, "a/c 9876543210") == [(E.BANK_ACCOUNT, "9876543210")]


# --- resolve_overlaps unit tests ---------------------------------------------


def det(entity_type, start, end, score):
    return Detection(entity_type, start, end, score, "test")


def test_higher_score_wins():
    a, b = det(E.PHONE, 0, 10, 0.9), det(E.BANK_ACCOUNT, 0, 10, 0.7)
    assert resolve_overlaps([b, a]) == [a]


def test_equal_score_longer_wins():
    short, long_ = det(E.PHONE, 0, 10, 0.9), det(E.UPI, 0, 16, 0.9)
    assert resolve_overlaps([short, long_]) == [long_]


def test_equal_score_and_length_more_specific_wins():
    aadhaar, bank = det(E.AADHAAR, 0, 12, 0.9), det(E.BANK_ACCOUNT, 0, 12, 0.9)
    assert resolve_overlaps([bank, aadhaar]) == [aadhaar]


def test_partial_overlap_drops_loser():
    a, b = det(E.PAN, 0, 10, 0.9), det(E.PHONE, 5, 15, 0.6)
    assert resolve_overlaps([a, b]) == [a]


def test_adjacent_and_disjoint_are_kept_in_order():
    a, b, c = det(E.PAN, 0, 10, 0.5), det(E.PHONE, 10, 20, 0.9), det(E.UPI, 30, 40, 0.7)
    assert resolve_overlaps([c, b, a]) == [a, b, c]


def test_resolve_empty():
    assert resolve_overlaps([]) == []


def test_ifsc_found_alone(engine):
    assert types_and_values(engine, IFSC) == [(E.IFSC, IFSC)]


def test_email_found_alone(engine):
    assert types_and_values(engine, EMAIL) == [(E.EMAIL, EMAIL)]


def test_pan_found_alone(engine):
    assert types_and_values(engine, PAN) == [(E.PAN, PAN)]
