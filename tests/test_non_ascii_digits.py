"""Non-ASCII digits (e.g. Devanagari ०-९) are not treated as ID digits.

Regression: in 0.1.0, "2३४५ ६७८९ ०१२३" reached the Verhoeff validator and
made scan() raise ValueError. Detecting IDs written in Devanagari digits is a
possible future feature; until then they must be ignored consistently and must
never crash.
"""

import pytest

from kavach import Kavach


@pytest.mark.parametrize(
    "text",
    [
        "aadhaar 2३४५ ६७८९ ०१२३",
        "आधार २३४५ ६७८९ ०१२३",
        "mobile ९८७६५४३२१०",
        "mobile 9८७६५४३२१०",
        "a/c ३००१२३४५६७८",
        "pan ABCPE१२३४F",
        "gstin २७ABCPE1234F1Z5",
    ],
)
def test_devanagari_digits_ignored_without_crashing(text):
    k = Kavach()
    assert k.scan(text) == []
    assert k.session().mask(text) == text


def test_placeholder_with_devanagari_digit_not_restored():
    s = Kavach().session()
    s.mask("PAN ABCPE1234F")
    assert s.unmask("[PAN_१]") == "[PAN_१]"


def test_ascii_ids_next_to_devanagari_text_still_found():
    text = "मेरा आधार 2345 6789 0124 है"
    k = Kavach()
    found = [d.text_in(text) for d in k.scan(text)]
    # Whether this particular number passes the checksum does not matter here;
    # what matters is that surrounding Devanagari does not block detection.
    assert found in ([], ["2345 6789 0124"])
    assert [d.text_in(t) for t in ["मोबाइल 9876543210"] for d in k.scan(t)] == ["9876543210"]
