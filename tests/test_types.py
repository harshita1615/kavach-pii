import dataclasses

import pytest

from kavach import Detection, EntityType


def test_detection_holds_no_raw_text():
    fields = {f.name for f in dataclasses.fields(Detection)}
    assert fields == {"entity_type", "start", "end", "score", "detector"}


def test_repr_does_not_contain_value():
    text = "PAN ABCPE1234F"
    d = Detection(EntityType.PAN, 4, 14, 0.85, "pan")
    assert "ABCPE1234F" not in repr(d)
    assert d.text_in(text) == "ABCPE1234F"


def test_detection_is_immutable():
    d = Detection(EntityType.PAN, 0, 10, 0.85, "pan")
    with pytest.raises(dataclasses.FrozenInstanceError):
        d.score = 1.0  # type: ignore[misc]


@pytest.mark.parametrize("start,end", [(-1, 3), (5, 5), (6, 5)])
def test_rejects_invalid_span(start, end):
    with pytest.raises(ValueError):
        Detection(EntityType.PAN, start, end, 0.5, "pan")


@pytest.mark.parametrize("score", [-0.1, 1.1])
def test_rejects_invalid_score(score):
    with pytest.raises(ValueError):
        Detection(EntityType.PAN, 0, 1, score, "pan")


def test_entity_type_str_is_placeholder_prefix():
    assert str(EntityType.BANK_ACCOUNT) == "BANK_ACCOUNT"
    assert EntityType("PHONE") is EntityType.PHONE
