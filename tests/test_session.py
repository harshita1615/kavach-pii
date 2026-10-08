import time

import pytest
from synthetic import (
    AADHAAR,
    AADHAAR_SPACED,
    BANK,
    EMAIL,
    GSTIN,
    IFSC,
    KITCHEN_SINK,
    PAN,
    PAN_2,
    PHONE,
    UPI,
)

from kavach import SYSTEM_PROMPT, Kavach

ALL_VALUES = (AADHAAR_SPACED, PAN, UPI, BANK, IFSC, PHONE, EMAIL, GSTIN)


@pytest.fixture
def session():
    return Kavach().session()


# --- mask --------------------------------------------------------------------


def test_masks_with_typed_placeholders(session):
    assert session.mask(f"My PAN is {PAN}, refund to {UPI}") == (
        "My PAN is [PAN_1], refund to [UPI_1]"
    )


def test_kitchen_sink_leaves_no_value_behind(session):
    masked = session.mask(KITCHEN_SINK)
    for value in ALL_VALUES:
        assert value not in masked
    assert "[AADHAAR_1]" in masked
    assert "[GSTIN_1]" in masked


def test_same_value_same_placeholder(session):
    assert session.mask(f"{PAN}. Verify {PAN}.") == "[PAN_1]. Verify [PAN_1]."


def test_different_values_numbered(session):
    assert session.mask(f"{PAN} and {PAN_2}") == "[PAN_1] and [PAN_2]"


def test_formatting_variants_share_placeholder(session):
    text = f"{AADHAAR_SPACED} aka {AADHAAR}; pan {PAN} aka {PAN.lower()}"
    assert session.mask(text) == "[AADHAAR_1] aka [AADHAAR_1]; pan [PAN_1] aka [PAN_1]"


def test_mapping_persists_across_messages(session):
    assert session.mask(f"PAN {PAN}") == "PAN [PAN_1]"
    assert session.mask(f"new PAN {PAN_2}, old PAN {PAN}") == "new PAN [PAN_2], old PAN [PAN_1]"


def test_sessions_are_independent():
    k = Kavach()
    s1, s2 = k.session(), k.session()
    s1.mask(f"{PAN} {PAN_2}")
    assert s2.mask(PAN_2) == "[PAN_1]"
    assert s2.unmask("[PAN_2]") == "[PAN_2]"


def test_existing_placeholder_text_is_not_reused(session):
    masked = session.mask(f"Earlier you saw [pan_1]; my PAN is {PAN}")
    assert masked == "Earlier you saw [pan_1]; my PAN is [PAN_2]"
    assert session.unmask(masked) == f"Earlier you saw [pan_1]; my PAN is {PAN}"


def test_empty_and_clean_text(session):
    assert session.mask("") == ""
    assert session.mask("hello world") == "hello world"


# --- unmask ------------------------------------------------------------------


def test_round_trip_kitchen_sink(session):
    assert session.unmask(session.mask(KITCHEN_SINK)) == KITCHEN_SINK


def test_llm_reply_restored(session):
    session.mask(f"Please check the refund for PAN {PAN}.")
    reply = "The refund associated with [PAN_1] is being processed."
    assert session.unmask(reply) == f"The refund associated with {PAN} is being processed."


def test_unmask_returns_first_seen_form(session):
    session.mask(f"{AADHAAR_SPACED} then {AADHAAR}")
    assert session.unmask("[AADHAAR_1]") == AADHAAR_SPACED


@pytest.mark.parametrize("variant", ["[pan_1]", "[ PAN_1 ]", "[PAN _ 1]", "[Pan_01]"])
def test_unmask_tolerates_small_llm_edits(session, variant):
    session.mask(PAN)
    assert session.unmask(f"ok {variant}") == f"ok {PAN}"


@pytest.mark.parametrize(
    "text",
    ["[PAN_9]", "[PAN_]", "[PAN 1]", "PAN_1", "[PAN_1", "PAN_1]", "[PASSPORT_1]", "[]"],
)
def test_unknown_or_malformed_placeholders_left_alone(session, text):
    session.mask(PAN)
    assert session.unmask(text) == text


def test_unmask_without_mask(session):
    assert session.unmask("[PAN_1]") == "[PAN_1]"


def test_clear_forgets_everything(session):
    session.mask(PAN)
    session.clear()
    assert session.unmask("[PAN_1]") == "[PAN_1]"
    assert session.counts == {}
    assert session.mask(PAN_2) == "[PAN_1]"


# --- modes -------------------------------------------------------------------


def test_redact_mode_cannot_be_reversed():
    session = Kavach(mode="redact").session()
    masked = session.mask(f"PAN {PAN} and {PAN_2}")
    assert masked == "PAN [PAN_1] and [PAN_2]"
    assert session.unmask(masked) == masked


def test_kavach_redact_shortcut():
    k = Kavach()
    assert k.redact(f"PAN {PAN}") == "PAN [PAN_1]"


def test_scan_mode_leaves_text_and_counts():
    session = Kavach(mode="scan").session()
    assert session.mask(KITCHEN_SINK) == KITCHEN_SINK
    assert session.counts["PAN"] == 1
    assert sum(session.counts.values()) == 8


def test_invalid_mode():
    with pytest.raises(ValueError):
        Kavach(mode="encrypt")


# --- audit and privacy -------------------------------------------------------


def test_counts_are_types_and_numbers_only(session):
    session.mask(f"{PAN} {PAN} {UPI}")
    assert session.counts == {"PAN": 2, "UPI": 1}


def test_repr_and_str_hold_no_values(session):
    session.mask(KITCHEN_SINK)
    for text in (repr(session), str(session), repr(Kavach())):
        for value in ALL_VALUES:
            assert value not in text


def test_scan_returns_positions_types_and_scores():
    text = f"PAN {PAN}"
    [d] = Kavach().scan(text)
    assert (d.entity_type.value, d.start, d.end) == ("PAN", 4, 14)
    assert 0 < d.score <= 1
    assert d.text_in(text) == PAN


def test_system_prompt_mentions_placeholders():
    assert "[PAN_1]" in SYSTEM_PROMPT


def test_very_long_input_is_fast(session):
    text = ("lorem ipsum dolor sit amet 12345 " * 3000) + KITCHEN_SINK
    start = time.perf_counter()
    masked = session.mask(text)
    assert time.perf_counter() - start < 2.0
    assert session.unmask(masked) == text
